/*
 ***** BEGIN LICENSE BLOCK *****
 * Version: MPL 1.1/GPL 2.0/LGPL 2.1
 *
 * The contents of this file are subject to the Mozilla Public License Version
 * 1.1 (the "License"); you may not use this file except in compliance with
 * the License. You may obtain a copy of the License at
 * http://www.mozilla.org/MPL/
 *
 * Software distributed under the License is distributed on an "AS IS" basis,
 * WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
 * for the specific language governing rights and limitations under the
 * License.
 * 
 * Copyright (C) 2008-2011 Laurent Gautier
 *
 * Alternatively, the contents of this file may be used under the terms of
 * either the GNU General Public License Version 2 or later (the "GPL"), or
 * the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
 * in which case the provisions of the GPL or the LGPL are applicable instead
 * of those above. If you wish to allow use of your version of this file only
 * under the terms of either the GPL or the LGPL, and not to allow others to
 * use your version of this file under the terms of the MPL, indicate your
 * decision by deleting the provisions above and replace them with the notice
 * and other provisions required by the GPL or the LGPL. If you do not delete
 * the provisions above, a recipient may use your version of this file under
 * the terms of any one of the MPL, the GPL or the LGPL.
 *
 * ***** END LICENSE BLOCK ***** */

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
	     " a pointer to a data structure implemented at the C level.\n"
	     "SexpExtPtr(extref, tag = None, protected = None)");

/* PyDoc_STRVAR(ExtPtrSexp___init___doc, */
/* 	     "Construct an external pointer. " */
/* 	     ); */

static int
ExtPtrSexp_init(PySexpObject *self, PyObject *args, PyObject *kwds)
{
#ifdef RPY_VERBOSE
  printf("Python:%p / R:%p - ExtPtrSexp initializing...\n", 
         self, RPY_SEXP((PySexpObject *)self));
#endif
  if (! RPY_SEXP(self)) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return -1;
  }

  PyObject *pyextptr = Py_None;
  PyObject *pytag = Py_None;
  PyObject *pyprotected = Py_None;
  static char *kwlist[] = {"extptr", "tag", "protected", NULL};
  if (! PyArg_ParseTupleAndKeywords(args, kwds, "O|O!O!", 
                                    kwlist,
                                    &pyextptr,
                                    &Sexp_Type, &pytag,
                                    &Sexp_Type, &pyprotected)) {
    return -1;
  }
  
  /*FIXME: twist here - MakeExternalPtr will "preserve" the tag
   * but the tag is already preserved (when exposed as a Python object) */
  /* R_ReleaseObject(pytag->sObj->sexp); */
  SEXP rtag, rprotected, rres;
  if (pytag == Py_None) {
    rtag = R_NilValue;
  } else {
    rtag = RPY_SEXP((PySexpObject *)pytag);
  }
  if (pyprotected == Py_None) {
    rprotected = R_NilValue;
  } else {
    rprotected = RPY_SEXP((PySexpObject *)pyprotected);
  }
  Py_INCREF(pyextptr);
  rres  = R_MakeExternalPtr(pyextptr, rtag, rprotected);
  R_RegisterCFinalizer(rres, (R_CFinalizer_t)R_PyObject_decref);
  RPY_SEXP(self) = rres;

#ifdef RPY_VERBOSE
  printf("done.\n");
#endif 
  return 0;
}


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
#if (PY_VERSION_HEX < 0x02070000) 
  PyObject *res = PyCObject_FromVoidPtr(R_ExternalPtrAddr(self->sObj->sexp), 
                                        NULL);
#else
  PyObject *res = PyCapsule_New(R_ExternalPtrAddr(self->sObj->sexp),
				"rpy2.rinterface._C_API_SEXP_",
				NULL);
#endif
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
        (initproc)ExtPtrSexp_init,                      /*tp_init*/
        0,                      /*tp_alloc*/
        /*FIXME: add new method */
        0,                     /*tp_new*/
        0,                      /*tp_free*/
        0                      /*tp_is_gc*/
};
