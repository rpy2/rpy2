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
 * Copyright (C) 2008-2012 Laurent Gautier
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


/* --- NA values --- */

#include <longintrepr.h>

PyDoc_STRVAR(NAInteger_Type_doc,
"Missing value for an integer in R."
);

static PyObject*
NAInteger_repr(PyObject *self)
{
  static PyObject* repr = NULL;
  if (repr == NULL) {
#if (PY_VERSION_HEX < 0x03010000)  
    repr = PyString_FromString("NA_integer_");
#else
    repr = PyUnicode_FromString("NA_integer_");
#endif
  }
  Py_XINCREF(repr);
  return repr;
}

static PyObject*
NA_str(PyObject *self)
{
  static PyObject* repr = NULL;
  if (repr == NULL) {
#if (PY_VERSION_HEX < 0x03010000)  
    repr = PyString_FromString("NA");
#else
    repr = PyUnicode_FromString("NA");
#endif
  }
  Py_XINCREF(repr);
  return repr;
}

/* Whenever an NA object is used for arithmetic or logic,
 * the results is NA. */
static PyObject*
NA_unaryfunc(PyObject *self)
{
  Py_XINCREF(self);
  return self;
}
static PyObject*
NA_binaryfunc(PyObject *self, PyObject *obj)
{
  Py_XINCREF(self);
  return self;

}
static PyObject*
NA_ternaryfunc(PyObject *self, PyObject *obj1, PyObject *obj2)
{
  Py_XINCREF(self);
  return self;
}

static int
NA_nonzero(PyObject *self)
{
  PyErr_Format(PyExc_ValueError, "NA values cannot be evaluated as booleans.");
  return 0;
}

static PyNumberMethods NAInteger_NumberMethods = {
  (binaryfunc)NA_binaryfunc, /* nb_add */
  (binaryfunc)NA_binaryfunc, /* nb_subtract; */
  (binaryfunc)NA_binaryfunc, /* nb_multiply; */
#if (PY_VERSION_HEX < 0x03010000)
  (binaryfunc)NA_binaryfunc, /* nb_divide; */
#endif
  (binaryfunc)NA_binaryfunc, /* nb_remainder; */
  (binaryfunc)NA_binaryfunc, /* nb_divmod; */
  (ternaryfunc)NA_ternaryfunc, /* nb_power; */
  (unaryfunc) NA_unaryfunc, /* nb_negative; */
  (unaryfunc) NA_unaryfunc, /* nb_positive; */
  (unaryfunc) NA_unaryfunc, /* nb_absolute; */
  (inquiry) NA_nonzero, /* nb_nonzero;       -- Used by PyObject_IsTrue */
  (unaryfunc) NA_unaryfunc, /* nb_invert; */
  (binaryfunc) NA_binaryfunc, /* nb_lshift; */
  (binaryfunc) NA_binaryfunc, /* nb_rshift; */
  (binaryfunc) NA_binaryfunc, /*  nb_and; */
  (binaryfunc) NA_binaryfunc, /*  nb_xor; */
  (binaryfunc) NA_binaryfunc, /* nb_or; */
#if (PY_VERSION_HEX < 0x03010000)
  0, //(coerce) NA_coerce, /* coercion nb_coerce;       -- Used by the coerce() function */
#endif
  (unaryfunc) NA_unaryfunc, /* nb_int; */
#if (PY_VERSION_HEX < 0x03010000)
  (unaryfunc) NA_unaryfunc, /* nb_long; */
#else
  NULL, /* reserved */
#endif
  (unaryfunc) NA_unaryfunc, /* nb_float; */
#if (PY_VERSION_HEX < 0x03010000)
  (unaryfunc) NA_unaryfunc, /* nb_oct; */
  (unaryfunc) NA_unaryfunc, /* nb_hex; */
#endif
  /* Added in release 2.0 */
  (binaryfunc)NA_binaryfunc, /* nb_inplace_add; */
  (binaryfunc)NA_binaryfunc, /* nb_inplace_subtract; */
  (binaryfunc)NA_binaryfunc, /* nb_inplace_multiply; */
#if (PY_VERSION_HEX < 0x03010000)
  (binaryfunc)NA_binaryfunc, /* nb_inplace_divide; */
#endif
  (binaryfunc)NA_binaryfunc, /* nb_inplace_remainder; */
  (ternaryfunc)NA_ternaryfunc, /* nb_inplace_power; */
  0, /* nb_inplace_lshift; */
  0, /* nb_inplace_rshift; */
  0, /* nb_inplace_and; */
  0, /* nb_inplace_xor; */
  0, /* nb_inplace_or; */
  /* Added in release 2.2 */
  (binaryfunc) NA_binaryfunc, /* nb_floor_divide; */
  (binaryfunc) NA_binaryfunc, /* nb_true_divide; */
  (binaryfunc)NA_binaryfunc, /* nb_inplace_floor_divide; */
  (binaryfunc)NA_binaryfunc, /* nb_inplace_true_divide; */
  /* Added in release 2.5 */
#if PY_VERSION_HEX >= 0x02050000
  (unaryfunc) NA_unaryfunc /* nb_index; */
#endif
};


