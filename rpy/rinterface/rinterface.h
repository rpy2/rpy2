
#ifndef RPY_RI_H
#define RPY_RI_H

#include <R.h>
#include <Python.h>


//#define RPY_VERBOSE

/* Representation of R objects (instances) as instances in Python.
 */

typedef struct {
  int count;
  SEXP sexp;
} SexpObject;


typedef struct {
  PyObject_HEAD 
  SexpObject *sObj;
  //SEXP sexp;
} PySexpObject;


#define RPY_GETCOUNT(obj) (((obj)->sObj)->count)
#define RPY_GETSEXP(obj) (((obj)->sObj)->sexp)
//#define RPY_GETSEXP(obj) ((obj)->sexp)

#define RPY_INCREF(obj) ((obj->sObj)->count++)
#define RPY_DECREF(obj) ((obj->sObj)->count--)


#endif /* !RPY_RI_H */
