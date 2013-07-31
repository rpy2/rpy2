#ifndef RPY_RU_H
#define RPY_RU_H

#include <Rdefines.h>
#include <Rversion.h>


SEXP rpy_serialize(SEXP object, SEXP rho);
SEXP rpy_unserialize(SEXP connection, SEXP rho);

SEXP rpy_list_attr(SEXP sexp);

#define __RPY_RSVN_SWITCH_VERSION__ 134914

#endif
