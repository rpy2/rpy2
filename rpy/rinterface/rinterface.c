/* A python-R interface*/

/* 
 * This is an attempt at cleaning up RPy, while adding features
 * at the same time. In other words, this can be seen as a rewrite 
 * of RPy.
 *
 * The authors for the original RPy code, as well as
 * belopolsky for his contributed code, are listed here as authors;
 * parts of this code is (sometimes shamelessly but with great 
 * respect for the work) "inspired/copied" from their contributions. 
 * 
 * FIXME: get everyone's name in the license block
 *
 * Laurent Gautier - 2008
 */

/*
 ***** BEGIN LICENSE BLOCK *****
 * Version: MPL 1.1/GPL 2.0/LGPL 2.1
 *
 * The contents of this file are subject to the Mozilla Public License Version
 * 1.1 (the "License"); you may not use this file except in compliance with
 * the License. You may obtain a copy of the License at
 * http://www.mozilla.org/MPL/
 *
 * Software distributed under the License is distributed on an "AS IS" basis,
 * WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
 * for the specific language governing rights and limitations under the
 * License.
 *
 * original RPy Authors: Walter Moreira.
 *                       Gregory R. Warnes <greg@warnes.net> (Maintainer)
 *
 * Original code for wrapping R's C-level SEXPs:   Alexander Belopolsky
 * (this code borrows a *lot* from it)
 *
 * This code: Laurent Gautier
 *
 *
 * Alternatively, the contents of this file may be used under the terms of
 * either the GNU General Public License Version 2 or later (the "GPL"), or
 * the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
 * in which case the provisions of the GPL or the LGPL are applicable instead
 * of those above. If you wish to allow use of your version of this file only
 * under the terms of either the GPL or the LGPL, and not to allow others to
 * use your version of this file under the terms of the MPL, indicate your
 * decision by deleting the provisions above and replace them with the notice
 * and other provisions required by the GPL or the LGPL. If you do not delete
 * the provisions above, a recipient may use your version of this file under
 * the terms of any one of the MPL, the GPL or the LGPL.
 *
 * ***** END LICENSE BLOCK ***** */

#include "Python.h"


#include <R.h>
#include <Rinternals.h>
#include <Rdefines.h>

#define R_INTERFACE_PTRS
#include <Rinterface.h>
#include <R_ext/Complex.h>
#include <Rembedded.h>

/* FIXME: consider the use of parsing */
/* #include <R_ext/Parse.h> */
#include <R_ext/Rdynload.h>

#include <signal.h>

#include "rinterface.h"
#include "array.h"
#include "r_utils.h"

//#define RPY_VERBOSE

/* Back-compatibility with Python 2.4 */
#if (PY_VERSION_HEX < 0x02050000)
typedef int Py_ssize_t;
typedef inquiry lenfunc;
typedef intargfunc ssizeargfunc;
typedef intobjargproc ssizeobjargproc;
#endif

/* A sequence that holds options to initialize R */
static PyObject *initOptions;

/* Helper variables to quickly resolve SEXP types.
 * The first variable gives the highest possible
 * SEXP type.
 * The second in an array of strings giving either
 * the SEXP name (INTSXP, REALSXP, etc...), or a NULL
 * if there is no such valid SEXP.
 */
static const int maxValidSexpType = 99;
static char **validSexpType;

static SEXP GetErrMessage_SEXP;
static PyObject *RPyExc_RuntimeError = NULL;

//FIXME: see the details of interruption
/* Indicates whether the R interpreter was interrupted by a SIGINT */
int interrupted = 0;
/* Abort the current R computation due to a SIGINT */
static void
interrupt_R(int signum)
{
  interrupted = 1;
  error("Interrupted");
}

/* Helper variable to store whether the embedded R is initialized
 * or not. 
 */
static PyObject *embeddedR_isInitialized;

/* The Python original SIGINT handler */
PyOS_sighandler_t python_sigint;

PyDoc_STRVAR(module_doc,
	     "Low-level functions to interface with R.\n\
 One should mostly consider calling the functions defined here when\
 writing a higher level interface between python and R.\
 Check the documentation for the module this is bundled into if\
 you only wish to have an off-the-shelf interface with R.\
\n\
");


static PySexpObject *globalEnv;
static PySexpObject *baseNameSpaceEnv;
static PySexpObject *na_string;

/* early definition of functions */
static PySexpObject* newPySexpObject(const SEXP sexp);
static SEXP newSEXP(PyObject *object, const int rType);


/* --- set output from the R console ---*/


static PyObject* writeConsoleCallback = NULL;

static PyObject* EmbeddedR_setWriteConsole(PyObject *self,
					   PyObject *args)
{
  
  PyObject *result = NULL;
  PyObject *function;
  
  if ( PyArg_ParseTuple(args, "O:console", 
			&function)) {
    
    if (!PyCallable_Check(function)) {
      PyErr_SetString(PyExc_TypeError, "parameter must be callable");
      return NULL;
    }

    Py_XDECREF(writeConsoleCallback);
    Py_XINCREF(function);
    writeConsoleCallback = function;
    Py_INCREF(Py_None);
    result = Py_None;
  } else {
    PyErr_SetString(PyExc_TypeError, "The parameter should be a callable.");
  }
  return result;
  
}

PyDoc_STRVAR(EmbeddedR_setWriteConsole_doc,
            "setWriteConsoleEmbeddedR()\n\
            \n\
            Set the R console output.");



static void
EmbeddedR_WriteConsole(char *buf, int len)
{
  PyOS_sighandler_t old_int;
  PyObject *arglist;
  PyObject *result;

  /* It is necessary to restore the Python handler when using a Python
     function for I/O. */
  old_int = PyOS_getsig(SIGINT);
  PyOS_setsig(SIGINT, python_sigint);
  arglist = Py_BuildValue("(s)", buf);
  if (! arglist) {
    PyErr_NoMemory();
    signal(SIGINT, old_int);
    //return NULL;
  }

  if (writeConsoleCallback == NULL) {
    return;
  }

  result = PyEval_CallObject(writeConsoleCallback, arglist);

  Py_DECREF(arglist);
  signal(SIGINT, old_int);
  
  if (result == NULL) {
    return;
  }

  Py_DECREF(result);
  
}


/* --- Initialize and terminate an embedded R --- */
/* Should having multiple threads of R become possible, 
 * useful routines could appear here...
 */
static PyObject* EmbeddedR_init(PyObject *self) 
{

  if (PyObject_IsTrue(embeddedR_isInitialized)) {
    PyErr_Format(PyExc_RuntimeError, "R can only be initialized once.");
    return NULL;
  }

  const Py_ssize_t n_args = PySequence_Size(initOptions);
  char *options[n_args];

  PyObject *opt_string;
  Py_ssize_t ii;
  for (ii = 0; ii < n_args; ii++) {
    opt_string = PyList_GetItem(initOptions, ii);
    options[ii] = PyString_AsString(opt_string);
  }


  /* int status = Rf_initEmbeddedR(n_args, options);*/
  int status = 1;
  Rf_initialize_R(n_args, options);
  R_Interactive = TRUE;
  setup_Rmainloop();

  Py_XDECREF(embeddedR_isInitialized);
  embeddedR_isInitialized = Py_True;
  Py_INCREF(Py_True);

  #ifdef R_INTERFACE_PTRS
  /* Redirect R console output */
  ptr_R_WriteConsole = EmbeddedR_WriteConsole;
  R_Outputfile = NULL;
  R_Consolefile = NULL;
  #endif

  RPY_SEXP(globalEnv) = R_GlobalEnv;
  RPY_SEXP(baseNameSpaceEnv) = R_BaseNamespace;
  RPY_SEXP(na_string) = NA_STRING;

  GetErrMessage_SEXP = findVar(install("geterrmessage"), 
			       R_BaseNamespace);

  PyObject *res = PyInt_FromLong(status);

#ifdef RPY_VERBOSE
  printf("R initialized - status: %i\n", status);
#endif

  return res;
}
PyDoc_STRVAR(EmbeddedR_init_doc,
	     "initEmbeddedR()\n\
	     \n\
	     Initialize an embedded R.");


