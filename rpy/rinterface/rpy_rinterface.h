
#ifndef RPY_RI_H
#define RPY_RI_H

#include <R.h>
#include <Python.h>

/* Back-compatibility with Python 2.4 */
#if (PY_VERSION_HEX < 0x02050000)
#define PY_SSIZE_T_MAX INT_MAX
#define PY_SSIZE_T_MIN INT_MIN
typedef int Py_ssize_t;
typedef inquiry lenfunc;
typedef intargfunc ssizeargfunc;
typedef intobjargproc ssizeobjargproc;
#endif


extern const unsigned int const RPY_R_INITIALIZED;
extern const unsigned int const RPY_R_BUSY;


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

#define RPY_PY_FROM_RBOOL(res, rbool)                   \
  if (rbool == NA_LOGICAL) {                            \
    Py_INCREF(Py_None);                                 \
    res = Py_None;                                      \
  } else {                                              \
    res = PyBool_FromLong((long)(rbool));               \
  }

#define RPY_GIL_ENSURE(is_threaded, gstate)  \
  is_threaded = PyEval_ThreadsInitialized(); \
  if (is_threaded) { \
    gstate = PyGILState_Ensure(); \
  }

#define RPY_GIL_RELEASE(is_threaded, gstate) \
  if (is_threaded) { \
    PyGILState_Release(gstate);                 \
  }

#define RPY_PYSCALAR_RVECTOR(py_obj, sexp)				\
  sexp = NULL;								\
  /* The argument is not a PySexpObject, so we are going to check
     if conversion from a scalar type is possible */		  \
if (PyLong_Check(py_obj) | PyInt_Check(py_obj)) {		  \
  sexp = allocVector(INTSXP, 1);				  \
  INTEGER_POINTER(sexp)[0] = PyInt_AS_LONG(py_obj);		  \
  PROTECT(sexp);						  \
  protect_count++;						  \
 } else if (PyBool_Check(py_obj)) {					\
  sexp = allocVector(LGLSXP, 1);					\
  LOGICAL_POINTER(sexp)[0] = py_obj == Py_True ? TRUE : FALSE;	\
  PROTECT(sexp);							\
  protect_count++;							\
 } else if (PyFloat_Check(py_obj)) {					\
  sexp = allocVector(REALSXP, 1);					\
  NUMERIC_POINTER(sexp)[0] = PyFloat_AS_DOUBLE(py_obj);		\
  PROTECT(sexp);							\
  protect_count++;							\
 } else if (py_obj == Py_None) {					\
  sexp = R_NilValue;							\
 }


#endif /* !RPY_RI_H */
