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
 * Copyright (C) 2008-2010 Laurent Gautier
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

#include <Python.h>
#include <Rdefines.h>
#include <Rinternals.h>
#include "rpy_rinterface.h"

#include "embeddedr.h"
#include "sexp.h"
#include "sequence.h"


/* len(x) */
static Py_ssize_t VectorSexp_len(PySexpObject* object)
{
  if (rpy_has_status(RPY_R_BUSY)) {
    PyErr_Format(PyExc_RuntimeError, "Concurrent access to R is not allowed.");
    return -1;
  }
  embeddedR_setlock();

  Py_ssize_t len;
  /* FIXME: sanity checks. */
  SEXP sexp = RPY_SEXP(object);
  if (! sexp) {
      PyErr_Format(PyExc_ValueError, "NULL SEXP.");
      return -1;
  }
  len = (Py_ssize_t)GET_LENGTH(sexp);

  embeddedR_freelock();
  return len;
}

/* a[i] */
static PyObject *
VectorSexp_item(PySexpObject* object, Py_ssize_t i)
{
  PyObject* res;
  R_len_t i_R, len_R;
  if (rpy_has_status(RPY_R_BUSY)) {
    PyErr_Format(PyExc_RuntimeError, "Concurrent access to R is not allowed.");
    return NULL;
  }
  embeddedR_setlock();
  SEXP *sexp = &(RPY_SEXP(object));

  if (! sexp) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    embeddedR_freelock();
    return NULL;
  }

  len_R = GET_LENGTH(*sexp);
  
  if (i < 0) {
    /*FIXME: check that unit tests are covering this properly */
    /*FIXME: is this valid for Python < 3 ? */
#if (PY_VERSION_HEX < 0x03010000)
    i = len_R - i;
#else
    i += len_R;
#endif
  }

  /* On 64bits, Python is apparently able to use larger integer
   * than R for indexing. */
  if (i >= R_LEN_T_MAX) {
    PyErr_Format(PyExc_IndexError, "Index value exceeds what R can handle.");
    embeddedR_freelock();
    res = NULL;
    return res;
  }

  if (i < 0) {
    PyErr_Format(PyExc_IndexError, 
                 "Mysterious error: likely an integer overflow.");
    res = NULL;
    embeddedR_freelock();
    return res;
  }
  if ((i >= GET_LENGTH(*sexp))) {
    PyErr_Format(PyExc_IndexError, "Index out of range.");
    res = NULL;
  }
  else {
    double vd;
    int vi;
    Rcomplex vc;
    const char *vs;
    SEXP tmp, sexp_item; /* needed by LANGSXP */
    i_R = (R_len_t)i;
    switch (TYPEOF(*sexp)) {
    case REALSXP:
      vd = (NUMERIC_POINTER(*sexp))[i_R];
      if (R_IsNA(vd)) {
        res = NAReal_New(1);
      } else {
        res = PyFloat_FromDouble(vd);
      }
      break;
    case INTSXP:
      vi = INTEGER_POINTER(*sexp)[i_R];
      if (vi == NA_INTEGER) {
        res = NAInteger_New(1);
      } else {
#if (PY_VERSION_HEX < 0x03010000)
        res = PyInt_FromLong((long)vi);
#else
	res = PyLong_FromLong((long)vi);
#endif
      }
      break;
    case LGLSXP:
      vi = LOGICAL_POINTER(*sexp)[i_R];
      if (vi == NA_LOGICAL) {
        res = NALogical_New(1);
      } else {
        RPY_PY_FROM_RBOOL(res, vi);
      }
      break;
    case CPLXSXP:
      vc = COMPLEX_POINTER(*sexp)[i_R];
      res = PyComplex_FromDoubles(vc.r, vc.i);
      break;
    case STRSXP:
      if (STRING_ELT(*sexp, i_R) == NA_STRING) {
        res = NACharacter_New(1);
      } else {
        vs = translateChar(STRING_ELT(*sexp, i_R));
#if (PY_VERSION_HEX < 0x03010000)
        res = PyString_FromString(vs);
#else
	res = PyUnicode_FromString(vs);
#endif
      }
      break;
/*     case CHARSXP: */
      /*       FIXME: implement handling of single char (if possible ?) */
/*       vs = (CHAR(*sexp)[i_R]); */
/*       res = PyString_FromStringAndSize(vs, 1); */
    case VECSXP:
    case EXPRSXP:
      sexp_item = VECTOR_ELT(*sexp, i_R);
      res = (PyObject *)newPySexpObject(sexp_item, 1);
      break;
    case LISTSXP:
      tmp = nthcdr(*sexp, i_R);
      sexp_item = allocVector(LISTSXP, 1);
      SETCAR(sexp_item, CAR(tmp));
      SET_TAG(sexp_item, TAG(tmp));
      res = (PyObject *)newPySexpObject(sexp_item, 1);
      break;      
    case LANGSXP:
      sexp_item = CAR(nthcdr(*sexp, i_R));
      res = (PyObject *)newPySexpObject(sexp_item, 1);
      break;
    default:
      PyErr_Format(PyExc_ValueError, "Cannot handle type %d", 
                   TYPEOF(*sexp));
      res = NULL;
      break;
    }
  }
  embeddedR_freelock();
  return res;
}

