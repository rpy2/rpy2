import cffi
import os

ffibuilder = cffi.FFI()
ffibuilder.set_source('_rinterface_cffi', None)


ffibuilder.cdef(
    """
typedef unsigned int SEXPTYPE;

const unsigned int NILSXP     =  0;
const unsigned int SYMSXP     =  1;
const unsigned int LISTSXP    =  2;
const unsigned int CLOSXP     =  3;
const unsigned int ENVSXP     =  4;
const unsigned int PROMSXP    =  5;
const unsigned int LANGSXP    =  6;
const unsigned int SPECIALSXP =  7;
const unsigned int BUILTINSXP =  8;
const unsigned int CHARSXP    =  9;
const unsigned int LGLSXP     = 10;
const unsigned int INTSXP     = 13;
const unsigned int REALSXP    = 14;
const unsigned int CPLXSXP    = 15;
const unsigned int STRSXP     = 16;
const unsigned int DOTSXP     = 17;
const unsigned int ANYSXP     = 18;
const unsigned int VECSXP     = 19;
const unsigned int EXPRSXP    = 20;
const unsigned int BCODESXP   = 21;
const unsigned int EXTPTRSXP  = 22;
const unsigned int WEAKREFSXP = 23;
const unsigned int RAWSXP     = 24;
const unsigned int S4SXP      = 25;

const unsigned int NEWSXP     = 30;
const unsigned int FREESXP    = 31;

const unsigned int FUNSXP     = 99;
    """)

# include/R_exts/Complex.h
ffibuilder.cdef("""
typedef struct {
    double r;
    double i;
} Rcomplex;
""")

# include/Rinternals.h
ffibuilder.cdef("""
typedef int R_len_t;
""")

if ffibuilder.sizeof('size_t') > 4:
    LONG_VECTOR_SUPPORT = True
    R_XLEN_T_MAX = 4503599627370496
    R_SHORT_LEN_MAX = 2147483647
    ffibuilder.cdef("""
typedef ptrdiff_t R_xlen_t;
    """)
else:
    ffibuilder.cdef("""
typedef int R_xlen_t;
    """)

ffibuilder.cdef("""
double R_NaN;		/* IEEE NaN */
double R_NaReal;	/* NA_REAL: IEEE */
int    R_NaInt;
""")

ffibuilder.cdef("""
typedef unsigned char Rbyte;
""")

ffibuilder.cdef(
    """
struct symsxp_struct {
    struct SEXPREC *pname;
    struct SEXPREC *value;
    struct SEXPREC *internal;
};

struct listsxp_struct {
    struct SEXPREC *carval;
    struct SEXPREC *cdrval;
    struct SEXPREC *tagval;
};

struct envsxp_struct {
    struct SEXPREC *frame;
    struct SEXPREC *enclos;
    struct SEXPREC *hashtab;
};

struct closxp_struct {
    struct SEXPREC *formals;
    struct SEXPREC *body;
    struct SEXPREC *env;
};

struct promsxp_struct {
    struct SEXPREC *value;
    struct SEXPREC *expr;
    struct SEXPREC *env;
};

typedef struct SEXPREC *SEXP;

struct sxpinfo_struct {
    SEXPTYPE type      : 5;
    unsigned int scalar: 1;
    unsigned int alt   : 1;
    unsigned int obj   : 1;
    unsigned int gp    : 16;
    unsigned int mark  : 1;
    unsigned int debug : 1;
    unsigned int trace : 1;
    unsigned int spare : 1;
    unsigned int gcgen : 1;
    unsigned int gccls : 3;
    unsigned int named : 16;
    unsigned int extra : 32;
};

struct primsxp_struct {
int offset;
};
    """)

ffibuilder.cdef(
    """
struct vecsxp_struct {
    R_xlen_t length;
    R_xlen_t truelength;
};
    """)

