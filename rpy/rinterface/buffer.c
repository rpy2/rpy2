
#include <Python.h>
#include <Rdefines.h>

#include "rpy_rinterface.h"
#include "buffer.h"

static int
sexp_rank(SEXP sexp)
{
  /* Return the number of dimensions for the buffer
   * (e.g., a vector will return 1, a matrix 2, ...)
   */
  SEXP dim = getAttrib(sexp, R_DimSymbol);
  if (dim == R_NilValue)
    return 1;
  return GET_LENGTH(dim);
}

static void
sexp_shape(SEXP sexp, Py_intptr_t *shape, int nd)
{
  /* Set the buffer 'shape', that is a vector of Py_intptr_t
   * containing the size of each dimension (see sexp_rank).
   */
  int i;
  SEXP dim = getAttrib(sexp, R_DimSymbol);
  if (dim == R_NilValue)
    shape[0] = LENGTH(sexp);
  else for (i = 0; i < nd; i++) {
      shape[i] = INTEGER(dim)[i];
    }
}

static void
sexp_strides(SEXP sexp, Py_intptr_t *strides, Py_ssize_t itemsize, 
	     Py_intptr_t *shape, int nd)
{
  /* Set the buffer 'strides', that is a vector or Py_intptr_t
   * containing the offset (in bytes) when progressing along
   * each dimension.
   */
  int i;
  strides[0] = itemsize;
  for (i = 1; i < nd; i++) {
    strides[i] = shape[i-1] * itemsize;
  }
}


#if PY_VERSION_HEX >= 0x02060000

static int
VectorSexp_getbuffer(PyObject *obj, Py_buffer *view, int flags)
{
  printf("getbuffer\n");
  if (view == NULL) {
    return 0;
  }
  
  if ((flags & PyBUF_F_CONTIGUOUS) == PyBUF_F_CONTIGUOUS) {
    PyErr_SetString(PyExc_ValueError, "Only FORTRAN-style contiguous arrays allowed.");
    return -1;
  }

  view->obj = obj;
  if (obj) {
    Py_INCREF(obj);
  }
  view->readonly = 0;
  
  PySexpObject *self = (PySexpObject *)obj;
  SEXP sexp = RPY_SEXP(self);

  switch (TYPEOF(sexp)) {
  case REALSXP:
    view->buf = NUMERIC_POINTER(sexp);
    view->len = GET_LENGTH(sexp) * sizeof(double);
    view->itemsize = sizeof(double);
    view->format = "f";
    break;
  case INTSXP:
    view->buf = INTEGER_POINTER(sexp);
    view->len = GET_LENGTH(sexp) * sizeof(int);
    view->itemsize = sizeof(int);
    view->format = "i";
    break;
  case LGLSXP:
    view->buf = LOGICAL_POINTER(sexp);
    view->len = GET_LENGTH(sexp) * sizeof(int);
    view->itemsize = sizeof(int);
    view->format = "i";
    break;
  case CPLXSXP:
    view->buf = COMPLEX_POINTER(sexp);
    view->len = GET_LENGTH(sexp) * sizeof(Rcomplex);
    view->itemsize = sizeof(Rcomplex);
    view->format = "B"; /* FIXME: correct format for complex ? */
    break;
  case RAWSXP:
    view->buf = RAW_POINTER(sexp);
    view->len = GET_LENGTH(sexp);
    view->itemsize = 1;
    view->format = "B";
    break;
  default:
    PyErr_Format(PyExc_ValueError, "Buffer for this type not yet supported.");
    return -1;
  }

  view->ndim = sexp_rank(sexp);

  view->shape = NULL;
  if ((flags & PyBUF_ND) == PyBUF_ND) {
    view->shape =  (Py_intptr_t*)PyMem_Malloc(sizeof(Py_intptr_t) * view->ndim);
    sexp_shape(sexp, view->shape, view->ndim);
  }

  view->strides = NULL;
  if ((flags & PyBUF_STRIDES) == PyBUF_STRIDES) {
    view->strides = (Py_intptr_t*)PyMem_Malloc(sizeof(Py_intptr_t) * view->ndim);
    sexp_strides(sexp, view->strides, view->itemsize, view->shape, view->ndim);
  }
  /* view->suboffsets = (Py_intptr_t*)PyMem_Malloc(sizeof(Py_intptr_t) * view->ndim); */
  /* int i; */
  /* for (i = 0; i < view->ndim; i++) { */
  /*   view->suboffsets[i] = 0; */
  /* } */
  view->suboffsets = NULL;
  view->internal = NULL;
  return 0;
}
#endif