static PyObject*
NAInteger_tp_new(PyTypeObject *type, PyObject *args, PyObject *kwds);


static PyTypeObject NAInteger_Type = {
        /* The ob_type field must be initialized in the module init function
         * to be portable to Windows without using C++. */
#if (PY_VERSION_HEX < 0x03010000)
        PyObject_HEAD_INIT(NULL)
        0,                      /*ob_size*/
#else
	PyVarObject_HEAD_INIT(NULL, 0)
#endif
        "rpy2.rinterface.NAIntegerType",       /*tp_name*/
        sizeof(PyLongObject),   /*tp_basicsize*/
        0,                      /*tp_itemsize*/
        /* methods */
        0, /*tp_dealloc*/
        0,                      /*tp_print*/
        0,                      /*tp_getattr*/
        0,                      /*tp_setattr*/
        0,                      /*tp_compare*/
        NAInteger_repr,                      /*tp_repr*/
        &NAInteger_NumberMethods,            /*tp_as_number*/
        0,                      /*tp_as_sequence*/
        0,                      /*tp_as_mapping*/
        0,                      /*tp_hash*/
        0,                      /*tp_call*/
        NA_str,                      /*tp_str*/
        0,                      /*tp_getattro*/
        0,                      /*tp_setattro*/
        0,                      /*tp_as_buffer*/
#if (PY_VERSION_HEX < 0x03010000)
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE|Py_TPFLAGS_CHECKTYPES, /*tp_flags*/
#else
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE, /*tp_flags*/
#endif
        NAInteger_Type_doc,                      /*tp_doc*/
        0,                      /*tp_traverse*/
        0,                      /*tp_clear*/
        0,                      /*tp_richcompare*/
        0,                      /*tp_weaklistoffset*/
        0,                      /*tp_iter*/
        0,                      /*tp_iternext*/
        0,                      /*tp_methods*/
        0,                      /*tp_members*/
        0,                      /*tp_getset*/
#if defined(Win32) || defined(Win64)
	NULL,
#else	
        &PyLong_Type,           /*tp_base*/
#endif
        0,                      /*tp_dict*/
        0,                      /*tp_descr_get*/
        0,                      /*tp_descr_set*/
        0,                      /*tp_dictoffset*/
        0, //(initproc)ClosureSexp_init,                      /*tp_init*/
        0,                      /*tp_alloc*/
        NAInteger_tp_new,                      /*tp_new*/
        0,                      /*tp_free*/
        0                      /*tp_is_gc*/
};

static PyObject*
NAInteger_tp_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  static PyLongObject *self = NULL;
  static char *kwlist[] = {0};
  PyObject *py_value;
  Py_ssize_t i, n;

  assert(PyType_IsSubtype(type, &PyLong_Type));

  if (! PyArg_ParseTupleAndKeywords(args, kwds, "", kwlist)) {
    return NULL;
  }
  
  if (self == NULL) {
    py_value = PyLong_FromLong((long)(NA_INTEGER));
    if (py_value == NULL) {
      return NULL;
    }

    assert(PyLong_CheckExact(py_value));
    n = Py_SIZE(py_value);
    if (n < 0)
      n = -n;
    self = (PyLongObject *)(PyLong_Type.tp_alloc(type, n));
    if (self == NULL) {
      Py_DECREF(py_value);
      return NULL;
    }
    assert(PyLong_Check(self));
    Py_SIZE(self) = Py_SIZE(py_value);
    for (i = 0; i < n; i++) {
      self->ob_digit[i] = ((PyLongObject *)py_value)->ob_digit[i];
    }
    Py_DECREF(py_value);
  }
  Py_XINCREF(self);
  return (PyObject *)self;
}

static PyObject*
NAInteger_New(int new)
{
  RPY_NA_NEW(NAInteger_Type, NAInteger_tp_new)
}

