#ifndef RPY_RU_H
#define RPY_RU_H

#include <Rdefines.h>

SEXP rpy_findFun(SEXP symbol, SEXP rho);

SEXP rpy_serialize(SEXP object, SEXP rho);

#endif