/* a[i1:i2] */
static PyObject *
VectorSexp_slice(PySexpObject* object, Py_ssize_t ilow, Py_ssize_t ihigh)
{
  R_len_t len_R;

  if (rpy_has_status(RPY_R_BUSY)) {
    PyErr_Format(PyExc_RuntimeError, "Concurrent access to R is not allowed.");
    return NULL;
  }
  embeddedR_setlock();
  SEXP *sexp = &(RPY_SEXP(object));
  SEXP res_sexp, tmp, tmp2;

  if (! sexp) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    embeddedR_freelock();
    return NULL;
  }


  len_R = GET_LENGTH(*sexp);

  /*FIXME: is this valid for Python < 3 ?*/  
#if (PY_VERSION_HEX < 0x03010000)
  if (ilow < 0) {
    ilow = (R_len_t)(len_R - ilow) + 1;
  }
  if (ihigh < 0) {
    ihigh = (R_len_t)(len_R - ihigh) + 1;
  }
#endif

  /* On 64bits, Python is apparently able to use larger integer
   * than R for indexing. */
  if ((ilow >= R_LEN_T_MAX) | (ihigh >= R_LEN_T_MAX)) {
    PyErr_Format(PyExc_IndexError, 
                 "Index values in the slice exceed what R can handle.");
    embeddedR_freelock();
    return NULL;
  }

  if ((ilow < 0) | (ihigh < 0)) {
    PyErr_Format(PyExc_IndexError, 
                 "Mysterious error: likely an integer overflow.");
    embeddedR_freelock();
    return NULL;
  }
  if ((ilow > GET_LENGTH(*sexp)) | (ihigh > GET_LENGTH(*sexp))) {
    PyErr_Format(PyExc_IndexError, "Index out of range.");
    return NULL;
  } else {
    if ( ilow > ihigh ) {
      /* Whenever this occurs for regular Python lists,
      * a sequence of length 0 is returned. Setting ilow:=ilow
      * causes the same whithout writing "special case" code.
      */
      ihigh = ilow;
    }
    R_len_t slice_len = ihigh-ilow;
    R_len_t slice_i;
    //const char *vs;
    //SEXP tmp, sexp_item; /* tmp and sexp_item needed for case LANGSXP */
    switch (TYPEOF(*sexp)) {
    case REALSXP:
      res_sexp = allocVector(REALSXP, slice_len);
      memcpy(NUMERIC_POINTER(res_sexp),
             NUMERIC_POINTER(*sexp) + ilow,  
             (ihigh-ilow) * sizeof(double));
      break;
    case INTSXP:
      res_sexp = allocVector(INTSXP, slice_len);
      memcpy(INTEGER_POINTER(res_sexp),
             INTEGER_POINTER(*sexp) + ilow,  
             (ihigh-ilow) * sizeof(int));
      break;
    case LGLSXP:
      res_sexp = allocVector(LGLSXP, slice_len);
      memcpy(LOGICAL_POINTER(res_sexp),
             LOGICAL_POINTER(*sexp) + ilow,  
             (ihigh-ilow) * sizeof(int));
      break;
    case CPLXSXP:
      res_sexp = allocVector(CPLXSXP, slice_len);
      for (slice_i = 0; slice_i < slice_len; slice_i++) {
        COMPLEX_POINTER(res_sexp)[slice_i] = (COMPLEX_POINTER(*sexp))[slice_i + ilow];
      }
      break;
    case STRSXP:
      res_sexp = allocVector(STRSXP, slice_len);
      for (slice_i = 0; slice_i < slice_len; slice_i++) {
        SET_STRING_ELT(res_sexp, slice_i, STRING_ELT(*sexp, slice_i + ilow));
      }
      break;
/*     case CHARSXP: */
      /*       FIXME: implement handling of single char (if possible ?) */
/*       vs = (CHAR(*sexp)[i_R]); */
/*       res = PyString_FromStringAndSize(vs, 1); */
    case VECSXP:
    case EXPRSXP:
      res_sexp = allocVector(VECSXP, slice_len);
      for (slice_i = 0; slice_i < slice_len; slice_i++) {
        SET_VECTOR_ELT(res_sexp, slice_i, VECTOR_ELT(*sexp, slice_i + ilow));
      }
      break;
    case LANGSXP:
      PROTECT(res_sexp = allocList(slice_len));
      if ( slice_len > 0 ) {
	SET_TYPEOF(res_sexp, LANGSXP);
      }
      for (tmp = *sexp, tmp2 = res_sexp, slice_i = 0; 
	   slice_i < slice_len + ilow; tmp = CDR(tmp)) {
	if (slice_i - ilow > 0) {
	  tmp2 = CDR(tmp2);
	  SETCAR(tmp2, tmp);
	}
	slice_i++;
      }
      UNPROTECT(1);
      break;
    case LISTSXP:
    default:
      PyErr_Format(PyExc_ValueError, "Cannot handle type %d", 
                   TYPEOF(*sexp));
      res_sexp = NULL;
      break;
    }

  }
  embeddedR_freelock();
  if (res_sexp == NULL) {    return NULL;
  }
  return (PyObject*)newPySexpObject(res_sexp, 1);
}


