/* A python-R interface*/

/* 
 * This is an attempt at cleaning up RPy, while adding features
 * at the same time. In other words, this can be seen as a rewrite 
 * of RPy.
 *
 * The authors for the original RPy code, as well as
 * belopolsky's contributed code, are listed here as authors;
 * parts of this code is (sometimes shamelessly but with great 
 * respect for the work) "inspired" from their contributions. 
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
#include <Rembedded.h>

/* FIXME: consider the use of parsing */
/* #include <R_ext/Parse.h> */
#include <R_ext/Rdynload.h>

#include <signal.h>

//FIXME: get this out ASAP
#define VERBOSE

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




/* The Python original SIGINT handler */
PyOS_sighandler_t python_sigint;

PyDoc_STRVAR(module_doc,
	     "Low-level functions to interface with R.\n\
 One should mostly consider calling the functions defined here when\
 writing a higher level interface between python and R.\
 Check the documentation for the module this is bundled into if\
 you only wish to have an off-the-shelf interface with R.\
\n\
 Example of usage:\
import rinterface\
rinterface.initEmbeddedR(\"foo\", \"--verbose\")\
n = rinterface.SexpVector(rinterface.REALSXP, (100,))\
hist = rinterface.findVarEmbeddedR(\"hist\")\
rnorm = rinterface.findVarEmbeddedR(\"rnorm\")\
x = rnorm(n)\
hist(x)\
");
//FIXME: check example above


/* Representation of R objects (instances) as instances in Python.
 */
typedef struct {
  PyObject_HEAD
  SEXP sexp;
} SexpObject;




/* --- Initialize and terminate an embedded R --- */
/* Should having multiple threads of R become possible, 
 * Useful routines deal with can could appear here...
 */
static PyObject* EmbeddedR_init(PyObject *self, PyObject *args) 
{
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
  PyObject *res = PyInt_FromLong(status);
  return res;
}
PyDoc_STRVAR(EmbeddedR_init_doc,
	     "initEmbeddedR()\n\
\n\
Initialize an embedded R.");