static PyObject* EmbeddedR_end(PyObject *self, Py_ssize_t fatal)
{
  //FIXME: Have a reference count for R objects known to Python.
  //ending R will not be possible until all such objects are already
  //deallocated in Python ?
  //other possibility would be to have a fallback for "unreachable" objects ?
  //FIXME: rpy has something to terminate R. Check the details of what they are. 
  /* taken from the tests/Embedded/shutdown.c in the R source tree */

  R_dot_Last();           
  R_RunExitFinalizers();  
  //CleanEd();              
  Rf_KillAllDevices();
  
  //R_CleanTempDir();
  //PrintWarnings();
  R_gc();
  /* */

  Rf_endEmbeddedR((int)fatal);
  RPY_SEXP(globalEnv) = R_EmptyEnv;
  RPY_SEXP(baseNameSpaceEnv) = R_EmptyEnv;
  GetErrMessage_SEXP = R_NilValue; 

  //FIXME: Is it possible to reinitialize R later ?
  //Py_XDECREF(embeddedR_isInitialized);
  //embeddedR_isInitialized = Py_False;
  //Py_INCREF(Py_False);

  Py_RETURN_NONE;
}
PyDoc_STRVAR(EmbeddedR_end_doc,
	     "endEmbeddedR()\n\
	     \n\
	     Terminate an embedded R.");




static void
EmbeddedR_exception_from_errmessage(void)
{
  SEXP expr, res;
  //PROTECT(GetErrMessage_SEXP);
  PROTECT(expr = allocVector(LANGSXP, 1));
  SETCAR(expr, GetErrMessage_SEXP);
  PROTECT(res = Rf_eval(expr, R_GlobalEnv));
  char *message = CHARACTER_VALUE(res);
  UNPROTECT(2);
  PyErr_SetString(RPyExc_RuntimeError, message);
}




/*
 * Access to R objects through Python objects
 */

static void
Sexp_clear(PySexpObject *self)
{
  RPY_DECREF(self);
#ifdef RPY_VERBOSE
  printf("Python:%p / R:%p -- sexp count is %i\n", 
	 self, RPY_SEXP(self), RPY_COUNT(self));
#endif

  if ((RPY_COUNT(self) == 0) && RPY_SEXP(self)) {
#ifdef RPY_VERBOSE
    printf("freeing SEXP resources...\n");
#endif 

    if (RPY_SEXP(self) != R_NilValue) {
      R_ReleaseObject(RPY_SEXP(self));
    }
    free(self->sObj);
    ////self->ob_type->tp_free((PyObject*)self);
#ifdef RPY_VERBOSE
    printf("done.\n");
#endif 
  }

}


static void
Sexp_dealloc(PySexpObject *self)
{
  Sexp_clear(self);
  self->ob_type->tp_free((PyObject*)self);

  //PyObject_Del(self);
}


static PyObject*
Sexp_repr(PyObject *self)
{
  //FIXME: make sure this is making any sense
  SEXP sexp = RPY_SEXP((PySexpObject *)self);
  //if (! sexp) {
  //  PyErr_Format(PyExc_ValueError, "NULL SEXP.");
  //  return NULL;
  //}
  return PyString_FromFormat("<%s - Python:\%p / R:\%p>",
			     self->ob_type->tp_name,
			     self,
			     sexp);
}


static PyObject*
Sexp_typeof(PyObject *self)
{
  SEXP sexp = RPY_SEXP(((PySexpObject*)self));
  if (! sexp) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return NULL;;
  }
  return PyInt_FromLong(TYPEOF(sexp));
}
PyDoc_STRVAR(Sexp_typeof_doc,
	     "\n\
	     Returns the R internal SEXPREC type.");


static PyObject*
Sexp_do_slot(PyObject *self, PyObject *name)
{
  SEXP sexp = RPY_SEXP(((PySexpObject*)self));
  if (! sexp) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return NULL;;
  }
  if (! PyString_Check(name)) {
    PyErr_SetString(PyExc_TypeError, "The name must be a string.");
    return NULL;
  }
  char *name_str = PyString_AS_STRING(name);

  if (! R_has_slot(sexp, install(name_str))) {
    PyErr_SetString(PyExc_LookupError, "The object has no such attribute.");
    return NULL;
  }
  SEXP res_R = GET_SLOT(sexp, install(name_str));

  PyObject *res = (PyObject *)newPySexpObject(res_R);
  return res;
}
PyDoc_STRVAR(Sexp_do_slot_doc,
"\n\
Returns the attribute/slot for an R object.\n\
The name of the slot as a string is the only parameter for\
 the method.\n");



static PyMethodDef Sexp_methods[] = {
  {"typeof", (PyCFunction)Sexp_typeof, METH_NOARGS,
  Sexp_typeof_doc},
  {"do_slot", (PyCFunction)Sexp_do_slot, METH_O,
  Sexp_do_slot_doc},
  {NULL, NULL}          /* sentinel */
};


staticforward PyTypeObject Sexp_Type;

static PyObject*
Sexp_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{

  PySexpObject *self;
  //unsigned short int rpy_only = 1;

  #ifdef RPY_VERBOSE
  printf("new '%s' object @...\n", type->tp_name);
  #endif 

  //self = (PySexpObject *)PyObject_New(PySexpObject, type);
  self = (PySexpObject *)type->tp_alloc(type, 0);
  #ifdef RPY_VERBOSE
  printf("  Python:%p / R:%p (R_NilValue) ...\n", self, R_NilValue);
  #endif 

  if (! self)
    PyErr_NoMemory();

  self->sObj = (SexpObject *)calloc(1, sizeof(SexpObject));
  if (! self->sObj) {
    Py_DECREF(self);
    PyErr_NoMemory();
  }

  RPY_COUNT(self) = 1;
  RPY_SEXP(self) = R_NilValue;
  //RPY_RPYONLY(self) = rpy_only;

  #ifdef RPY_VERBOSE
  printf("done.\n");
  #endif 

  return (PyObject *)self;

}

static int
Sexp_init(PyObject *self, PyObject *args, PyObject *kwds)
{
#ifdef RPY_VERBOSE
  printf("Python:%p / R:%p - Sexp initializing...\n", 
	 self, RPY_SEXP((PySexpObject *)self));
#endif 

  PyObject *sourceObject;

  Py_INCREF(Py_True);
  PyObject *copy = Py_True;

  SexpObject *tmpSexpObject;


  static char *kwlist[] = {"sexp", "copy", NULL};
  //FIXME: handle the copy argument

  if (! PyArg_ParseTupleAndKeywords(args, kwds, "O|O!", 
				    kwlist,
				    &sourceObject,
				    &PyBool_Type, &copy)) {
    Py_DECREF(Py_True);
    return -1;
  }

  if (! PyObject_IsInstance(sourceObject, 
			    (PyObject*)&Sexp_Type)) {
    PyErr_Format(PyExc_ValueError, 
		 "Can only instanciate from Sexp objects.");
    Py_DECREF(Py_True);
    return -1;
  }

  if (PyObject_IsTrue(copy)) {
    tmpSexpObject = ((PySexpObject *)self)->sObj;
    ((PySexpObject *)self)->sObj = ((PySexpObject *)sourceObject)->sObj;
    free(tmpSexpObject);
    RPY_INCREF((PySexpObject *)self);
#ifdef RPY_VERBOSE
    printf("Python: %p / R: %p - sexp count is now %i.\n", 
	   (PySexpObject *)self, RPY_SEXP((PySexpObject *)self), RPY_COUNT((PySexpObject *)self));
#endif 

  } else {
    PyErr_Format(PyExc_ValueError, "Cast without copy is not yet implemented.");
    Py_DECREF(Py_True);
    return -1;
  }
  Py_DECREF(Py_True);

#ifdef RPY_VERBOSE
  printf("done.\n");
#endif 


  return 0;
}


/*
 * Generic Sexp_Type. It represents SEXP objects at large.
 */
static PyTypeObject Sexp_Type = {
	/* The ob_type field must be initialized in the module init function
	 * to be portable to Windows without using C++. */
	PyObject_HEAD_INIT(NULL)
	0,			/*ob_size*/
	"rinterface.Sexp",	/*tp_name*/
	sizeof(PySexpObject),	/*tp_basicsize*/
	0,			/*tp_itemsize*/
	/* methods */
	(destructor)Sexp_dealloc, /*tp_dealloc*/
	0,			/*tp_print*/
	0,                      /*tp_getattr*/
	0,                      /*tp_setattr*/
	0,			/*tp_compare*/
	Sexp_repr,		/*tp_repr*/
	0,			/*tp_as_number*/
	0,			/*tp_as_sequence*/
	0,			/*tp_as_mapping*/
	0,			/*tp_hash*/
	0,                      /*tp_call*/
        0,                      /*tp_str*/
        0,                      /*tp_getattro*/
        0,                      /*tp_setattro*/
        0,                      /*tp_as_buffer*/
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE,     /*tp_flags*/
        0,                      /*tp_doc*/
        0,                      /*tp_traverse*/
        Sexp_clear,                      /*tp_clear*/
        0,                      /*tp_richcompare*/
        0,                      /*tp_weaklistoffset*/
        0,                      /*tp_iter*/
        0,                      /*tp_iternext*/
        Sexp_methods,           /*tp_methods*/
        0,                      /*tp_members*/
        0,//Sexp_getset,            /*tp_getset*/
        0,                      /*tp_base*/
        0,                      /*tp_dict*/
        0,                      /*tp_descr_get*/
        0,                      /*tp_descr_set*/
        0,                      /*tp_dictoffset*/
        (initproc)Sexp_init,    /*tp_init*/
        0,                      /*tp_alloc*/
        Sexp_new,               /*tp_new*/
        0,                      /*tp_free*/
        0,                      /*tp_is_gc*/
};


