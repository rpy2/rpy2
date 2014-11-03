#ifndef RPY_RU_H
#define RPY_RU_H

#include <Rdefines.h>
#include <Rversion.h>


SEXP rpy_serialize(SEXP object, SEXP rho);
SEXP rpy_unserialize(SEXP connection, SEXP rho);
SEXP rpy_remove(SEXP symbol, SEXP environment, SEXP rho);

SEXP rpy_list_attr(SEXP sexp);

SEXP rpy_lang2str(SEXP sexp, SEXPTYPE t);

SEXP externallymanaged_vector(SEXPTYPE rtype, void *array, int length);

typedef struct {
  int rfree;
  void *array;
} ExternallyManagedVector;

#define __RPY_RSVN_SWITCH_VERSION__ 134914

#endif
