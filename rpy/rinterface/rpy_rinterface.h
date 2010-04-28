
#ifndef _RPY_RI_H_
#define _RPY_RI_H_



#include <R.h>
#include <Rinternals.h>
#include <Python.h>

/* Back-compatibility with Python 2.4 */
#if (PY_VERSION_HEX < 0x02050000)
#define PY_SSIZE_T_MAX INT_MAX
#define PY_SSIZE_T_MIN INT_MIN
typedef int Py_ssize_t;
typedef inquiry lenfunc;
typedef intargfunc ssizeargfunc;
typedef intobjargproc ssizeobjargproc;
typedef PyObject *(*ssizessizeargfunc)(PyObject *, Py_ssize_t, Py_ssize_t);
typedef int(*ssizessizeobjargproc)(PyObject *, Py_ssize_t, Py_ssize_t, 
PyObject *);

#endif


/* Representation of R objects (instances) as instances in Python.
 */
typedef struct {
  Py_ssize_t count;
  /* unsigned short int rpy_only; */
  SEXP sexp;
} SexpObject;


typedef struct {
  PyObject_HEAD 
  SexpObject *sObj;
  /* SEXP sexp; */
} PySexpObject;


#define RPY_COUNT(obj) (((obj)->sObj)->count)
#define RPY_SEXP(obj) (((obj)->sObj)->sexp)
/* #define RPY_SEXP(obj) ((obj)->sexp) */
/* #define RPY_RPYONLY(obj) (((obj)->sObj)->rpy_only) */

#define RPY_INCREF(obj) (((obj)->sObj)->count++)
#define RPY_DECREF(obj) (((obj)->sObj)->count--)


  
#define RPY_RINT_FROM_LONG(value)               \
  ((value<=(long)INT_MAX && value>=(long)INT_MIN)?(int)value:NA_INTEGER)

#define RPY_PY_FROM_RBOOL(res, rbool)                   \
  if (rbool == NA_LOGICAL) {                            \
    Py_INCREF(Py_None);                                 \
    res = Py_None;                                      \
  } else {                                              \
    res = PyBool_FromLong((long)(rbool));               \
  }

#define RPY_GIL_ENSURE(is_threaded, gstate)	\
  is_threaded = PyEval_ThreadsInitialized();	\
  if (is_threaded) {				\
    gstate = PyGILState_Ensure();		\
  } 

#define RPY_GIL_RELEASE(is_threaded, gstate)    \
  if (is_threaded) {                            \
    PyGILState_Release(gstate);                 \
  }



#define RPY_PYSCALAR_RVECTOR(py_obj, sexp)                              \
  sexp = NULL;                                                          \
  /* The argument is not a PySexpObject, so we are going to check       \
     if conversion from a scalar type is possible */                    \
  if ((py_obj) == NACharacter_New(0)) {                                 \
    sexp = NA_STRING;                                                   \
  } else if ((py_obj) == NAInteger_New(0)) {				\
    sexp = allocVector(INTSXP, 1);					\
    PROTECT(sexp);							\
    protect_count++;                                                    \
    INTEGER_POINTER(sexp)[0] = NA_INTEGER;                              \
  } else if ((py_obj) == NALogical_New(0)) {                            \
    sexp = allocVector(LGLSXP, 1);                                      \
    PROTECT(sexp);                                                      \
    protect_count++;                                                    \
    LOGICAL_POINTER(sexp)[0] = NA_LOGICAL;                              \
  } else if ((py_obj) == NAReal_New(0)) {				\
    sexp = allocVector(REALSXP, 1);					\
    PROTECT(sexp);                                                      \
    protect_count++;                                                    \
    NUMERIC_POINTER(sexp)[0] = NA_REAL;					\
 } else if (PyBool_Check(py_obj)) {                                     \
    sexp = allocVector(LGLSXP, 1);                                      \
    LOGICAL_POINTER(sexp)[0] = py_obj == Py_True ? TRUE : FALSE;        \
    PROTECT(sexp);                                                      \
    protect_count++;                                                    \
  } else if (PyInt_Check(py_obj)) {                                     \
    sexp = allocVector(INTSXP, 1);                                      \
    INTEGER_POINTER(sexp)[0] = (int)(PyInt_AS_LONG(py_obj));            \
    PROTECT(sexp);                                                      \
    protect_count++;                                                    \
  } else if (PyLong_Check(py_obj)) {                                    \
    sexp = allocVector(INTSXP, 1);                                      \
    INTEGER_POINTER(sexp)[0] = RPY_RINT_FROM_LONG(PyLong_AsLong(py_obj)); \
    if ((INTEGER_POINTER(sexp)[0] == -1) && PyErr_Occurred() ) {        \
      INTEGER_POINTER(sexp)[0] = NA_INTEGER;                            \
      PyErr_Clear();                                                    \
    }                                                                   \
    PROTECT(sexp);                                                      \
    protect_count++;                                                    \
 } else if (PyFloat_Check(py_obj)) {                                    \
    sexp = allocVector(REALSXP, 1);                                     \
    NUMERIC_POINTER(sexp)[0] = PyFloat_AS_DOUBLE(py_obj);               \
    PROTECT(sexp);                                                      \
    protect_count++;                                                    \
  } else if (py_obj == Py_None) {                                       \
    sexp = R_NilValue;                                                  \
  }


#define RPY_NA_TP_NEW(type_name, parent_type, pyconstructor, value)        \
  static PyObject *self = NULL;                                         \
  static char *kwlist[] = {0};                                          \
  PyObject *py_value, *new_args;					\
                                                                        \
  if (! PyArg_ParseTupleAndKeywords(args, kwds, "", kwlist)) {          \
    return NULL;                                                        \
  }                                                                     \
                                                                        \
  if (self == NULL) {							\
    py_value = (pyconstructor)(value);				    	\
    if (py_value == NULL) {						\
      return NULL;							\
    }									\
    new_args = PyTuple_Pack(1, py_value);				\
    self = (parent_type).tp_new(type, new_args, kwds);                  \
    Py_DECREF(new_args);                                                \
    if (self == NULL) {                                                 \
      return NULL;                                                      \
    }                                                                   \
  }                                                                     \
  Py_XINCREF(self);                                                     \
  return (PyObject *)self;                                              \


#define RPY_NA_NEW(type, type_tp_new)                                   \
  static PyObject *args = NULL;                                         \
  static PyObject *kwds = NULL;                                         \
  PyObject *res;                                                        \
                                                                        \
  if (args == NULL) {                                                   \
    args = PyTuple_Pack(0);                                             \
  }                                                                     \
  if (kwds == NULL) {                                                   \
    kwds = PyDict_New();                                                \
  }                                                                     \
                                                                        \
  res = (type_tp_new)(&(type), args, kwds);                             \
  if (! new) {                                                          \
    Py_DECREF(res);                                                     \
  }                                                                     \
  return res;                                                           \


#endif /* !RPY_RI_H */