/* static PyObject* */
/* Sexp_new(PyTypeObject *type, PyObject *args) */
/* { */
/*   PyObject object, res; */
/*   if (!PyArg_ParseTuple(args, "O:new", */
/* 			&object)) */
/*     PyErr_Format(PyExc_ValueError, "Can only instanciate from PySexpObject"); */
/*   return NULL; */
/*   res = (PySexpObject *)_PyObject_New(&Sexp_Type); */
/*   if (!res) */
/*     PyErr_NoMemory(); */
/*   res->sexp = sexp; */
/*   return res; */
/* } */




/*
 * Closure-type Sexp.
 */


/* Evaluate a SEXP. It must be constructed by hand. It raises a Python
   exception if an error ocurred in the evaluation */
SEXP do_eval_expr(SEXP expr_R, SEXP env_R) {
  SEXP res_R = NULL;
  int error = 0;
  PyOS_sighandler_t old_int;


  //FIXME: if env_R is null, use R_BaseEnv
  if (isNull(env_R)) {
    env_R = R_BaseEnv;
  }

  /* Enable our handler for SIGINT inside the R
     interpreter. Otherwise, we cannot stop R calculations, since
     SIGINT is only processed between Python bytecodes. Also, save the
     Python SIGINT handler because it is necessary to temporally
	   restore it in user defined I/O Python functions. */
  /* stop_events(); */
  
#ifdef _WIN32
  old_int = PyOS_getsig(SIGBREAK);
#else
  old_int = PyOS_getsig(SIGINT);
#endif
  python_sigint = old_int;
  
  signal(SIGINT, interrupt_R);
  
  interrupted = 0;
  //FIXME: evaluate expression in the given
  res_R = R_tryEval(expr_R, env_R, &error);

#ifdef _WIN32
  PyOS_setsig(SIGBREAK, old_int);   
#else 
  PyOS_setsig(SIGINT, old_int);
#endif
  
  /* start_events(); */
  
  if (error) {
    if (interrupted) {
      PyErr_SetNone(PyExc_KeyboardInterrupt);
    //FIXME: handling of interruptions
    } else {
      EmbeddedR_exception_from_errmessage();
    }
    return NULL;
  }

  return res_R;
}


/* This is the method to call when invoking an 'Sexp' */
static PyObject *
Sexp_call(PyObject *self, PyObject *args, PyObject *kwds)
{
  SEXP call_R, c_R, res_R;
  int largs, lkwds;
  SEXP tmp_R, fun_R;
  
  largs = lkwds = 0;
  if (args)
    largs = PyObject_Length(args);
  if (kwds)
    lkwds = PyObject_Length(kwds);
  if ((largs<0) || (lkwds<0)) {
    PyErr_Format(PyExc_ValueError, "Negative number of parameters !?.");
    return NULL;
  }

  /* A SEXP with the function to call and the arguments and keywords. */
  PROTECT(c_R = call_R = allocList(largs+lkwds+1));
  SET_TYPEOF(c_R, LANGSXP);
  fun_R = RPY_SEXP((PySexpObject *)self);
  if (! fun_R) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    goto fail;
  }
  SETCAR(c_R, fun_R);
  c_R = CDR(c_R);

  int arg_i;
  PyObject *tmp_obj;
  int is_PySexpObject;
  for (arg_i=0; arg_i<largs; arg_i++) {
    tmp_obj = PyTuple_GetItem(args, arg_i);
    is_PySexpObject = PyObject_TypeCheck(tmp_obj, &Sexp_Type);
    if (! is_PySexpObject) {
      PyErr_Format(PyExc_ValueError, 
		   "All parameters must be of type Sexp_Type.");
      Py_DECREF(tmp_obj);
      goto fail;
    }
    tmp_R = RPY_SEXP((PySexpObject *)tmp_obj);
    if (! tmp_R) {
      PyErr_Format(PyExc_ValueError, "NULL SEXP.");
      Py_DECREF(tmp_obj);
      goto fail;
    }
    SETCAR(c_R, tmp_R);
    c_R = CDR(c_R);
  }

  /* named args */
  PyObject *citems, *argValue, *argName;
  char *argNameString;

  if (kwds) {
    citems = PyMapping_Items(kwds);

    for (arg_i=0; arg_i<lkwds; arg_i++) {
      tmp_obj = PySequence_GetItem(citems, arg_i);
      if (! tmp_obj) {
	PyErr_Format(PyExc_ValueError, "No un-named item %i !?", arg_i);
	Py_DECREF(tmp_obj);
	Py_XDECREF(citems);
	goto fail;
      }
      argName = PyTuple_GetItem(tmp_obj, 0);
      if (! PyString_Check(argName)) {
	PyErr_SetString(PyExc_TypeError, "keywords must be strings");
	Py_DECREF(tmp_obj);
	Py_XDECREF(citems);
	goto fail;
      }
      argValue = PyTuple_GetItem(tmp_obj, 1);
      is_PySexpObject = PyObject_TypeCheck(argValue, &Sexp_Type);
      if (! is_PySexpObject) {
	PyErr_Format(PyExc_ValueError, 
		     "All named parameters must be of type Sexp_Type.");
	Py_DECREF(tmp_obj);	
	Py_XDECREF(citems);
	goto fail;
      }
      Py_DECREF(tmp_obj);
      tmp_R = RPY_SEXP((PySexpObject *)argValue);
      if (! tmp_R) {
	PyErr_Format(PyExc_ValueError, "NULL SEXP.");
	Py_DECREF(tmp_obj);
	Py_XDECREF(citems);
	goto fail;
      }
      SETCAR(c_R, tmp_R);
      argNameString = PyString_AsString(argName);
      SET_TAG(c_R, install(argNameString));
    //printf("PyMem_Free...");
    //PyMem_Free(argNameString);
      c_R = CDR(c_R);
    }
    Py_XDECREF(citems);
  }
  
//FIXME: R_GlobalContext ?
  //PROTECT(res_R = do_eval_expr(call_R, R_GlobalEnv));
  PROTECT(res_R = do_eval_expr(call_R, CLOENV(fun_R)));

/*   if (!res) { */
/*     UNPROTECT(2); */
/*     return NULL; */
/*   } */
  UNPROTECT(2);

  if (! res_R) {
    EmbeddedR_exception_from_errmessage();
    //PyErr_Format(PyExc_RuntimeError, "Error while running R code");
    return NULL;
  }

  //FIXME: standardize R outputs
  extern void Rf_PrintWarnings(void);
  Rf_PrintWarnings(); /* show any warning messages */

  PyObject *res = (PyObject *)newPySexpObject(res_R);
  return res;
  
 fail:
  UNPROTECT(1);
  return NULL;

}




static PySexpObject*
Sexp_closureEnv(PyObject *self)
{
  SEXP closureEnv, sexp;
  sexp = RPY_SEXP((PySexpObject*)self);
  if (! sexp) {
      PyErr_Format(PyExc_ValueError, "NULL SEXP.");
      return NULL;
  }
  closureEnv = CLOENV(sexp);
  return newPySexpObject(closureEnv);
}
PyDoc_STRVAR(Sexp_closureEnv_doc,
	     "\n\
Returns the environment the object is defined in.\
This corresponds to the C-level function CLOENV(SEXP).");

static PyMethodDef ClosureSexp_methods[] = {
  {"closureEnv", (PyCFunction)Sexp_closureEnv, METH_NOARGS,
  Sexp_closureEnv_doc},
  {NULL, NULL}          /* sentinel */
};

PyDoc_STRVAR(ClosureSexp_Type_doc,
"A R object that is a closure, that is a function. \
In R a function is defined within an enclosing \
environment, thus the name closure. \
In Python, 'nested scopes' could be the closest similar thing.\
\n\
The closure can be accessed with the method 'closureEnv'.\
");

static int
ClosureSexp_init(PyObject *self, PyObject *args, PyObject *kwds);