SEXPREC_HEADER = """
    struct sxpinfo_struct sxpinfo;
    struct SEXPREC *attrib;
    struct SEXPREC *gengc_next_node, *gengc_prev_node;
"""

ffibuilder.cdef("""
typedef struct SEXPREC {
%(SEXPREC_HEADER)s
    union {
        struct primsxp_struct primsxp;
        struct symsxp_struct symsxp;
        struct listsxp_struct listsxp;
        struct envsxp_struct envsxp;
        struct closxp_struct closxp;
        struct promsxp_struct promsxp;
    } u;
} SEXPREC;
""" % {'SEXPREC_HEADER': SEXPREC_HEADER}
)

ffibuilder.cdef("""
typedef struct {
%(SEXPREC_HEADER)s
    struct vecsxp_struct vecsxp;
} VECTOR_SEXPREC, *VECSEXP;
""" % {'SEXPREC_HEADER': SEXPREC_HEADER}
)

ffibuilder.cdef("""
typedef union {
    VECTOR_SEXPREC s;
    double align;
} SEXPREC_ALIGN;
""")

ffibuilder.cdef("""
const char *(R_CHAR)(SEXP x);
""")

# include/R_ext/Boolean.h
ffibuilder.cdef("""
typedef enum { FALSE = 0, TRUE } Rboolean;
""")

# include/Rembedded.h
ffibuilder.cdef("""
int Rf_initialize_R(int ac, char **av);
void R_RunExitFinalizers(void);
void Rf_KillAllDevices(void);
void R_CleanTempDir(void);

void Rf_endEmbeddedR(int fatal);
""")

# include/R_ext/Memory.h
ffibuilder.cdef("""
void	R_gc(void);
""")

# include/Rinternals.h
ffibuilder.cdef("""
void R_ClearExternalPtr(SEXP s);
void R_dot_Last(void);
""")

# src/include/Rinlinedfunc.h
ffibuilder.cdef("""
void* DATAPTR(SEXP x);
""")

# include/Rinternals.h
ffibuilder.cdef("""
SEXP (TAG)(SEXP e);
SEXP SET_TAG(SEXP x, SEXP y);
""")

ffibuilder.cdef("""
SEXP (CDR)(SEXP e);
SEXP SETCDR(SEXP x, SEXP y);
SEXP Rf_nthcdr(SEXP, int);
""")

ffibuilder.cdef("""
SEXP (CAR)(SEXP e);
SEXP SETCAR(SEXP x, SEXP y);
""")

ffibuilder.cdef("""
SEXP Rf_getAttrib(SEXP sexp, SEXP what);
SEXP Rf_setAttrib(SEXP x, SEXP what, SEXP n);
""")

ffibuilder.cdef("""
SEXP Rf_namesgets(SEXP, SEXP);
""")

ffibuilder.cdef("""
int R_has_slot(SEXP sexp, SEXP name);
SEXP R_do_slot(SEXP sexp, SEXP name);
SEXP R_do_slot_assign(SEXP sexp, SEXP name, SEXP value);
""")

ffibuilder.cdef("""
SEXP (ATTRIB)(SEXP x);
""")

ffibuilder.cdef("""
SEXP Rf_asChar(SEXP sexp);
""")

ffibuilder.cdef("""
SEXP Rf_allocList(int n);
SEXP Rf_allocVector(SEXPTYPE sexp_t, R_xlen_t n);
SEXP Rf_elt(SEXP, int);
""")

ffibuilder.cdef("""
typedef void (*R_CFinalizer_t)(SEXP);
void R_RegisterCFinalizer(SEXP s, R_CFinalizer_t fun);
""")

ffibuilder.cdef("""
typedef void* (*DL_FUNC)();
SEXP R_MakeExternalPtr(DL_FUNC p, SEXP tag, SEXP prot);
""")

