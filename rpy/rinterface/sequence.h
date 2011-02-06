#ifndef _RPY_PRIVATE_SEQUENCE_H_
#define _RPY_PRIVATE_SEQUENCE_H_

#ifndef _RPY_RINTERFACE_MODULE_
#error sequence.h should not be included directly
#endif

static PySequenceMethods VectorSexp_sequenceMethods;


typedef int (* RPy_seqobjtosexpproc)(PyObject *, SEXP *);

#endif 