static PyObject* EmbeddedR_end(PyObject *self, PyObject *arg)
{
  //FIXME: Have a reference count for R objects known to Python.
  //ending R will not be possible until all such objects are already
  //deallocated in Python ?
  //other possibility would be to have a fallback for "unreachable" objects ?
  //FIXME: rpy has something to terminate R. Check the details of what it is. 
  if (! PyInt_Check(arg)) {
  } else {
    /* sanity checks needed ? */
    const long fatal = PyInt_AsLong(arg);
    Rf_endEmbeddedR((int)fatal);
  }
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

static void
Sexp_dealloc(SexpObject *self)
{
  if (self->sexp)
    R_ReleaseObject(self->sexp);
  self->ob_type->tp_free((PyObject*)self);
}


static PyObject*
Sexp_repr(PyObject *self)
{
  return PyString_FromFormat("<%s - Python:\%p / R:\%p>",
			     self->ob_type->tp_name,
			     self,
			     &(((SexpObject *)self)->sexp));
}


static PyObject*
Sexp_typeof(PyObject *self)
{
  return PyInt_FromLong(TYPEOF(((SexpObject*)self)->sexp));
}
PyDoc_STRVAR(Sexp_typeof_doc,
"\n\
Returns the R internal SEXP type.");

static PyMethodDef Sexp_methods[] = {
  {"typeof", (PyCFunction)Sexp_typeof, METH_NOARGS,
  Sexp_typeof_doc},
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
        0,//Sexp_new,               /*tp_new*/
        0,                      /*tp_free*/
        0,                      /*tp_is_gc*/
};


/*
 * Closure-type Sexp.
 */

static SexpObject* newSexpObject(SEXP);
static SEXP newSEXP(PyObject *object, int rType);

/* Evaluate a SEXP. It must be constructed by hand. It raises a Python
   exception if an error ocurred in the evaluation */
SEXP do_eval_expr(SEXP expr_R) {
  SEXP res_R;
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
  res_R = R_tryEval(expr_R, R_GlobalEnv, &error);

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
  
  largs = lkwds = 0;
  if (args)
    largs = PyObject_Length(args);
  if (kwds)
    lkwds = PyObject_Length(kwds);
  if ((largs<0) || (lkwds<0))
    return NULL;

  /* A SEXP with the function to call and the arguments and keywords. */
  PROTECT(c_R = call_R = allocList(largs+lkwds+1));
  SET_TYPEOF(c_R, LANGSXP);
  SETCAR(c_R, ((SexpObject *)self)->sexp);
  c_R = CDR(c_R);

  int arg_i;
  SEXP tmp_R;
  for (arg_i=0; arg_i<largs; arg_i++) {
    //FIXME: assert that all are SexpObjects
    tmp_R = ((SexpObject *)PyTuple_GetItem(args, arg_i))->sexp;
    SETCAR(c_R, tmp_R);
    c_R = CDR(c_R);
  }
  
/*   if (!make_kwds(lkwds, kwds, &e)) { */
/*     UNPROTECT(1); */
/*     return NULL; */
/*   } */

//FIXME: R_GlobalContext ?
  PROTECT(res_R = do_eval_expr(call_R));

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
}




static SexpObject*
Sexp_closureEnv(PyObject *self)
{
  SEXP closureEnv = CLOENV(((SexpObject*)self)->sexp);
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
In R a function a function is defined in an enclosing \
environement, thus the name of closure. \
\n\
The closure can be accessed with the method 'closureEnv'.\
");

static PyTypeObject ClosureSexp_Type = {
	/* The ob_type field must be initialized in the module init function
	 * to be portable to Windows without using C++. */
	PyObject_HEAD_INIT(NULL)
	0,			/*ob_size*/
	"rinterface.ClosureSexp",	/*tp_name*/
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
        0,                      /*tp_doc*/
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
VectorSexp_new(PyTypeObject *type, PyObject *args)
{
  int rType = -1;
  PyObject *seq = 0;
  if (!PyArg_ParseTuple(args, "iO:new",
			&rType, &seq))
    return NULL;
  #ifdef VERBOSE
  printf("type: %i\n", rType);
  #endif
  SEXP sexp;
  sexp = newSEXP(seq, rType);
  PyObject *res = (PyObject *)newSexpObject(sexp);
  return res;
}

static Py_ssize_t VectorSexp_len(PyObject *object)
{
  Py_ssize_t len;
  //FIXME: sanity checks.
  len = (Py_ssize_t)LENGTH(((SexpObject *)object)->sexp);
  return len;
}

static PySequenceMethods VectorSexp_sequenceMethods = {
  (inquiry)VectorSexp_len,              /* sq_length */
  0,                              /* sq_concat */
  0,                              /* sq_repeat */
  //FIXME: implement
  0, //(ssizeargfunc)Sexp_item,        /* sq_item */
  //FIXME: implement
  0, //(ssizessizeargfunc)Sexp_slice,  /* sq_slice */
  //FIXME: implement
  0, //(ssizeobjargproc)Sexp_ass_item,   /* sq_ass_item */
  0,                              /* sq_ass_slice */
  0,                              /* sq_contains */
  0,                              /* sq_inplace_concat */
  0                               /* sq_inplace_repeat */
};

//FIXME: write more doc
PyDoc_STRVAR(VectorSexp_Type_doc,
"An R object that is a vector.\
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
	"rinterface.VectorSexp",	/*tp_name*/
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


//FIXME: write more doc
PyDoc_STRVAR(EnvironmentSexp_Type_doc,
"An R object that is an environment.\
 R environments can be seen as similar to Python\
 dictionnaries, with the twist that looking for\
 a key can be recursively propagated to the enclosing\
 environment whenever the key is not found.\
\n\
 The subsetting operator is made to match Python's\
 behavior, that is the enclosing environment are not\
 inspect upon absence of a given key.\
");

static PyTypeObject EnvironmentSexp_Type = {
	/* The ob_type field must be initialized in the module init function
	 * to be portable to Windows without using C++. */
	PyObject_HEAD_INIT(NULL)
	0,			/*ob_size*/
	"rinterface.EnvironmentSexp",	/*tp_name*/
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
        EnvironmentSexp_Type_doc,                      /*tp_doc*/
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
        0, //EnvironmentSexp_new,               /*tp_new*/
        0,                      /*tp_free*/
        0                      /*tp_is_gc*/
};


//FIXME: write more doc
PyDoc_STRVAR(S4Sexp_Type_doc,
"An R object that is an 'S4 object'.\
");

static PyTypeObject S4Sexp_Type = {
	/* The ob_type field must be initialized in the module init function
	 * to be portable to Windows without using C++. */
	PyObject_HEAD_INIT(NULL)
	0,			/*ob_size*/
	"rinterface.S4Sexp",	/*tp_name*/
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
newSexpObject(SEXP sexp)
{
  SexpObject *object;
  SEXP env_R;
  
  //FIXME: let the possibility to manipulate un-evaluated promises ?
  if (TYPEOF(sexp) == PROMSXP) {
    #ifdef VERBOSE
    printf("evaluating promise...");
    #endif
    env_R = PRENV(sexp);
    sexp = eval(sexp, env_R);
    #ifdef VERBOSE
    printf("done.\n");
    #endif
  }

  switch (TYPEOF(sexp)) {
  case CLOSXP:
    object  = (SexpObject *)_PyObject_New(&ClosureSexp_Type); 
    break;
    //FIXME: handle other callable types ?
    //case SPECIALSXP:
    //callable type
    //break;
    //case BUILTINSXP:
    //callable type
    //break;
  case REALSXP: 
  case INTSXP: 
  case LGLSXP: 
  case STRSXP:
    object = (SexpObject *)_PyObject_New(&VectorSexp_Type);
    break;
  case ENVSXP:
    object = (SexpObject *)_PyObject_New(&EnvironmentSexp_Type);
    break;
  case S4SXP:
    object = (SexpObject *)_PyObject_New(&S4Sexp_Type);
    break;
  default:
    object  = (SexpObject *)_PyObject_New(&Sexp_Type); 
    break;
  }
  if (!object)
    PyErr_NoMemory();
  object->sexp = sexp;
  if (sexp)
    R_PreserveObject(sexp);
  return object;
}

static SEXP
newSEXP(PyObject *object, int rType)
{
  SEXP sexp;
  PyObject *seq_object, *item; 
  seq_object = PySequence_Fast(object, "Cannot create"
			   " R object from non-sequence Python object.");
  if (! seq_object)
    return NULL;
  
  const Py_ssize_t length = PySequence_Fast_GET_SIZE(seq_object);
  //FIXME: PROTECT THIS
  #ifdef VERBOSE
  printf("size: %i", length);
  #endif
  sexp = allocVector(rType, length);

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
	  PyErr_NoMemory();
	  sexp = NULL;
	  break;
	}
	SET_STRING_ELT(sexp, i, str_R);
      }
      else {
	PyErr_Clear();
	SET_STRING_ELT(sexp, i, NA_STRING);
      }
    }
    break;
  default:
    PyErr_Format(PyExc_ValueError, "cannot handle type %d", rType);
    sexp = NULL;
  }
  return sexp;
}



static PyObject*
EmbeddedR_newSexpObject(SEXP sexp)
{
  SexpObject *res;

  return (PyObject *)res;
}

//ClosureSexp_Type.tp_call = &Sexp_call; 
//ClosureSexp_Type.tp_call = 0; 


//(PyTypeObject *)ClosureSexp_Type.tp_new = 0;//ClosureSexp_methods; 


static PyObject*
Sexp_GlobalEnv(PyTypeObject* type)
{
	SexpObject* res = (SexpObject*)type->tp_alloc(type, 0);
	res->sexp = R_GlobalEnv;
	return (PyObject*)res;
}



/* --- Find a variable in an environment --- */


static SexpObject*
EmbeddedR_findVar(PyObject *self, PyObject *args)
//EmbeddedR_findVar(PyTypeObject *type, PyObject *args)
{
  char *name;
  SEXP rho = R_GlobalEnv, res;
  PyObject *ErrorObject;

  if (!PyArg_ParseTuple(args, "s", &name)) { 
    //, "s|O&", &name, Get_SEXP, &rho)) {
    return NULL; 
  }
  res = findVar(install(name), rho);
  if (res != R_UnboundValue) {
    #ifdef VERBOSE
    printf("found.\n");
    #endif
    return newSexpObject(res);
  }
  PyErr_Format(ErrorObject, "'%s' not found", name);
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

  PyObject *m;
  m = Py_InitModule3("rinterface", EmbeddedR_methods, module_doc);
  if (m == NULL)
    return;

  PyModule_AddObject(m, "Sexp", (PyObject *)&Sexp_Type);
  PyModule_AddObject(m, "SexpClosure", (PyObject *)&ClosureSexp_Type);
  PyModule_AddObject(m, "SexpVector", (PyObject *)&VectorSexp_Type);

  //FIXME: clean the exception stuff
  if (ErrorObject == NULL) {
    ErrorObject = PyErr_NewException("rinterface.error", NULL, NULL);
    if (ErrorObject == NULL)
      return;
  }
  Py_INCREF(ErrorObject);
  PyModule_AddObject(m, "RobjectNotFound", ErrorObject);


  /* Add some symbolic constants to the module */
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
  ADD_INT_CONSTANT(m, VECSXP);
  ADD_INT_CONSTANT(m, EXPRSXP);
  ADD_INT_CONSTANT(m, BCODESXP);
  ADD_INT_CONSTANT(m, EXTPTRSXP);
  ADD_INT_CONSTANT(m, RAWSXP);
  ADD_INT_CONSTANT(m, S4SXP);
}
