#ifndef RPY_RU_H
#define RPY_RU_H

#include <Rdefines.h>
#include <Rversion.h>


SEXP rpy_serialize(SEXP object, SEXP rho);
SEXP rpy_unserialize(SEXP connection, SEXP rho);

SEXP rpy_list_attr(SEXP sexp);

const char *RPY_R_VERSION_LIST[5] = {R_MAJOR, R_MINOR, R_STATUS, 
				     R_SVN_REVISION, NULL};
#endif
