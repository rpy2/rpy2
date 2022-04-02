#define PY_SSIZE_T_CLEAN
#include <Python.h>


static PyObject *
memoryview_swapstrides(PyObject *self, PyObject *args)
{
  Py_buffer *view;
  PyObject *memoryview;
  
  if (!PyArg_ParseTuple(args, "O",
			&memoryview)) {
    return NULL;
  }
  
  if (!PyMemoryView_Check(memoryview)) {
    PyErr_SetString(PyExc_ValueError, "obj must be a memoryview.");
    return NULL;
  }
  view = PyMemoryView_GET_BUFFER(memoryview);
  if (!PyBuffer_IsContiguous(view, 'A')) {
    PyErr_SetString(PyExc_ValueError, "obj must have a continuous buffer.");
    return NULL;
  }
  int ndim = view->ndim;
  Py_ssize_t prod_prev_dim = 1;
  for (Py_ssize_t i=0; i < ndim; i++) {
    view->strides[i] = view->itemsize*prod_prev_dim;
    prod_prev_dim *= view->shape[i];
  }
  ((PyMemoryViewObject *)memoryview)->flags |= PyBUF_F_CONTIGUOUS;
  return Py_None;
};


static PyMethodDef _BufferProtocolMethods[] =
  {
   {"memoryview_swapstrides", memoryview_swapstrides, METH_VARARGS,
    "memoryview_swapstrides(obj). Swap the strides to be Fortran-ordered."},
   {NULL, NULL, 0, NULL}
  };


static struct PyModuleDef _bufferprotocolmodule = {
  PyModuleDef_HEAD_INIT,
  "_bufferprotocol",
  NULL, //_bufferprotocol_doc,
  -1,
  _BufferProtocolMethods
};

PyMODINIT_FUNC
PyInit__bufferprotocol(void)
{
  return PyModule_Create(&_bufferprotocolmodule);  
};