/* NA Boolean / Logical */

PyDoc_STRVAR(NALogical_Type_doc,
"Missing value for a boolean in R."
);

static PyObject*
NALogical_tp_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  RPY_NA_TP_NEW("NALogicalType", PyLong_Type, PyLong_FromLong, 
                (long)NA_LOGICAL)
}

static PyObject*
NALogical_New(int new)
{
  RPY_NA_NEW(NALogical_Type, NALogical_tp_new)
}

static PyObject*
NALogical_repr(PyObject *self)
{
  static PyObject* repr = NULL;
  if (repr == NULL) {
#if (PY_VERSION_HEX < 0x03010000)  
    repr = PyString_FromString("NA");
#else
    repr = PyUnicode_FromString("NA");
#endif
  }
  Py_XINCREF(repr);
  return repr;
}

static PyNumberMethods NALogical_NumberMethods = {
  0, /* nb_add */
  0, /* nb_subtract; */
  0, /* nb_multiply; */
#if (PY_VERSION_HEX < 0x03010000)
  0, /* nb_divide; */
#endif
  0, /* nb_remainder; */
  0, /* nb_divmod; */
  0, /* nb_power; */
  0, /* nb_negative; */
  0, /* nb_positive; */
  0, /* nb_absolute; */
  0, /* nb_nonzero;  --  Used by PyObject_IsTrue */
  0, /* nb_invert; */
  0, /* nb_lshift; */
  0, /* nb_rshift; */
  (binaryfunc) NA_binaryfunc, /*  nb_and; */
  (binaryfunc) NA_binaryfunc, /*  nb_xor; */
  (binaryfunc) NA_binaryfunc, /* nb_or; */
#if (PY_VERSION_HEX < 0x03010000)
  0, //(coerce) NA_coerce, /* coercion nb_coerce;       -- Used by the coerce() function */
#endif
  0, /* nb_int; */
#if (PY_VERSION_HEX < 0x03010000)
  0, /* nb_long; */
#else
  NULL, /* reserved */
#endif
  0, /* nb_float; */
#if (PY_VERSION_HEX < 0x03010000)
  0, /* nb_oct; */
  0, /* nb_hex; */
#endif
  /* Added in release 2.0 */
  0, /* nb_inplace_add; */
  0, /* nb_inplace_subtract; */
  0, /* nb_inplace_multiply; */
#if (PY_VERSION_HEX < 0x03010000)
  0, /* nb_inplace_divide; */
#endif
  0, /* nb_inplace_remainder; */
  0, /* nb_inplace_power; */
  0, /* nb_inplace_lshift; */
  0, /* nb_inplace_rshift; */
  0, /* nb_inplace_and; */
  0, /* nb_inplace_xor; */
  0, /* nb_inplace_or; */
  /* Added in release 2.2 */
  0, /* nb_floor_divide; */
  0, /* nb_true_divide; */
  0, /* nb_inplace_floor_divide; */
  0, /* nb_inplace_true_divide; */
  /* Added in release 2.5 */
#if PY_VERSION_HEX >= 0x02050000
  0 /* nb_index; */
#endif
};

static PyTypeObject NALogical_Type = {
        /* The ob_type field must be initialized in the module init function
         * to be portable to Windows without using C++. */
#if (PY_VERSION_HEX < 0x03010000)
        PyObject_HEAD_INIT(NULL)
        0,                      /*ob_size*/
#else
	PyVarObject_HEAD_INIT(NULL, 0)
#endif
        "rpy2.rinterface.NALogicalType",       /*tp_name*/
        sizeof(PyLongObject),   /*tp_basicsize*/
        0,                      /*tp_itemsize*/
        /* methods */
        0, /*tp_dealloc*/
        0,                      /*tp_print*/
        0,                      /*tp_getattr*/
        0,                      /*tp_setattr*/
        0,                      /*tp_compare*/
        NALogical_repr,                      /*tp_repr*/
        &NALogical_NumberMethods,                      /*tp_as_number*/
        0,                      /*tp_as_sequence*/
        0,                      /*tp_as_mapping*/
        0,                      /*tp_hash*/
        0,                      /*tp_call*/
        NA_str,                      /*tp_str*/
        0,                      /*tp_getattro*/
        0,                      /*tp_setattro*/
        0,                      /*tp_as_buffer*/
#if (PY_VERSION_HEX < 0x03010000)
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE|Py_TPFLAGS_CHECKTYPES, /*tp_flags*/
#else
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE, /*tp_flags*/
#endif
        NALogical_Type_doc,                      /*tp_doc*/
        0,                      /*tp_traverse*/
        0,                      /*tp_clear*/
        0,                      /*tp_richcompare*/
        0,                      /*tp_weaklistoffset*/
        0,                      /*tp_iter*/
        0,                      /*tp_iternext*/
        0, //NAInteger_methods,           /*tp_methods*/
        0,                      /*tp_members*/
        0,                      /*tp_getset*/
#if defined(Win32) || defined(Win64)
	NULL,
#else
        &PyLong_Type,             /*tp_base*/
#endif
        0,                      /*tp_dict*/
        0,                      /*tp_descr_get*/
        0,                      /*tp_descr_set*/
        0,                      /*tp_dictoffset*/
        0, //(initproc)ClosureSexp_init,                      /*tp_init*/
        0,                      /*tp_alloc*/
        NALogical_tp_new,                      /*tp_new*/
        0,                      /*tp_free*/
        0                      /*tp_is_gc*/
};

