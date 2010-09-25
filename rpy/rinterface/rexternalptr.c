/* Finalizer for R external pointers that are arbitrary Python objects */
static SEXP
R_PyObject_decref(SEXP s)
{
  PyObject* pyo = (PyObject*)R_ExternalPtrAddr(s);
  if (pyo) {
    Py_DECREF(pyo);
    R_ClearExternalPtr(s);
  }
  return R_NilValue;
}


PyDoc_STRVAR(ExtPtrSexp_Type_doc,
	     "R object that is an 'external pointer',"
	     "that a pointer to a data structure R is not necessarily capable of manipulating.");


PyDoc_STRVAR(ExtPtrSexp___address___doc,
	     "The C handle to external data as a PyCObject."
	     );

static PyObject*
ExtPtrSexp_address(PySexpObject *self)
{
  if (! RPY_SEXP(self)) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return NULL;
  }
  embeddedR_setlock();
  PyObject *res = PyCObject_FromVoidPtr(R_ExternalPtrAddr(self->sObj->sexp), 
                                        SexpObject_CObject_destroy);
  embeddedR_freelock();
  return res;
}

PyDoc_STRVAR(ExtPtrSexp___tag___doc,
	     "The R tag associated with the external pointer"
	     );

static PySexpObject*
ExtPtrSexp_tag(PySexpObject *self)
{
  if (! RPY_SEXP(self)) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return NULL;
  }
  embeddedR_setlock();
  SEXP rtag = R_ExternalPtrTag(self->sObj->sexp);
  PySexpObject *res = newPySexpObject(rtag, 0);
  embeddedR_freelock();
  return res;
}

PyDoc_STRVAR(ExtPtrSexp___protected___doc,
	     "The R 'protected' object associated with the external pointer"
	     );

static PySexpObject*
ExtPtrSexp_protected(PySexpObject *self)
{
  if (! RPY_SEXP(self)) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return NULL;
  }
  embeddedR_setlock();
  SEXP rtag = R_ExternalPtrProtected(self->sObj->sexp);
  PySexpObject *res = newPySexpObject(rtag, 0);
  embeddedR_freelock();
  return res;
}

static PyGetSetDef ExtPtrSexp_getsets[] = {
  {"__address__", 
   (getter)ExtPtrSexp_address,
   (setter)0,
   ExtPtrSexp___address___doc},
  {"__tag__", 
   (getter)ExtPtrSexp_tag,
   (setter)0,
   ExtPtrSexp___tag___doc},
  {"__protected__", 
   (getter)ExtPtrSexp_protected,
   (setter)0,
   ExtPtrSexp___protected___doc},
{NULL, NULL, NULL, NULL} /* sentinel */
};

static PyTypeObject ExtPtrSexp_Type = {
        /* The ob_type field must be initialized in the module init function
         * to be portable to Windows without using C++. */
#if (PY_VERSION_HEX < 0x03010000)
        PyObject_HEAD_INIT(NULL)
        0,                      /*ob_size*/
#else
	PyVarObject_HEAD_INIT(NULL, 0)
#endif
        "rpy2.rinterface.SexpExtPtr",    /*tp_name*/
        sizeof(PySexpObject),   /*tp_basicsize*/
        0,                      /*tp_itemsize*/
        /* methods */
        0, /*tp_dealloc*/
        0,                      /*tp_print*/
        0,                      /*tp_getattr*/
        0,                      /*tp_setattr*/
        0,                      /*tp_compare*/
        0,                      /*tp_repr*/
        0,                      /*tp_as_number*/
        0,                      /*tp_as_sequence*/
        0,                      /*tp_as_mapping*/
        0,                      /*tp_hash*/
        0,              /*tp_call*/
        0,                      /*tp_str*/
        0,                      /*tp_getattro*/
        0,                      /*tp_setattro*/
        0,                      /*tp_as_buffer*/
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE,     /*tp_flags*/
        ExtPtrSexp_Type_doc,                      /*tp_doc*/
        0,                      /*tp_traverse*/
        0,                      /*tp_clear*/
        0,                      /*tp_richcompare*/
        0,                      /*tp_weaklistoffset*/
        0,                      /*tp_iter*/
        0,                      /*tp_iternext*/
        0,           /*tp_methods*/
        0,                      /*tp_members*/
        ExtPtrSexp_getsets,                      /*tp_getset*/
        &Sexp_Type,             /*tp_base*/
        0,                      /*tp_dict*/
        0,                      /*tp_descr_get*/
        0,                      /*tp_descr_set*/
        0,                      /*tp_dictoffset*/
        0,                      /*tp_init*/
        0,                      /*tp_alloc*/
        /*FIXME: add new method */
        0,                     /*tp_new*/
        0,                      /*tp_free*/
        0                      /*tp_is_gc*/
};