ffibuilder.cdef("""
SEXP Rf_lang1(SEXP);
SEXP Rf_lang2(SEXP, SEXP);
SEXP Rf_lang3(SEXP, SEXP, SEXP);
SEXP Rf_lang4(SEXP, SEXP, SEXP, SEXP);
SEXP Rf_lang5(SEXP, SEXP, SEXP, SEXP, SEXP);
SEXP Rf_lang6(SEXP, SEXP, SEXP, SEXP, SEXP, SEXP);
R_len_t Rf_length(SEXP x);
""")

ffibuilder.cdef("""
SEXP Rf_ScalarComplex(Rcomplex c);
SEXP Rf_ScalarInteger(int n);
SEXP Rf_ScalarLogical(int n);
SEXP Rf_ScalarRaw(Rbyte b);
SEXP Rf_ScalarReal(double f);
SEXP Rf_ScalarString(SEXP s);
""")

ffibuilder.cdef("""
void *(STDVEC_DATAPTR)(SEXP x);

/* Integer.*/
int (INTEGER_ELT)(SEXP x, R_xlen_t i);
void SET_INTEGER_ELT(SEXP x, R_xlen_t i, int v);
int *(INTEGER)(SEXP x);

/* Double / real. */
double (REAL_ELT)(SEXP x, R_xlen_t i);
void SET_REAL_ELT(SEXP x, R_xlen_t i, double v);
double *(REAL)(SEXP x);

/* Boolean / logical. */
int (LOGICAL_ELT)(SEXP x, R_xlen_t i);
void SET_LOGICAL_ELT(SEXP x, R_xlen_t i, int v);
int *(LOGICAL)(SEXP x);

/* Complex. */
Rcomplex (COMPLEX_ELT)(SEXP x, R_xlen_t i);
Rcomplex *(COMPLEX)(SEXP x);

/* Bytes / raw. */
Rbyte *(RAW)(SEXP x);
Rbyte (RAW_ELT)(SEXP x, R_xlen_t i);

SEXP (STRING_ELT)(SEXP x, R_xlen_t i);
void SET_STRING_ELT(SEXP x, R_xlen_t i, SEXP v);

SEXP (VECTOR_ELT)(SEXP x, R_xlen_t i);
SEXP SET_VECTOR_ELT(SEXP x, R_xlen_t i, SEXP v);
""")

ffibuilder.cdef("""
SEXP (CLOENV)(SEXP x);
""")

ffibuilder.cdef("""
SEXP Rf_eval(SEXP, SEXP);
SEXP R_tryEval(SEXP, SEXP, int*);
""")

ffibuilder.cdef("""
SEXP Rf_findFun(SEXP sym, SEXP env);
SEXP Rf_findFun3(SEXP, SEXP, SEXP);
""")

ffibuilder.cdef("""
SEXP Rf_findVar(SEXP sym, SEXP env);
SEXP Rf_findVarInFrame(SEXP env, SEXP sym);
SEXP Rf_findVarInFrame3(SEXP, SEXP, Rboolean);
""")

ffibuilder.cdef("""
R_xlen_t Rf_xlength(SEXP);
""")

ffibuilder.cdef("""
SEXP R_lsInternal(SEXP, Rboolean);
""")

ffibuilder.cdef("""
SEXP Rf_duplicate(SEXP s);
""")

ffibuilder.cdef("""
SEXP Rf_defineVar(SEXP sym, SEXP s, SEXP env);
""")

ffibuilder.cdef("""
SEXP Rf_protect(SEXP s);
void Rf_unprotect(int n);
""")

ffibuilder.cdef("""
void R_PreserveObject(SEXP s);
void R_ReleaseObject(SEXP s);
""")

ffibuilder.cdef("""
SEXP R_NaString; /* a CHARSXP */
SEXP R_BlankString;
SEXP R_BlankScalarString;
""")

ffibuilder.cdef("""
SEXP R_GlobalEnv;
""")

ffibuilder.cdef("""
SEXP R_EmptyEnv;
""")