/* NA Float / Real */

PyDoc_STRVAR(NAReal_Type_doc,
"Missing value for a float in R."
);

static PyObject*
NAReal_tp_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  //printf("--->0x%llx\n", *(unsigned long long *)&(NAREAL_IEEE.value));
  static PyObject *self = NULL;
  static char *kwlist[] = {0};
  PyObject *py_value;

  assert(PyType_IsSubtype(type, &PyFloat_Type));

  if (! PyArg_ParseTupleAndKeywords(args, kwds, "", kwlist)) {
    return NULL;
  }

  if (self == NULL) {
    py_value = PyFloat_FromDouble((double)(NAREAL_IEEE.value));
    //(double)0x7ff00000000007a2
    //NA_REAL
    //py_value = PyFloat_FromDouble(NA_REAL);
    if (py_value == NULL) {
      return NULL;
    }
    assert(PyFloat_CheckExact(py_value));
    self = type->tp_alloc(type, 0);
    if (self == NULL) {
      //printf("--->\n");
      Py_DECREF(py_value);
      return NULL;
    }
    ((PyFloatObject *)self)->ob_fval = ((PyFloatObject *)py_value)->ob_fval;
    //((PyFloatObject *)self)->ob_fval = (double)(NAREAL_IEEE.value);
    Py_DECREF(py_value);
  }
  Py_INCREF(self);
  return self;
  /* RPY_NA_TP_NEW("NARealType", PyFloat_Type, PyFloat_FromDouble, */
  /* 		  NA_REAL); */
}

static PyObject*
NAReal_New(int new)
{
  RPY_NA_NEW(NAReal_Type, NAReal_tp_new)
}

static PyObject*
NAReal_repr(PyObject *self)
{
  static PyObject* repr = NULL;
  if (repr == NULL) {
#if (PY_VERSION_HEX < 0x03010000)  
    repr = PyString_FromString("NA_real_");
#else
    repr = PyUnicode_FromString("NA_real_");
#endif
  }
  Py_XINCREF(repr);
  return repr;
}


static PyNumberMethods NAReal_NumberMethods = {
  (binaryfunc)NA_binaryfunc, /* nb_add */
  (binaryfunc)NA_binaryfunc, /* nb_subtract; */
  (binaryfunc)NA_binaryfunc, /* nb_multiply; */
#if (PY_VERSION_HEX < 0x03010000)
  (binaryfunc)NA_binaryfunc, /* nb_divide; */
#endif
  (binaryfunc)NA_binaryfunc, /* nb_remainder; */
  (binaryfunc)NA_binaryfunc, /* nb_divmod; */
  (ternaryfunc)NA_ternaryfunc, /* nb_power; */
  (unaryfunc) NA_unaryfunc, /* nb_negative; */
  (unaryfunc) NA_unaryfunc, /* nb_positive; */
  (unaryfunc) NA_unaryfunc, /* nb_absolute; */
  (inquiry) NA_nonzero, /* nb_nonzero;   -- Used by PyObject_IsTrue */
  0, /* nb_invert; */
  0, /* nb_lshift; */
  0, /* nb_rshift; */
  0, /*  nb_and; */
  0, /*  nb_xor; */
  0, /* nb_or; */
#if (PY_VERSION_HEX < 0x03010000)
  0, //(coerce) NA_coerce, /* coercion nb_coerce;       -- Used by the coerce() function */
#endif
  (unaryfunc) NA_unaryfunc, /* nb_int; */
#if (PY_VERSION_HEX < 0x03010000)
  (unaryfunc) NA_unaryfunc, /* nb_long; */
#else
  NULL, /* reserved */
#endif
  (unaryfunc) NA_unaryfunc, /* nb_float; */
#if (PY_VERSION_HEX < 0x03010000)
  0, /* nb_oct; */
  0, /* nb_hex; */
#endif
  /* Added in release 2.0 */
  0, /* nb_inplace_add; */
  0, /* nb_inplace_subtract; */
  0, /* nb_inplace_multiply; */
#if (PY_VERSION_HEX < 0x03010000)
  0, /* nb_inplace_divide; */
#endif
  0, /* nb_inplace_remainder; */
  0, /* nb_inplace_power; */
  0, /* nb_inplace_lshift; */
  0, /* nb_inplace_rshift; */
  0, /* nb_inplace_and; */
  0, /* nb_inplace_xor; */
  0, /* nb_inplace_or; */
  /* Added in release 2.2 */
  (binaryfunc) NA_binaryfunc, /* nb_floor_divide; */
  (binaryfunc) NA_binaryfunc, /* nb_true_divide; */
  0, /* nb_inplace_floor_divide; */
  0, /* nb_inplace_true_divide; */
  /* Added in release 2.5 */
#if PY_VERSION_HEX >= 0x02050000
  0 /* nb_index; */
#endif
};


