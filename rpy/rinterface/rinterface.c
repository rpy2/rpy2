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
 * Original code from wrapping R's C-level SEXPs:   belopolsky
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
#include <Rinterface.h>
#include <R_ext/Complex.h>
#include <Rembedded.h>

/* FIXME: consider the use of parsing */
/* #include <R_ext/Parse.h> */
#include <R_ext/Rdynload.h>

#include <signal.h>

/* Back-compatibility with Python 2.4 */
#if (PY_VERSION_HEX < 0x02050000)
typedef int Py_ssize_t;
typedef inquiry lenfunc;
typedef intargfunc ssizeargfunc;
typedef intobjargproc ssizeobjargproc;
#endif


//FIXME: see the details of error handling
static PyObject *ErrorObject;

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
 Example of usage:n\
import rinterface\n\
rinterface.initEmbeddedR(\"foo\", \"--verbose\")\n\
n = rinterface.SexpVector((100, ), rinterface.REALSXP)\n\
hist = rinterface.globalEnv.get(\"hist\")\n\
rnorm = rinterface.globalEnv.get(\"rnorm\")\n\
x = rnorm(n)\n\
hist(x)\n\
\
len(x)\n\
\n\
");
//FIXME: check example above


/* Representation of R objects (instances) as instances in Python.
 */
typedef struct {
  PyObject_HEAD 
  SEXP sexp;
} SexpObject;


static SexpObject* globalEnv;
static SexpObject* baseNameSpaceEnv;

/* early definition of functions */
static SexpObject* newSexpObject(const SEXP sexp);
static SEXP newSEXP(PyObject *object, const int rType);


/* --- Initialize and terminate an embedded R --- */
/* Should having multiple threads of R become possible, 
 * useful routines could appear here...
 */
static PyObject* EmbeddedR_init(PyObject *self, PyObject *args) 
{

  if (PyObject_IsTrue(embeddedR_isInitialized)) {
    PyErr_Format(PyExc_RuntimeError, "Already initialized.");
    return NULL;
  }

  //FIXME: arbitrary number of options
  //char *defaultargv[] = {"rpython", "--verbose"};
  char *options[5] = {"", "", "", "", ""};

  if (!PyArg_ParseTuple(args, "s|ssss", 
			&options[0], &options[1],
			&options[2], &options[3],
			&options[4]
			)) { 
    return NULL; 
  }
  
  int n_opt;
  for (n_opt=0; n_opt<5; n_opt++) {
    if (options[n_opt] == "") {
      break;
    }
  }
  
  int status = Rf_initEmbeddedR(n_opt, options);

  embeddedR_isInitialized = PyBool_FromLong((long)1);

  globalEnv->sexp = R_GlobalEnv;

  baseNameSpaceEnv->sexp = R_BaseNamespace;

  PyObject *res = PyInt_FromLong(status);

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
  /* sanity checks needed ? */

  Rf_endEmbeddedR((int)fatal);
  globalEnv->sexp = R_EmptyEnv;
  baseNameSpaceEnv->sexp = R_EmptyEnv;

  Py_RETURN_NONE;
}
PyDoc_STRVAR(EmbeddedR_end_doc,
	     "endEmbeddedR()\n\
\n\
Terminate an embedded R.");


/* --- set output from the R console ---*/

static void
EmbeddedR_WriteConsole(char *buf, int len)
{
  PyOS_sighandler_t old_int;

  /* It is necessary to restore the Python handler when using a Python
     function for I/O. */
  old_int = PyOS_getsig(SIGINT);
  PyOS_setsig(SIGINT, python_sigint);
  PySys_WriteStdout(buf);
  signal(SIGINT, old_int);
}


/* Redirect R console output */
//  R_Outputfile = NULL;


/* FIXME: implement possibility to specify arbitrary callback functions */
extern void (*ptr_R_WriteConsole)(char *, int);
static PyObject* EmbeddedR_setWriteConsole(PyObject *self)
{
  ptr_R_WriteConsole = EmbeddedR_WriteConsole;
  Py_RETURN_NONE;
}
PyDoc_STRVAR(EmbeddedR_setWriteConsole_doc,
	     "setWriteConsoleEmbeddedR()\n\
\n\
Set the R console output to the Python console.");


static PyObject*
EmbeddedR_exception_from_errmessage(void)
{
  //FIXME: sort the error message thing geterrmessage
  PyErr_SetString(ErrorObject, "Error.");
  return NULL;
}