ffibuilder.cdef("""
Rboolean R_EnvironmentIsLocked(SEXP env);
""")

ffibuilder.cdef("""
SEXP R_BaseEnv;
SEXP R_BaseNamespace;
SEXP R_BaseNamespaceRegistry;
""")

ffibuilder.cdef("""
SEXP R_BaseEnv;
SEXP R_BaseNamespace;
SEXP R_BaseNamespaceRegistry;
""")

ffibuilder.cdef("""
SEXP R_NilValue;
SEXP R_UnboundValue;
SEXP R_MissingArg;

Rboolean (Rf_isNull)(SEXP s);
Rboolean (Rf_isList)(SEXP s);
""")

ffibuilder.cdef("""
SEXP Rf_install(const char *);
SEXP Rf_installChar(SEXP x);
SEXP Rf_mkChar(const char *);
SEXP Rf_mkString(const char *);

typedef enum {
  CE_NATIVE = 0,
  CE_UTF8   = 1,
  CE_LATIN1 = 2,
  CE_BYTES  = 3,
  CE_SYMBOL = 5,
  CE_ANY    = 99
} cetype_t;

cetype_t Rf_getCharCE(SEXP);
SEXP Rf_mkCharCE(const char *, cetype_t);
SEXP Rf_mkCharLenCE(const char *, int n, cetype_t encoding);
""")

ffibuilder.cdef("""
typedef enum {
  Bytes = 0,
  Chars = 1,
  Width = 2
} nchar_type;

int R_nchar(SEXP string, nchar_type type_,
            Rboolean allowNA, Rboolean keepNA,
            const char* msg_name);
""")

ffibuilder.cdef("""
SEXP (PRINTNAME)(SEXP x);
""")

ffibuilder.cdef("""
SEXP (FRAME)(SEXP x);
SEXP (ENCLOS)(SEXP x);
SEXP (HASHTAB)(SEXP x);
int (ENVFLAGS)(SEXP x);
void (SET_ENVFLAGS)(SEXP x, int v);
""")

# TODO: Why isn't this working ?
# ffibuilder.cdef("""
# void SET_FRAME(SEXP x, SEXP, v);
# void SET_ENCLOS(SEXP x, SEXP, v);
# void SET_HASHTAB(SEXP x, SEXP, v);
# """)

# include/Rdefines.h

ffibuilder.cdef("""
SEXP R_ClassSymbol;
SEXP R_NameSymbol;
SEXP R_DimSymbol;
""")

# include/R_ext/Parse.h
ffibuilder.cdef("""
typedef enum {
    PARSE_NULL,
    PARSE_OK,
    PARSE_INCOMPLETE,
    PARSE_ERROR,
    PARSE_EOF
} ParseStatus;

SEXP R_ParseVector(SEXP text, int num, ParseStatus *status, SEXP srcfile);
""")

# include/Rinterface.h

ffibuilder.cdef("""
extern Rboolean R_Interactive ;
extern int R_SignalHandlers;
extern uintptr_t R_CStackLimit;
""")


ffibuilder.cdef("""
typedef enum {
    SA_NORESTORE,/* = 0 */
    SA_RESTORE,
    SA_DEFAULT,/* was === SA_RESTORE */
    SA_NOSAVE,
    SA_SAVE,
    SA_SAVEASK,
    SA_SUICIDE
} SA_TYPE;
""")

