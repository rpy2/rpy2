#include <Rdefines.h>


SEXP rpy_findFun(SEXP symbol, SEXP rho)
{
    SEXP vl;
    while (rho != R_EmptyEnv) {
        /* This is not really right.  Any variable can mask a function */
        vl = findVarInFrame3(rho, symbol, TRUE);

        if (vl != R_UnboundValue) {
            if (TYPEOF(vl) == PROMSXP) {
                PROTECT(vl);
                vl = eval(vl, rho);
                UNPROTECT(1);
            }
            if (TYPEOF(vl) == CLOSXP || TYPEOF(vl) == BUILTINSXP ||
                TYPEOF(vl) == SPECIALSXP)
               return (vl);

            if (vl == R_MissingArg) {
              printf("R_MissingArg in rpy_FindFun.\n");
              return R_UnboundValue;
            }
        }
        rho = ENCLOS(rho);
    }
    return R_UnboundValue;
}