/*
 * Access to R objects through Python objects
 */

/* static PyObject* */
/* Sexp_new(PyTypeObject *type, PyObject *args) */
/* { */
/*   PyObject object, res; */
/*   if (!PyArg_ParseTuple(args, "O:new", */
/* 			&object)) */
/*     PyErr_Format(PyExc_ValueError, "Can only instanciate from SexpObject"); */
/*   return NULL; */
/*   res = (SexpObject *)_PyObject_New(&Sexp_Type); */
/*   if (!res) */
/*     PyErr_NoMemory(); */
/*   res->sexp = sexp; */
/*   return res; */
/* } */

static void
Sexp_dealloc(SexpObject *self)
{
  if (self->sexp)
    R_ReleaseObject(self->sexp);
  //self->ob_type->tp_free((PyObject*)self);
  PyObject_Del(self);
}


static PyObject*
Sexp_repr(PyObject *self)
{
  //FIXME: make sure this is making any sense
  SEXP sexp = ((SexpObject *)self)->sexp;
  if (! sexp) {
      PyErr_Format(PyExc_ValueError, "NULL SEXP.");
      return NULL;;
    }
  return PyString_FromFormat("<%s - Python:\%p / R:\%p>",
			     self->ob_type->tp_name,
			     self,
			     sexp);
}


