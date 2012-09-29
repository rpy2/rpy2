

/* Helper variable to store R's status
 */
const unsigned int const RPY_R_INITIALIZED = 0x01;
const unsigned int const RPY_R_BUSY = 0x02;
/* Initial status is 0 */
static unsigned int embeddedR_status = 0;

/* R's precious list-like*/
static SEXP RPY_R_Precious = NULL;

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
  R_ReleaseObject(RPY_R_Precious);
  PROTECT(RPY_R_Precious);
  RPY_R_Precious = CONS(object, RPY_R_Precious);
  UNPROTECT(1);
  R_PreserveObject(RPY_R_Precious);
}

static Py_ssize_t Rpy_ReleaseObject(SEXP object) {
  SEXP parentnode, node;
  Py_ssize_t res = -1;
  if (isNull(RPY_R_Precious)) {
    return res;
  }
  res++;
  if (object == CAR(RPY_R_Precious)) {
    RPY_R_Precious = CDR(RPY_R_Precious);
    return res;
  }
  parentnode = RPY_R_Precious;
  node = CDR(RPY_R_Precious);
  while (!isNull(node)) {
    res++;
    if (object == CAR(node)) {
      SETCDR(parentnode, CDR(node));
      return res;
    }
    parentnode = node;
    node = CDR(node);
  }
  return -1;
}


PyDoc_STRVAR(Rpy_ProtectedIDs_doc,
             "Return a tuple with the R IDs for the objects protected\
 from R's garbage collection by rpy2.\n");
/* Return a tuple with IDs of R objects protected by rpy2 */
static PyObject* Rpy_ProtectedIDs(PyObject *self) {
  Py_ssize_t pos = 0;
  SEXP node = RPY_R_Precious;
  while (!isNull(node)) {
    pos++;
    node = CDR(node);
  }
  PyObject *ids = PyTuple_New(pos);
  pos = 0;
  node = RPY_R_Precious;
  while (!isNull(node)) {
    PyTuple_SET_ITEM(ids, pos, PyLong_FromVoidPtr((void *)(CAR(node))));
    pos++;
    node = CDR(node);
  }
  return ids;
}