static PyTypeObject NAReal_Type = {
        /* The ob_type field must be initialized in the module init function
         * to be portable to Windows without using C++. */
#if (PY_VERSION_HEX < 0x03010000)
        PyObject_HEAD_INIT(NULL)
        0,                      /*ob_size*/
#else
	PyVarObject_HEAD_INIT(NULL, 0)
#endif
        "rpy2.rinterface.NARealType",       /*tp_name*/
        sizeof(PyFloatObject),   /*tp_basicsize*/
        0,                      /*tp_itemsize*/
        /* methods */
        0, /*tp_dealloc*/
        0,                      /*tp_print*/
        0,                      /*tp_getattr*/
        0,                      /*tp_setattr*/
        0,                      /*tp_compare*/
        NAReal_repr,                      /*tp_repr*/
        &NAReal_NumberMethods,                      /*tp_as_number*/
        0,                      /*tp_as_sequence*/
        0,                      /*tp_as_mapping*/
        0,                      /*tp_hash*/
        0,                      /*tp_call*/
        NA_str,                      /*tp_str*/
        0,                      /*tp_getattro*/
        0,                      /*tp_setattro*/
        0,                      /*tp_as_buffer*/
#if (PY_VERSION_HEX < 0x03010000)
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE|Py_TPFLAGS_CHECKTYPES, /*tp_flags*/
#else
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE, /*tp_flags*/
#endif
        NAReal_Type_doc,                      /*tp_doc*/
        0,                      /*tp_traverse*/
        0,                      /*tp_clear*/
        0,                      /*tp_richcompare*/
        0,                      /*tp_weaklistoffset*/
        0,                      /*tp_iter*/
        0,                      /*tp_iternext*/
        0, //NAInteger_methods,           /*tp_methods*/
        0,                      /*tp_members*/
        0,                      /*tp_getset*/
#if defined(Win32) || defined(Win64)
	NULL,
#else
        &PyFloat_Type,             /*tp_base*/
#endif	
        0,                      /*tp_dict*/
        0,                      /*tp_descr_get*/
        0,                      /*tp_descr_set*/
        0,                      /*tp_dictoffset*/
        0, //(initproc)ClosureSexp_init,                      /*tp_init*/
        0,                      /*tp_alloc*/
        NAReal_tp_new,                      /*tp_new*/
        0,                      /*tp_free*/
        0                      /*tp_is_gc*/
};

/* NA Character */

PyDoc_STRVAR(NACharacter_Type_doc,
"Missing value for a string."
);

static PyObject*
NACharacter_tp_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
#if (PY_VERSION_HEX < 0x03010000)
  RPY_NA_TP_NEW("NACharacterType", PyString_Type, PyString_FromString, "")
#else
    RPY_NA_TP_NEW("NACharacterType", PyUnicode_Type, PyUnicode_FromString, "")
#endif
}

static PyObject*
NACharacter_New(int new)
{
  RPY_NA_NEW(NACharacter_Type, NACharacter_tp_new)
}