static PyObject*
Sexp_typeof(PyObject *self)
{
  SEXP sexp =((SexpObject*)self)->sexp;
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
  SEXP sexp =((SexpObject*)self)->sexp;
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

  PyObject *res = (PyObject *)newSexpObject(res_R);
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


/*
 * Generic Sexp_Type. It represents SEXP objects at large.
 */
static PyTypeObject Sexp_Type = {
	/* The ob_type field must be initialized in the module init function
	 * to be portable to Windows without using C++. */
	PyObject_HEAD_INIT(NULL)
	0,			/*ob_size*/
	"rinterface.Sexp",	/*tp_name*/
	sizeof(SexpObject),	/*tp_basicsize*/
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
        0,//Sexp_str,               /*tp_str*/
        0,                      /*tp_getattro*/
        0,                      /*tp_setattro*/
        0,                      /*tp_as_buffer*/
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE,     /*tp_flags*/
        0,                      /*tp_doc*/
        0,                      /*tp_traverse*/
        0,                      /*tp_clear*/
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
        0,                      /*tp_init*/
        0,                      /*tp_alloc*/
        0, //Sexp_new,               /*tp_new*/
        0,                      /*tp_free*/
        0,                      /*tp_is_gc*/
};


/*
 * Closure-type Sexp.
 */


/* Evaluate a SEXP. It must be constructed by hand. It raises a Python
   exception if an error ocurred in the evaluation */
SEXP do_eval_expr(SEXP expr_R, SEXP env_R) {
  SEXP res_R = NULL;
  int error = 0;
  PyOS_sighandler_t old_int;
  
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
  SEXP tmp_R;
  
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
  tmp_R = ((SexpObject *)self)->sexp;
  if (! tmp_R) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    goto fail;
  }
  SETCAR(c_R, tmp_R);
  c_R = CDR(c_R);

  int arg_i;
  PyObject *tmp_obj;
  int is_SexpObject;
  for (arg_i=0; arg_i<largs; arg_i++) {
    tmp_obj = PyTuple_GetItem(args, arg_i);
    is_SexpObject = PyObject_TypeCheck(tmp_obj, &Sexp_Type);
    if (! is_SexpObject) {
      PyErr_Format(PyExc_ValueError, 
		   "All parameters must be of type Sexp_Type.");
      Py_DECREF(tmp_obj);
      goto fail;
    }
    tmp_R = ((SexpObject *)tmp_obj)->sexp;
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
      is_SexpObject = PyObject_TypeCheck(argValue, &Sexp_Type);
      if (! is_SexpObject) {
	PyErr_Format(PyExc_ValueError, 
		     "All named parameters must be of type Sexp_Type.");
	Py_DECREF(tmp_obj);	
	Py_XDECREF(citems);
	goto fail;
      }
      Py_DECREF(tmp_obj);
      tmp_R = ((SexpObject *)argValue)->sexp;
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
  PROTECT(res_R = do_eval_expr(call_R, R_GlobalEnv));

/*   if (!res) { */
/*     UNPROTECT(2); */
/*     return NULL; */
/*   } */
  UNPROTECT(2);
  //FIXME: standardize R outputs
  extern void Rf_PrintWarnings(void);
  Rf_PrintWarnings(); /* show any warning messages */

  PyObject *res = (PyObject *)newSexpObject(res_R);
  return res;
  
 fail:
  printf("failed.\n");
  UNPROTECT(1);
  return NULL;

}




static SexpObject*
Sexp_closureEnv(PyObject *self)
{
  SEXP closureEnv, sexp;
  sexp = ((SexpObject*)self)->sexp;
  if (! sexp) {
      PyErr_Format(PyExc_ValueError, "NULL SEXP.");
      return NULL;
  }
  closureEnv = CLOENV(sexp);
  return newSexpObject(closureEnv);
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

//FIXME: write more doc
PyDoc_STRVAR(ClosureSexp_Type_doc,
"A R object that is a closure, that is a function. \
In R a function is defined within an enclosing \
environment, thus the name closure. \
In Python, 'nested scopes' could be the closest similar thing.\
\n\
The closure can be accessed with the method 'closureEnv'.\
");

static PyTypeObject ClosureSexp_Type = {
	/* The ob_type field must be initialized in the module init function
	 * to be portable to Windows without using C++. */
	PyObject_HEAD_INIT(NULL)
	0,			/*ob_size*/
	"rinterface.SexpClosure",	/*tp_name*/
	sizeof(SexpObject),	/*tp_basicsize*/
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
        0,                      /*tp_init*/
        0,                      /*tp_alloc*/
        0,//Sexp_new,               /*tp_new*/
        0,                      /*tp_free*/
        0                      /*tp_is_gc*/
};

static PyObject*
VectorSexp_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  int rType = -1;
  PyObject *seq = 0;
  if (!PyArg_ParseTuple(args, "Oi:new",
			&seq, &rType))
    return NULL;
  const SEXP sexp = newSEXP(seq, rType);
  if (! sexp)
    return NULL;
  PyObject *res = (PyObject *)newSexpObject(sexp);
  return res;
}

/* len(x) */
static Py_ssize_t VectorSexp_len(PyObject *object)
{
  Py_ssize_t len;
  //FIXME: sanity checks.
  SEXP sexp = ((SexpObject *)object)->sexp;
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
  SEXP *sexp = &(((SexpObject *)object)->sexp);

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
    case VECSXP:
      res = (PyObject *)newSexpObject(VECTOR_ELT(*sexp, i_R));
      break;
    default:
      PyErr_Format(PyExc_ValueError, "cannot handle type %d", 
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

  SEXP *sexp = &(((SexpObject *)object)->sexp);
  if (i >= GET_LENGTH(*sexp)) {
    PyErr_Format(PyExc_IndexError, "Index out of range.");
    return -1;
  }

  if (! sexp) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return -1;
  }

  int is_SexpObject = PyObject_TypeCheck(val, &Sexp_Type);
  if (! is_SexpObject) {
    PyErr_Format(PyExc_ValueError, "Any new value must be of "
		 "type 'Sexp_Type'.");
    return -1;
  }
  SEXP *sexp_val = &(((SexpObject *)val)->sexp);
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
    SET_STRING_ELT(*sexp, i_R, *sexp_val);
    break;
  case VECSXP:
    SET_VECTOR_ELT(*sexp, i_R, *sexp_val);
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
  //FIXME: implement
  (ssizeargfunc)VectorSexp_item,        /* sq_item */
  //FIXME: implement
  0, //(ssizessizeargfunc)VectorSexp_slice,  /* sq_slice */
  //FIXME: implement
  (ssizeobjargproc)VectorSexp_ass_item,   /* sq_ass_item */
  0,                              /* sq_ass_slice */
  0,                              /* sq_contains */
  0,                              /* sq_inplace_concat */
  0                               /* sq_inplace_repeat */
};

//FIXME: write more doc
PyDoc_STRVAR(VectorSexp_Type_doc,
"R object that is a vector.\
 R vectors start their indexing at one,\
 while Python lists or arrays start indexing\
 at zero.\
\n\
In the hope to avoid confusion, the indexing\
 from the Python subset operator (__getitem__)\
 is done at zero.");
/* ", while an other method to perform\ */
/*  it at one is provided (_not yet implemented_).\ */
/*  That other method is also performing indexing."); */
//FIXME: implement offset-one indexing.

static PyTypeObject VectorSexp_Type = {
	/* The ob_type field must be initialized in the module init function
	 * to be portable to Windows without using C++. */
	PyObject_HEAD_INIT(NULL)
	0,			/*ob_size*/
	"rinterface.SexpVector",	/*tp_name*/
	sizeof(SexpObject),	/*tp_basicsize*/
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
        0,//Sexp_getset,            /*tp_getset*/
        &Sexp_Type,             /*tp_base*/
        0,                      /*tp_dict*/
        0,                      /*tp_descr_get*/
        0,                      /*tp_descr_set*/
        0,                      /*tp_dictoffset*/
        0,                      /*tp_init*/
        0,                      /*tp_alloc*/
        VectorSexp_new,               /*tp_new*/
        0,                      /*tp_free*/
        0                      /*tp_is_gc*/
};


/* --- */

static SexpObject*
EnvironmentSexp_findVar(PyObject *self, PyObject *args)
{
  char *name;
  SEXP res_R = NULL;

  if (!PyArg_ParseTuple(args, "s", &name)) { 
    return NULL; 
  }

  const SEXP rho_R = ((SexpObject *)self)->sexp;
  if (! rho_R) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return NULL;
  }

  if (rho_R == R_EmptyEnv) {
    PyErr_Format(PyExc_LookupError, "Fatal error: R_UnboundValue.");
  }

  res_R = findVar(install(name), rho_R);


  if (res_R != R_UnboundValue) {
    return newSexpObject(res_R);
  }
  PyErr_Format(PyExc_LookupError, "'%s' not found", name);
  return NULL;
}
PyDoc_STRVAR(EnvironmentSexp_findVar_doc,
	     "Find an R object in the environment.");

