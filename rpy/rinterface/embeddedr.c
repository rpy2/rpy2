

/* Helper variable to store R's status
 */
const unsigned int const RPY_R_INITIALIZED = 0x01;
const unsigned int const RPY_R_BUSY = 0x02;
/* Initial status is 0 */
static unsigned int embeddedR_status = 0;

/* R's precious list-like*/
//static SEXP RPY_R_Precious = NULL;
static PyObject *Rpy_R_Precious;

static inline void embeddedR_setlock(void) {
  embeddedR_status = embeddedR_status | RPY_R_BUSY;
}
static inline void embeddedR_freelock(void) {
  embeddedR_status = embeddedR_status ^ RPY_R_BUSY;
}
static inline unsigned int rpy_has_status(unsigned int status) {
  return (embeddedR_status & status) == status;
}

/* Keep track of R objects preserved by rpy2 
   The int returned is from the call to PyDict_SetItem 
   (0 on success, -1 on failure).
 */
static int _Rpy_PreserveObject(SEXP object) {
  /* PyDict can be confused if an error has been raised.
     We put aside the exception if the case, to restore it at the end.
     FIXME: this situation can occur because of presumed shortcomings
     in the overall design of rpy2.
   */
  int reset_error_state = 0; 
  PyObject *ptype, *pvalue, *ptraceback;

  if (PyErr_Occurred()) {
    reset_error_state = 1;
    PyErr_Fetch(&ptype, &pvalue, &ptraceback);
  }

  PyObject *key = PyLong_FromVoidPtr((void *)object);
  PyObject *val = PyDict_GetItem(Rpy_R_Precious, key);
  /* val is a borrowed reference */
  long val_count;
  if (val == NULL) {
    val_count = 1;
  } else {
    val_count = PyLong_AsLong(val);
    val_count++;
  }
  PyObject *newval = PyLong_FromLong(val_count);
  int res = PyDict_SetItem(Rpy_R_Precious, key, newval);
  Py_DECREF(newval);
  Py_DECREF(key);

  if (reset_error_state) {
    if (PyErr_Occurred()) {
      PyErr_Print();
      PyErr_Clear();
    }
    PyErr_Restore(ptype, pvalue, ptraceback);
  }

  return res;
} 

static int Rpy_PreserveObject(SEXP object) {
  int res = _Rpy_PreserveObject(object);
  if (res == -1) {
    printf("Error while logging preserved object\n");
  }
  R_PreserveObject(object);
  return res;
}
/* static int Rpy_PreserveObject(SEXP object) { */
/* R_ReleaseObject(RPY_R_Precious); */
/* PROTECT(RPY_R_Precious); */
/* RPY_R_Precious = CONS(object, RPY_R_Precious); */
/* UNPROTECT(1); */
/* R_PreserveObject(RPY_R_Precious); */
/* } */

static int Rpy_ReleaseObject(SEXP object) {
  /* PyDict can be confused if an error has been raised.
     We put aside the exception if the case, to restore it at the end.
     FIXME: this situation can occur because of presumed shortcomings
     in the overall design of rpy2.
   */
  int reset_error_state = 0; 
  PyObject *ptype, *pvalue, *ptraceback; 
  if (PyErr_Occurred()) {
    reset_error_state = 1;
    PyErr_Fetch(&ptype, &pvalue, &ptraceback);
  }

  PyObject *key = PyLong_FromVoidPtr((void *)object);
  PyObject *val = PyDict_GetItem(Rpy_R_Precious, key);

  if (val == NULL) {
    if (reset_error_state) {
      PyErr_Restore(ptype, pvalue, ptraceback);
      printf("Error:Trying to release object ID %ld while not preserved\n",
	     PyLong_AsLong(key));
    } else {
      PyErr_Format(PyExc_KeyError, 
		   "Trying to release object ID %ld while not preserved\n",
		   PyLong_AsLong(key));
    }
    return -1;
  } 

  long val_count = PyLong_AsLong(val);
  PyObject *newval;
  int res = 0;

  switch (val_count) {
  case 0:
    res = -1;
    PyErr_Format(PyExc_ValueError,
		 "Preserved object ID %ld with a count of zero\n", 
		 PyLong_AsLong(key));
    break;
  case 1:
    res = PyDict_DelItem(Rpy_R_Precious, key);
    if (res == -1)
    PyErr_Format(PyExc_ValueError,
		 "Occured while deleting preserved object ID %ld\n",  
		 PyLong_AsLong(key));
    break;
  default:
    val_count--;
    newval = PyLong_FromLong(val_count);
    res = PyDict_SetItem(Rpy_R_Precious, key, newval);
    Py_DECREF(newval);
    if (res == -1) {
      PyErr_Format(PyExc_ValueError,
		   "Decrementing count for reserved object ID %ld to %ld\n",  
		   PyLong_AsLong(key), val_count);
    }
    break;
  }
  R_ReleaseObject(object);
  /* SEXP parentnode, node; */
  /* Py_ssize_t res = -1; */
  /* if (isNull(RPY_R_Precious)) { */
  /*   return res; */
  /* } */
  /* res++; */
  /* if (object == CAR(RPY_R_Precious)) { */
  /*   RPY_R_Precious = CDR(RPY_R_Precious); */
  /*   return res; */
  /* } */
  /* parentnode = RPY_R_Precious; */
  /* node = CDR(RPY_R_Precious); */
  /* while (!isNull(node)) { */
  /*   res++; */
  /*   if (object == CAR(node)) { */
  /*     SETCDR(parentnode, CDR(node)); */
  /*     return res; */
  /*   } */
  /*   parentnode = node; */
  /*   node = CDR(node); */
  /* } */
  Py_DECREF(key);
  if (reset_error_state) {
    if (PyErr_Occurred()) {
      PyErr_Print();
    }
    PyErr_Restore(ptype, pvalue, ptraceback);
  }
  return res;
}


PyDoc_STRVAR(Rpy_ProtectedIDs_doc,
             "Return a tuple with the R IDs for the objects protected\
 from R's garbage collection by rpy2.\n");
/* Return a tuple with IDs of R objects protected by rpy2 */
static PyObject* Rpy_ProtectedIDs(PyObject *self) {
  PyObject *key, *value;
  Py_ssize_t pos = 0;

  Py_ssize_t len_ids = 0;
  while (PyDict_Next(Rpy_R_Precious, &pos, &key, &value)) {
    long val_count = PyLong_AsLong(value);
    len_ids += val_count;
  }

  pos = 0;
  PyObject *ids = PyTuple_New(len_ids);
  Py_ssize_t pos_ids = 0;

  while (PyDict_Next(Rpy_R_Precious, &pos, &key, &value)) {
    long val_count = PyLong_AsLong(value);
    Py_ssize_t i;
    for (i=0; i < val_count; i++) { 
      Py_INCREF(key);
      PyTuple_SET_ITEM(ids, pos_ids, key);
      pos_ids++;
    }
  }
  return ids;
  
  /* Py_ssize_t pos = 0; */
  /* SEXP node = RPY_R_Precious; */
  /* while (!isNull(node)) { */
  /*   pos++; */
  /*   node = CDR(node); */
  /* } */
  /* PyObject *ids = PyTuple_New(pos); */
  /* pos = 0; */
  /* node = RPY_R_Precious; */
  /* while (!isNull(node)) { */
  /*   PyTuple_SET_ITEM(ids, pos, PyLong_FromVoidPtr((void *)(CAR(node)))); */
  /*   pos++; */
  /*   node = CDR(node); */
  /* } */
  /* return ids; */
}