static PyObject*
NACharacter_repr(PyObject *self)
{
  static PyObject* repr = NULL;
  if (repr == NULL) {
#if (PY_VERSION_HEX < 0x03010000)
    repr = PyString_FromString("NA_character_");
#else
    repr = PyUnicode_FromString("NA_character_");
#endif
  }
  Py_XINCREF(repr);
  return repr;
}


static PyTypeObject NACharacter_Type = {
        /* The ob_type field must be initialized in the module init function
         * to be portable to Windows without using C++. */
#if (PY_VERSION_HEX < 0x03010000)
        PyObject_HEAD_INIT(NULL)
        0,                      /*ob_size*/
#else
	PyVarObject_HEAD_INIT(NULL, 0)
#endif
        "rpy2.rinterface.NACharacterType",       /*tp_name*/
#if (PY_VERSION_HEX < 0x03010000)
        sizeof(PyStringObject),             /*tp_basicsize*/
#else
	sizeof(PyUnicodeObject),             /*tp_basicsize*/
#endif
        0,                      /*tp_itemsize*/
        /* methods */
        0, /*tp_dealloc*/
        0,                      /*tp_print*/
        0,                      /*tp_getattr*/
        0,                      /*tp_setattr*/
        0,                      /*tp_compare*/
        NACharacter_repr,                      /*tp_repr*/
        0,                      /*tp_as_number*/
        0,                      /*tp_as_sequence*/
        0,                      /*tp_as_mapping*/
        0,                      /*tp_hash*/
        0,                      /*tp_call*/
        NA_str,                      /*tp_str*/
        0,                      /*tp_getattro*/
        0,                      /*tp_setattro*/
        0,                      /*tp_as_buffer*/
#if (PY_VERSION_HEX < 0x03010000)
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE|Py_TPFLAGS_CHECKTYPES, /*tp_flags*/
#else
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE, /*tp_flags*/
#endif
        NACharacter_Type_doc,                      /*tp_doc*/
        0,                      /*tp_traverse*/
        0,                      /*tp_clear*/
        0,                      /*tp_richcompare*/
        0,                      /*tp_weaklistoffset*/
        0,                      /*tp_iter*/
        0,                      /*tp_iternext*/
        0, //NAInteger_methods,           /*tp_methods*/
        0,                      /*tp_members*/
        0,                      /*tp_getset*/
#if defined(Win32) || defined(Win64)
	NULL,
#elif (PY_VERSION_HEX < 0x03010000)
        &PyString_Type,             /*tp_base*/
#else
	&PyUnicode_Type,
#endif
        0,                      /*tp_dict*/
        0,                      /*tp_descr_get*/
        0,                      /*tp_descr_set*/
        0,                      /*tp_dictoffset*/
        0, //(initproc)ClosureSexp_init,                      /*tp_init*/
        0,                      /*tp_alloc*/
        NACharacter_tp_new,                      /*tp_new*/
        0,                      /*tp_free*/
        0                      /*tp_is_gc*/
};


/* NA Complex */

PyDoc_STRVAR(NAComplex_Type_doc,
"Missing value for a complex in R."
);

static PyObject*
NAComplex_tp_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  //static PyObject *self = NULL;
  //static char *kwlist[] = {0};

  Py_complex pyvalue = {(double)NAREAL_IEEE.value,
			(double)NAREAL_IEEE.value};

   
  assert(PyType_IsSubtype(type, &PyComplex_Type));

  RPY_NA_TP_NEW('Complex', PyComplex_Type, 
		PyComplex_FromCComplex, pyvalue);

}

static PyObject*
NAComplex_New(int new)
{
  RPY_NA_NEW(NAComplex_Type, NAComplex_tp_new)
}

static PyObject*
NAComplex_repr(PyObject *self)
{
  static PyObject* repr = NULL;
  if (repr == NULL) {
#if (PY_VERSION_HEX < 0x03010000)
    repr = PyString_FromString("NA_complex_");
#else
    repr = PyUnicode_FromString("NA_complex_");
#endif
  }
  Py_XINCREF(repr);
  return repr;
}