static PyMethodDef EnvironmentSexp_methods[] = {
  {"get", (PyCFunction)EnvironmentSexp_findVar, METH_VARARGS,
  EnvironmentSexp_findVar_doc},
  {NULL, NULL}          /* sentinel */
};


static SexpObject*
EnvironmentSexp_subscript(PyObject *self, PyObject *key)
{
  char *name;
  SEXP res_R = NULL;

  if (!PyString_Check(key)) {
    PyErr_Format(PyExc_ValueError, "Keys must be string objects.");
    return NULL;
  }

  name = PyString_AsString(key);
  
  SEXP rho_R = ((SexpObject *)self)->sexp;
  if (! rho_R) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return NULL;
  }
  res_R = findVarInFrame(rho_R, install(name));

  if (res_R != R_UnboundValue) {
    return newSexpObject(res_R);
  }
  PyErr_Format(PyExc_LookupError, "'%s' not found", name);
  return NULL;
}
PyDoc_STRVAR(EnvironmentSexp_subscript_doc,
	     "Find an R object in the environment.\n\
 Not all R environment are hash tables, and this may\
 influence performances when doing repeated lookups.");

static int
EnvironmentSexp_ass_subscript(PyObject *self, PyObject *key, PyObject *value)
{
  char *name;

  if (!PyString_Check(key)) {
    PyErr_Format(PyExc_ValueError, "Keys must be string objects.");
    return -1;
  }

  int is_SexpObject = PyObject_TypeCheck(value, &Sexp_Type);
  if (! is_SexpObject) {
    PyErr_Format(PyExc_ValueError, 
		 "All parameters must be of type Sexp_Type.");
    //PyDecRef(value);
    return -1;
  }

  name = PyString_AsString(key);
  
  SEXP rho_R = ((SexpObject *)self)->sexp;
  if (! rho_R) {
    PyErr_Format(PyExc_ValueError, "The environment has NULL SEXP.");
    return -1;
  }

  SEXP sexp_copy;
  SEXP sexp = ((SexpObject *)value)->sexp;
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
  SEXP rho_R = ((SexpObject *)self)->sexp;
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

static PyMappingMethods EnvironmentSexp_mappignMethods = {
  (lenfunc)EnvironmentSexp_length, /* mp_length */
  (binaryfunc)EnvironmentSexp_subscript, /* mp_subscript */
  (objobjargproc)EnvironmentSexp_ass_subscript  /* mp_ass_subscript */
};

static PyObject* 
EnvironmentSexp_iter(PyObject *sexpEnvironment)
{
  SEXP rho_R = ((SexpObject *)sexpEnvironment)->sexp;

  if (! rho_R) {
    PyErr_Format(PyExc_ValueError, "The environment has NULL SEXP.");
    return NULL;
  }
  SEXP symbols;
  PROTECT(symbols = R_lsInternal(rho_R, TRUE));
  SexpObject *seq = newSexpObject(symbols);
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

static PyTypeObject EnvironmentSexp_Type = {
	/* The ob_type field must be initialized in the module init function
	 * to be portable to Windows without using C++. */
	PyObject_HEAD_INIT(NULL)
	0,			/*ob_size*/
	"rinterface.SexpEnvironment",	/*tp_name*/
	sizeof(SexpObject),	/*tp_basicsize*/
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
	&EnvironmentSexp_mappignMethods,			/*tp_as_mapping*/
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
        0,                      /*tp_init*/
        0,                      /*tp_alloc*/
	//FIXME: add new method
        0, //EnvironmentSexp_new,               /*tp_new*/
        0,                      /*tp_free*/
        0                      /*tp_is_gc*/
};


//FIXME: write more doc
PyDoc_STRVAR(S4Sexp_Type_doc,
"R object that is an 'S4 object'.\
");

static PyTypeObject S4Sexp_Type = {
	/* The ob_type field must be initialized in the module init function
	 * to be portable to Windows without using C++. */
	PyObject_HEAD_INIT(NULL)
	0,			/*ob_size*/
	"rinterface.SexpS4",	/*tp_name*/
	sizeof(SexpObject),	/*tp_basicsize*/
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
static SexpObject*
newSexpObject(const SEXP sexp)
{
  SexpObject *object;
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
    object  = (SexpObject *)PyObject_New(SexpObject,
					 &ClosureSexp_Type);
    break;
    //FIXME: BUILTINSXP and SPECIALSXP really like CLOSXP ?
  case REALSXP: 
  case INTSXP: 
  case LGLSXP:
  case CPLXSXP:
  case VECSXP:
  case STRSXP:
    object = (SexpObject *)PyObject_New(SexpObject,
					&VectorSexp_Type);
    break;
  case ENVSXP:
    object = (SexpObject *)PyObject_New(SexpObject,
					&EnvironmentSexp_Type);
    break;
  case S4SXP:
    object = (SexpObject *)PyObject_New(SexpObject,
					&S4Sexp_Type);
    break;
  default:
    object  = (SexpObject *)PyObject_New(SexpObject,
					 &Sexp_Type); 
    break;
  }
  if (!object) {
    R_ReleaseObject(sexp_ok);
    PyErr_NoMemory();
    return NULL;
  }
  //PyObject_Init(&object, &ClosureSexp_Type);
  object->sexp = sexp_ok;
  //FIXME: Increment reference ?
  //Py_INCREF(object);
  return object;
}

static SEXP
newSEXP(PyObject *object, int rType)
{
  SEXP sexp;
  PyObject *seq_object, *item; 
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
	int is_SexpObject = PyObject_TypeCheck(item, &Sexp_Type);
	if (! is_SexpObject) {
	  Py_DECREF(item);
	  PyErr_Format(PyExc_ValueError, "All elements of the list must be of "
		       "type 'Sexp_Type'.");
	  return NULL;
	}
	SET_ELEMENT(sexp, i, ((SexpObject *)item)->sexp);
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
    PyErr_Format(PyExc_ValueError, "cannot handle type %d", rType);
    sexp = NULL;
  }
  UNPROTECT(1);
  return sexp;
}



/* --- Find a variable in an environment --- */


static SexpObject*
EmbeddedR_findVar(PyObject *self, PyObject *args)
{
  char *name;
  SEXP rho_R = R_GlobalEnv, res;
  PyObject rho;
  PyObject *ErrorObject;

  if (!PyArg_ParseTuple(args, "s", &name, &rho)) { 
    return NULL; 
  }

  res = findVar(install(name), rho_R);


  if (res != R_UnboundValue) {
    return newSexpObject(res);
  }
  PyErr_Format(PyExc_LookupError, "'%s' not found", name);
  return NULL;
}
PyDoc_STRVAR(EmbeddedR_findVar_doc,
	     "Find a variable in R's .GlobalEnv.");




/* --- List of functions defined in the module --- */

static PyMethodDef EmbeddedR_methods[] = {
  {"initEmbeddedR",     (PyCFunction)EmbeddedR_init,   METH_VARARGS,
   EmbeddedR_init_doc},
  {"endEmbeddedR",	(PyCFunction)EmbeddedR_end,    METH_O,
   EmbeddedR_end_doc},
  {"setWriteConsole",	(PyCFunction)EmbeddedR_setWriteConsole,	 METH_NOARGS,
   EmbeddedR_setWriteConsole_doc},
  {"findVarEmbeddedR",	(PyCFunction)EmbeddedR_findVar,	 METH_VARARGS,
   EmbeddedR_findVar_doc},
  {NULL,		NULL}		/* sentinel */
};




/* --- Initialize the module ---*/

#define ADD_INT_CONSTANT(module, name) PyModule_AddIntConstant(module, #name, name)


PyMODINIT_FUNC
initrinterface(void)
{
  
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

  PyModule_AddObject(m, "Sexp", (PyObject *)&Sexp_Type);
  PyModule_AddObject(m, "SexpClosure", (PyObject *)&ClosureSexp_Type);
  PyModule_AddObject(m, "SexpVector", (PyObject *)&VectorSexp_Type);
  PyModule_AddObject(m, "SexpEnvironment", (PyObject *)&EnvironmentSexp_Type);
  PyModule_AddObject(m, "SexpS4", (PyObject *)&S4Sexp_Type);

  //FIXME: clean the exception stuff
  if (ErrorObject == NULL) {
    ErrorObject = PyErr_NewException("rinterface.error", NULL, NULL);
    if (ErrorObject == NULL)
      return;
  }
  Py_INCREF(ErrorObject);
  PyModule_AddObject(m, "RobjectNotFound", ErrorObject);

  embeddedR_isInitialized = PyBool_FromLong((long)0);
  if (PyModule_AddObject(m, "isInitialized", embeddedR_isInitialized) < 0)
    return;
  //FIXME: DECREF ?
  //Py_DECREF(embeddedR_isInitialized);

  globalEnv = (SexpObject *)PyObject_New(SexpObject, 
					 &EnvironmentSexp_Type);
  globalEnv->sexp = R_EmptyEnv;
  if (PyDict_SetItemString(d, "globalEnv", (PyObject *)globalEnv) < 0)
    return;
  //FIXME: DECREF ?
  Py_DECREF(globalEnv);

  baseNameSpaceEnv = (SexpObject*)PyObject_New(SexpObject, 
					       &EnvironmentSexp_Type);
  baseNameSpaceEnv->sexp = R_EmptyEnv;
  if (PyDict_SetItemString(d, "baseNameSpaceEnv", (PyObject *)baseNameSpaceEnv) < 0)
    return;
  //FIXME: DECREF ?
  Py_DECREF(baseNameSpaceEnv);

  /* Add SXP types */
  ADD_INT_CONSTANT(m, NILSXP);
  ADD_INT_CONSTANT(m, SYMSXP);
  ADD_INT_CONSTANT(m, LISTSXP);
  ADD_INT_CONSTANT(m, CLOSXP);
  ADD_INT_CONSTANT(m, ENVSXP);
  ADD_INT_CONSTANT(m, PROMSXP);
  ADD_INT_CONSTANT(m, LANGSXP);
  ADD_INT_CONSTANT(m, SPECIALSXP);
  ADD_INT_CONSTANT(m, BUILTINSXP);
  ADD_INT_CONSTANT(m, CHARSXP);
  ADD_INT_CONSTANT(m, STRSXP);
  ADD_INT_CONSTANT(m, LGLSXP);
  ADD_INT_CONSTANT(m, INTSXP);
  ADD_INT_CONSTANT(m, REALSXP);
  ADD_INT_CONSTANT(m, CPLXSXP);
  ADD_INT_CONSTANT(m, DOTSXP);
  ADD_INT_CONSTANT(m, ANYSXP);
  ADD_INT_CONSTANT(m, VECSXP);
  ADD_INT_CONSTANT(m, EXPRSXP);
  ADD_INT_CONSTANT(m, BCODESXP);
  ADD_INT_CONSTANT(m, EXTPTRSXP);
  ADD_INT_CONSTANT(m, RAWSXP);
  ADD_INT_CONSTANT(m, S4SXP);

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

  
  /* Rinternals.h */
  SexpObject *na_string = (SexpObject *)PyObject_New(SexpObject,
						     &VectorSexp_Type);
  na_string->sexp = NA_STRING;
  if (PyDict_SetItemString(d, "NA_STRING", (PyObject *)na_string) < 0)
    return;
  //FIXME: DECREF ?
  Py_DECREF(na_string);

   
}