static PyTypeObject ClosureSexp_Type = {
	/* The ob_type field must be initialized in the module init function
	 * to be portable to Windows without using C++. */
	PyObject_HEAD_INIT(NULL)
	0,			/*ob_size*/
	"rinterface.SexpClosure",	/*tp_name*/
	sizeof(PySexpObject),	/*tp_basicsize*/
	0,			/*tp_itemsize*/
	/* methods */
	0, /*tp_dealloc*/
	0,			/*tp_print*/
	0,                      /*tp_getattr*/
	0,                      /*tp_setattr*/
	0,			/*tp_compare*/
	0,		        /*tp_repr*/
	0,			/*tp_as_number*/
	0,			/*tp_as_sequence*/
	0,			/*tp_as_mapping*/
	0,			/*tp_hash*/
	Sexp_call,              /*tp_call*/
        0,//Sexp_str,               /*tp_str*/
        0,                      /*tp_getattro*/
        0,                      /*tp_setattro*/
        0,                      /*tp_as_buffer*/
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE,     /*tp_flags*/
        ClosureSexp_Type_doc,                      /*tp_doc*/
        0,                      /*tp_traverse*/
        0,                      /*tp_clear*/
        0,                      /*tp_richcompare*/
        0,                      /*tp_weaklistoffset*/
        0,                      /*tp_iter*/
        0,                      /*tp_iternext*/
        ClosureSexp_methods,           /*tp_methods*/
        0,                      /*tp_members*/
        0,//Sexp_getset,            /*tp_getset*/
        &Sexp_Type,             /*tp_base*/
        0,                      /*tp_dict*/
        0,                      /*tp_descr_get*/
        0,                      /*tp_descr_set*/
        0,                      /*tp_dictoffset*/
        (initproc)ClosureSexp_init,                      /*tp_init*/
        0,                      /*tp_alloc*/
        0,//Sexp_new,               /*tp_new*/
        0,                      /*tp_free*/
        0                      /*tp_is_gc*/
};


static int
ClosureSexp_init(PyObject *self, PyObject *args, PyObject *kwds)
{
  PyObject *object;
  PyObject *copy;
  static char *kwlist[] = {"sexpclos", "copy", NULL};
  //FIXME: handle the copy argument
  if (! PyArg_ParseTupleAndKeywords(args, kwds, "O|O!", 
				    kwlist,
				    &object,
				    &PyBool_Type, &copy)) {
    return -1;
  }
  if (PyObject_IsInstance(object, 
			  (PyObject*)&ClosureSexp_Type)) {
    //call parent's constructor
    if (Sexp_init(self, args, NULL) == -1) {
      PyErr_Format(PyExc_RuntimeError, "Error initializing instance.");
      return -1;
    }
  } else {
    PyErr_Format(PyExc_ValueError, "Cannot instantiate from this type.");
    return -1;
  }
  return 0;
}




/* len(x) */
static Py_ssize_t VectorSexp_len(PyObject *object)
{
  Py_ssize_t len;
  //FIXME: sanity checks.
  SEXP sexp = RPY_SEXP((PySexpObject *)object);
  if (! sexp) {
      PyErr_Format(PyExc_ValueError, "NULL SEXP.");
      return -1;
  }
  len = (Py_ssize_t)GET_LENGTH(sexp);
  return len;
}

/* a[i] */
static PyObject *
VectorSexp_item(PyObject *object, Py_ssize_t i)
{
  PyObject* res;
  R_len_t i_R;
  SEXP *sexp = &(RPY_SEXP((PySexpObject *)object));

  if (! sexp) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return NULL;
  }

  /* R is still with int for indexes */
  if (i >= R_LEN_T_MAX) {
    PyErr_Format(PyExc_IndexError, "Index value exceeds what R can handle.");
    res = NULL;
  }
  else if (i >= GET_LENGTH(*sexp)) {
    PyErr_Format(PyExc_IndexError, "Index out of range.");
    res = NULL;
  }
  else {
    double vd;
    int vi;
    Rcomplex vc;
    const char *vs;
    i_R = (R_len_t)i;
    switch (TYPEOF(*sexp)) {
    case REALSXP:
      vd = (NUMERIC_POINTER(*sexp))[i_R];
      res = PyFloat_FromDouble(vd);
      break;
    case INTSXP:
      vi = INTEGER_POINTER(*sexp)[i_R];
      res = PyInt_FromLong((long)vi);
      break;
    case LGLSXP:
      vi = LOGICAL_POINTER(*sexp)[i_R];
      res = PyBool_FromLong((long)vi);
      break;
    case CPLXSXP:
      vc = COMPLEX_POINTER(*sexp)[i_R];
      res = PyComplex_FromDoubles(vc.r, vc.i);
      break;
    case STRSXP:
      vs = translateChar(STRING_ELT(*sexp, i_R));
      res = PyString_FromString(vs);
      break;
/*     case CHARSXP: */
/*       //FIXME: implement handling of single char (if possible ?) */
/*       vs = (CHAR(*sexp)[i_R]); */
/*       res = PyString_FromStringAndSize(vs, 1); */
    case VECSXP:
      res = (PyObject *)newPySexpObject(VECTOR_ELT(*sexp, i_R));
      break;
    default:
      PyErr_Format(PyExc_ValueError, "Cannot handle type %d", 
		   TYPEOF(*sexp));
      res = NULL;
      break;
    }
  }
  return res;
}

/* a[i] = val */
static int
VectorSexp_ass_item(PyObject *object, Py_ssize_t i, PyObject *val)
{
  R_len_t i_R;

  /* R is still with int for indexes */
  if (i >= R_LEN_T_MAX) {
    PyErr_Format(PyExc_IndexError, "Index value exceeds what R can handle.");
    return -1;
  }

  SEXP *sexp = &(RPY_SEXP((PySexpObject *)object));
  if (i >= GET_LENGTH(*sexp)) {
    PyErr_Format(PyExc_IndexError, "Index out of range.");
    return -1;
  }

  if (! sexp) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return -1;
  }

  int is_PySexpObject = PyObject_TypeCheck(val, &Sexp_Type);
  if (! is_PySexpObject) {
    PyErr_Format(PyExc_ValueError, "Any new value must be of "
		 "type 'Sexp_Type'.");
    return -1;
  }
  SEXP *sexp_val = &(RPY_SEXP((PySexpObject *)val));
  if (! sexp_val) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return -1;
  }

  if (TYPEOF(*sexp_val) != TYPEOF(*sexp)) {
    PyErr_Format(PyExc_ValueError, "The type for the new value cannot be different.");
    return -1;
  }

  if ((TYPEOF(*sexp_val) != VECSXP) & (LENGTH(*sexp_val) != 1)) {
    PyErr_Format(PyExc_ValueError, "The new value must be of length 1.");
    return -1;
  }

  SEXP sexp_copy;
  i_R = (R_len_t)i;
  switch (TYPEOF(*sexp)) {
  case REALSXP:
    (NUMERIC_POINTER(*sexp))[i_R] = (NUMERIC_POINTER(*sexp_val))[0];
    break;
  case INTSXP:
    (INTEGER_POINTER(*sexp))[i_R] = (INTEGER_POINTER(*sexp_val))[0];
    break;
  case LGLSXP:
    (LOGICAL_POINTER(*sexp))[i_R] = (LOGICAL_POINTER(*sexp_val))[0];
    break;
  case CPLXSXP:
    (COMPLEX_POINTER(*sexp))[i_R] = (COMPLEX_POINTER(*sexp_val))[0];
    break;
  case STRSXP:
    SET_STRING_ELT(*sexp, i_R, STRING_ELT(*sexp_val, 0));
    break;
  case VECSXP:
    PROTECT(sexp_copy = Rf_duplicate(*sexp_val));
    SET_VECTOR_ELT(*sexp, i_R, sexp_copy);
    UNPROTECT(1);
    break;
  default:
    PyErr_Format(PyExc_ValueError, "cannot handle type %d", 
		 TYPEOF(*sexp));
    return -1;
    break;
  }
  return 0;
}

static PySequenceMethods VectorSexp_sequenceMethods = {
  (lenfunc)VectorSexp_len,              /* sq_length */
  0,                              /* sq_concat */
  0,                              /* sq_repeat */
  (ssizeargfunc)VectorSexp_item,        /* sq_item */
  0, //(ssizessizeargfunc)VectorSexp_slice,  /* sq_slice */
  (ssizeobjargproc)VectorSexp_ass_item,   /* sq_ass_item */
  0,                              /* sq_ass_slice */
  0,                              /* sq_contains */
  0,                              /* sq_inplace_concat */
  0                               /* sq_inplace_repeat */
};


static PyGetSetDef VectorSexp_getsets[] = {
  {"__array_struct__", 
   (getter)array_struct_get,
   (setter)0,
   "Array protocol: struct"},
  {NULL, NULL, NULL, NULL}          /* sentinel */
};