/* a[i] = val */
static int
VectorSexp_ass_item(PySexpObject* object, Py_ssize_t i, PyObject* val)
{
  R_len_t i_R, len_R;
  int self_typeof;

  /* Check for 64 bits platforms */
  if (i >= R_LEN_T_MAX) {
    PyErr_Format(PyExc_IndexError, "Index value exceeds what R can handle.");
    return -1;
  }

  SEXP *sexp = &(RPY_SEXP(object));
  len_R = GET_LENGTH(*sexp);
  
  if (i < 0) {
    /* FIXME: Is this valid for Python < 3 ?*/
#if (PY_VERSION_HEX < 0x03010000)
    i = len_R - i;
#else
    i = len_R + i;
#endif
  }

  if (i >= len_R) {
    PyErr_Format(PyExc_IndexError, "Index out of range.");
    return -1;
  }

  if (! sexp) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return -1;
  }
  
  int is_PySexpObject = PyObject_TypeCheck(val, &Sexp_Type);
  if (! is_PySexpObject) {
    PyErr_Format(PyExc_ValueError, "Any new value must be of "
                 "type 'Sexp_Type'.");
    return -1;
  }
  SEXP *sexp_val = &(RPY_SEXP((PySexpObject *)val));
  if (! sexp_val) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return -1;
  }

  self_typeof = TYPEOF(*sexp);

  if ( (self_typeof != VECSXP) && self_typeof != LANGSXP ) {
    if (TYPEOF(*sexp_val) != self_typeof) {
      PyErr_Format(PyExc_ValueError, 
                   "The new value cannot be of 'typeof' other than %i ('%i' given)", 
                   self_typeof, TYPEOF(*sexp_val));
      return -1;
    }
    
    if (LENGTH(*sexp_val) != 1) {
      PyErr_Format(PyExc_ValueError, "The new value must be of length 1.");
      return -1;
    }

  }

  SEXP sexp_copy;
  i_R = (R_len_t)i;
  switch (self_typeof) {
  case REALSXP:
    (NUMERIC_POINTER(*sexp))[i_R] = (NUMERIC_POINTER(*sexp_val))[0];
    break;
  case INTSXP:
    (INTEGER_POINTER(*sexp))[i_R] = (INTEGER_POINTER(*sexp_val))[0];
    break;
  case LGLSXP:
    (LOGICAL_POINTER(*sexp))[i_R] = (LOGICAL_POINTER(*sexp_val))[0];
    break;
  case CPLXSXP:
    (COMPLEX_POINTER(*sexp))[i_R] = (COMPLEX_POINTER(*sexp_val))[0];
    break;
  case STRSXP:
    SET_STRING_ELT(*sexp, i_R, STRING_ELT(*sexp_val, 0));
    break;
  case VECSXP:
    PROTECT(sexp_copy = Rf_duplicate(*sexp_val));
    SET_VECTOR_ELT(*sexp, i_R, sexp_copy);
    UNPROTECT(1);
    break;
  case LANGSXP:
    SETCAR(nthcdr(*sexp, i_R), *sexp_val);
    break;
  default:
    PyErr_Format(PyExc_ValueError, "Cannot handle typeof '%d'", 
                 self_typeof);
    return -1;
    break;
  }
  return 0;
}

