
#ifndef RPY_RI_H
#define RPY_RI_H

#include <R.h>
#include <Python.h>


//#define RPY_VERBOSE


extern const unsigned int const RPY_R_INITIALIZED;
extern const unsigned int const RPY_R_BUSY;

/* Representation of R objects (instances) as instances in Python.
 */

typedef struct {
  int count;
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