PyDoc_STRVAR(VectorSexp_Type_doc,
	     "R object that is a vector."
	     " R vectors start their indexing at one,"
	     " while Python lists or arrays start indexing"
	     " at zero.\n"
	     "In the hope to avoid confusion, the indexing"
	     " from the Python subset operator (__getitem__)"
	     " is done at zero.");

static int
VectorSexp_init(SexpObject *self, PyObject *args, PyObject *kwds);

static PyTypeObject VectorSexp_Type = {
	/* The ob_type field must be initialized in the module init function
	 * to be portable to Windows without using C++. */
	PyObject_HEAD_INIT(NULL)
	0,			/*ob_size*/
	"rinterface.SexpVector",	/*tp_name*/
	sizeof(PySexpObject),	/*tp_basicsize*/
	0,			/*tp_itemsize*/
	/* methods */
	0, /*tp_dealloc*/
	0,			/*tp_print*/
	0,                      /*tp_getattr*/
	0,                      /*tp_setattr*/
	0,			/*tp_compare*/
	0,		        /*tp_repr*/
	0,			/*tp_as_number*/
	&VectorSexp_sequenceMethods,			/*tp_as_sequence*/
	0,			/*tp_as_mapping*/
	0,			/*tp_hash*/
	0,              /*tp_call*/
        0,//Sexp_str,               /*tp_str*/
        0,                      /*tp_getattro*/
        0,                      /*tp_setattro*/
        0,                      /*tp_as_buffer*/
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE,     /*tp_flags*/
        VectorSexp_Type_doc,                      /*tp_doc*/
        0,                      /*tp_traverse*/
        0,                      /*tp_clear*/
        0,                      /*tp_richcompare*/
        0,                      /*tp_weaklistoffset*/
        0,                      /*tp_iter*/
        0,                      /*tp_iternext*/
	0,           /*tp_methods*/
        0,                      /*tp_members*/
        VectorSexp_getsets,            /*tp_getset*/
        &Sexp_Type,             /*tp_base*/
        0,                      /*tp_dict*/
        0,                      /*tp_descr_get*/
        0,                      /*tp_descr_set*/
        0,                      /*tp_dictoffset*/
        (initproc)VectorSexp_init,                      /*tp_init*/
        0,                      /*tp_alloc*/
        0,               /*tp_new*/
        0,                      /*tp_free*/
        0                      /*tp_is_gc*/
};
 

static int
VectorSexp_init(SexpObject *self, PyObject *args, PyObject *kwds)
{
#ifdef RPY_VERBOSE
  printf("%p: VectorSexp initializing...\n", self);
#endif 

  PyObject *object;
  int sexptype = -1;
  PyObject *copy;
  static char *kwlist[] = {"sexpvector", "sexptype", "copy", NULL};


  //FIXME: handle the copy argument
  if (! PyArg_ParseTupleAndKeywords(args, kwds, "O|iO!", 
				    kwlist,
				    &object,
				    &sexptype,
				    &PyBool_Type, &copy)) {
    return -1;
  }

  if (PyObject_IsInstance(object, 
			  (PyObject*)&VectorSexp_Type)) {
    //call parent's constructor
    if (Sexp_init(self, args, NULL) == -1) {
      //PyErr_Format(PyExc_RuntimeError, "Error initializing instance.");
      return -1;
    }
  } else if (PySequence_Check(object)) {
    if ((sexptype < 0) || (sexptype > maxValidSexpType) || 
	(! validSexpType[sexptype])) {
      PyErr_Format(PyExc_ValueError, "Invalid SEXP type.");
      return -1;
    }
    //FIXME: implemement automagic type ?
    //(RPy has something)... or leave it to extensions ?

    RPY_SEXP((PySexpObject *)self) = newSEXP(object, sexptype);
  } else {
    PyErr_Format(PyExc_ValueError, "Invalid sexpvector.");
    return -1;
  }

#ifdef RPY_VERBOSE
  printf("done (VectorSexp_init).\n");
#endif 
  
  return 0;
}


/* --- */
static PyObject*
EnvironmentSexp_findVar(PyObject *self, PyObject *args, PyObject *kwds)
{
  char *name;
  SEXP res_R = NULL;
  PySexpObject *res;
  PyObject *wantFun = Py_False;
  Py_INCREF(Py_False);
  static char *kwlist[] = {"name", "wantFun", NULL};
 
  if (!PyArg_ParseTupleAndKeywords(args, kwds, "s|O!",
				   kwlist,
				   &name, 
				   &PyBool_Type, &wantFun)) { 
    Py_DECREF(Py_False);
    return NULL; 
  }

  const SEXP rho_R = RPY_SEXP((PySexpObject *)self);
  if (! rho_R) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    Py_DECREF(Py_False);
    return NULL;
  }

  if (rho_R == R_EmptyEnv) {
    PyErr_Format(PyExc_LookupError, "Fatal error: R_EmptyEnv.");
  }

  if (wantFun == Py_True) {
    res_R = rpy_findFun(install(name), rho_R);
  } else {
    res_R = findVar(install(name), rho_R);
  }

  if (res_R != R_UnboundValue) {
    //FIXME rpy_only
    res = newPySexpObject(res_R);
  } else {
    PyErr_Format(PyExc_LookupError, "'%s' not found", name);
    res = NULL;
  }
  Py_DECREF(Py_False);
  return res;
}
PyDoc_STRVAR(EnvironmentSexp_findVar_doc,
	     "Find an R object in a given environment.");

static PyMethodDef EnvironmentSexp_methods[] = {
  {"get", (PyCFunction)EnvironmentSexp_findVar, METH_VARARGS | METH_KEYWORDS,
  EnvironmentSexp_findVar_doc},
  {NULL, NULL}          /* sentinel */
};


static PySexpObject*
EnvironmentSexp_subscript(PyObject *self, PyObject *key)
{
  char *name;
  SEXP res_R = NULL;

  if (!PyString_Check(key)) {
    PyErr_Format(PyExc_ValueError, "Keys must be string objects.");
    return NULL;
  }

  name = PyString_AsString(key);
  
  SEXP rho_R = RPY_SEXP((PySexpObject *)self);
  if (! rho_R) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return NULL;
  }
  res_R = findVarInFrame(rho_R, install(name));

  if (res_R != R_UnboundValue) {
    return newPySexpObject(res_R);
  }
  PyErr_Format(PyExc_LookupError, "'%s' not found", name);
  return NULL;
}
PyDoc_STRVAR(EnvironmentSexp_subscript_doc,
	     "Find an R object in the environment.\n"
	     "Not all R environment are hash tables, and this may"
	     " influence performances when doing repeated lookups.");

static int
EnvironmentSexp_ass_subscript(PyObject *self, PyObject *key, PyObject *value)
{
  char *name;

  if (!PyString_Check(key)) {
    PyErr_Format(PyExc_ValueError, "Keys must be string objects.");
    return -1;
  }

  int is_PySexpObject = PyObject_TypeCheck(value, &Sexp_Type);
  if (! is_PySexpObject) {
    PyErr_Format(PyExc_ValueError, 
		 "All parameters must be of type Sexp_Type.");
    //PyDecRef(value);
    return -1;
  }

  name = PyString_AsString(key);
  
  SEXP rho_R = RPY_SEXP((PySexpObject *)self);
  if (! rho_R) {
    PyErr_Format(PyExc_ValueError, "The environment has NULL SEXP.");
    return -1;
  }

  SEXP sexp_copy;
  SEXP sexp = RPY_SEXP((PySexpObject *)value);
  if (! sexp) {
    PyErr_Format(PyExc_ValueError, "The value has NULL SEXP.");
    return -1;
  }
  SEXP sym = Rf_install(name);
  PROTECT(sexp_copy = Rf_duplicate(sexp));
  Rf_defineVar(sym, sexp_copy, rho_R);
  UNPROTECT(1);
  return 0;
}

static Py_ssize_t EnvironmentSexp_length(PyObject *self) 
{
  SEXP rho_R = RPY_SEXP((PySexpObject *)self);
  if (! rho_R) {
    PyErr_Format(PyExc_ValueError, "The environment has NULL SEXP.");
    return -1;
  }
  SEXP symbols;
  PROTECT(symbols = R_lsInternal(rho_R, TRUE));
  Py_ssize_t len = (Py_ssize_t)GET_LENGTH(symbols);
  UNPROTECT(1);
  return len;
}

