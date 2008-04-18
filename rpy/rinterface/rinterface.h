
#ifndef RPY_RI_H
#define RPY_RI_H

#include <R.h>
#include <Python.h>

/* Representation of R objects (instances) as instances in Python.
 */
typedef struct {
  PyObject_HEAD 
  SEXP sexp;
} SexpObject;


#endif /* !RPY_RI_H */
