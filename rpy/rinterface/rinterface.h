
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
  //unsigned short int rpy_only;
  SEXP sexp;
} SexpObject;


typedef struct {
  PyObject_HEAD 
  SexpObject *sObj;
  //SEXP sexp;
} PySexpObject;


#define RPY_COUNT(obj) (((obj)->sObj)->count)
#define RPY_SEXP(obj) (((obj)->sObj)->sexp)
//#define RPY_SEXP(obj) ((obj)->sexp)
//#define RPY_RPYONLY(obj) (((obj)->sObj)->rpy_only)

#define RPY_INCREF(obj) (((obj)->sObj)->count++)
#define RPY_DECREF(obj) (((obj)->sObj)->count--)


#endif /* !RPY_RI_H */