static PyMappingMethods EnvironmentSexp_mappingMethods = {
  (lenfunc)EnvironmentSexp_length, /* mp_length */
  (binaryfunc)EnvironmentSexp_subscript, /* mp_subscript */
  (objobjargproc)EnvironmentSexp_ass_subscript  /* mp_ass_subscript */
};

static PyObject* 
EnvironmentSexp_iter(PyObject *sexpEnvironment)
{
  SEXP rho_R = RPY_SEXP((PySexpObject *)sexpEnvironment);

  if (! rho_R) {
    PyErr_Format(PyExc_ValueError, "The environment has NULL SEXP.");
    return NULL;
  }
  SEXP symbols;
  PROTECT(symbols = R_lsInternal(rho_R, TRUE));
  PySexpObject *seq = newPySexpObject(symbols);
  Py_INCREF(seq);
  UNPROTECT(1);
 
  PyObject *it = PyObject_GetIter((PyObject *)seq);
  Py_DECREF(seq);
  return it;
}

PyDoc_STRVAR(EnvironmentSexp_Type_doc,
"R object that is an environment.\
 R environments can be seen as similar to Python\
 dictionnaries, with the following twists:\n\
 - an environment can be a list of frames to sequentially\
 search into\n\
-  the search can be recursively propagated to the enclosing\
 environment whenever the key is not found (in that respect\
 they can be seen as scopings).\n\
\n\
 The subsetting operator \"[\" is made to match Python's\
 behavior, that is the enclosing environments are not\
 inspected upon absence of a given key.\n\
");


static int
EnvironmentSexp_init(PySexpObject *self, PyObject *args, PyObject *kwds);

static PyTypeObject EnvironmentSexp_Type = {
	/* The ob_type field must be initialized in the module init function
	 * to be portable to Windows without using C++. */
	PyObject_HEAD_INIT(NULL)
	0,			/*ob_size*/
	"rinterface.SexpEnvironment",	/*tp_name*/
	sizeof(PySexpObject),	/*tp_basicsize*/
	0,			/*tp_itemsize*/
	/* methods */
	0, /*tp_dealloc*/
	0,			/*tp_print*/
	0,                      /*tp_getattr*/
	0,                      /*tp_setattr*/
	0,			/*tp_compare*/
	0,		        /*tp_repr*/
	0,			/*tp_as_number*/
	0,			/*tp_as_sequence*/
	&EnvironmentSexp_mappingMethods,/*tp_as_mapping*/
	0,			/*tp_hash*/
	0,              /*tp_call*/
        0,//Sexp_str,               /*tp_str*/
        0,                      /*tp_getattro*/
        0,                      /*tp_setattro*/
        0,                      /*tp_as_buffer*/
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE,     /*tp_flags*/
        EnvironmentSexp_Type_doc,                      /*tp_doc*/
        0,                      /*tp_traverse*/
        0,                      /*tp_clear*/
        0,                      /*tp_richcompare*/
        0,                      /*tp_weaklistoffset*/
        EnvironmentSexp_iter,                      /*tp_iter*/
        0,                      /*tp_iternext*/
        EnvironmentSexp_methods,           /*tp_methods*/
        0,                      /*tp_members*/
        0,//Sexp_getset,            /*tp_getset*/
        &Sexp_Type,             /*tp_base*/
        0,                      /*tp_dict*/
        0,                      /*tp_descr_get*/
        0,                      /*tp_descr_set*/
        0,                      /*tp_dictoffset*/
        (initproc)EnvironmentSexp_init,                      /*tp_init*/
        0,                      /*tp_alloc*/
	//FIXME: add new method
        0, //EnvironmentSexp_new,               /*tp_new*/
        0,                      /*tp_free*/
        0                      /*tp_is_gc*/
};

static int
EnvironmentSexp_init(PySexpObject *self, PyObject *args, PyObject *kwds)
{
  PyObject *object;
  PyObject *copy;
  static char *kwlist[] = {"sexpenv", "copy", NULL};
  //FIXME: handle the copy argument
  if (! PyArg_ParseTupleAndKeywords(args, kwds, "O|O!", 
				    kwlist,
				    &object,
				    &PyBool_Type, &copy)) {
    return -1;
  }
  if (PyObject_IsInstance(object, 
			  (PyObject*)&EnvironmentSexp_Type)) {
    //call parent's constructor
    if (Sexp_init(self, args, NULL) == -1) {
      PyErr_Format(PyExc_RuntimeError, "Error initializing instance.");
      return -1;
    }
  } else {
    PyErr_Format(PyExc_ValueError, "Cannot instantiate from this type.");
    return -1;
  }
  return 0;
}


//FIXME: write more doc
PyDoc_STRVAR(S4Sexp_Type_doc,
"R object that is an 'S4 object'.\
Attributes can be accessed using the method 'do_slot'.\
");


static PyTypeObject S4Sexp_Type = {
	/* The ob_type field must be initialized in the module init function
	 * to be portable to Windows without using C++. */
	PyObject_HEAD_INIT(NULL)
	0,			/*ob_size*/
	"rinterface.SexpS4",	/*tp_name*/
	sizeof(PySexpObject),	/*tp_basicsize*/
	0,			/*tp_itemsize*/
	/* methods */
	0, /*tp_dealloc*/
	0,			/*tp_print*/
	0,                      /*tp_getattr*/
	0,                      /*tp_setattr*/
	0,			/*tp_compare*/
	0,		        /*tp_repr*/
	0,			/*tp_as_number*/
	0,			/*tp_as_sequence*/
	0,			/*tp_as_mapping*/
	0,			/*tp_hash*/
	0,              /*tp_call*/
        0,//Sexp_str,               /*tp_str*/
        0,                      /*tp_getattro*/
        0,                      /*tp_setattro*/
        0,                      /*tp_as_buffer*/
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE,     /*tp_flags*/
        S4Sexp_Type_doc,                      /*tp_doc*/
        0,                      /*tp_traverse*/
        0,                      /*tp_clear*/
        0,                      /*tp_richcompare*/
        0,                      /*tp_weaklistoffset*/
        0,                      /*tp_iter*/
        0,                      /*tp_iternext*/
        0,           /*tp_methods*/
        0,                      /*tp_members*/
        0,//Sexp_getset,            /*tp_getset*/
        &Sexp_Type,             /*tp_base*/
        0,                      /*tp_dict*/
        0,                      /*tp_descr_get*/
        0,                      /*tp_descr_set*/
        0,                      /*tp_dictoffset*/
        0,                      /*tp_init*/
        0,                      /*tp_alloc*/
	//FIXME: add new method
        0, //S4Sexp_new,               /*tp_new*/
        0,                      /*tp_free*/
        0                      /*tp_is_gc*/
};



/* --- Create a SEXP object --- */
static PySexpObject*
newPySexpObject(const SEXP sexp)
{
  PySexpObject *object;
  SEXP sexp_ok, env_R;

  if (! sexp) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return NULL;
  }
  //FIXME: let the possibility to manipulate un-evaluated promises ?
  if (TYPEOF(sexp) == PROMSXP) {
    env_R = PRENV(sexp);
    sexp_ok = eval(sexp, env_R);
  } 
  else {
    sexp_ok = sexp;
  }
  if (sexp_ok)
    R_PreserveObject(sexp_ok);

  switch (TYPEOF(sexp_ok)) {
  case CLOSXP:
  case BUILTINSXP:
  case SPECIALSXP:
    object  = (PySexpObject *)Sexp_new(&ClosureSexp_Type, Py_None, Py_None);
    break;
    //FIXME: BUILTINSXP and SPECIALSXP really like CLOSXP ?
  case REALSXP: 
  case INTSXP: 
  case LGLSXP:
  case CPLXSXP:
  case VECSXP:
  case STRSXP:
    object = (PySexpObject *)Sexp_new(&VectorSexp_Type, Py_None, Py_None);
    break;
  case ENVSXP:
    object = (PySexpObject *)Sexp_new(&EnvironmentSexp_Type, Py_None, Py_None);
    break;
  case S4SXP:
    object = (PySexpObject *)Sexp_new(&S4Sexp_Type, Py_None, Py_None);
    break;
  default:
    object = (PySexpObject *)Sexp_new(&Sexp_Type, Py_None, Py_None);
    break;
  }
  if (!object) {
    R_ReleaseObject(sexp_ok);
    PyErr_NoMemory();
    return NULL;
  }
  //PyObject_Init(&object, &ClosureSexp_Type);
  RPY_SEXP(object) = sexp_ok;
  //FIXME: Increment reference ?
  //Py_INCREF(object);
  return object;
}

