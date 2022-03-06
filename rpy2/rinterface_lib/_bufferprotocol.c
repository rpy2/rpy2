#define PY_SSIZE_T_CLEAN
#include <Python.h>


static PyObject *
memoryview_fordered(PyObject *self, PyObject *args)
{
    const char *cast_str;
    Py_buffer view;
    PyObject *shape;
    PyObject *memoryview;
    Py_ssize_t tmp_stride;
    int ndim;

    if (!PyArg_ParseTuple(args, "OsO!",
			  &memoryview,
			  &cast_str,
			  &PyTuple_Type, &shape))
        return NULL;

    int status = PyObject_GetBuffer(memoryview, &view,
				    PyBUF_WRITABLE | PyBUF_FORMAT |
				    PyBUF_STRIDES | PyBUF_F_CONTIGUOUS);
    // test status
    ndim = view.ndim;
    for (int i=0; i < (ndim/2); i++) {
      tmp_stride = view.strides[ndim - i];
      view.strides[ndim - i] = view.strides[i];
      view.strides[i] = tmp_stride;
    }
    PyBuffer_Release(&view);
    return Py_None;
};


static PyMethodDef _BufferProtocolMethods[] =
  {
   {"memoryview_fordered", memoryview_fordered, METH_VARARGS,
    "Set the strides to be Fortran-ordered."},
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
