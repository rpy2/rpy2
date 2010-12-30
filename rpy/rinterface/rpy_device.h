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

#define RPY_GRDEV_BOOL_SET(self, value, attrname)	\
  int res = 0;						\
  if (value == NULL) {					\
    PyErr_SetString(PyExc_TypeError,					\
		  "The attribute "#attrname"cannot be deleted");	\
    res = -1;								\
  } else if (! PyBool_Check(value)) {					\
    PyErr_SetString(PyExc_TypeError,					\
		    "The attribute "#attrname" must be a boolean");	\
    res = -1;								\
  } else if (value == Py_True) {					\
    ((PyGrDevObject *)self)->grdev->attrname = TRUE;			\
  } else if (value == Py_False) {					\
    ((PyGrDevObject *)self)->grdev->attrname = FALSE;			\
  } else {								\
    PyErr_SetString(PyExc_TypeError,					\
		    "Mysterious error when setting the attribute "#attrname"."); \
    res = -1;								\
  }									\
  return res								\


#endif /* !RPY_RD_H */
