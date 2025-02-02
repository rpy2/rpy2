# ifdef R_LEGACY_RCOMPLEX
  # include "Rcomplex_legacy.h"
# else
  # include "Rcomplex.h"
# endif

# include "R_API.h"
# include "R_API_eventloop.h"

void rpy2_runHandlers(InputHandler *handlers) {{
    R_runHandlers(handlers, R_checkActivity(0, 1));
  }};