ffibuilder.cdef("""
typedef struct
{
    Rboolean R_Quiet;
    Rboolean R_Slave;
    Rboolean R_Interactive;
    Rboolean R_Verbose;
    Rboolean LoadSiteFile;
    Rboolean LoadInitFile;
    Rboolean DebugInitFile;
    SA_TYPE RestoreAction;
    SA_TYPE SaveAction;
    %(R_SIZE_T)s vsize;
    %(R_SIZE_T)s nsize;
    %(R_SIZE_T)s max_vsize;
    %(R_SIZE_T)s max_nsize;
    %(R_SIZE_T)s ppsize;
    int NoRenviron;

%(win32)s

} structRstart;

typedef structRstart *Rstart;

void R_DefParams(Rstart);
void R_SetParams(Rstart);
void R_SetWin32(Rstart);
void R_SizeFromEnv(Rstart);
void R_common_command_line(int *, char **, Rstart);

void R_set_command_line_arguments(int argc, char **argv);

void setup_Rmainloop(void);

""" % {
    'R_SIZE_T': 'size_t',
    'win32': """
    char *rhome;               /* R_HOME */
    char *home;                /* HOME  */
    blah1 ReadConsole;
    blah2 WriteConsole;
    blah3 CallBack;
    blah4 ShowMessage;
    blah5 YesNoCancel;
    blah6 Busy;
    UImode CharacterMode;
    blah7 WriteConsoleEx; /* used only if WriteConsole is NULL */
    """ if os.name == 'nt' else ''
})

ffibuilder.cdef("""
extern FILE *R_Consolefile;
extern FILE *R_Outputfile;

extern void (*ptr_R_Suicide)(const char *);
extern void (*ptr_R_ShowMessage)(const char *);
extern int  (*ptr_R_ReadConsole)(const char *, unsigned char *, int, int);
extern void (*ptr_R_WriteConsole)(const char *, int);
extern void (*ptr_R_WriteConsoleEx)(const char *, int, int);
extern void (*ptr_R_ResetConsole)(void);
extern void (*ptr_R_FlushConsole)(void);
extern void (*ptr_R_ClearerrConsole)(void);
extern void (*ptr_R_Busy)(int);
extern void (*ptr_R_CleanUp)(SA_TYPE, int, int);
extern int  (*ptr_R_ShowFiles)(int, const char **, const char **,
                               const char *, Rboolean, const char *);
extern int  (*ptr_R_ChooseFile)(int, char *, int);
extern int  (*ptr_R_EditFile)(const char *);
extern void (*ptr_R_loadhistory)(SEXP, SEXP, SEXP, SEXP);
extern void (*ptr_R_savehistory)(SEXP, SEXP, SEXP, SEXP);
extern void (*ptr_R_addhistory)(SEXP, SEXP, SEXP, SEXP);

// added in 3.0.0
extern int  (*ptr_R_EditFiles)(int, const char **,
                               const char **, const char *);
// naming follows earlier versions in R.app
extern SEXP (*ptr_do_selectlist)(SEXP, SEXP, SEXP, SEXP);
extern SEXP (*ptr_do_dataentry)(SEXP, SEXP, SEXP, SEXP);
extern SEXP (*ptr_do_dataviewer)(SEXP, SEXP, SEXP, SEXP);
extern void (*ptr_R_ProcessEvents)();
""")


ffibuilder.cdef("""
typedef unsigned int R_NativePrimitiveArgType;

typedef struct {
    const char *name;
    DL_FUNC     fun;
    int         numArgs;
    R_NativePrimitiveArgType *types;
} R_CMethodDef;

typedef R_CMethodDef R_FortranMethodDef;


typedef struct {
    const char *name;
    DL_FUNC     fun;
    int         numArgs;
} R_CallMethodDef;

typedef R_CallMethodDef R_ExternalMethodDef;

typedef struct _DllInfo DllInfo;

int R_registerRoutines(DllInfo *info,
                       const R_CMethodDef * const croutines,
                       const R_CallMethodDef * const callRoutines,
                       const R_FortranMethodDef * const fortranRoutines,
                       const R_ExternalMethodDef * const externalRoutines);

DllInfo *R_getEmbeddingDllInfo(void);

void *R_ExternalPtrAddr(SEXP s);
""")


if __name__ == '__main__':
    ffibuilder.compile(verbose=True)