static SEXP
newSEXP(PyObject *object, int rType)
{
  SEXP sexp;
  PyObject *seq_object, *item; 

#ifdef RPY_VERBOSE
  printf("  new SEXP for Python:%p.\n", object);
#endif 

  seq_object = PySequence_Fast(object, 
			       "Cannot create R object from non-sequence Python object.");
  //FIXME: Isn't the call above supposed to fire an Exception ?

  if (! seq_object) {
    return NULL;
  }
  const Py_ssize_t length = PySequence_Fast_GET_SIZE(seq_object);
  //FIXME: PROTECT THIS ?
  PROTECT(sexp = allocVector(rType, length));

  int i;
  switch(rType) {
  case REALSXP:
    for (i = 0; i < length; ++i) {
      if((item = PyNumber_Float(PySequence_Fast_GET_ITEM(seq_object, i)))) {
	REAL(sexp)[i] = PyFloat_AS_DOUBLE(item);
	Py_DECREF(item);
      }
      else {
	PyErr_Clear();
	REAL(sexp)[i] = NA_REAL;
      }
    }
    break;
  case INTSXP:
    for (i = 0; i < length; ++i) {
      if((item = PyNumber_Int(PySequence_Fast_GET_ITEM(seq_object, i)))) {
	long l = PyInt_AS_LONG(item);
	INTEGER(sexp)[i] = (l<=INT_MAX && l>=INT_MIN)?l:NA_INTEGER;
	Py_DECREF(item);
      }
      else {
	PyErr_Clear();
	INTEGER(sexp)[i] = NA_INTEGER;
      }
    }
    break;
  case LGLSXP:
    for (i = 0; i < length; ++i) {
      int q = PyObject_IsTrue(PySequence_Fast_GET_ITEM(seq_object, i));
      if (q != -1)
	LOGICAL(sexp)[i] = q;
      else {
	PyErr_Clear();
	LOGICAL(sexp)[i] = NA_LOGICAL;
      }
    }
    break;
  case STRSXP:
    for (i = 0; i < length; ++i) {
      if((item = PyObject_Str(PySequence_Fast_GET_ITEM(seq_object, i)))) {
	SEXP str_R = mkChar(PyString_AS_STRING(item));
	if (!str_R) {
	  Py_DECREF(item);
	  PyErr_NoMemory();
	  sexp = NULL;
	  break;
	}
	Py_DECREF(item);
	SET_STRING_ELT(sexp, i, str_R);
      }
      else {
	PyErr_Clear();
	SET_STRING_ELT(sexp, i, NA_STRING);
      }
    }
    break;
  case VECSXP:
    for (i = 0; i < length; ++i) {
      if((item = PySequence_Fast_GET_ITEM(seq_object, i))) {
	int is_PySexpObject = PyObject_TypeCheck(item, &Sexp_Type);
	if (! is_PySexpObject) {
	  Py_DECREF(item);
	  PyErr_Format(PyExc_ValueError, "All elements of the list must be of "
		       "type 'Sexp_Type'.");
	  return NULL;
	}
	SET_ELEMENT(sexp, i, RPY_SEXP((PySexpObject *)item));
	Py_DECREF(item);
      }
    }
    break;
  case CPLXSXP:
    for (i = 0; i < length; ++i) {
        item = PySequence_Fast_GET_ITEM(seq_object, i);
        if (PyComplex_Check(item)) {
 	  Py_complex cplx = PyComplex_AsCComplex(item);
	  COMPLEX(sexp)[i].r = cplx.real;
	  COMPLEX(sexp)[i].i = cplx.imag;
	  Py_DECREF(item);
        }
        else {
	  PyErr_Clear();
	  COMPLEX(sexp)[i].r = NA_REAL;
          COMPLEX(sexp)[i].i = NA_REAL;
        }
    }
    break;
  default:
    PyErr_Format(PyExc_ValueError, "Cannot handle type %d", rType);
    sexp = NULL;
  }
  UNPROTECT(1);
#ifdef RPY_VERBOSE
  printf("  new SEXP for Python:%p is %p.\n", object, sexp);
#endif 

  return sexp;
}



/* --- Find a variable in an environment --- */

//FIXME: is this any longer useful ?
static PySexpObject*
EmbeddedR_findVar(PyObject *self, PyObject *args)
{
  char *name;
  SEXP rho_R = R_GlobalEnv, res;
  PyObject rho;

  if (!PyArg_ParseTuple(args, "s", &name, &rho)) { 
    return NULL; 
  }

  res = findVar(install(name), rho_R);


  if (res != R_UnboundValue) {
    return newPySexpObject(res);
  }
  PyErr_Format(PyExc_LookupError, "'%s' not found", name);
  return NULL;
}
PyDoc_STRVAR(EmbeddedR_findVar_doc,
	     "Find a variable in R's .GlobalEnv.");

static PyObject*
EmbeddedR_sexpType(PyObject *self, PyObject *args)
{
  /* Return the C-defined name for R types */
  int sexp_i;

  if (! PyArg_ParseTuple(args, "i", &sexp_i)) {
    //PyErr_Format(PyExc_LookupError, "Value should be an integer");
    return NULL;
  }

  const char *sexp_type = validSexpType[sexp_i];

  if ((sexp_i < 0) || (sexp_i > maxValidSexpType) || (! sexp_type)) {

    PyErr_Format(PyExc_LookupError, "'%i' is not a valid SEXP value.", sexp_i);
    return NULL;
  }
  //FIXME: store python strings when initializing validSexpType instead
  PyObject *res = PyString_FromString(sexp_type);
  return res;

}

/* --- List of functions defined in the module --- */

static PyMethodDef EmbeddedR_methods[] = {
  {"initEmbeddedR",     (PyCFunction)EmbeddedR_init,   METH_NOARGS,
   EmbeddedR_init_doc},
  {"endEmbeddedR",	(PyCFunction)EmbeddedR_end,    METH_O,
   EmbeddedR_end_doc},
  {"setWriteConsole",	(PyCFunction)EmbeddedR_setWriteConsole,	 METH_VARARGS,
   EmbeddedR_setWriteConsole_doc},
  {"findVarEmbeddedR",	(PyCFunction)EmbeddedR_findVar,	 METH_VARARGS,
   EmbeddedR_findVar_doc},
  {"sexpTypeEmbeddedR",	(PyCFunction)EmbeddedR_sexpType, METH_VARARGS,
   "Return the SEXP name tag corresponding to an integer."},
  {NULL,		NULL}		/* sentinel */
};




/* A. Belopolsky's callback */

/* R representation of a PyObject */

static SEXP R_PyObject_type_tag;

static SEXP
R_PyObject_decref(SEXP s)
{
	PyObject* pyo = (PyObject*)R_ExternalPtrAddr(s);
	if (pyo) {
		Py_DECREF(pyo);
		R_ClearExternalPtr(s);
	}
	return R_NilValue;
}

static SEXP
mkPyObject(PyObject* pyo)
{
	SEXP res;
	Py_INCREF(pyo);
	res = R_MakeExternalPtr(pyo, R_PyObject_type_tag, R_NilValue);
	R_RegisterCFinalizer(res, (R_CFinalizer_t)R_PyObject_decref);
	return res;
}

#define R_PyObject_TYPE_CHECK(s) \
  (TYPEOF(s) == EXTPTRSXP && R_ExternalPtrTag(s) == R_PyObject_type_tag)

static SEXP
do_Python(SEXP args)
{
  SEXP sexp = CADR(args);
  SEXP res;
  if (!R_PyObject_TYPE_CHECK(sexp)) {
    error(".Python: invalid python type");
    return R_NilValue;
  }
  //PyTypeObject* type = R_ExternalPtrAddr(sexp);
  args = CDDR(args);
  sexp = CAR(args);
  if (!R_PyObject_TYPE_CHECK(sexp)) {
    error(".Python: invalid function");
    return R_NilValue;
  }
  PyObject *pyf = R_ExternalPtrAddr(sexp);
  
  /* create argument list */
  PyObject *pyargs = PyList_New(0);
  PyObject *pyres;
  for (args = CDR(args); args != R_NilValue; args = CDR(args)) {
    sexp = CAR(args);
    if (R_PyObject_TYPE_CHECK(sexp)) {
      PyList_Append(pyargs, (PyObject *)R_ExternalPtrAddr(sexp));
    }
    else {
      PyList_Append(pyargs, (PyObject *)newPySexpObject(sexp));
    }
  }
  PyObject *pyargstup = PyList_AsTuple(pyargs);
  /*FIXME: named arguments are not supported yet */
  pyres = PyObject_Call(pyf, pyargstup, NULL);
  if (!pyres) {
    PyObject *exctype;
    PyObject *excvalue; 
    PyObject *exctraceback;
    PyObject *excstr;
    PyErr_Fetch(&exctype, &excvalue, &exctraceback);
    excstr = PyObject_Str(excvalue);
    if (excstr) {
      error(PyString_AS_STRING(excstr));
      Py_DECREF(excstr);
    } 
    else {
      error("Python error");
    }
    PyErr_Clear();
  }
  Py_DECREF(pyargs);
  Py_DECREF(pyargstup);
  if (PyObject_IsInstance((PyObject*)pyres, 
			  (PyObject*)&Sexp_Type)) {
    res = RPY_SEXP((PySexpObject*)pyres);
  }
  else {
    res = mkPyObject(pyres);
  }
  Py_DECREF(pyres);
  
  return res;
}

