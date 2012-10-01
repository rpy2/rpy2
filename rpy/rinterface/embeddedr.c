

/* Helper variable to store R's status
 */
const unsigned int const RPY_R_INITIALIZED = 0x01;
const unsigned int const RPY_R_BUSY = 0x02;
/* Initial status is 0 */
static unsigned int embeddedR_status = 0;

/* R's precious list-like*/
//static SEXP RPY_R_Precious = NULL;
static PyObject *RPY_R_Precious;

static inline void embeddedR_setlock(void) {
  embeddedR_status = embeddedR_status | RPY_R_BUSY;
}
static inline void embeddedR_freelock(void) {
  embeddedR_status = embeddedR_status ^ RPY_R_BUSY;
}
static inline unsigned int rpy_has_status(unsigned int status) {
  return (embeddedR_status & status) == status;
}

static inline void Rpy_PreserveObject(SEXP object) {
  /* R_ReleaseObject(RPY_R_Precious); */
  /* PROTECT(RPY_R_Precious); */
  /* RPY_R_Precious = CONS(object, RPY_R_Precious); */
  /* UNPROTECT(1); */
  /* R_PreserveObject(RPY_R_Precious); */
  PyObject *key = PyLong_FromVoidPtr((void *)object);
  PyObject *val = PyDict_GetItem(RPY_R_Precious, key);
  /* val is a borrowed reference */
  long val_count;
  if (val == NULL) {
    val_count = 1;
  } else {
    val_count = PyLong_AsLong(val);
    val_count++;
  }
  PyObject *newval = PyLong_FromLong(val_count);
  int res = PyDict_SetItem(RPY_R_Precious, key, newval);
  Py_DECREF(newval);
  if (res == -1) {
    printf("Error while logging preserved object\n");
  }
  R_PreserveObject(object);
}

static Py_ssize_t Rpy_ReleaseObject(SEXP object) {
  PyObject *ikey, *ivalue;
  Py_ssize_t ipos = 0;

  PyObject *key = PyLong_FromVoidPtr((void *)object);
  PyObject *val = PyDict_GetItem(RPY_R_Precious, key);
  PyObject *newval;
  if (val == NULL) {
    printf("Releasing a non-preserved object (!?)\n");
    return -1;
  } 
  long val_count = PyLong_AsLong(val);
  int res;

  switch (val_count) {
  case 0:
    printf("Preserved object with a count of zero (!?)\n");
    break;
  case 1:
    res = PyDict_DelItem(RPY_R_Precious, key);
    if (res == -1)
      printf("Error while deleting preserved object\n");    
    break;
  default:
    val_count--;
    newval = PyLong_FromLong(val_count);
    res = PyDict_SetItem(RPY_R_Precious, key, newval);
    Py_DECREF(newval);
    if (res == -1)
      printf("Error while logging preserved object\n");    
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
  return -1;
}


PyDoc_STRVAR(Rpy_ProtectedIDs_doc,
             "Return a tuple with the R IDs for the objects protected\
 from R's garbage collection by rpy2.\n");
/* Return a tuple with IDs of R objects protected by rpy2 */
static PyObject* Rpy_ProtectedIDs(PyObject *self) {
  PyObject *ids = PyTuple_New(PyDict_Size(RPY_R_Precious));
  Py_ssize_t pos_ids = 0;
  PyObject *key, *value;
  Py_ssize_t pos = 0;
  
  while (PyDict_Next(RPY_R_Precious, &pos, &key, &value)) {
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