static PyNumberMethods NAComplex_NumberMethods = {
  (binaryfunc)NA_binaryfunc, /* nb_add */
  (binaryfunc)NA_binaryfunc, /* nb_subtract; */
  (binaryfunc)NA_binaryfunc, /* nb_multiply; */
#if (PY_VERSION_HEX < 0x03010000)
  (binaryfunc)NA_binaryfunc, /* nb_divide; */
#endif
  (binaryfunc)NA_binaryfunc, /* nb_remainder; */
  (binaryfunc)NA_binaryfunc, /* nb_divmod; */
  (ternaryfunc)NA_ternaryfunc, /* nb_power; */
  (unaryfunc) NA_unaryfunc, /* nb_negative; */
  (unaryfunc) NA_unaryfunc, /* nb_positive; */
  (unaryfunc) NA_unaryfunc, /* nb_absolute; */
  (inquiry) NA_nonzero, /* nb_nonzero;   -- Used by PyObject_IsTrue */
  0, /* nb_invert; */
  0, /* nb_lshift; */
  0, /* nb_rshift; */
  0, /*  nb_and; */
  0, /*  nb_xor; */
  0, /* nb_or; */
#if (PY_VERSION_HEX < 0x03010000)
  0, //(coerce) NA_coerce, /* coercion nb_coerce;       -- Used by the coerce() function */
#endif
  (unaryfunc) NA_unaryfunc, /* nb_int; */
#if (PY_VERSION_HEX < 0x03010000)
  (unaryfunc) NA_unaryfunc, /* nb_long; */
#else
  NULL, /* reserved */
#endif
  (unaryfunc) NA_unaryfunc, /* nb_float; */
#if (PY_VERSION_HEX < 0x03010000)
  0, /* nb_oct; */
  0, /* nb_hex; */
#endif
  /* Added in release 2.0 */
  0, /* nb_inplace_add; */
  0, /* nb_inplace_subtract; */
  0, /* nb_inplace_multiply; */
#if (PY_VERSION_HEX < 0x03010000)
  0, /* nb_inplace_divide; */
#endif
  0, /* nb_inplace_remainder; */
  0, /* nb_inplace_power; */
  0, /* nb_inplace_lshift; */
  0, /* nb_inplace_rshift; */
  0, /* nb_inplace_and; */
  0, /* nb_inplace_xor; */
  0, /* nb_inplace_or; */
  /* Added in release 2.2 */
  (binaryfunc) NA_binaryfunc, /* nb_floor_divide; */
  (binaryfunc) NA_binaryfunc, /* nb_true_divide; */
  0, /* nb_inplace_floor_divide; */
  0, /* nb_inplace_true_divide; */
  /* Added in release 2.5 */
#if PY_VERSION_HEX >= 0x02050000
  0 /* nb_index; */
#endif
};


static PyTypeObject NAComplex_Type = {
        /* The ob_type field must be initialized in the module init function
         * to be portable to Windows without using C++. */
#if (PY_VERSION_HEX < 0x03010000)
        PyObject_HEAD_INIT(NULL)
        0,                      /*ob_size*/
#else
	PyVarObject_HEAD_INIT(NULL, 0)
#endif
        "rpy2.rinterface.NAComplexType",       /*tp_name*/
        sizeof(PyComplexObject),   /*tp_basicsize*/
        0,                      /*tp_itemsize*/
        /* methods */
        0, /*tp_dealloc*/
        0,                      /*tp_print*/
        0,                      /*tp_getattr*/
        0,                      /*tp_setattr*/
        0,                      /*tp_compare*/
        NAComplex_repr,                      /*tp_repr*/
        &NAComplex_NumberMethods,                      /*tp_as_number*/
        0,                      /*tp_as_sequence*/
        0,                      /*tp_as_mapping*/
        0,                      /*tp_hash*/
        0,                      /*tp_call*/
        NA_str,                      /*tp_str*/
        0,                      /*tp_getattro*/
        0,                      /*tp_setattro*/
        0,                      /*tp_as_buffer*/
#if (PY_VERSION_HEX < 0x03010000)
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE|Py_TPFLAGS_CHECKTYPES, /*tp_flags*/
#else
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE, /*tp_flags*/
#endif
        NAComplex_Type_doc,                      /*tp_doc*/
        0,                      /*tp_traverse*/
        0,                      /*tp_clear*/
        0,                      /*tp_richcompare*/
        0,                      /*tp_weaklistoffset*/
        0,                      /*tp_iter*/
        0,                      /*tp_iternext*/
        0, //NAInteger_methods,           /*tp_methods*/
        0,                      /*tp_members*/
        0,                      /*tp_getset*/
#if defined(Win32) || defined(Win64)
	NULL,
#else
        &PyComplex_Type,             /*tp_base*/
#endif
        0,                      /*tp_dict*/
        0,                      /*tp_descr_get*/
        0,                      /*tp_descr_set*/
        0,                      /*tp_dictoffset*/
        0, //(initproc)ClosureSexp_init,                      /*tp_init*/
        0,                      /*tp_alloc*/
        NAComplex_tp_new,                      /*tp_new*/
        0,                      /*tp_free*/
        0                      /*tp_is_gc*/
};


