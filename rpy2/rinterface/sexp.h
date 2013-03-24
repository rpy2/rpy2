#ifndef _RPY_PRIVATE_SEXP_H_
#define _RPY_PRIVATE_SEXP_H_

#ifndef _RPY_RINTERFACE_MODULE_
#error sexp.h should not be included directly
#endif

#include <Python.h>
#include <R.h>
#include <Rinternals.h>
#include <Rdefines.h>


static PyObject* EmbeddedR_unserialize(PyObject* self, PyObject* args);

static PyObject *rinterface_unserialize;

static PyTypeObject Sexp_Type;

#endif