/* a[i:j] = val */
static int
VectorSexp_ass_slice(PySexpObject* object, Py_ssize_t ilow, Py_ssize_t ihigh, PyObject *val)
{
  R_len_t len_R;
  int self_typeof;

  if (rpy_has_status(RPY_R_BUSY)) {
    PyErr_Format(PyExc_RuntimeError, "Concurrent access to R is not allowed.");
    return -1;
  }
  embeddedR_setlock();

  if (! PyObject_TypeCheck(val, &Sexp_Type)) {
    PyErr_Format(PyExc_ValueError, "Any new value must be of "
		 "type 'Sexp_Type'.");
    embeddedR_freelock();
    return -1;
  }

  SEXP *sexp = &(RPY_SEXP(object));
  len_R = GET_LENGTH(*sexp);

  /* FIXME: Is this valid for Python < 3 ? */
#if (PY_VERSION_HEX < 0x03010000)  
  if (ilow < 0) {
    ilow = (R_len_t)(len_R - ilow) + 1;
  }
  if (ihigh < 0) {
    ihigh = (R_len_t)(len_R - ihigh) + 1;
  }
#endif

  if (! sexp) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    embeddedR_freelock();
    return -1;
  }
  
  /* On 64bits, Python is apparently able to use larger integer
   * than R for indexing. */
  if ((ilow >= R_LEN_T_MAX) | (ihigh >= R_LEN_T_MAX)) {
    PyErr_Format(PyExc_IndexError, 
                 "Index values in the slice exceed what R can handle.");
    embeddedR_freelock();
    return -1;
  }

  if ((ilow < 0) | (ihigh < 0)) {
    PyErr_Format(PyExc_IndexError, 
                 "Mysterious error: likely an integer overflow.");
    embeddedR_freelock();
    return -1;
  }
  if ((ilow > GET_LENGTH(*sexp)) | (ihigh > GET_LENGTH(*sexp))) {
    PyErr_Format(PyExc_IndexError, "Index out of range.");
    return -1;
  } else {
    if ( ilow > ihigh ) {
      /* Whenever this occurs for regular Python lists,
      * a sequence of length 0 is returned. Setting ilow:=ilow
      * causes the same whithout writing "special case" code.
      */
      ihigh = ilow;
    }

    R_len_t slice_len = ihigh-ilow;
    R_len_t slice_i;
    const char *vs;
    SEXP tmp, sexp_item; /* tmp and sexp_item needed for case LANGSXP */

    SEXP sexp_val = RPY_SEXP((PySexpObject *)val);
    if (! sexp_val) {
      PyErr_Format(PyExc_ValueError, "NULL SEXP.");
      embeddedR_freelock();
      return -1;
    }

    if (slice_len != GET_LENGTH(sexp_val)) {
      PyErr_Format(PyExc_ValueError, "The length of the replacement value differs from the length of the slice.");
      embeddedR_freelock();
      return -1;
    }

    switch (TYPEOF(*sexp)) {
    case REALSXP:
      memcpy(NUMERIC_POINTER(*sexp) + ilow,
	     NUMERIC_POINTER(sexp_val),
             (ihigh-ilow) * sizeof(double));
      break;
    case INTSXP:
      memcpy(INTEGER_POINTER(*sexp) + ilow,
             INTEGER_POINTER(sexp_val),
             (ihigh-ilow) * sizeof(int));
      break;
    case LGLSXP:
      memcpy(LOGICAL_POINTER(*sexp) + ilow,
	     LOGICAL_POINTER(sexp_val),
             (ihigh-ilow) * sizeof(int));
      break;
    case CPLXSXP:
      for (slice_i = 0; slice_i < slice_len; slice_i++) {
        (COMPLEX_POINTER(*sexp))[slice_i + ilow] = COMPLEX_POINTER(sexp_val)[slice_i];
      }
      break;
    case STRSXP:
      for (slice_i = 0; slice_i < slice_len; slice_i++) {
        SET_STRING_ELT(*sexp, slice_i + ilow, STRING_ELT(sexp_val, slice_i));
      }
      break;
    case VECSXP:
    case EXPRSXP:
      for (slice_i = 0; slice_i < slice_len; slice_i++) {
        SET_VECTOR_ELT(*sexp, slice_i + ilow, VECTOR_ELT(sexp_val, slice_i));
      }
      break;
    case CHARSXP:
    case LISTSXP:
    case LANGSXP:
    default:
      PyErr_Format(PyExc_ValueError, "Cannot handle type %d", 
                   TYPEOF(*sexp));
      embeddedR_freelock();
      return -1;
      break;
    }
  }
  embeddedR_freelock();
  return 0;
}