/* Missing parameter value (not an NA in the usual sense) */

PyDoc_STRVAR(MissingArg_Type_doc,
"Missing argument (in a function call)."
);

#if (PY_VERSION_HEX < 0x03010000)
staticforward PyTypeObject MissingArg_Type;
#else
static PyTypeObject MissingArg_Type;
#endif

static PyObject*
MissingArgType_tp_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  static PySexpObject *self = NULL;
  static char *kwlist[] = {0};

  if (! PyArg_ParseTupleAndKeywords(args, kwds, "", kwlist)) {
    return NULL;
  }

  if (self == NULL) {
    self = (PySexpObject*)(Sexp_Type.tp_new(&MissingArg_Type, Py_None, Py_None));
    if (self == NULL) {
      return NULL;
    }
  }
  Py_XINCREF(self);
  return (PyObject *)self;
}

static PyObject*
MissingArgType_tp_init(PyObject *self, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = {0};
  if (! PyArg_ParseTupleAndKeywords(args, kwds, "", kwlist)) {
    return NULL;
  }
  return 0;
}

static PyObject*
MissingArgType_repr(PyObject *self)
{
  static PyObject* repr = NULL;
  if (repr == NULL) {
#if (PY_VERSION_HEX < 0x03010000)
    repr = PyString_FromString("rpy2.rinterface.MissingArg");
#else
    repr = PyUnicode_FromString("rpy2.rinterface.MissingArg");
#endif
  }
  Py_XINCREF(repr);
  return repr;
}

static PyObject*
MissingArgType_str(PyObject *self)
{
  static PyObject* repr = NULL;
  if (repr == NULL) {
#if (PY_VERSION_HEX < 0x03010000)  
    repr = PyString_FromString("MissingArg");
#else
    repr = PyUnicode_FromString("MissingArg");
#endif
  }
  Py_XINCREF(repr);
  return repr;
}

static PyTypeObject MissingArg_Type = {
        /* The ob_type field must be initialized in the module init function
         * to be portable to Windows without using C++. */
#if (PY_VERSION_HEX < 0x03010000)
        PyObject_HEAD_INIT(NULL)
        0,                      /*ob_size*/
#else
	PyVarObject_HEAD_INIT(NULL, 0)
#endif
        "rpy2.rinterface.MissingArgType",       /*tp_name*/
        sizeof(PySexpObject),   /*tp_basicsize*/
        0,                      /*tp_itemsize*/
        /* methods */
        0, /*tp_dealloc*/
        0,                      /*tp_print*/
        0,                      /*tp_getattr*/
        0,                      /*tp_setattr*/
        0,                      /*tp_compare*/
        MissingArgType_repr,                      /*tp_repr*/
        0,                      /*tp_as_number*/
        0,                      /*tp_as_sequence*/
        0,                      /*tp_as_mapping*/
        0,                      /*tp_hash*/
        0,                      /*tp_call*/
        MissingArgType_str,                      /*tp_str*/
        0,                      /*tp_getattro*/
        0,                      /*tp_setattro*/
        0,                      /*tp_as_buffer*/
#if (PY_VERSION_HEX < 0x03010000)
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE|Py_TPFLAGS_CHECKTYPES, /*tp_flags*/
#else
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE, /*tp_flags*/
#endif
        MissingArg_Type_doc,                      /*tp_doc*/
        0,                      /*tp_traverse*/
        0,                      /*tp_clear*/
        0,                      /*tp_richcompare*/
        0,                      /*tp_weaklistoffset*/
        0,                      /*tp_iter*/
        0,                      /*tp_iternext*/
        0, //NAInteger_methods,           /*tp_methods*/
        0,                      /*tp_members*/
        0,                      /*tp_getset*/
        &Sexp_Type,             /*tp_base*/
        0,                      /*tp_dict*/
        0,                      /*tp_descr_get*/
        0,                      /*tp_descr_set*/
        0,                      /*tp_dictoffset*/
        (initproc)MissingArgType_tp_init,                      /*tp_init*/
        0,                      /*tp_alloc*/
        MissingArgType_tp_new,                      /*tp_new*/
        0,                      /*tp_free*/
        0                      /*tp_is_gc*/
};


static PyObject*
MissingArg_Type_New(int new)
{
  RPY_NA_NEW(MissingArg_Type, MissingArgType_tp_new)
}