static Py_ssize_t
VectorSexp_getsegcount(PySexpObject *self, Py_ssize_t *lenp)
{
  printf("getsegcount\n");
  SEXP sexp = RPY_SEXP(self);

  switch (TYPEOF(sexp)) {
  case REALSXP:
    *lenp = GET_LENGTH(sexp) * sizeof(double);
    break;
  case INTSXP:
    *lenp = GET_LENGTH(sexp) * sizeof(int);
    break;
  case LGLSXP:
    *lenp = GET_LENGTH(sexp) * sizeof(int);
    break;
  case CPLXSXP:
    *lenp = GET_LENGTH(sexp) * sizeof(Rcomplex);
    break;
  case RAWSXP:
    *lenp = GET_LENGTH(sexp) * 1;
    break;
  default:
    PyErr_Format(PyExc_ValueError, "Buffer for this type not yet supported.");
    *lenp = 0;
    return -1;
  }

  return 0;
}

static Py_ssize_t
VectorSexp_getreadbuf(PySexpObject *self, Py_ssize_t segment, void **ptrptr)
{
  printf("getreadbuf\n");
  if (segment != 0) {
    PyErr_SetString(PyExc_ValueError,
		    "accessing non-existing data segment");
    return -1;
  }
  SEXP sexp = RPY_SEXP(self);
  Py_ssize_t len;

  switch (TYPEOF(sexp)) {
  case REALSXP:
    *ptrptr = NUMERIC_POINTER(sexp);
    len = GET_LENGTH(sexp) * sizeof(double);
    break;
  case INTSXP:
    *ptrptr = INTEGER_POINTER(sexp);
    len = GET_LENGTH(sexp) * sizeof(int);
    break;
  case LGLSXP:
    *ptrptr = LOGICAL_POINTER(sexp);
    len = GET_LENGTH(sexp) * sizeof(int);
    break;
  case CPLXSXP:
    *ptrptr = COMPLEX_POINTER(sexp);
    len = GET_LENGTH(sexp) * sizeof(Rcomplex);
    break;
  case RAWSXP:
    *ptrptr = RAW_POINTER(sexp);
    len = GET_LENGTH(sexp) * 1;
    break;
  default:
    PyErr_Format(PyExc_ValueError, "Buffer for this type not yet supported.");
    *ptrptr = NULL;
    return -1;
  }
  return 0;
}

static Py_ssize_t
VectorSexp_getwritebuf(PySexpObject *self, Py_ssize_t segment, void **ptrptr)
{
  printf("getwritebuf\n");
  /*FIXME: introduce a "writeable" flag for SexpVector objects ? */
  return VectorSexp_getreadbuf(self, segment, (void **)ptrptr);
}

static Py_ssize_t
VectorSexp_getcharbuf(PySexpObject *self, Py_ssize_t segment, const char **ptrptr)
{
  /*FIXME: introduce a "writeable" flag for SexpVector objects ? */
  return VectorSexp_getreadbuf(self, segment, (void **)ptrptr);
}

static PyBufferProcs VectorSexp_as_buffer = {
        (readbufferproc)VectorSexp_getreadbuf,
        (writebufferproc)VectorSexp_getwritebuf,
        (segcountproc)VectorSexp_getsegcount,
	(charbufferproc)VectorSexp_getcharbuf,
#if PY_VERSION_HEX >= 0x02060000
	(getbufferproc)VectorSexp_getbuffer,
	(releasebufferproc)0,
#endif
};