static PySequenceMethods VectorSexp_sequenceMethods = {
  (lenfunc)VectorSexp_len,              /* sq_length */
  0,                              /* sq_concat */
  0,                              /* sq_repeat */
  (ssizeargfunc)VectorSexp_item,        /* sq_item */
#if (PY_VERSION_HEX < 0x03010000)
  (ssizessizeargfunc)VectorSexp_slice,  /* sq_slice */
#else
  0,                                         /* sq_slice */
#endif
  (ssizeobjargproc)VectorSexp_ass_item, /* sq_ass_item */
#if (PY_VERSION_HEX < 0x03010000)
  (ssizessizeobjargproc)VectorSexp_ass_slice, /* sq_ass_slice */
#else
  0,
#endif
  0,                              /* sq_contains */
  0,                              /* sq_inplace_concat */
  0                               /* sq_inplace_repeat */
};

#if (PY_VERSION_HEX < 0x03010000)
#else
/* generic a[i] for Python3 */
static PyObject*
VectorSexp_subscript(PySexpObject *object, PyObject* item)
{
  Py_ssize_t i;
  if (PyIndex_Check(item)) {
    i = PyNumber_AsSsize_t(item, PyExc_IndexError);
    if (i == -1 && PyErr_Occurred()) {
      return NULL;
    }
    /* currently checked in VectorSexp_item */
    /* (but have it here nevertheless) */
    if (i < 0)
       i += VectorSexp_len(object);
    return VectorSexp_item(object, i);
  } 
  else if (PySlice_Check(item)) {
    Py_ssize_t start, stop, step, slicelength;
    Py_ssize_t vec_len = VectorSexp_len(object);
    if (vec_len == -1)
      /* propagate the error */
      return NULL;
    if (PySlice_GetIndicesEx((PySliceObject*)item,
			     vec_len,
			     &start, &stop, &step, &slicelength) < 0) {
      return NULL;
    }
    if (slicelength <= 0) {
      PyErr_Format(PyExc_IndexError,
		   "The slice's length can't be < 0.");
      return NULL;
      /* return VectorSexp_New(0); */
    }
    else {
      if (step == 1) {
	PyObject *result = VectorSexp_slice(object, start, stop);
	return result;
      }
      else {
	PyErr_Format(PyExc_IndexError,
		     "Only slicing with step==1 is supported for the moment.");
	return NULL;
      }
    }
  }
  else {
    PyErr_Format(PyExc_TypeError,
		 "SexpVector indices must be integers, not %.200s",
		 Py_TYPE(item)->tp_name);
    return NULL;
  }
}

