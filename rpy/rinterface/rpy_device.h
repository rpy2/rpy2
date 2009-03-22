#ifndef RPY_RD_H
#define RPY_RD_H
#include <R_ext/GraphicsEngine.h>
#include <R_ext/GraphicsDevice.h>
#include <Python.h>

typedef struct {
  PyObject_HEAD;
  SEXP devnum;
  pDevDesc grdev;
} PyGrDevObject;

#define RPY_DEV_NUM(obj) (((PyGrDevObject *)obj)->devnum)

#endif /* !RPY_RD_H */