static R_ExternalMethodDef externalMethods[] = { 
	{".Python", (DL_FUNC)&do_Python, -1},
	{NULL, NULL, 0} 
};



/* --- Initialize the module ---*/

#define ADD_INT_CONSTANT(module, name) \
  PyModule_AddIntConstant(module, #name, name)
#define ADD_VALID_SEXP(name) \
  validSexpType[name] = #name
#define PYASSERT_ZERO(code) \
  if ((code) != 0) {return ; }


#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif

PyMODINIT_FUNC
initrinterface(void)
{
//PyMODINIT_FUNC
//RPY_RINTERFACE_INIT(void)
//{

  /* Finalize the type object including setting type of the new type
	 * object; doing it here is required for portability to Windows 
	 * without requiring C++. */
  if (PyType_Ready(&Sexp_Type) < 0)
    return;
  if (PyType_Ready(&ClosureSexp_Type) < 0)
    return;
  if (PyType_Ready(&VectorSexp_Type) < 0)
    return;
  if (PyType_Ready(&EnvironmentSexp_Type) < 0)
    return;
  if (PyType_Ready(&S4Sexp_Type) < 0)
    return;

  PyObject *m, *d;
  m = Py_InitModule3("rinterface", EmbeddedR_methods, module_doc);
  if (m == NULL)
    return;
  d = PyModule_GetDict(m);

  initOptions = PyList_New(4);
  PYASSERT_ZERO(
		PyList_SetItem(initOptions, 0, 
			       PyString_FromString("rpy2"))
		);
  PYASSERT_ZERO(
		PyList_SetItem(initOptions, 1, 
			       PyString_FromString("--quiet"))
		);
  PYASSERT_ZERO(
		PyList_SetItem(initOptions, 2, 
			       PyString_FromString("--vanilla"))
		);
  PYASSERT_ZERO(
		PyList_SetItem(initOptions, 3, 
			       PyString_FromString("--no-save"))
		);
  PyModule_AddObject(m, "initOptions", initOptions);
			       //			       PyString_FromString("--quiet"))


  PyModule_AddObject(m, "Sexp", (PyObject *)&Sexp_Type);
  PyModule_AddObject(m, "SexpClosure", (PyObject *)&ClosureSexp_Type);
  PyModule_AddObject(m, "SexpVector", (PyObject *)&VectorSexp_Type);
  PyModule_AddObject(m, "SexpEnvironment", (PyObject *)&EnvironmentSexp_Type);
  PyModule_AddObject(m, "SexpS4", (PyObject *)&S4Sexp_Type);


  if (RPyExc_RuntimeError == NULL) {
    RPyExc_RuntimeError = PyErr_NewException("rinterface.RRuntimeError", 
					     NULL, NULL);
    if (RPyExc_RuntimeError == NULL)
      return;
  }
  
  Py_INCREF(RPyExc_RuntimeError);
  PyModule_AddObject(m, "RRuntimeError", RPyExc_RuntimeError);

  embeddedR_isInitialized = Py_False;
  Py_INCREF(Py_False);

  if (PyModule_AddObject(m, "isInitialized", embeddedR_isInitialized) < 0)
    return;
  //FIXME: DECREF ?
  //Py_DECREF(embeddedR_isInitialized);

  globalEnv = (PySexpObject *)Sexp_new(&EnvironmentSexp_Type, 
				       Py_None, Py_None);
  RPY_SEXP(globalEnv) = R_EmptyEnv;

  if (PyDict_SetItemString(d, "globalEnv", (PyObject *)globalEnv) < 0)
    return;
  //FIXME: DECREF ?
  //Py_DECREF(globalEnv);

  baseNameSpaceEnv = (PySexpObject*)Sexp_new(&EnvironmentSexp_Type,
					     Py_None, Py_None);
  RPY_SEXP(baseNameSpaceEnv) = R_EmptyEnv;
  if (PyDict_SetItemString(d, "baseNameSpaceEnv", 
			   (PyObject *)baseNameSpaceEnv) < 0)
    return;
/*   //FIXME: DECREF ? */
/*   Py_DECREF(baseNameSpaceEnv); */


  /* Add SXP types */
  validSexpType = calloc(maxValidSexpType, sizeof(char *));
  if (! validSexpType) {
    PyErr_NoMemory();
    return;
  }
  ADD_INT_CONSTANT(m, NILSXP);
  ADD_VALID_SEXP(NILSXP);
  ADD_INT_CONSTANT(m, SYMSXP);
  ADD_VALID_SEXP(SYMSXP);
  ADD_INT_CONSTANT(m, LISTSXP);
  ADD_VALID_SEXP(LISTSXP);
  ADD_INT_CONSTANT(m, CLOSXP);
  ADD_VALID_SEXP(CLOSXP);
  ADD_INT_CONSTANT(m, ENVSXP);
  ADD_VALID_SEXP(ENVSXP);
  ADD_INT_CONSTANT(m, PROMSXP);
  ADD_VALID_SEXP(PROMSXP);
  ADD_INT_CONSTANT(m, LANGSXP);
  ADD_VALID_SEXP(LANGSXP);
  ADD_INT_CONSTANT(m, SPECIALSXP);
  ADD_VALID_SEXP(SPECIALSXP);
  ADD_INT_CONSTANT(m, BUILTINSXP);
  ADD_VALID_SEXP(BUILTINSXP);
  ADD_INT_CONSTANT(m, CHARSXP);
  ADD_VALID_SEXP(CHARSXP);
  ADD_INT_CONSTANT(m, STRSXP);
  ADD_VALID_SEXP(STRSXP);
  ADD_INT_CONSTANT(m, LGLSXP);
  ADD_VALID_SEXP(LGLSXP);
  ADD_INT_CONSTANT(m, INTSXP);
  ADD_VALID_SEXP(INTSXP);
  ADD_INT_CONSTANT(m, REALSXP);
  ADD_VALID_SEXP(REALSXP);
  ADD_INT_CONSTANT(m, CPLXSXP);
  ADD_VALID_SEXP(CPLXSXP);
  ADD_INT_CONSTANT(m, DOTSXP);
  ADD_VALID_SEXP(DOTSXP);
  ADD_INT_CONSTANT(m, ANYSXP);
  ADD_VALID_SEXP(ANYSXP);
  ADD_INT_CONSTANT(m, VECSXP);
  ADD_VALID_SEXP(VECSXP);
  ADD_INT_CONSTANT(m, EXPRSXP);
  ADD_VALID_SEXP(EXPRSXP);
  ADD_INT_CONSTANT(m, BCODESXP);
  ADD_VALID_SEXP(BCODESXP);
  ADD_INT_CONSTANT(m, EXTPTRSXP);
  ADD_VALID_SEXP(EXTPTRSXP);
  ADD_INT_CONSTANT(m, RAWSXP);
  ADD_VALID_SEXP(RAWSXP);
  ADD_INT_CONSTANT(m, S4SXP);
  ADD_VALID_SEXP(S4SXP);

  /* longuest integer for R indexes */
  ADD_INT_CONSTANT(m, R_LEN_T_MAX);

  /* "Logical" (boolean) values */
  ADD_INT_CONSTANT(m, TRUE);
  ADD_INT_CONSTANT(m, FALSE);

  /* R_ext/Arith.h */
  ADD_INT_CONSTANT(m, NA_LOGICAL);
  ADD_INT_CONSTANT(m, NA_INTEGER);
  PyObject *na_real = PyFloat_FromDouble(NA_REAL);
  if (PyDict_SetItemString(d, "NA_REAL", (PyObject *)na_real) < 0)
    return;
  //FIXME: DECREF ?
  Py_DECREF(na_real);

  
/*   /\* Rinternals.h *\/ */
  na_string = (PySexpObject *)Sexp_new(&VectorSexp_Type,
				       Py_None, Py_None);

  RPY_SEXP(na_string) = NA_STRING;
  if (PyDict_SetItemString(d, "NA_STRING", (PyObject *)na_string) < 0)
    return;
/*   //FIXME: DECREF ? */
  //Py_DECREF(na_string);


}