/* genericc a[i] = foo for Python 3 */
static int
VectorSexp_ass_subscript(PySexpObject* self, PyObject* item, PyObject* value)
{
    if (PyIndex_Check(item)) {
        Py_ssize_t i = PyNumber_AsSsize_t(item, PyExc_IndexError);
        if (i == -1 && PyErr_Occurred())
            return -1;
        if (i < 0)
            i += VectorSexp_len(self);
        return VectorSexp_ass_item(self, i, value);
    }
    else if (PySlice_Check(item)) {
      Py_ssize_t start, stop, step, slicelength;
      Py_ssize_t vec_len = VectorSexp_len(self);
      if (vec_len == -1)
      /* propagate the error */
      return -1;
      if (PySlice_GetIndicesEx((PySliceObject*)item, vec_len,
			       &start, &stop, &step, &slicelength) < 0) {
	return -1;
      }
      if (step == 1) {
	return VectorSexp_ass_slice(self, start, stop, value);
      } else {
	PyErr_Format(PyExc_IndexError,
		     "Only slicing with step==1 is supported for the moment.");
	return -1;
      }
    }
    else {
      PyErr_Format(PyExc_TypeError,
                     "VectorSexp indices must be integers, not %.200s",
                     item->ob_type->tp_name);
        return -1;
    }
}

static PyMappingMethods VectorSexp_as_mapping = {
  (lenfunc)VectorSexp_len,
  (binaryfunc)VectorSexp_subscript,
  (objobjargproc)VectorSexp_ass_subscript
};
#endif



static PyObject *
VectorSexp_index(PySexpObject *self, PyObject *args)
{
  Py_ssize_t i,  start, stop;
  PyObject *v;
  PyObject *item;

  SEXP sexp = RPY_SEXP(self);
  if (! sexp) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return NULL;
  }
  start = 0;
  stop = (Py_ssize_t)(GET_LENGTH(sexp));

  if (!PyArg_ParseTuple(args, "O|O&O&:index", &v,
			_PyEval_SliceIndex, &start,
			_PyEval_SliceIndex, &stop))
    return NULL;
  if (start < 0) {
    start += (Py_ssize_t)(GET_LENGTH(sexp));
    if (start < 0)
      start = 0;
  }
  if (stop < 0) {
    stop += (Py_ssize_t)(GET_LENGTH(sexp));
    if (stop < 0)
      stop = 0;
  }
  for (i = start; i < stop && i < (Py_ssize_t)(GET_LENGTH(sexp)); i++) {
    item = VectorSexp_item(self, i);
    int cmp = PyObject_RichCompareBool(item, v, Py_EQ);
    Py_DECREF(item);
    if (cmp > 0)
#if (PY_VERSION_HEX < 0x03010000)
      return PyInt_FromSsize_t(i);
#else
      return PyLong_FromSsize_t(i);
#endif
    else if (cmp < 0)
      return NULL;
        }
  PyErr_SetString(PyExc_ValueError, "list.index(x): x not in list");
  return NULL;
  
}

PyDoc_STRVAR(VectorSexp_index_doc,
             "V.index(value, [start, [stop]]) -> integer -- return first index of value."
             "Raises ValueError if the value is not present.");

static PyMethodDef VectorSexp_methods[] = {
  {"index", (PyCFunction)VectorSexp_index, METH_VARARGS, VectorSexp_index_doc},
  {NULL, NULL}
};
  
