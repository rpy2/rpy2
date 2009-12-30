/* A python-R interface*/

/* 
 * The authors for the original RPy code, as well as
 * belopolsky for his contributed code, are listed here as authors;
 * although the design is largely new, parts of this code is
 * derived from their contributions. 
 * 
 * Laurent Gautier - 2008
 */

/*
 ***** BEGIN LICENSE BLOCK *****
 * Version: MPL 1.1/GPL 2.0/LGPL 2.1
 *
 * The contents of this file are subject to the Mozilla Public License Version
 * 1.1 (the "License"); you may not use this file except in compliance with
 * the License. You may obtain a copy of the License at
 * http://www.mozilla.org/MPL/
 *
 * Software distributed under the License is distributed on an "AS IS" basis,
 * WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
 * for the specific language governing rights and limitations under the
 * License.
 * 
 * Copyright (C) 2008-2009 Laurent Gautier
 *
 * Portions created by Alexander Belopolsky are 
 * Copyright (C) 2006 Alexander Belopolsky.
 *
 * Portions created by Gregory R. Warnes are
 * Copyright (C) 2003-2008 Gregory Warnes.
 *
 * Portions created by Walter Moreira are 
 * Copyright (C) 2002-2003 Walter Moreira
 *
 * Alternatively, the contents of this file may be used under the terms of
 * either the GNU General Public License Version 2 or later (the "GPL"), or
 * the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
 * in which case the provisions of the GPL or the LGPL are applicable instead
 * of those above. If you wish to allow use of your version of this file only
 * under the terms of either the GPL or the LGPL, and not to allow others to
 * use your version of this file under the terms of the MPL, indicate your
 * decision by deleting the provisions above and replace them with the notice
 * and other provisions required by the GPL or the LGPL. If you do not delete
 * the provisions above, a recipient may use your version of this file under
 * the terms of any one of the MPL, the GPL or the LGPL.
 *
 * ***** END LICENSE BLOCK ***** */

#include <signal.h>
#include <setjmp.h>

#include "Python.h"

#if Win32
#include <winsock2.h>
#endif

#include <R.h>
#include <Rinternals.h>
#include <Rdefines.h>

#include <Rinterface.h>
#include <R_ext/Complex.h>
#include <Rembedded.h>


#include <R_ext/eventloop.h>

/* FIXME: consider the use of parsing */
/* #include <R_ext/Parse.h> */
#include <R_ext/Rdynload.h>
#include <R_ext/RStartup.h>

/* From Defn.h */
#ifdef HAVE_POSIX_SETJMP
#define SIGJMP_BUF sigjmp_buf
#else
#define SIGJMP_BUF jmp_buf
#endif

#include "rpy_rinterface.h"
#include "array.h"
#include "r_utils.h"

/* Helper variables to quickly resolve SEXP types.
 * The first variable gives the highest possible
 * SEXP type.
 * The second in an array of strings giving either
 * the SEXP name (INTSXP, REALSXP, etc...), or a NULL
 * if there is no such valid SEXP.
 */
#define RPY_MAX_VALIDSEXTYPE 99
static char **validSexpType;

/* A tuple that holds options to initialize R */
static PyObject *initOptions;

static SEXP errMessage_SEXP;
static PyObject *RPyExc_RuntimeError = NULL;

#ifdef Win32
/* R instance as a global */
Rstart Rp;
#endif

/* FIXME: see the details of interruption */
/* Indicates whether the R interpreter was interrupted by a SIGINT */
int interrupted = 0;
/* Abort the current R computation due to a SIGINT */
static void
interrupt_R(int signum)
{
  /* printf('interrupted.\n'); */
  interrupted = 1;
  error("Interrupted");
}

/* Helper variable to store R's status
 */
const unsigned int const RPY_R_INITIALIZED = 0x01;
const unsigned int const RPY_R_BUSY = 0x02;

static unsigned int embeddedR_status = 0;
static PyObject *embeddedR_isInitialized;

inline void embeddedR_setlock(void) {
  embeddedR_status = embeddedR_status | RPY_R_BUSY;
}
inline void embeddedR_freelock(void) {
  embeddedR_status = embeddedR_status ^ RPY_R_BUSY;
}

SIGJMP_BUF env_sigjmp;
/* Python's signal handler */
static PyOS_sighandler_t python_sighandler, last_sighandler;

/* In SAGE, explicit defintions */
/* /\* Python handler (definition varies across platforms) *\/ */
/* #if defined(__CYGWIN32__) /\* Windows XP *\/ */
/*   _sig_func_ptr python_sighandler; */
/* #elif defined(__FreeBSD__) /\* FreeBSD *\/ */
/*   sig_t python_sighandler; */
/* #elif defined(__APPLE__) /\* OSX *\/ */
/*   sig_t python_sighandler; */
/* #elif defined (__sun__) || defined (__sun) /\* Solaris *\/ */
/*   __sighandler_t python_sighandler; */
/* #else /\* Other, e.g., Linux *\/ */
/*   __sighandler_t python_sighandler; */
/* #endif   */


PyDoc_STRVAR(module_doc,
             "Low-level functions to interface with R.\n\
 One should mostly consider calling the functions defined here when\
 writing a higher level interface between python and R.\
 Check the documentation for the module this is bundled into if\
 you only wish to have an off-the-shelf interface with R.\
\n\
");


static PySexpObject *globalEnv;
static PySexpObject *baseNameSpaceEnv;
static PySexpObject *emptyEnv;
static PySexpObject *rpy_R_MissingArg;
static PySexpObject *rpy_R_NilValue;

static PyObject *rinterface_unserialize;

#ifdef RPY_DEBUG_PRESERVE
static int preserved_robjects = 0;
#endif


/* early definition of functions */
static PySexpObject* newPySexpObject(const SEXP sexp);
static SEXP newSEXP(PyObject *object, const int rType);


/* --- set output from the R console ---*/

static inline PyObject* EmbeddedR_setAnyCallback(PyObject *self,
                                                 PyObject *args,
                                                 PyObject **target)
{
  
  PyObject *result = NULL;
  PyObject *function;
  
  if ( PyArg_ParseTuple(args, "O:console", 
                        &function)) {
    
    if (function != Py_None && !PyCallable_Check(function)) {
      PyErr_SetString(PyExc_TypeError, "parameter must be callable");
      return NULL;
    }

    Py_XDECREF(*target);
    if (function == Py_None) {
      *target = NULL;
    } else {
      Py_XINCREF(function);
      *target = function;
    }
    Py_INCREF(Py_None);
    result = Py_None;
  } else {
    PyErr_SetString(PyExc_TypeError, "The parameter should be a callable.");
  }
  return result;
  
}

static PyObject* EmbeddedR_getAnyCallback(PyObject *self,
                                                 PyObject *args,
                                                 PyObject *target)
{
  PyObject *result = NULL;

  if (PyArg_ParseTuple(args, "")) {
    if (target == NULL) {
      result = Py_None;
    } else {
      result = target;
    }
  } else {

  }
  Py_XINCREF(result);
  return result;
}


static PyObject* writeConsoleCallback = NULL;

static PyObject* EmbeddedR_setWriteConsole(PyObject *self,
                                           PyObject *args)
{
  PyObject *res = EmbeddedR_setAnyCallback(self, args, &writeConsoleCallback);
  return res;
}

PyDoc_STRVAR(EmbeddedR_setWriteConsole_doc,
             "set_writeconsole(f)\n\n"
             "Set how to handle output from the R console with either None"
             " or a function f such as f(output) returns None"
             " (f only has side effects).");

static PyObject * EmbeddedR_getWriteConsole(PyObject *self,
                                            PyObject *args)
{
  return EmbeddedR_getAnyCallback(self, args, writeConsoleCallback);
}

PyDoc_STRVAR(EmbeddedR_getWriteConsole_doc,
             "get_writeconsole()\n\n"
             "Retrieve the current R console output handler"
             " (see set_writeconsole)");



static void
EmbeddedR_WriteConsole(const char *buf, int len)
{
  PyObject *arglist;
  PyObject *result;

  int is_threaded ;
  PyGILState_STATE gstate;
  RPY_GIL_ENSURE(is_threaded, gstate);

  /* It is necessary to restore the Python handler when using a Python
     function for I/O. */
  PyOS_setsig(SIGINT, python_sighandler);
  arglist = Py_BuildValue("(s)", buf);
  if (! arglist) {
    PyErr_NoMemory();
/*     signal(SIGINT, old_int); */
/*     return NULL; */
  }

  if (writeConsoleCallback == NULL) {
    return;
  }

  result = PyEval_CallObject(writeConsoleCallback, arglist);
  PyObject* pythonerror = PyErr_Occurred();
  if (pythonerror != NULL) {
    /* All R actions should be stopped since the Python callback failed,
     and the Python exception raised up.*/
    /* FIXME: Print the exception in the meanwhile */
    PyErr_Print();
    PyErr_Clear();
  }

  Py_DECREF(arglist);
/*   signal(SIGINT, old_int); */
  
  Py_XDECREF(result);  
  RPY_GIL_RELEASE(is_threaded, gstate);
}

static PyObject* showMessageCallback = NULL;

static PyObject* EmbeddedR_setShowMessage(PyObject *self,
                                          PyObject *args)
{
  return EmbeddedR_setAnyCallback(self, args, &showMessageCallback);  
}

PyDoc_STRVAR(EmbeddedR_setShowMessage_doc,
             "set_showmessage(f)\n\n"
             "Set how to handle alert message from R with either None"
             " or a function f such as f(message) returns None"
             " (f only has side effects).");

static PyObject * EmbeddedR_getShowMessage(PyObject *self,
                                            PyObject *args)
{
  return EmbeddedR_getAnyCallback(self, args, showMessageCallback);
}

PyDoc_STRVAR(EmbeddedR_getShowMessage_doc,
             "get_showmessage()\n\n"
             "Retrieve the current R alert message handler"
             " (see set_showmessage)");


static void
EmbeddedR_ShowMessage(const char *buf)
{
  PyOS_sighandler_t old_int;
  PyObject *arglist;
  PyObject *result;

  int is_threaded ;
  PyGILState_STATE gstate;
  RPY_GIL_ENSURE(is_threaded, gstate);

  /* It is necessary to restore the Python handler when using a Python
     function for I/O. */
  old_int = PyOS_getsig(SIGINT);
  PyOS_setsig(SIGINT, python_sighandler);
  arglist = Py_BuildValue("(s)", buf);
  if (! arglist) {
    PyErr_NoMemory();
/*     signal(SIGINT, old_int); */
/*     return NULL;  */
  }

  if (showMessageCallback == NULL) {
    return;
  }

  result = PyEval_CallObject(showMessageCallback, arglist);
  PyObject* pythonerror = PyErr_Occurred();
  if (pythonerror != NULL) {
    /* All R actions should be stopped since the Python callback failed,
     and the Python exception raised up.*/
    /* FIXME: Print the exception in the meanwhile */
    PyErr_Print();
    PyErr_Clear();
  }

  Py_DECREF(arglist);
/*   signal(SIGINT, old_int); */
  
  Py_XDECREF(result);
  RPY_GIL_RELEASE(is_threaded, gstate);
}

static PyObject* readConsoleCallback = NULL;

static PyObject* EmbeddedR_setReadConsole(PyObject *self,
                                          PyObject *args)
{
  return EmbeddedR_setAnyCallback(self, args, &readConsoleCallback); 
}

PyDoc_STRVAR(EmbeddedR_setReadConsole_doc,
             "set_readconsole(f)\n\n"
             "Set how to handle input to R with either None"
             " or a function f such as f(prompt) returns the string"
             " message to be passed to R");

static PyObject * EmbeddedR_getReadConsole(PyObject *self,
                                            PyObject *args)
{
  return EmbeddedR_getAnyCallback(self, args, readConsoleCallback);
}

PyDoc_STRVAR(EmbeddedR_getReadConsole_doc,
             "get_readconsole()\n\n"
             "Retrieve the current R alert message handler"
             " (see set_readconsole)");

static int
EmbeddedR_ReadConsole(const char *prompt, unsigned char *buf, 
                      int len, int addtohistory)
{
  PyObject *arglist;
  PyObject *result;

  int is_threaded ;
  PyGILState_STATE gstate;
  RPY_GIL_ENSURE(is_threaded, gstate);

  /* It is necessary to restore the Python handler when using a Python
     function for I/O. */
/*   old_int = PyOS_getsig(SIGINT); */
/*   PyOS_setsig(SIGINT, python_sighandler); */
  arglist = Py_BuildValue("(s)", prompt);
  if (! arglist) {
    PyErr_NoMemory();
/*     signal(SIGINT, old_int); */
/* return NULL; */
  }

  if (readConsoleCallback == NULL) {
    Py_DECREF(arglist);
    RPY_GIL_RELEASE(is_threaded, gstate);
    return -1;
  }

  #ifdef RPY_DEBUG_CONSOLE
  printf("Callback for console input...");
  #endif
  result = PyEval_CallObject(readConsoleCallback, arglist);
  #ifdef RPY_DEBUG_CONSOLE
  printf("done.(%p)\n", result);
  #endif

  PyObject* pythonerror = PyErr_Occurred();
  if (pythonerror != NULL) {
    /* All R actions should be stopped since the Python callback failed,
     and the Python exception raised up.*/
    /* FIXME: Print the exception in the meanwhile */
    PyErr_Print();
    PyErr_Clear();
    Py_XDECREF(arglist);
    RPY_GIL_RELEASE(is_threaded, gstate);
    return 0;
  }


  if (result == NULL) {
    /* FIXME: can this be reached ? result == NULL while no error ? */
/*     signal(SIGINT, old_int); */
    Py_XDECREF(arglist);
    RPY_GIL_RELEASE(is_threaded, gstate);
    return 0;
  }

  char *input_str = PyString_AsString(result);
  if (! input_str) {
    Py_XDECREF(arglist);
    RPY_GIL_RELEASE(is_threaded, gstate);
    return 0;
  }

  /* Snatched from Rcallbacks.c in JRI */
  int l=strlen(input_str);
  strncpy((char *)buf, input_str, (l>len-1)?len-1:l);
  buf[(l>len-1)?len-1:l]=0;
  /* --- */
  
  Py_XDECREF(result);
/*   signal(SIGINT, old_int); */

  RPY_GIL_RELEASE(is_threaded, gstate);
  return 1;
}

static PyObject* flushConsoleCallback = NULL;

static PyObject* EmbeddedR_setFlushConsole(PyObject *self,
                                           PyObject *args)
{
  return EmbeddedR_setAnyCallback(self, args, &flushConsoleCallback);  
}

PyDoc_STRVAR(EmbeddedR_setFlushConsole_doc,
             "set_flushconsole(f)\n\n"
             "Set how to handle the flushing to the R conso with either None"
             " or a function f such as f() returns None"
             " (f only has side effects).");

static PyObject * EmbeddedR_getFlushConsole(PyObject *self,
                                            PyObject *args)
{
  return EmbeddedR_getAnyCallback(self, args, flushConsoleCallback);
}

PyDoc_STRVAR(EmbeddedR_getFlushConsole_doc,
             "get_flushconsole()\n\n"
             "Retrieve the current R handler to flush the console"
             " (see set_flushconsole)");

static void
EmbeddedR_FlushConsole(void)
{
  PyObject *result;

  int is_threaded ;
  PyGILState_STATE gstate;
  RPY_GIL_ENSURE(is_threaded, gstate);

  result = PyEval_CallObject(flushConsoleCallback, NULL);
  PyObject* pythonerror = PyErr_Occurred();
  if (pythonerror != NULL) {
    /* All R actions should be stopped since the Python callback failed,
     and the Python exception raised up.*/
    /* FIXME: Print the exception in the meanwhile */
    PyErr_Print();
    PyErr_Clear();
  }

  RPY_GIL_RELEASE(is_threaded, gstate);
  return;
}

static PyObject* chooseFileCallback = NULL;

static PyObject* EmbeddedR_setChooseFile(PyObject *self,
                                         PyObject *args)
{
  return EmbeddedR_setAnyCallback(self, args, &chooseFileCallback);  
}

PyDoc_STRVAR(EmbeddedR_setChooseFile_doc,
             "Use the function to handle R's requests for choosing a file.");

static PyObject * EmbeddedR_getChooseFile(PyObject *self,
                                            PyObject *args)
{
  return EmbeddedR_getAnyCallback(self, args, chooseFileCallback);
}

PyDoc_STRVAR(EmbeddedR_getChooseFile_doc,
             "Retrieve current R console output handler (see setChooseFile).");

static int
EmbeddedR_ChooseFile(int new, char *buf, int len)
{
  PyObject *arglist;
  PyObject *result;

  int is_threaded ;
  PyGILState_STATE gstate;
  RPY_GIL_ENSURE(is_threaded, gstate);

  arglist = Py_BuildValue("(s)", buf);
  if (! arglist) {
    PyErr_NoMemory();
  }

  if (chooseFileCallback == NULL) {
    Py_DECREF(arglist);
    RPY_GIL_RELEASE(is_threaded, gstate);
    return 0;
  }

  result = PyEval_CallObject(chooseFileCallback, arglist);

  PyObject* pythonerror = PyErr_Occurred();
  if (pythonerror != NULL) {
    /* All R actions should be stopped since the Python callback failed,
     and the Python exception raised up.*/
    /* FIXME: Print the exception in the meanwhile */
    PyErr_Print();
    PyErr_Clear();
    Py_XDECREF(arglist);
    RPY_GIL_RELEASE(is_threaded, gstate);
    return 0;
  }
  
  if (result == NULL) {
    /* FIXME: can this be reached ? result == NULL while no error ? */
    Py_XDECREF(arglist);
    RPY_GIL_RELEASE(is_threaded, gstate);
    return 0;
  }

  char *path_str = PyString_AsString(result);
  if (! path_str) {
    Py_DECREF(result);
    PyErr_SetString(PyExc_TypeError, 
                    "Returned value should have a string representation");
    PyErr_Print();
    PyErr_Clear();
    Py_DECREF(arglist);
    RPY_GIL_RELEASE(is_threaded, gstate);
    return 0;
  }

  /* As shown in gnomeGUI */
  int l=strlen(path_str);
  strncpy((char *)buf, path_str, (l>len-1)?len-1:l);
  buf[(l>len-1)?len-1:l] = '\0';
  /* --- */

  Py_DECREF(arglist);  
  Py_DECREF(result);

  RPY_GIL_RELEASE(is_threaded, gstate);
  return l;
}

static PyObject* showFilesCallback = NULL;

static PyObject* EmbeddedR_setShowFiles(PyObject *self,
                                        PyObject *args)
{
  return EmbeddedR_setAnyCallback(self, args, &showFilesCallback);  
}

PyDoc_STRVAR(EmbeddedR_setShowFiles_doc,
             "Use the function to display files.");

static PyObject * EmbeddedR_getShowFiles(PyObject *self,
                                            PyObject *args)
{
  return EmbeddedR_getAnyCallback(self, args, showFilesCallback);
}

PyDoc_STRVAR(EmbeddedR_getShowFiles_doc,
             "Retrieve current R console output handler (see setShowFiles).");

static int
EmbeddedR_ShowFiles(int nfile, const char **file, const char **headers,
                    const char *wtitle, Rboolean del, const char *pager)
{

  int is_threaded ;
  PyGILState_STATE gstate;
  RPY_GIL_ENSURE(is_threaded, gstate);

  if (showFilesCallback == NULL) {
    RPY_GIL_RELEASE(is_threaded, gstate);
    return 0;
  }
   
  if (nfile < 1) {
    RPY_GIL_RELEASE(is_threaded, gstate);
    return 0;
  }

  PyObject *arglist;
  PyObject *result;

  PyObject *py_wtitle = PyString_FromString(wtitle);
  PyObject *py_del;
  RPY_PY_FROM_RBOOL(py_del, del);
  PyObject *py_pager = PyString_FromString(pager);

  PyObject *py_fileheaders_tuple = PyTuple_New(nfile);
  PyObject *py_fileheader;
  int f_i;
  for (f_i = 0; f_i < nfile; f_i++) {
    py_fileheader = PyTuple_New(2);
    if (PyTuple_SetItem(py_fileheader, 0,
                        PyString_FromString(headers[f_i])) != 0) {
      Py_DECREF(py_fileheaders_tuple);
      /*FIXME: decref other PyObject arguments */
      RPY_GIL_RELEASE(is_threaded, gstate);
      return 0;
    }
    if (PyTuple_SetItem(py_fileheader, 1,
                        PyString_FromString(file[f_i])) != 0) {
      Py_DECREF(py_fileheaders_tuple);
      /*FIXME: decref other PyObject arguments */
      RPY_GIL_RELEASE(is_threaded, gstate);
      return 0;
    }
    if (PyTuple_SetItem(py_fileheaders_tuple, f_i,
                        py_fileheader) != 0) {
      Py_DECREF(py_fileheaders_tuple);
      /*FIXME: decref other PyObject arguments */
      RPY_GIL_RELEASE(is_threaded, gstate);
      return 0;
    }
  }

  arglist = Py_BuildValue("OOOO", py_fileheaders_tuple, py_wtitle, py_del, py_pager);
  if (! arglist) {
    PyErr_Print();
    PyErr_NoMemory();
    /*FIXME: decref PyObject arguments */
    RPY_GIL_RELEASE(is_threaded, gstate);
    return 0;
  }

  result = PyEval_CallObject(showFilesCallback, arglist);

  PyObject* pythonerror = PyErr_Occurred();
  if (pythonerror != NULL) {
    /* All R actions should be stopped since the Python callback failed,
     and the Python exception raised up.*/
    /* FIXME: Print the exception in the meanwhile */
    PyErr_Print();
    PyErr_Clear();
    Py_XDECREF(arglist);
    RPY_GIL_RELEASE(is_threaded, gstate);
    return 0;
  }
  
  if (result == NULL) {
    /* FIXME: can this be reached ? result == NULL while no error ? */
    Py_XDECREF(arglist);
    RPY_GIL_RELEASE(is_threaded, gstate);
    return 0;
  }

  /*FIXME: check that nothing is returned ? */
  if (! 1) {
    Py_DECREF(result);
    PyErr_SetString(PyExc_TypeError, 
                    "Returned value should be None");
    PyErr_Print();
    PyErr_Clear();
    Py_DECREF(arglist);
    RPY_GIL_RELEASE(is_threaded, gstate);
    return 0;
  }

  Py_DECREF(arglist);
  Py_DECREF(result);
  RPY_GIL_RELEASE(is_threaded, gstate);
  return 1;
}

static PyObject* cleanUpCallback = NULL;
static PyObject* EmbeddedR_setCleanUp(PyObject *self,
                                       PyObject *args)
{
  return EmbeddedR_setAnyCallback(self, args, &cleanUpCallback);  
}

PyDoc_STRVAR(EmbeddedR_setCleanUp_doc,
             "Set the function called to clean up when exiting R.");

static PyObject * EmbeddedR_getCleanUp(PyObject *self,
                                       PyObject *args)
{
  PyObject* res = EmbeddedR_getAnyCallback(self, args, cleanUpCallback);
  return res;
}

PyDoc_STRVAR(EmbeddedR_getCleanUp_doc,
             "Get the function called to clean up when exiting R.");

extern SA_TYPE SaveAction; 
static void
EmbeddedR_CleanUp(SA_TYPE saveact, int status, int runLast)
{
  /*
    R_CleanUp is invoked at the end of the session to give the user the
    option of saving their data.
    If ask == SA_SAVEASK the user should be asked if possible (and this
    option should not occur in non-interactive use).
    If ask = SA_SAVE or SA_NOSAVE the decision is known.
    If ask = SA_DEFAULT use the SaveAction set at startup.
    In all these cases run .Last() unless quitting is cancelled.
    If ask = SA_SUICIDE, no save, no .Last, possibly other things.
  */

  int is_threaded ;
  PyGILState_STATE gstate;

  if(saveact == SA_DEFAULT) { /* The normal case apart from R_Suicide */
    saveact = SaveAction;
  }
  
  RPY_GIL_ENSURE(is_threaded, gstate);
  
  PyObject *arglist = Py_BuildValue("iii", saveact, status, runLast);
  PyObject *result = PyEval_CallObject(cleanUpCallback, arglist);
  PyObject* pythonerror = PyErr_Occurred();
  
  if (pythonerror != NULL) {
    /* All R actions should be stopped since the Python callback failed,
             and the Python exception raised up.*/
    /* FIXME: Print the exception in the meanwhile */
    PyErr_Print();
    PyErr_Clear();
  } else {
    if (result == Py_None)
      jump_to_toplevel();

    int res_true = PyObject_IsTrue(result);
    switch(res_true) {
    case -1:
      printf("*** error while testing of the value returned from the cleanup callback is true.\n");
      jump_to_toplevel();
      break;
    case 1:
      saveact = SA_SAVE;
      break;
    case 0:
      saveact = SA_NOSAVE;
      break;
    }
    Py_XDECREF(arglist);
    RPY_GIL_RELEASE(is_threaded, gstate);
  }

  if (saveact == SA_SAVEASK) {
    if (R_Interactive) {
      /* if (cleanUpCallback != NULL) {  */
        
      /*        } */
      /* } else { */
        saveact = SaveAction;
      /* } */
    } else {
        saveact = SaveAction;
    }
  }
  switch (saveact) {
  case SA_SAVE:
    if(runLast) R_dot_Last();
    if(R_DirtyImage) R_SaveGlobalEnv();
/*     if (CharacterMode == RGui) { */
/*       R_setupHistory(); /\* re-read the history size and filename *\/ */
/*       wgl_savehistory(R_HistoryFile, R_HistorySize); */
/*     } else if(R_Interactive && CharacterMode == RTerm) { */
/*       R_setupHistory(); /\* re-read the history size and filename *\/ */
/*       gl_savehistory(R_HistoryFile, R_HistorySize); */
/*     } */
    break;
  case SA_NOSAVE:
    if(runLast) R_dot_Last();
    break;
  case SA_SUICIDE:
  default:
    break;
  }
  R_RunExitFinalizers();
/*   editorcleanall(); */
/*   CleanEd(); */
  R_CleanTempDir();
  Rf_KillAllDevices();
/*   AllDevicesKilled = TRUE; */
/*   if (R_Interactive && CharacterMode == RTerm) */
/*     SetConsoleTitle(oldtitle); */
/*   if (R_CollectWarnings && saveact != SA_SUICIDE */
/*       && CharacterMode == RTerm) */
/*     PrintWarnings(); */
/*   app_cleanup(); */
/*   RConsole = NULL; */
/*   if(ifp) fclose(ifp); */
/*   if(ifile[0]) unlink(ifile); */
  /* exit(status); */
  
}

/* --- Initialize and terminate an embedded R --- */
static PyObject* EmbeddedR_getinitoptions(PyObject *self) 
{
  return initOptions;
}
PyDoc_STRVAR(EmbeddedR_get_initoptions_doc,
             "\
Get the options used to initialize R.\
");

static PyObject* EmbeddedR_setinitoptions(PyObject *self, PyObject *tuple) 
{

  if (embeddedR_status & RPY_R_INITIALIZED) {
    PyErr_Format(PyExc_RuntimeError, 
                 "Options cannot be set once R has been initialized.");
    return NULL;
  }

  int istuple = PyTuple_Check(tuple);
  if (! istuple) {
    PyErr_Format(PyExc_ValueError, "Parameter should be a tuple.");
    return NULL;
  }
  Py_DECREF(initOptions);
  Py_INCREF(tuple);
  initOptions = tuple;
  Py_INCREF(Py_None);
  return Py_None;
}
PyDoc_STRVAR(EmbeddedR_set_initoptions_doc,
             "\
Set the options used to initialize R.\
");


/* --- R_ProcessEvents ---*/

static PyObject* EmbeddedR_ProcessEvents(PyObject *self)
{
  if (! (embeddedR_status & RPY_R_INITIALIZED)) {
    PyErr_Format(PyExc_RuntimeError, 
                 "R should not process events before being initialized.");
    return NULL;
  }
  if (embeddedR_status & RPY_R_BUSY) {
    PyErr_Format(PyExc_RuntimeError, "Concurrent access to R is not allowed.");
    return NULL;
  }
  embeddedR_setlock();
#if defined(HAVE_AQUA) || defined(Win32)
  /* Can the call to R_ProcessEvents somehow fail ? */
  R_ProcessEvents();
#endif
#if !defined(Win32)
  R_runHandlers(R_InputHandlers, R_checkActivity(0, 1));
#endif
  embeddedR_freelock();
  Py_INCREF(Py_None);
  return Py_None;
}
PyDoc_STRVAR(EmbeddedR_ProcessEvents_doc,
             "Process R events. This function is a simple wrapper around\n"
             "R_ProcessEvents (on win32 and MacOS X-Aqua)\n"
             "and R_runHandlers (on other platforms).");


#ifdef Win32
void win32CallBack()
{
   /* called during i/o, eval, graphics in ProcessEvents */
}
void Re_Busy(int which)
{
  
}
#endif

static PyObject* EmbeddedR_init(PyObject *self) 
{

  static int status;
  
  if (embeddedR_status & RPY_R_INITIALIZED) {
    return PyInt_FromLong(status);
/*     PyErr_Format(PyExc_RuntimeError, "R can only be initialized once."); */
/*     return NULL; */
  }

  const Py_ssize_t n_args = PySequence_Size(initOptions);
  char *options[n_args];

  PyObject *opt_string;
  Py_ssize_t ii;
  for (ii = 0; ii < n_args; ii++) {
    opt_string = PyTuple_GetItem(initOptions, ii);
    options[ii] = PyString_AsString(opt_string);
  }


#ifndef Win32

#else
  /* --- Win32 --- */
  structRstart rp;
  Rp = &rp;

  char RHome[260];
  char RUser[260];

  R_setStartTime();
  R_DefParams(Rp);
  if (getenv("R_HOME")) {
    strcpy(RHome, getenv("R_HOME"));
  } else {
    PyErr_Format(PyExc_RuntimeError, "R_HOME not defined.");
    return NULL;
  }
  Rp->rhome = RHome;

  if (getenv("R_USER")) {
    strcpy(RUser, getenv("R_USER"));
  } else if (getenv("HOME")) {
    strcpy(RUser, getenv("HOME"));
  } else if (getenv("HOMEDIR")) {
    strcpy(RUser, getenv("HOMEDIR"));
    strcat(RUser, getenv("HOMEPATH"));
  } else {
    PyErr_Format(PyExc_RuntimeError, "R_USER not defined.");
    return NULL;
  }
  Rp->home = RUser;
  /* Rp->CharacterMode = LinkDLL; */
  Rp->ReadConsole = EmbeddedR_ReadConsole;
  Rp->WriteConsole = NULL;
  Rp->WriteConsoleEx = EmbeddedR_WriteConsole;

  Rp->Busy = Re_Busy;
  Rp->ShowMessage = EmbeddedR_ShowMessage;
  /* Rp->FlushConsole = EmbeddedR_FlushConsole; */
  Rp->CallBack = win32CallBack;
  Rp->R_Quiet = FALSE;
  Rp->R_Interactive = TRUE;
  Rp->RestoreAction = SA_RESTORE;
  Rp->SaveAction = SA_SAVEASK;
  /* hocus-pocus for R-win32 - just don't ask why*/
  R_SetParams(Rp);
  R_SizeFromEnv(Rp);
  R_SetParams(Rp);
  setup_term_ui();
#endif

#ifdef RIF_HAS_RSIGHAND
  R_SignalHandlers = 0;
#endif  
  /* int status = Rf_initEmbeddedR(n_args, options);*/
  status = Rf_initialize_R(n_args, options);
  if (status < 0) {
    PyErr_SetString(PyExc_RuntimeError, "Error while initializing R.");
    return NULL;
  }

  R_Interactive = TRUE;
#ifdef RIF_HAS_RSIGHAND
  R_SignalHandlers = 0;
#endif  

#ifdef R_INTERFACE_PTRS
  ptr_R_CleanUp = EmbeddedR_CleanUp;
  /* Redirect R console output */
  ptr_R_ShowMessage = EmbeddedR_ShowMessage;
  ptr_R_WriteConsole = EmbeddedR_WriteConsole;
  ptr_R_FlushConsole = EmbeddedR_FlushConsole;
  R_Outputfile = NULL;
  R_Consolefile = NULL;
  /* Redirect R console input */
  ptr_R_ReadConsole = EmbeddedR_ReadConsole;
  ptr_R_ChooseFile = EmbeddedR_ChooseFile;
  ptr_R_ShowFiles = EmbeddedR_ShowFiles;
#endif

  /* Taken from JRI:
   * disable stack checking, because threads will thow it off */
  R_CStackLimit = (uintptr_t) -1;
  /* --- */

  setup_Rmainloop();

  Py_XDECREF(embeddedR_isInitialized);
  embeddedR_status = RPY_R_INITIALIZED;
  embeddedR_isInitialized = Py_True;
  Py_INCREF(embeddedR_isInitialized);

  RPY_SEXP(globalEnv) = R_GlobalEnv;
  RPY_SEXP(baseNameSpaceEnv) = R_BaseNamespace;
  RPY_SEXP(emptyEnv) = R_EmptyEnv;
  RPY_SEXP(rpy_R_MissingArg) = R_MissingArg;
  RPY_SEXP(rpy_R_NilValue) = R_NilValue;

  errMessage_SEXP = findVar(install("geterrmessage"), 
                            R_BaseNamespace);

  PyObject *res = PyInt_FromLong(status);

#ifdef RPY_VERBOSE
  printf("R initialized - status: %i\n", status);
#endif

  return res;
}
PyDoc_STRVAR(EmbeddedR_init_doc,
             "\
Initialize an embedded R.\
");


static PyObject* EmbeddedR_end(PyObject *self, Py_ssize_t fatal)
{
  /* FIXME: Have a reference count for R objects known to Python.
   * ending R will not be possible until all such objects are already
   * deallocated in Python ?
   *other possibility would be to have a fallback for "unreachable" objects ? 
   */
  /*FIXME: rpy has something to terminate R. Check the details of what they are. */
  /* taken from the tests/Embedded/shutdown.c in the R source tree */

  R_dot_Last();           
  R_RunExitFinalizers();  
  /* CleanEd(); */
  Rf_KillAllDevices();
  
  R_CleanTempDir();
  /* PrintWarnings(); */
  R_gc();
  /* */

  Rf_endEmbeddedR((int)fatal);
  embeddedR_status = embeddedR_status & (! RPY_R_INITIALIZED);

  RPY_SEXP(globalEnv) = R_EmptyEnv;
  RPY_SEXP(baseNameSpaceEnv) = R_EmptyEnv;
  RPY_SEXP(emptyEnv) = R_EmptyEnv;
  errMessage_SEXP = R_NilValue; 

  /* FIXME: Is it possible to reinitialize R later ?
   * Py_XDECREF(embeddedR_isInitialized);
   * embeddedR_isInitialized = Py_False;
   *Py_INCREF(embeddedR_isInitialized); 
   */

  Py_RETURN_NONE;
}
PyDoc_STRVAR(EmbeddedR_end_doc,
             "endEmbeddedR()\n\
             \n\
             Terminate an embedded R.");



static PyObject* EmbeddedR_setinteractive(PyObject *self, PyObject *status)
{
  if (! PyBool_Check(status)) {
    PyErr_SetString(PyExc_ValueError, "The status must be a boolean");
    return NULL;
  }
  int rtruefalse;
  if (PyObject_IsTrue(status)) {
    rtruefalse = TRUE;
  } else {
    rtruefalse = FALSE;
  }
  #ifdef Win32
  Rp->R_Interactive = rtruefalse;
  #else
  R_Interactive = rtruefalse;
  #endif
  Py_RETURN_NONE;
}
PyDoc_STRVAR(EmbeddedR_setinteractive_doc,
             "set_interactive(status)\n\
             \n\
             Set the interactivity status for R.\n\
             (This function exists for experimentation purposes,\n\
             and could lead to an unpredictable outcome.)");




static void
EmbeddedR_exception_from_errmessage(void)
{
  SEXP expr, res;
  /* PROTECT(errMessage_SEXP) */
  PROTECT(expr = allocVector(LANGSXP, 1));
  SETCAR(expr, errMessage_SEXP);
  PROTECT(res = Rf_eval(expr, R_GlobalEnv));
  const char *message = CHARACTER_VALUE(res);
  UNPROTECT(2);
  PyErr_SetString(RPyExc_RuntimeError, message);
}




/*
 * Access to R objects through Python objects
 */

staticforward PyTypeObject Sexp_Type;

void SexpObject_clear(SexpObject *sexpobj)
{

  (*sexpobj).count--;

#ifdef RPY_VERBOSE
  printf("R:%p -- sexp count is %i...", 
         sexpobj->sexp, sexpobj->count);
#endif
  if (((*sexpobj).count == 0) && (*sexpobj).sexp) {
#ifdef RPY_VERBOSE
    printf("freeing SEXP resources...");
#endif 

    if (sexpobj->sexp != R_NilValue) {
#ifdef RPY_DEBUG_PRESERVE
      printf("  PRESERVE -- Sexp_clear: R_ReleaseObject -- %p ", 
             sexpobj->sexp);
      preserved_robjects -= 1;
      printf("-- %i\n", preserved_robjects);
#endif 
    R_ReleaseObject(sexpobj->sexp);
    }
    PyMem_Free(sexpobj);
    /* self->ob_type->tp_free((PyObject*)self); */
#ifdef RPY_VERBOSE
    printf("done.\n");
#endif 
  }  
}

static void
Sexp_clear(PySexpObject *self)
{
  
  SexpObject_clear(self->sObj);

}


static void
Sexp_dealloc(PySexpObject *self)
{
  Sexp_clear(self);
  self->ob_type->tp_free((PyObject*)self);

  /* PyObject_Del(self); */
}


static PyObject*
Sexp_repr(PyObject *self)
{
  /* FIXME: make sure this is making any sense */
  SEXP sexp = RPY_SEXP((PySexpObject *)self);
  /* if (! sexp) {
   *  PyErr_Format(PyExc_ValueError, "NULL SEXP.");
   *  return NULL;
   *}
   */
  return PyString_FromFormat("<%s - Python:\%p / R:\%p>",
                             self->ob_type->tp_name,
                             self,
                             sexp);
}


static PyObject*
Sexp_typeof_get(PyObject *self)
{
  PySexpObject *pso = (PySexpObject*)self;
  SEXP sexp = RPY_SEXP(pso);
  if (! sexp) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return NULL;;
  }
  return PyInt_FromLong(TYPEOF(sexp));
}
PyDoc_STRVAR(Sexp_typeof_doc,
             "R internal SEXPREC type.");


static PyObject*
Sexp_do_slot(PyObject *self, PyObject *name)
{
  SEXP sexp = RPY_SEXP(((PySexpObject*)self));
  if (! sexp) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return NULL;;
  }
  if (! PyString_Check(name)) {
    PyErr_SetString(PyExc_TypeError, "The name must be a string.");
    return NULL;
  }
  char *name_str = PyString_AS_STRING(name);

  if (! R_has_slot(sexp, install(name_str))) {
    PyErr_SetString(PyExc_LookupError, "The object has no such attribute.");
    return NULL;
  }
  SEXP res_R = GET_SLOT(sexp, install(name_str));

  PyObject *res = (PyObject *)newPySexpObject(res_R);
  return res;
}
PyDoc_STRVAR(Sexp_do_slot_doc,
             "Returns the attribute/slot for an R object.\n"
             " The name of the slot (a string) is the only parameter for\n"
             "the method.\n"
             ":param name: string\n"
             ":rtype: instance of type or subtype :class:`rpy2.rinterface.Sexp`");

static PyObject*
Sexp_do_slot_assign(PyObject *self, PyObject *args)
{

  SEXP sexp = RPY_SEXP(((PySexpObject*)self));
  if (! sexp) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return NULL;;
  }

  char *name_str;
  PyObject *value;
  if (! PyArg_ParseTuple(args, "sO", 
                         &name_str,
                         &value)) {
    return NULL;
  }

  if (! PyObject_IsInstance(value, 
                          (PyObject*)&Sexp_Type)) {
      PyErr_Format(PyExc_ValueError, "Value must be an instance of Sexp.");
      return NULL;
  }

  SEXP value_sexp = RPY_SEXP((PySexpObject *)value);
  if (! value_sexp) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return NULL;;
  }

  SET_SLOT(sexp, install(name_str), value_sexp);
  Py_INCREF(Py_None);
  return Py_None;
}
PyDoc_STRVAR(Sexp_do_slot_assign_doc,
             "Set the attribute/slot for an R object.\n"
             "\n"
             ":param name: string\n"
             ":param value: instance of :class:`rpy2.rinterface.Sexp`");

static PyObject*
Sexp_named_get(PyObject *self)
{
  SEXP sexp = RPY_SEXP(((PySexpObject*)self));
  if (! sexp) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return NULL;;
  }
  unsigned int res = NAMED(sexp);
  return PyInt_FromLong((long)res);
}
PyDoc_STRVAR(Sexp_named_doc,
"Integer code for the R object reference-pseudo counting.\n\
This method corresponds to the macro NAMED.\n\
See the R-extensions manual for further details.");

void SexpObject_CObject_destroy(void *cobj)
{
  SexpObject* sexpobj_ptr = (SexpObject *)cobj;
  SexpObject_clear(sexpobj_ptr);
}

static PyObject*
Sexp_sexp_get(PyObject *self, void *closure)
{
  PySexpObject* rpyobj = (PySexpObject*)self;

  if (! RPY_SEXP(rpyobj)) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return NULL;;
  }
  
  RPY_INCREF(rpyobj);
  PyObject *res = PyCObject_FromVoidPtr(rpyobj->sObj, 
                                        SexpObject_CObject_destroy);
  return res;
}

static int
Sexp_sexp_set(PyObject *self, PyObject *obj, void *closure)
{
  if (! PyCObject_Check(obj)) {
    PyErr_SetString(PyExc_TypeError, "The value must be a CObject.");
    return -1;
  }

  SexpObject *sexpobj_orig = ((PySexpObject*)self)->sObj;
  SexpObject *sexpobj = (SexpObject *)(PyCObject_AsVoidPtr(obj));
  #ifdef RPY_DEBUG_COBJECT
  printf("Setting %p (count: %i) to %p (count: %i)\n", 
         sexpobj_orig, (int)sexpobj_orig->count,
         sexpobj, (int)sexpobj->count);
  #endif

  if ( (sexpobj_orig->sexp != R_NilValue) &
       (TYPEOF(sexpobj_orig->sexp) != TYPEOF(sexpobj->sexp))
      ) {
    PyErr_Format(PyExc_ValueError, 
                 "Mismatch in SEXP type (as returned by typeof)");
    return -1;
  }

  SEXP sexp = sexpobj->sexp;
  if (! sexp) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return -1;
  }

  /*FIXME: increment count seems needed, but is this leak free ? */
  sexpobj->count += 2;
  sexpobj_orig->count += 1;

  SexpObject_clear(sexpobj_orig);
  RPY_SEXP(((PySexpObject*)self)) = sexp;

  return 0;
}
PyDoc_STRVAR(Sexp_sexp_doc,
             "Opaque C pointer to the underlying R object");

static PyObject*
Sexp_rsame(PyObject *self, PyObject *other)
{
  
  if (! PyObject_IsInstance(other, 
                            (PyObject*)&Sexp_Type)) {
    PyErr_Format(PyExc_ValueError, 
                 "Can only compare Sexp objects.");
    return NULL;
  }
  
  SEXP sexp_self = RPY_SEXP(((PySexpObject*)self));
  if (! sexp_self) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return NULL;;
  }
  
  SEXP sexp_other = RPY_SEXP(((PySexpObject*)other));
  if (! sexp_other) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return NULL;;
  }
  
  long same = (sexp_self == sexp_other);
  return PyBool_FromLong(same);
}
PyDoc_STRVAR(Sexp_rsame_doc,
             "Is the given object representing the same underlying R object as the instance.");

static PyObject*
Sexp_duplicate(PyObject *self, PyObject *kwargs)
{
  SEXP sexp_self, sexp_copy;
  PyObject *res;
  
  sexp_self = RPY_SEXP((PySexpObject*)self);
  if (! sexp_self) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return NULL;;
  }
  PROTECT(sexp_copy = Rf_duplicate(sexp_self));
  res = (PyObject *) newPySexpObject(sexp_copy);
  UNPROTECT(1);
  return res;
}
PyDoc_STRVAR(Sexp_duplicate_doc,
             "Makes a copy of the underlying Sexp object, and returns it.");

static PyObject*
Sexp___getstate__(PyObject *self)
{

  PyObject *res_string;

  SEXP sexp = RPY_SEXP((PySexpObject *)self);
  if (! sexp) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return NULL;
  }

  SEXP sexp_ser;
  PROTECT(sexp_ser = rpy_serialize(sexp, R_GlobalEnv));
  if (TYPEOF(sexp_ser) != RAWSXP) {
    UNPROTECT(1);
    PyErr_Format(PyExc_RuntimeError, 
                 "R's serialize did not return a raw vector.");
    return NULL;
  }
  /* PyByteArray is only available with Python >= 2.6 */
          /* res = PyByteArray_FromStringAndSize(sexp_ser, len); */

  /*FIXME: is this working on 64bit archs ? */
  res_string = PyString_FromStringAndSize((void *)RAW_POINTER(sexp_ser), 
                                          (Py_ssize_t)LENGTH(sexp_ser));
  UNPROTECT(1);
  return res_string;
}

PyDoc_STRVAR(Sexp___getstate___doc,
             "Returns a serialized object for the underlying R object");


static PyObject*
Sexp___setstate__(PyObject *self, PyObject *state)
{

  Py_INCREF(Py_None);
  return Py_None;

}

PyDoc_STRVAR(Sexp___setstate___doc,
             "set the state of an instance (dummy).");


static PyObject*
EmbeddedR_unserialize(PyObject* self, PyObject* args)
{
  PyObject *res;

  if (! (embeddedR_status & RPY_R_INITIALIZED)) {
    PyErr_Format(PyExc_RuntimeError, 
                 "R cannot evaluate code before being initialized.");
    return NULL;
  }
  

  char *raw;
  Py_ssize_t raw_size;
  int rtype;
  if (! PyArg_ParseTuple(args, "s#i",
                         &raw, &raw_size,
                         &rtype)) {
    return NULL;
  }

  if (embeddedR_status & RPY_R_BUSY) {
    PyErr_Format(PyExc_RuntimeError, "Concurrent access to R is not allowed.");
    return NULL;
  }
  embeddedR_setlock();

  /* Not the most memory-efficient; an other option would
  * be to create a dummy RAW and rebind "raw" as its content
  * (wich seems clearly off the charts).
  */
  SEXP raw_sexp, sexp_ser;
  PROTECT(raw_sexp = NEW_RAW((int)raw_size));

  /*FIXME: use of the memcpy seems to point in the direction of
  * using the option mentioned above anyway. */
  int raw_i;
  for (raw_i = 0; raw_i < raw_size; raw_i++) {
    RAW_POINTER(raw_sexp)[raw_i] = raw[raw_i];
  }
  PROTECT(sexp_ser = rpy_unserialize(raw_sexp, R_GlobalEnv));

  if (TYPEOF(sexp_ser) != rtype) {
    UNPROTECT(2);
    PyErr_Format(PyExc_ValueError, 
                 "Mismatch between the serialized object"
                 " and the expected R type"
                 " (expected %i but got %i)", rtype, TYPEOF(raw_sexp));
    return NULL;
  }
  res = (PyObject*)newPySexpObject(sexp_ser);
  
  UNPROTECT(2);
  embeddedR_freelock();
  return res;
}

static PyObject*
Sexp___reduce__(PyObject* self)
{
  PyObject *dict, *result;

  if (! (embeddedR_status & RPY_R_INITIALIZED)) {
    PyErr_Format(PyExc_RuntimeError, 
                 "R cannot evaluate code before being initialized.");
    return NULL;
  }
  
  dict = PyObject_GetAttrString((PyObject *)self,
                                "__dict__");
  if (dict == NULL) {
    PyErr_Clear();
    dict = Py_None;
    Py_INCREF(dict);
  }

  if (embeddedR_status & RPY_R_BUSY) {
    PyErr_Format(PyExc_RuntimeError, "Concurrent access to R is not allowed.");
    return NULL;
  }
  embeddedR_setlock();

  result = Py_BuildValue("O(Oi)O",
                         rinterface_unserialize, /* constructor */
                         Sexp___getstate__(self),
                         TYPEOF(RPY_SEXP((PySexpObject *)self)),
                         dict);

  embeddedR_freelock();

  Py_DECREF(dict);
  return result;

}

PyDoc_STRVAR(Sexp___reduce___doc,
             "Prepare an instance for serialization.");



static PyMethodDef Sexp_methods[] = {
  {"do_slot", (PyCFunction)Sexp_do_slot, METH_O,
   Sexp_do_slot_doc},
  {"do_slot_assign", (PyCFunction)Sexp_do_slot_assign, METH_VARARGS,
   Sexp_do_slot_assign_doc},
  {"rsame", (PyCFunction)Sexp_rsame, METH_O,
   Sexp_rsame_doc},
  {"__deepcopy__", (PyCFunction)Sexp_duplicate, METH_KEYWORDS,
   Sexp_duplicate_doc},
  {"__getstate__", (PyCFunction)Sexp___getstate__, METH_NOARGS,
   Sexp___getstate___doc},
  {"__setstate__", (PyCFunction)Sexp___setstate__, METH_O,
   Sexp___setstate___doc},
  {"__reduce__", (PyCFunction)Sexp___reduce__, METH_NOARGS,
   Sexp___reduce___doc},
  {NULL, NULL}          /* sentinel */
};


static PyGetSetDef Sexp_getsets[] = {
  {"named", 
   (getter)Sexp_named_get,
   (setter)0,
   Sexp_named_doc},
  {"typeof", 
   (getter)Sexp_typeof_get,
   (setter)0,
   Sexp_typeof_doc},
  {"__sexp__",
   (getter)Sexp_sexp_get,
   (setter)Sexp_sexp_set,
   Sexp_sexp_doc},
  {NULL, NULL, NULL, NULL}          /* sentinel */
};


static PyObject*
Sexp_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{

  PySexpObject *self;
  /* unsigned short int rpy_only = 1; */

  #ifdef RPY_VERBOSE
  printf("new '%s' object @...\n", type->tp_name);
  #endif 

  /* self = (PySexpObject *)PyObject_New(PySexpObject, type); */
  self = (PySexpObject *)type->tp_alloc(type, 0);
  #ifdef RPY_VERBOSE
  printf("  Python:%p / R:%p (R_NilValue) ...\n", self, R_NilValue);
  #endif 

  if (! self)
    PyErr_NoMemory();

  self->sObj = (SexpObject *)PyMem_Malloc(1 * sizeof(SexpObject));
  if (! self->sObj) {
    Py_DECREF(self);
    PyErr_NoMemory();
  }

  RPY_COUNT(self) = 1;
  RPY_SEXP(self) = R_NilValue;
  /* RPY_RPYONLY(self) = rpy_only; */

  #ifdef RPY_VERBOSE
  printf("done.\n");
  #endif 

  return (PyObject *)self;

}

static int
Sexp_init(PyObject *self, PyObject *args, PyObject *kwds)
{
#ifdef RPY_VERBOSE
  printf("Python:%p / R:%p - Sexp initializing...\n", 
         self, RPY_SEXP((PySexpObject *)self));
#endif 

  PyObject *sourceObject;

  PyObject *copy = Py_True;
  int sexptype = -1;
  SexpObject *tmpSexpObject;


  static char *kwlist[] = {"sexp", "sexptype", "copy", NULL};
  /* FIXME: handle the copy argument */

  /* the "sexptype" is as a quick hack to make calls from
   the constructor of SexpVector */
  if (! PyArg_ParseTupleAndKeywords(args, kwds, "O|iO!", 
                                    kwlist,
                                    &sourceObject,
                                    &sexptype,
                                    &PyBool_Type, &copy)) {
    return -1;
  }

  if (! PyObject_IsInstance(sourceObject, 
                            (PyObject*)&Sexp_Type)) {
    PyErr_Format(PyExc_ValueError, 
                 "Can only instanciate from Sexp objects.");
    return -1;
  }

  if (PyObject_IsTrue(copy)) {
    tmpSexpObject = ((PySexpObject *)self)->sObj;
    ((PySexpObject *)self)->sObj = ((PySexpObject *)sourceObject)->sObj;
    free(tmpSexpObject);
    RPY_INCREF((PySexpObject *)self);
#ifdef RPY_VERBOSE
    printf("Python: %p / R: %p - sexp count is now %i.\n", 
           (PySexpObject *)self, RPY_SEXP((PySexpObject *)self), RPY_COUNT((PySexpObject *)self));
#endif 

  } else {
    PyErr_Format(PyExc_ValueError, "Cast without copy is not yet implemented.");
    return -1;
  }

#ifdef RPY_VERBOSE
  printf("done.\n");
#endif 

  /* SET_NAMED(RPY_SEXP((PySexpObject *)self), (unsigned int)2); */
  return 0;
}


/*
 * Generic Sexp_Type. It represents SEXP objects at large.
 */
static PyTypeObject Sexp_Type = {
        /* The ob_type field must be initialized in the module init function
         * to be portable to Windows without using C++. */
        PyObject_HEAD_INIT(NULL)
        0,                      /*ob_size*/
        "rpy2.rinterface.Sexp",      /*tp_name*/
        sizeof(PySexpObject),   /*tp_basicsize*/
        0,                      /*tp_itemsize*/
        /* methods */
        (destructor)Sexp_dealloc, /*tp_dealloc*/
        0,                      /*tp_print*/
        0,                      /*tp_getattr*/
        0,                      /*tp_setattr*/
        0,                      /*tp_compare*/
        Sexp_repr,              /*tp_repr*/
        0,                      /*tp_as_number*/
        0,                      /*tp_as_sequence*/
        0,                      /*tp_as_mapping*/
        0,                      /*tp_hash*/
        0,                      /*tp_call*/
        0,                      /*tp_str*/
        0,                      /*tp_getattro*/
        0,                      /*tp_setattro*/
        0,                      /*tp_as_buffer*/
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE,     /*tp_flags*/
        0,                      /*tp_doc*/
        0,                      /*tp_traverse*/
        (inquiry)Sexp_clear,                      /*tp_clear*/
        0,                      /*tp_richcompare*/
        0,                      /*tp_weaklistoffset*/
        0,                      /*tp_iter*/
        0,                      /*tp_iternext*/
        Sexp_methods,           /*tp_methods*/
        0,                      /*tp_members*/
        Sexp_getsets,            /*tp_getset*/
        0,                      /*tp_base*/
        0,                      /*tp_dict*/
        0,                      /*tp_descr_get*/
        0,                      /*tp_descr_set*/
        0,                      /*tp_dictoffset*/
        (initproc)Sexp_init,    /*tp_init*/
        0,                      /*tp_alloc*/
        Sexp_new,               /*tp_new*/
        0,                      /*tp_free*/
        0,                      /*tp_is_gc*/
};




/*
 * Closure-type Sexp.
 */


/* Evaluate a SEXP. It must be constructed by hand. It raises a Python
   exception if an error ocurred in the evaluation */
SEXP do_eval_expr(SEXP expr_R, SEXP env_R) {

  SEXP res_R = NULL;
  int error = 0;

  /* FIXME: if env_R is null, use R_BaseEnv
   * shouldn't it be R_GlobalContext (but then it throws a NULL error) ? */
  if (isNull(env_R)) {
    /* env_R = R_BaseEnv; */
    env_R = R_GlobalEnv;
    /* env_R = R_GlobalContext; */
  }

  /* Py_BEGIN_ALLOW_THREADS */

#ifdef _WIN32  
  last_sighandler = PyOS_setsig(SIGBREAK, interrupt_R);
#else
  last_sighandler = PyOS_setsig(SIGINT, interrupt_R);
#endif

  python_sighandler = last_sighandler;

  /* FIXME: evaluate expression in the given */
  interrupted = 0;
  res_R = R_tryEval(expr_R, env_R, &error);
  
  /* Py_END_ALLOW_THREADS */
#ifdef _WIN32
  PyOS_setsig(SIGBREAK, python_sighandler);   
#else 
  PyOS_setsig(SIGINT, python_sighandler);
#endif

  /* printf("interrupted: %i\n", interrupted); */
  if (error) {
    if (interrupted) {
      printf("Keyboard interrupt.\n");
      PyErr_SetNone(PyExc_KeyboardInterrupt);
      /* FIXME: handling of interruptions */
    } else {
      EmbeddedR_exception_from_errmessage();
    }
    return NULL;
  }
  return res_R;
}


/* This is the method to call when invoking an 'Sexp' */
static PyObject *
Sexp_call(PyObject *self, PyObject *args, PyObject *kwds)
{

  if (! (embeddedR_status & RPY_R_INITIALIZED)) {
    PyErr_Format(PyExc_RuntimeError, 
                 "R must be initialized before any call to R functions is possible.");
    return NULL;
  }

  if (embeddedR_status & RPY_R_BUSY) {
    PyErr_Format(PyExc_RuntimeError, "Concurrent access to R is not allowed.");
    return NULL;
  }
  embeddedR_setlock();

  SEXP call_R, c_R, res_R;
  int largs, lkwds;
  SEXP tmp_R, fun_R;
  
  largs = lkwds = 0;
  if (args)
    largs = PyObject_Length(args);
  if (kwds)
    lkwds = PyObject_Length(kwds);
  if ((largs<0) || (lkwds<0)) {
    PyErr_Format(PyExc_ValueError, "Negative number of parameters !?.");
    embeddedR_freelock();
    return NULL;
  }

  /* A SEXP with the function to call and the arguments and keywords. */
  PROTECT(c_R = call_R = allocList(largs+lkwds+1));
  SET_TYPEOF(c_R, LANGSXP);
  fun_R = RPY_SEXP((PySexpObject *)self);
  if (! fun_R) {
    PyErr_Format(PyExc_ValueError, "Underlying R function is a NULL SEXP.");
    goto fail;
  }
  SETCAR(c_R, fun_R);
  c_R = CDR(c_R);

  int arg_i;
  PyObject *tmp_obj;
  int is_PySexpObject;
  for (arg_i=0; arg_i<largs; arg_i++) {
    tmp_obj = PyTuple_GetItem(args, arg_i);
    is_PySexpObject = PyObject_TypeCheck(tmp_obj, &Sexp_Type);
    if (! is_PySexpObject) {
      PyErr_Format(PyExc_ValueError, 
                   "All parameters must be of type Sexp_Type.");
      Py_DECREF(tmp_obj);
      goto fail;
    }
    tmp_R = RPY_SEXP((PySexpObject *)tmp_obj);
    /* tmp_R = Rf_duplicate(tmp_R); */
    if (! tmp_R) {
      PyErr_Format(PyExc_ValueError, "An unnamed parameter is a NULL SEXP.");
      Py_DECREF(tmp_obj);
      goto fail;
    }
    SETCAR(c_R, tmp_R);
    c_R = CDR(c_R);
  }

  /* named args */
  PyObject *citems, *argValue, *argName;
  char *argNameString;
  unsigned int addArgName;

  if (kwds) {
    citems = PyMapping_Items(kwds);

    for (arg_i=0; arg_i<lkwds; arg_i++) {
      tmp_obj = PySequence_GetItem(citems, arg_i);
      if (! tmp_obj) {
        PyErr_Format(PyExc_ValueError, "No un-named item %i !?", arg_i);
        Py_XDECREF(tmp_obj);
        Py_XDECREF(citems);
        goto fail;
      }
      argName = PyTuple_GetItem(tmp_obj, 0);

      if (argName == Py_None) {
        addArgName = 0;
        PyErr_SetString(PyExc_TypeError, 
                        "None/missing keywords not yet supported.");
        Py_DECREF(tmp_obj);
        Py_XDECREF(citems);
        goto fail;
      } else if (PyString_Check(argName)) {
        addArgName = 1;
      } else {
        PyErr_SetString(PyExc_TypeError, "All keywords must be strings.");
        Py_DECREF(tmp_obj);
        Py_XDECREF(citems);
        goto fail;
      }
      
      argValue = PyTuple_GetItem(tmp_obj, 1);
      is_PySexpObject = PyObject_TypeCheck(argValue, &Sexp_Type);
      if (! is_PySexpObject) {
        if ( argValue == Py_None ) {
          argValue = (PyObject *)rpy_R_NilValue;
        } else {
          PyErr_Format(PyExc_ValueError, 
                       "All named parameters must be of type Sexp_Type or None");
          Py_DECREF(tmp_obj);     
          Py_XDECREF(citems);
          goto fail;
        }
      }
      tmp_R = RPY_SEXP((PySexpObject *)argValue);
      Py_DECREF(tmp_obj);
      /* SET_NAMED(tmp_R, 2); */
      /* tmp_R = Rf_duplicate(tmp_R); */
      if (! tmp_R) {
        PyErr_Format(PyExc_ValueError, "A named parameter is a NULL SEXP.");
        Py_DECREF(tmp_obj);
        Py_XDECREF(citems);
        goto fail;
      }
      SETCAR(c_R, tmp_R);
      if (addArgName) {
        argNameString = PyString_AsString(argName);
        SET_TAG(c_R, install(argNameString));
        /* printf("PyMem_Free..."); */
        /* FIXME: probably memory leak with argument names. */
        /* PyMem_Free(argNameString); */
      }
      c_R = CDR(c_R);
    }
    Py_XDECREF(citems);
  }

  /* FIXME: R_GlobalContext ? */
  PROTECT(res_R = do_eval_expr(call_R, R_GlobalEnv));
  /* PROTECT(res_R = do_eval_expr(call_R, CLOENV(fun_R))); */

/*   if (!res) { */
/*     UNPROTECT(2); */
/*     return NULL; */
/*   } */
  UNPROTECT(2);


  if (! res_R) {
    /* EmbeddedR_exception_from_errmessage(); */
    /* PyErr_Format(PyExc_RuntimeError, "Error while running R code"); */
    embeddedR_freelock();
    return NULL;
  }

  /* FIXME: standardize R outputs */
  extern void Rf_PrintWarnings(void);
  Rf_PrintWarnings(); /* show any warning messages */

  PyObject *res = (PyObject *)newPySexpObject(res_R);
  embeddedR_freelock();
  return res;
  
 fail:
  UNPROTECT(1);
  embeddedR_freelock();
  return NULL;

}

static PyTypeObject EnvironmentSexp_Type;

/* This is the method to call when invoking an 'Sexp' */
static PyObject *
Sexp_rcall(PyObject *self, PyObject *args)
{
  
  if (! (embeddedR_status & RPY_R_INITIALIZED)) {
    PyErr_Format(PyExc_RuntimeError, 
                 "R must be initialized before any call to R functions is possible.");
    return NULL;
  }

  PyObject *params, *env;

  if (! PyArg_ParseTuple(args, "OO",
                         &params, &env)) {
    return NULL;
  }

  if (! PyTuple_Check(params)) {
    PyErr_Format(PyExc_ValueError, "The first parameter must be a tuple.");
    return NULL;
  }
  if (! PyObject_IsInstance(env,
                            (PyObject*)&EnvironmentSexp_Type)) {
    PyErr_Format(PyExc_ValueError, 
                 "The second parameter must be an EnvironmentSexp_Type.");
    return NULL;
  }

  if (embeddedR_status & RPY_R_BUSY) {
    PyErr_Format(PyExc_RuntimeError, "Concurrent access to R is not allowed.");
    return NULL;
  }
  embeddedR_setlock();
    
  SEXP call_R, c_R, res_R;
  int nparams;
  SEXP tmp_R, fun_R;
  
  if (! PySequence_Check(args)) {
    PyErr_Format(PyExc_ValueError, 
                 "The one argument to the function must implement the sequence protocol.");
    embeddedR_freelock();
    return NULL;
  }
  nparams = PySequence_Length(params);
  
  /* A SEXP with the function to call and the arguments and keywords. */
  PROTECT(c_R = call_R = allocList(nparams+1));
  SET_TYPEOF(c_R, LANGSXP);
  fun_R = RPY_SEXP((PySexpObject *)self);
  if (! fun_R) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    goto fail;
  }
  SETCAR(c_R, fun_R);
  c_R = CDR(c_R);

  int arg_i;
  PyObject *tmp_obj;
  int is_PySexpObject;

  /* named args */
  PyObject *argValue, *argName;
  char *argNameString;
  unsigned int addArgName;
  Py_ssize_t itemLength;
  /* Loop through the elements in the sequence "args"
   * and build the R call.
   * Each element in the sequence is expected to be a tuple
   * of length 2 (name, value).
   */
  for (arg_i=0; arg_i<nparams; arg_i++) {
    /* printf("item: %i\n", arg_i); */
    tmp_obj = PyTuple_GetItem(params, arg_i);
    if (! tmp_obj) {
      PyErr_Format(PyExc_ValueError, "No un-named item %i !?", arg_i);
      goto fail;
    }
    itemLength = PyObject_Length(tmp_obj);
    if (itemLength != 2) {
      PyErr_Format(PyExc_ValueError, "Item %i in the sequence passed as an argument"
                   "should have two elements.", 
                   arg_i);
      goto fail;
    }
    /* First check the name for the parameter */
    argName = PyTuple_GetItem(tmp_obj, 0);
    if (argName == Py_None) {
      addArgName = 0;
    } else if (PyString_Check(argName)) {
      addArgName = 1;
    } else {
      PyErr_SetString(PyExc_TypeError, "All keywords must be strings (or None).");
      goto fail;
    }
    /* Then take care of the value associated with that name. */
    argValue = PyTuple_GetItem(tmp_obj, 1);
    is_PySexpObject = PyObject_TypeCheck(argValue, &Sexp_Type);
    if (! is_PySexpObject) {
      PyErr_Format(PyExc_ValueError, 
                   "All parameters must be of type Sexp_Type.");
      goto fail;
    }
    tmp_R = RPY_SEXP((PySexpObject *)argValue);
    /* tmp_R = Rf_duplicate(tmp_R); */
    if (! tmp_R) {
      PyErr_Format(PyExc_ValueError, "NULL SEXP.");
      goto fail;
    }
    /* Put the value into the R call being built
    * (adding the name of the argument if relevant)
    */
    SETCAR(c_R, tmp_R);
    if (addArgName) {
      argNameString = PyString_AsString(argName);
      SET_TAG(c_R, install(argNameString));
    }
    c_R = CDR(c_R);
  }

  /* Py_BEGIN_ALLOW_THREADS */
  /* FIXME: R_GlobalContext ? */
  PROTECT(res_R = do_eval_expr(call_R, RPY_SEXP((PySexpObject *)env)));
  /* PROTECT(res_R = do_eval_expr(call_R, CLOENV(fun_R))); */

/*   if (!res) { */
/*     UNPROTECT(2); */
/*     return NULL; */
/*   } */
  UNPROTECT(2);
  /* Py_END_ALLOW_THREADS */

  if (! res_R) {
    /* EmbeddedR_exception_from_errmessage(); */
    /* PyErr_Format(PyExc_RuntimeError, "Error while running R code"); */
    embeddedR_freelock();
    return NULL;
  }

  /* FIXME: standardize R outputs */
  extern void Rf_PrintWarnings(void);
  Rf_PrintWarnings(); /* show any warning messages */

  PyObject *res = (PyObject *)newPySexpObject(res_R);
  embeddedR_freelock();
  return res;
  
 fail:
  UNPROTECT(1);
  embeddedR_freelock();
  return NULL;

}

PyDoc_STRVAR(SexpClosure_rcall_doc,
             "Call using the items of the object passed as Python \n"
             "argument to build the list of parameters passed to the \n"
             "R function.\n\n"
             ":param args: tuple of two-elements items"
             " or class::`rlike.container.ArgsDict`\n\n"
             ":rtype: instance of type or subtype :class:`rpy2.rinterface.Sexp`\n");

static PySexpObject*
Sexp_closureEnv(PyObject *self)
{
  SEXP closureEnv, sexp;
  sexp = RPY_SEXP((PySexpObject*)self);
  if (! sexp) {
      PyErr_Format(PyExc_ValueError, "NULL SEXP.");
      return NULL;
  }
  if (embeddedR_status & RPY_R_BUSY) {
    PyErr_Format(PyExc_RuntimeError, "Concurrent access to R is not allowed.");
    return NULL;
  }
  embeddedR_setlock();
  closureEnv = CLOENV(sexp);
  embeddedR_freelock();
  return newPySexpObject(closureEnv);
}
PyDoc_STRVAR(Sexp_closureEnv_doc,
             "\n\
Returns the environment the object is defined in.\n\
This corresponds to the C-level function CLOENV(SEXP).\n\
\n\
:rtype: :class:`rpy2.rinterface.SexpEnvironment`\n");

static PyMethodDef ClosureSexp_methods[] = {
  {"closureEnv", (PyCFunction)Sexp_closureEnv, METH_NOARGS,
   Sexp_closureEnv_doc},
  {"rcall", (PyCFunction)Sexp_rcall, METH_VARARGS,
   SexpClosure_rcall_doc},
  {NULL, NULL}          /* sentinel */
};

PyDoc_STRVAR(ClosureSexp_Type_doc,
"A R object that is a closure, that is a function. \
In R a function is defined within an enclosing \
environment, thus the name closure. \
In Python, 'nested scopes' could be the closest similar thing.\
\n\
The closure can be accessed with the method 'closureEnv'.\
");

static int
ClosureSexp_init(PyObject *self, PyObject *args, PyObject *kwds);


static PyTypeObject ClosureSexp_Type = {
        /* The ob_type field must be initialized in the module init function
         * to be portable to Windows without using C++. */
        PyObject_HEAD_INIT(NULL)
        0,                      /*ob_size*/
        "rpy2.rinterface.SexpClosure",       /*tp_name*/
        sizeof(PySexpObject),   /*tp_basicsize*/
        0,                      /*tp_itemsize*/
        /* methods */
        0, /*tp_dealloc*/
        0,                      /*tp_print*/
        0,                      /*tp_getattr*/
        0,                      /*tp_setattr*/
        0,                      /*tp_compare*/
        0,                      /*tp_repr*/
        0,                      /*tp_as_number*/
        0,                      /*tp_as_sequence*/
        0,                      /*tp_as_mapping*/
        0,                      /*tp_hash*/
        Sexp_call,              /*tp_call*/
        0,                      /*tp_str*/
        0,                      /*tp_getattro*/
        0,                      /*tp_setattro*/
        0,                      /*tp_as_buffer*/
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE,     /*tp_flags*/
        ClosureSexp_Type_doc,                      /*tp_doc*/
        0,                      /*tp_traverse*/
        0,                      /*tp_clear*/
        0,                      /*tp_richcompare*/
        0,                      /*tp_weaklistoffset*/
        0,                      /*tp_iter*/
        0,                      /*tp_iternext*/
        ClosureSexp_methods,           /*tp_methods*/
        0,                      /*tp_members*/
        0,                      /*tp_getset*/
        &Sexp_Type,             /*tp_base*/
        0,                      /*tp_dict*/
        0,                      /*tp_descr_get*/
        0,                      /*tp_descr_set*/
        0,                      /*tp_dictoffset*/
        (initproc)ClosureSexp_init,                      /*tp_init*/
        0,                      /*tp_alloc*/
        0,                      /*tp_new*/
        0,                      /*tp_free*/
        0                      /*tp_is_gc*/
};


static int
ClosureSexp_init(PyObject *self, PyObject *args, PyObject *kwds)
{
  PyObject *object;
  PyObject *copy;
  static char *kwlist[] = {"sexpclos", "copy", NULL};
  /* FIXME: handle the copy argument */
  if (! PyArg_ParseTupleAndKeywords(args, kwds, "O|O!", 
                                    kwlist,
                                    &object,
                                    &PyBool_Type, &copy)) {
    return -1;
  }
  if (PyObject_IsInstance(object, 
                          (PyObject*)&ClosureSexp_Type)) {
    /* call parent's constructor */
    if (Sexp_init(self, args, NULL) == -1) {
      PyErr_Format(PyExc_RuntimeError, "Error initializing instance.");
      return -1;
    }
  } else {
    PyErr_Format(PyExc_ValueError, "Cannot instantiate from this type.");
    return -1;
  }
  return 0;
}




/* len(x) */
static Py_ssize_t VectorSexp_len(PyObject *object)
{
  if (embeddedR_status & RPY_R_BUSY) {
    PyErr_Format(PyExc_RuntimeError, "Concurrent access to R is not allowed.");
    return -1;
  }
  embeddedR_setlock();

  Py_ssize_t len;
  /* FIXME: sanity checks. */
  SEXP sexp = RPY_SEXP((PySexpObject *)object);
  if (! sexp) {
      PyErr_Format(PyExc_ValueError, "NULL SEXP.");
      return -1;
  }
  len = (Py_ssize_t)GET_LENGTH(sexp);

  embeddedR_freelock();
  return len;
}

/* a[i] */
static PyObject *
VectorSexp_item(PyObject *object, Py_ssize_t i)
{
  PyObject* res;
  R_len_t i_R, len_R;

  if (embeddedR_status & RPY_R_BUSY) {
    PyErr_Format(PyExc_RuntimeError, "Concurrent access to R is not allowed.");
    return NULL;
  }
  embeddedR_setlock();
  SEXP *sexp = &(RPY_SEXP((PySexpObject *)object));

  if (! sexp) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    embeddedR_freelock();
    return NULL;
  }

  /* On 64bits, Python is apparently able to use larger integer
   * than R for indexing. */
  if (i >= R_LEN_T_MAX) {
    PyErr_Format(PyExc_IndexError, "Index value exceeds what R can handle.");
    embeddedR_freelock();
    res = NULL;
    return res;
  }

  len_R = GET_LENGTH(*sexp);
  
  if (i < 0) {
    i = len_R - i;
  }

  if (i < 0) {
    PyErr_Format(PyExc_IndexError, 
                 "Mysterious error: likely an integer overflow.");
    res = NULL;
    embeddedR_freelock();
    return res;
  }
  if ((i >= GET_LENGTH(*sexp))) {
    PyErr_Format(PyExc_IndexError, "Index out of range.");
    res = NULL;
  }
  else {
    double vd;
    int vi;
    Rcomplex vc;
    const char *vs;
    SEXP tmp, sexp_item; /* needed by LANGSXP */
    i_R = (R_len_t)i;
    switch (TYPEOF(*sexp)) {
    case REALSXP:
      vd = (NUMERIC_POINTER(*sexp))[i_R];
      res = PyFloat_FromDouble(vd);
      break;
    case INTSXP:
      vi = INTEGER_POINTER(*sexp)[i_R];
      res = PyInt_FromLong((long)vi);
      break;
    case LGLSXP:
      vi = LOGICAL_POINTER(*sexp)[i_R];
      RPY_PY_FROM_RBOOL(res, vi);
      break;
    case CPLXSXP:
      vc = COMPLEX_POINTER(*sexp)[i_R];
      res = PyComplex_FromDoubles(vc.r, vc.i);
      break;
    case STRSXP:
      vs = translateChar(STRING_ELT(*sexp, i_R));
      res = PyString_FromString(vs);
      break;
/*     case CHARSXP: */
      /*       FIXME: implement handling of single char (if possible ?) */
/*       vs = (CHAR(*sexp)[i_R]); */
/*       res = PyString_FromStringAndSize(vs, 1); */
    case VECSXP:
    case EXPRSXP:
      sexp_item = VECTOR_ELT(*sexp, i_R);
      res = (PyObject *)newPySexpObject(sexp_item);
      break;
    case LISTSXP:
      tmp = nthcdr(*sexp, i_R);
      sexp_item = allocVector(LISTSXP, 1);
      SETCAR(sexp_item, CAR(tmp));
      SET_TAG(sexp_item, TAG(tmp));
      res = (PyObject *)newPySexpObject(sexp_item);
      break;      
    case LANGSXP:
      tmp = nthcdr(*sexp, i_R);
      sexp_item = allocVector(LANGSXP, 1);
      SETCAR(sexp_item, CAR(tmp));
      SET_TAG(sexp_item, TAG(tmp));
      res = (PyObject *)newPySexpObject(sexp_item);
      break;
    default:
      PyErr_Format(PyExc_ValueError, "Cannot handle type %d", 
                   TYPEOF(*sexp));
      res = NULL;
      break;
    }
  }
  embeddedR_freelock();
  return res;
}

/* a[i] = val */
static int
VectorSexp_ass_item(PyObject *object, Py_ssize_t i, PyObject *val)
{
  R_len_t i_R, len_R;

  /* Check for 64 bits platforms */
  if (i >= R_LEN_T_MAX) {
    PyErr_Format(PyExc_IndexError, "Index value exceeds what R can handle.");
    return -1;
  }

  SEXP *sexp = &(RPY_SEXP((PySexpObject *)object));
  len_R = GET_LENGTH(*sexp);
  
  if (i < 0) {
    i = len_R - i;
  }

  if (i >= len_R) {
    PyErr_Format(PyExc_IndexError, "Index out of range.");
    return -1;
  }

  if (! sexp) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return -1;
  }

  int is_PySexpObject = PyObject_TypeCheck(val, &Sexp_Type);
  if (! is_PySexpObject) {
    PyErr_Format(PyExc_ValueError, "Any new value must be of "
                 "type 'Sexp_Type'.");
    return -1;
  }
  SEXP *sexp_val = &(RPY_SEXP((PySexpObject *)val));
  if (! sexp_val) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return -1;
  }

  if (TYPEOF(*sexp_val) != TYPEOF(*sexp)) {
    PyErr_Format(PyExc_ValueError, "The type for the new value cannot be different.");
    return -1;
  }

  if ((TYPEOF(*sexp_val) != VECSXP) & (LENGTH(*sexp_val) != 1)) {
    PyErr_Format(PyExc_ValueError, "The new value must be of length 1.");
    return -1;
  }

  SEXP sexp_copy;
  i_R = (R_len_t)i;
  switch (TYPEOF(*sexp)) {
  case REALSXP:
    (NUMERIC_POINTER(*sexp))[i_R] = (NUMERIC_POINTER(*sexp_val))[0];
    break;
  case INTSXP:
    (INTEGER_POINTER(*sexp))[i_R] = (INTEGER_POINTER(*sexp_val))[0];
    break;
  case LGLSXP:
    (LOGICAL_POINTER(*sexp))[i_R] = (LOGICAL_POINTER(*sexp_val))[0];
    break;
  case CPLXSXP:
    (COMPLEX_POINTER(*sexp))[i_R] = (COMPLEX_POINTER(*sexp_val))[0];
    break;
  case STRSXP:
    SET_STRING_ELT(*sexp, i_R, STRING_ELT(*sexp_val, 0));
    break;
  case VECSXP:
    PROTECT(sexp_copy = Rf_duplicate(*sexp_val));
    SET_VECTOR_ELT(*sexp, i_R, sexp_copy);
    UNPROTECT(1);
    break;
  default:
    PyErr_Format(PyExc_ValueError, "cannot handle type %d", 
                 TYPEOF(*sexp));
    return -1;
    break;
  }
  return 0;
}

static PySequenceMethods VectorSexp_sequenceMethods = {
  (lenfunc)VectorSexp_len,              /* sq_length */
  0,                              /* sq_concat */
  0,                              /* sq_repeat */
  (ssizeargfunc)VectorSexp_item,        /* sq_item */
  0, /*(ssizessizeargfunc)VectorSexp_slice,  sq_slice */
  (ssizeobjargproc)VectorSexp_ass_item,   /* sq_ass_item */
  0,                              /* sq_ass_slice */
  0,                              /* sq_contains */
  0,                              /* sq_inplace_concat */
  0                               /* sq_inplace_repeat */
};


static PyGetSetDef VectorSexp_getsets[] = {
  {"__array_struct__", 
   (getter)array_struct_get,
   (setter)0,
   "Array protocol: struct"},
  {NULL, NULL, NULL, NULL}          /* sentinel */
};


PyDoc_STRVAR(VectorSexp_Type_doc,
             "R object that is a vector."
             " R vectors start their indexing at one,"
             " while Python lists or arrays start indexing"
             " at zero.\n"
             "In the hope to avoid confusion, the indexing"
             " in Python (e.g., :meth:`__getitem__` / :meth:`__setitem__`)"
             " starts at zero.");

static int
VectorSexp_init(PyObject *self, PyObject *args, PyObject *kwds);

static PyTypeObject VectorSexp_Type = {
        /* The ob_type field must be initialized in the module init function
         * to be portable to Windows without using C++. */
        PyObject_HEAD_INIT(NULL)
        0,                      /*ob_size*/
        "rpy2.rinterface.SexpVector",        /*tp_name*/
        sizeof(PySexpObject),   /*tp_basicsize*/
        0,                      /*tp_itemsize*/
        /* methods */
        0, /*tp_dealloc*/
        0,                      /*tp_print*/
        0,                      /*tp_getattr*/
        0,                      /*tp_setattr*/
        0,                      /*tp_compare*/
        0,                      /*tp_repr*/
        0,                      /*tp_as_number*/
        &VectorSexp_sequenceMethods,                    /*tp_as_sequence*/
        0,                      /*tp_as_mapping*/
        0,                      /*tp_hash*/
        0,              /*tp_call*/
        0,              /*tp_str*/
        0,                      /*tp_getattro*/
        0,                      /*tp_setattro*/
        0,                      /*tp_as_buffer*/
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE,     /*tp_flags*/
        VectorSexp_Type_doc,                      /*tp_doc*/
        0,                      /*tp_traverse*/
        0,                      /*tp_clear*/
        0,                      /*tp_richcompare*/
        0,                      /*tp_weaklistoffset*/
        0,                      /*tp_iter*/
        0,                      /*tp_iternext*/
        0,           /*tp_methods*/
        0,                      /*tp_members*/
        VectorSexp_getsets,            /*tp_getset*/
        &Sexp_Type,             /*tp_base*/
        0,                      /*tp_dict*/
        0,                      /*tp_descr_get*/
        0,                      /*tp_descr_set*/
        0,                      /*tp_dictoffset*/
        (initproc)VectorSexp_init,                      /*tp_init*/
        0,                      /*tp_alloc*/
        0,               /*tp_new*/
        0,                      /*tp_free*/
        0                      /*tp_is_gc*/
};
 

static int
VectorSexp_init(PyObject *self, PyObject *args, PyObject *kwds)
{
#ifdef RPY_VERBOSE
  printf("%p: VectorSexp initializing...\n", self);
#endif 

  if (! (embeddedR_status & RPY_R_INITIALIZED)) {
    PyErr_Format(PyExc_RuntimeError, 
                 "R must be initialized before any instance can be created.");
    return -1;
  }

  PyObject *object;
  int sexptype = -1;
  PyObject *copy = Py_False;
  static char *kwlist[] = {"sexpvector", "sexptype", "copy", NULL};


  /* FIXME: handle the copy argument */
  if (! PyArg_ParseTupleAndKeywords(args, kwds, "O|iO!", 
                                    kwlist,
                                    &object,
                                    &sexptype,
                                    &PyBool_Type, &copy)) {
    return -1;
  }

  if (embeddedR_status & RPY_R_BUSY) {
    PyErr_Format(PyExc_RuntimeError, "Concurrent access to R is not allowed.");
    return -1;
  }
  embeddedR_setlock();

  if (PyObject_IsInstance(object, 
                          (PyObject*)&VectorSexp_Type)) {
    /* call parent's constructor */
      if (Sexp_init(self, args, NULL) == -1) {
      /* PyErr_Format(PyExc_RuntimeError, "Error initializing instance."); */
      embeddedR_freelock();
      return -1;
    }
  } else if (PySequence_Check(object)) {
    if ((sexptype < 0) || (sexptype > RPY_MAX_VALIDSEXTYPE) || 
        (! validSexpType[sexptype])) {
      PyErr_Format(PyExc_ValueError, "Invalid SEXP type.");
      embeddedR_freelock();
      return -1;
    }
    /* FIXME: implemement automagic type ?
     *(RPy has something)... or leave it to extensions ? 
     */

    SEXP sexp = newSEXP(object, sexptype);
    if (sexp == NULL) {
      /* newSEXP returning NULL will also have raised an exception
       * (not-so-clear design :/ )
       */
      embeddedR_freelock();
      return -1;
    }
    RPY_SEXP((PySexpObject *)self) = sexp;
    #ifdef RPY_DEBUG_OBJECTINIT
    printf("  SEXP vector is %p.\n", RPY_SEXP((PySexpObject *)self));
    #endif
    /* SET_NAMED(RPY_SEXP((PySexpObject *)self), 2); */
  } else {
    PyErr_Format(PyExc_ValueError, "Invalid sexpvector.");
    embeddedR_freelock();
    return -1;
  }

#ifdef RPY_VERBOSE
  printf("done (VectorSexp_init).\n");
#endif 

  embeddedR_freelock();
  return 0;
}


/* --- */
static PyObject*
EnvironmentSexp_findVar(PyObject *self, PyObject *args, PyObject *kwds)
{
  char *name;
  SEXP res_R = NULL;
  PySexpObject *res = NULL;
  PyObject *wantFun = Py_False;

  static char *kwlist[] = {"name", "wantfun", NULL};
 
  if (!PyArg_ParseTupleAndKeywords(args, kwds, "s|O!",
                                   kwlist,
                                   &name, 
                                   &PyBool_Type, &wantFun)) { 
    return NULL; 
  }

  if (embeddedR_status & RPY_R_BUSY) {
    PyErr_Format(PyExc_RuntimeError, "Concurrent access to R is not allowed.");
    return NULL;
  }
  embeddedR_setlock();

  const SEXP rho_R = RPY_SEXP((PySexpObject *)self);
  if (! rho_R) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    embeddedR_freelock();
    return NULL;
  }

  if (strlen(name) == 0) {
    PyErr_Format(PyExc_ValueError, "Invalid name.");
    embeddedR_freelock();
    return NULL;
  }

  if (rho_R == R_EmptyEnv) {
    PyErr_Format(PyExc_LookupError, "Fatal error: R_EmptyEnv.");
    return NULL;
  }

  if (PyObject_IsTrue(wantFun)) {
    res_R = rpy_findFun(install(name), rho_R);
  } else {
    res_R = findVar(install(name), rho_R);
  }

  if (res_R != R_UnboundValue) {
    /* FIXME rpy_only */
    res = newPySexpObject(res_R);
  } else {
    PyErr_Format(PyExc_LookupError, "'%s' not found", name);
    res = NULL;
  }
  embeddedR_freelock();
  return (PyObject *)res;
}
PyDoc_STRVAR(EnvironmentSexp_findVar_doc,
             "Find a name/symbol in the environment, following the chain of enclosing\n"
             "environments until either the topmost environment is reached or the name\n"
             "is found, and returned the associated object. \n"
             "The optional parameter `wantfun` indicates whether functions should be\n"
             "returned or not.\n"
             ":rtype: instance of type of subtype :class:`rpy2.rinterface.Sexp`");

static PyObject*
EnvironmentSexp_frame(PyObject *self)
{
  if (! (embeddedR_status & RPY_R_INITIALIZED)) {
    PyErr_Format(PyExc_RuntimeError, 
                 "R must be initialized before environments can be accessed.");
    return NULL;
  }
  SEXP res_R = NULL;
  PySexpObject *res;

  if (embeddedR_status & RPY_R_BUSY) {
    PyErr_Format(PyExc_RuntimeError, "Concurrent access to R is not allowed.");
    return NULL;
  }
  embeddedR_setlock();

  res_R = FRAME(RPY_SEXP((PySexpObject *)self));
  res = newPySexpObject(res_R);
  return (PyObject *)res;
}
PyDoc_STRVAR(EnvironmentSexp_frame_doc,
             "Return the frame the environment is in.");

static PyObject*
EnvironmentSexp_enclos(PyObject *self)
{
  if (! (embeddedR_status & RPY_R_INITIALIZED)) {
    PyErr_Format(PyExc_RuntimeError, 
                 "R must be initialized before environments can be accessed.");
    return NULL;
  }
  if (embeddedR_status & RPY_R_BUSY) {
    PyErr_Format(PyExc_RuntimeError, "Concurrent access to R is not allowed.");
    return NULL;
  }
  embeddedR_setlock();

  SEXP res_R = NULL;
  PySexpObject *res;
  res_R = ENCLOS(RPY_SEXP((PySexpObject *)self));
  res = newPySexpObject(res_R);
  embeddedR_freelock();
  return (PyObject *)res;
}
PyDoc_STRVAR(EnvironmentSexp_enclos_doc,
             "Return the enclosure the environment is in.");

static PyMethodDef EnvironmentSexp_methods[] = {
  {"get", (PyCFunction)EnvironmentSexp_findVar, METH_VARARGS | METH_KEYWORDS,
  EnvironmentSexp_findVar_doc},
  {"frame", (PyCFunction)EnvironmentSexp_frame, METH_NOARGS,
  EnvironmentSexp_frame_doc},
  {"enclos", (PyCFunction)EnvironmentSexp_enclos, METH_NOARGS,
  EnvironmentSexp_enclos_doc},
  {NULL, NULL}          /* sentinel */
};


static PySexpObject*
EnvironmentSexp_subscript(PyObject *self, PyObject *key)
{
  char *name;
  SEXP res_R = NULL;

  if (!PyString_Check(key)) {
    PyErr_Format(PyExc_ValueError, "Keys must be string objects.");
    return NULL;
  }

  name = PyString_AsString(key);

  if (strlen(name) == 0) {
    PyErr_Format(PyExc_KeyError, name);
    return NULL;
  }

  if (embeddedR_status & RPY_R_BUSY) {
    PyErr_Format(PyExc_RuntimeError, "Concurrent access to R is not allowed.");
    return NULL;
  }
  embeddedR_setlock();

  SEXP rho_R = RPY_SEXP((PySexpObject *)self);
  if (! rho_R) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    embeddedR_freelock();
    return NULL;
  }
  res_R = findVarInFrame(rho_R, install(name));

  if (res_R != R_UnboundValue) {
    embeddedR_freelock();
    return newPySexpObject(res_R);
  }
  PyErr_Format(PyExc_LookupError, "'%s' not found", name);
  embeddedR_freelock();
  return NULL;
}


static int
EnvironmentSexp_ass_subscript(PyObject *self, PyObject *key, PyObject *value)
{
  char *name;

  if (!PyString_Check(key)) {
    PyErr_Format(PyExc_ValueError, "Keys must be string objects.");
    return -1;
  }

  int is_PySexpObject = PyObject_TypeCheck(value, &Sexp_Type);
  if (! is_PySexpObject) {
    PyErr_Format(PyExc_ValueError, 
                 "All parameters must be of type Sexp_Type.");
    /* PyDecRef(value); */
    return -1;
  }

  name = PyString_AsString(key);

  if (embeddedR_status & RPY_R_BUSY) {
    PyErr_Format(PyExc_RuntimeError, "Concurrent access to R is not allowed.");
    return -1;
  }
  embeddedR_setlock();

  SEXP rho_R = RPY_SEXP((PySexpObject *)self);
  if (! rho_R) {
    PyErr_Format(PyExc_ValueError, "The environment has NULL SEXP.");
    embeddedR_freelock();
    return -1;
  }

  SEXP sexp_copy;
  SEXP sexp = RPY_SEXP((PySexpObject *)value);
  if (! sexp) {
    PyErr_Format(PyExc_ValueError, "The value has NULL SEXP.");
    embeddedR_freelock();
    return -1;
  }
  SEXP sym = Rf_install(name);
  PROTECT(sexp_copy = Rf_duplicate(sexp));
  Rf_defineVar(sym, sexp_copy, rho_R);
  UNPROTECT(1);
  embeddedR_freelock();
  return 0;
}

static Py_ssize_t EnvironmentSexp_length(PyObject *self) 
{
  if (embeddedR_status & RPY_R_BUSY) {
    PyErr_Format(PyExc_RuntimeError, "Concurrent access to R is not allowed.");
    return -1;
  }
  embeddedR_setlock();

  SEXP rho_R = RPY_SEXP((PySexpObject *)self);
  if (! rho_R) {
    PyErr_Format(PyExc_ValueError, "The environment has NULL SEXP.");
    embeddedR_freelock();
    return -1;
  }
  SEXP symbols;
  PROTECT(symbols = R_lsInternal(rho_R, TRUE));
  Py_ssize_t len = (Py_ssize_t)GET_LENGTH(symbols);
  UNPROTECT(1);
  embeddedR_freelock();
  return len;
}

static PyMappingMethods EnvironmentSexp_mappingMethods = {
  (lenfunc)EnvironmentSexp_length, /* mp_length */
  (binaryfunc)EnvironmentSexp_subscript, /* mp_subscript */
  (objobjargproc)EnvironmentSexp_ass_subscript  /* mp_ass_subscript */
};

static PyObject* 
EnvironmentSexp_iter(PyObject *sexpEnvironment)
{
  if (embeddedR_status & RPY_R_BUSY) {
    PyErr_Format(PyExc_RuntimeError, "Concurrent access to R is not allowed.");
    return NULL;
  }
  embeddedR_setlock();

  SEXP rho_R = RPY_SEXP((PySexpObject *)sexpEnvironment);

  if (! rho_R) {
    PyErr_Format(PyExc_ValueError, "The environment has NULL SEXP.");
    embeddedR_freelock();
    return NULL;
  }
  SEXP symbols;
  PROTECT(symbols = R_lsInternal(rho_R, TRUE));
  PySexpObject *seq = newPySexpObject(symbols);
  Py_INCREF(seq);
  UNPROTECT(1);
 
  PyObject *it = PyObject_GetIter((PyObject *)seq);
  Py_DECREF(seq);
  embeddedR_freelock();
  return it;
}

PyDoc_STRVAR(EnvironmentSexp_Type_doc,
"R object that is an environment.\n"
"R environments can be seen as similar to Python\n"
"dictionnaries, with the following twists:\n"
"\n"
"- an environment can be a list of frames to sequentially\n"
"search into\n"
"\n"
"- the search can be recursively propagated to the enclosing\n"
"environment whenever the key is not found (in that respect\n"
"they can be seen as scopings).\n"
"\n"
"The subsetting operator \"[\" is made to match Python's\n"
"behavior, that is the enclosing environments are not\n"
"inspected upon absence of a given key.\n");


static int
EnvironmentSexp_init(PyObject *self, PyObject *args, PyObject *kwds);

static PyTypeObject EnvironmentSexp_Type = {
        /* The ob_type field must be initialized in the module init function
         * to be portable to Windows without using C++. */
        PyObject_HEAD_INIT(NULL)
        0,                      /*ob_size*/
        "rpy2.rinterface.SexpEnvironment",   /*tp_name*/
        sizeof(PySexpObject),   /*tp_basicsize*/
        0,                      /*tp_itemsize*/
        /* methods */
        0, /*tp_dealloc*/
        0,                      /*tp_print*/
        0,                      /*tp_getattr*/
        0,                      /*tp_setattr*/
        0,                      /*tp_compare*/
        0,                      /*tp_repr*/
        0,                      /*tp_as_number*/
        0,                      /*tp_as_sequence*/
        &EnvironmentSexp_mappingMethods,/*tp_as_mapping*/
        0,                      /*tp_hash*/
        0,              /*tp_call*/
        0,                      /*tp_str*/
        0,                      /*tp_getattro*/
        0,                      /*tp_setattro*/
        0,                      /*tp_as_buffer*/
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE,     /*tp_flags*/
        EnvironmentSexp_Type_doc,                      /*tp_doc*/
        0,                      /*tp_traverse*/
        0,                      /*tp_clear*/
        0,                      /*tp_richcompare*/
        0,                      /*tp_weaklistoffset*/
        EnvironmentSexp_iter,                      /*tp_iter*/
        0,                      /*tp_iternext*/
        EnvironmentSexp_methods,           /*tp_methods*/
        0,                      /*tp_members*/
        0,                      /*tp_getset*/
        &Sexp_Type,             /*tp_base*/
        0,                      /*tp_dict*/
        0,                      /*tp_descr_get*/
        0,                      /*tp_descr_set*/
        0,                      /*tp_dictoffset*/
        (initproc)EnvironmentSexp_init,                      /*tp_init*/
        0,                      /*tp_alloc*/
        /* FIXME: add new method */
        0,                      /*tp_new*/
        0,                      /*tp_free*/
        0                      /*tp_is_gc*/
};

static int
EnvironmentSexp_init(PyObject *self, PyObject *args, PyObject *kwds)
{
  PyObject *object;
  PyObject *copy = Py_False;
  static char *kwlist[] = {"sexpenv", "copy", NULL};
  /* FIXME: handle the copy argument */
  if (! PyArg_ParseTupleAndKeywords(args, kwds, "O|O!", 
                                    kwlist,
                                    &object,
                                    &PyBool_Type, &copy)) {
    return -1;
  }

  if (embeddedR_status & RPY_R_BUSY) {
    PyErr_Format(PyExc_RuntimeError, "Concurrent access to R is not allowed.");
    return -1;
  }
  embeddedR_setlock();

  if (PyObject_IsInstance(object, 
                          (PyObject*)&EnvironmentSexp_Type)) {
    /* call parent's constructor */
    if (Sexp_init(self, args, NULL) == -1) {
      PyErr_Format(PyExc_RuntimeError, "Error initializing instance.");
      embeddedR_freelock();
      return -1;
    }
  } else {
    PyErr_Format(PyExc_ValueError, "Cannot instantiate from this type.");
    embeddedR_freelock();
    return -1;
  }
  embeddedR_freelock();
  return 0;
}


/* FIXME: write more doc */
PyDoc_STRVAR(S4Sexp_Type_doc,
"R object that is an 'S4 object'.\
Attributes can be accessed using the method 'do_slot'.\
");


static PyTypeObject S4Sexp_Type = {
        /* The ob_type field must be initialized in the module init function
         * to be portable to Windows without using C++. */
        PyObject_HEAD_INIT(NULL)
        0,                      /*ob_size*/
        "rpy2.rinterface.SexpS4",    /*tp_name*/
        sizeof(PySexpObject),   /*tp_basicsize*/
        0,                      /*tp_itemsize*/
        /* methods */
        0, /*tp_dealloc*/
        0,                      /*tp_print*/
        0,                      /*tp_getattr*/
        0,                      /*tp_setattr*/
        0,                      /*tp_compare*/
        0,                      /*tp_repr*/
        0,                      /*tp_as_number*/
        0,                      /*tp_as_sequence*/
        0,                      /*tp_as_mapping*/
        0,                      /*tp_hash*/
        0,              /*tp_call*/
        0,                      /*tp_str*/
        0,                      /*tp_getattro*/
        0,                      /*tp_setattro*/
        0,                      /*tp_as_buffer*/
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE,     /*tp_flags*/
        S4Sexp_Type_doc,                      /*tp_doc*/
        0,                      /*tp_traverse*/
        0,                      /*tp_clear*/
        0,                      /*tp_richcompare*/
        0,                      /*tp_weaklistoffset*/
        0,                      /*tp_iter*/
        0,                      /*tp_iternext*/
        0,           /*tp_methods*/
        0,                      /*tp_members*/
        0,                      /*tp_getset*/
        &Sexp_Type,             /*tp_base*/
        0,                      /*tp_dict*/
        0,                      /*tp_descr_get*/
        0,                      /*tp_descr_set*/
        0,                      /*tp_dictoffset*/
        0,                      /*tp_init*/
        0,                      /*tp_alloc*/
        /*FIXME: add new method */
        0,                     /*tp_new*/
        0,                      /*tp_free*/
        0                      /*tp_is_gc*/
};

/* FIXME: write more doc */
PyDoc_STRVAR(LangSexp_Type_doc,
"Language object.");


static PyTypeObject LangSexp_Type = {
        /* The ob_type field must be initialized in the module init function
         * to be portable to Windows without using C++. */
        PyObject_HEAD_INIT(NULL)
        0,                      /*ob_size*/
        "rpy2.rinterface.SexpLang",  /*tp_name*/
        sizeof(PySexpObject),   /*tp_basicsize*/
        0,                      /*tp_itemsize*/
        /* methods */
        0, /*tp_dealloc*/
        0,                      /*tp_print*/
        0,                      /*tp_getattr*/
        0,                      /*tp_setattr*/
        0,                      /*tp_compare*/
        0,                      /*tp_repr*/
        0,                      /*tp_as_number*/
        0,                      /*tp_as_sequence*/
        0,                      /*tp_as_mapping*/
        0,                      /*tp_hash*/
        0,              /*tp_call*/
        0,                      /*tp_str*/
        0,                      /*tp_getattro*/
        0,                      /*tp_setattro*/
        0,                      /*tp_as_buffer*/
        Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE,     /*tp_flags*/
        LangSexp_Type_doc,                      /*tp_doc*/
        0,                      /*tp_traverse*/
        0,                      /*tp_clear*/
        0,                      /*tp_richcompare*/
        0,                      /*tp_weaklistoffset*/
        0,                      /*tp_iter*/
        0,                      /*tp_iternext*/
        0,           /*tp_methods*/
        0,                      /*tp_members*/
        0,                      /*tp_getset*/
        &Sexp_Type,             /*tp_base*/
        0,                      /*tp_dict*/
        0,                      /*tp_descr_get*/
        0,                      /*tp_descr_set*/
        0,                      /*tp_dictoffset*/
        0,                      /*tp_init*/
        0,                      /*tp_alloc*/
        /* FIXME: add new method */
        0,                      /*tp_new*/
        0,                      /*tp_free*/
        0                      /*tp_is_gc*/
};


/* --- Create a SEXP object --- */
static PySexpObject*
newPySexpObject(const SEXP sexp)
{
  PySexpObject *object;
  SEXP sexp_ok, env_R;

  if (! sexp) {
    PyErr_Format(PyExc_ValueError, "NULL SEXP.");
    return NULL;
  }
  /* FIXME: let the possibility to manipulate un-evaluated promises ? */
  if (TYPEOF(sexp) == PROMSXP) {
    env_R = PRENV(sexp);
    sexp_ok = eval(sexp, env_R);
#ifdef RPY_DEBUG_PROMISE
    printf("  evaluating promise %p into %p.\n", sexp, sexp_ok);
#endif 
  } 
  else {
    sexp_ok = sexp;
  }
  if (sexp_ok) {
    R_PreserveObject(sexp_ok);
#ifdef RPY_DEBUG_PRESERVE
    preserved_robjects += 1;
    printf("  PRESERVE -- R_PreserveObject -- %p -- %i\n", 
           sexp_ok, preserved_robjects);
#endif 
  }

  switch (TYPEOF(sexp_ok)) {
  case CLOSXP:
  case BUILTINSXP:
  case SPECIALSXP:
    object  = (PySexpObject *)Sexp_new(&ClosureSexp_Type, Py_None, Py_None);
    break;
    /*FIXME: BUILTINSXP and SPECIALSXP really like CLOSXP ? */
  case REALSXP: 
  case INTSXP: 
  case LGLSXP:
  case CPLXSXP:
  case VECSXP:
  case LISTSXP:
  case LANGSXP:
  case EXPRSXP:
  case STRSXP:
  case RAWSXP:
    object = (PySexpObject *)Sexp_new(&VectorSexp_Type, Py_None, Py_None);
    break;
  case ENVSXP:
    object = (PySexpObject *)Sexp_new(&EnvironmentSexp_Type, Py_None, Py_None);
    break;
  case S4SXP:
    object = (PySexpObject *)Sexp_new(&S4Sexp_Type, Py_None, Py_None);
    break;
  default:
    object = (PySexpObject *)Sexp_new(&Sexp_Type, Py_None, Py_None);
    break;
  }
  if (!object) {
#ifdef RPY_DEBUG_PRESERVE
    printf("  PRESERVE -- Sexp_clear: R_ReleaseObject -- %p ", 
           sexp_ok);
    preserved_robjects -= 1;
    printf("-- %i\n", preserved_robjects);
#endif
    R_ReleaseObject(sexp_ok);
    PyErr_NoMemory();
    return NULL;
  }
  /* PyObject_Init(&object, &ClosureSexp_Type); */
  RPY_SEXP(object) = sexp_ok;
  /* FIXME: Increment reference ? */
  /* Py_INCREF(object); */
  return object;
}


/* This function is only able to create a R-Python object 
   for an R vector-like 'rType', and from an 'object'
   that is a sequence. */
static SEXP
newSEXP(PyObject *object, int rType)
{
  SEXP sexp;
  SEXP str_R; /* used whenever there a string / unicode */
  PyObject *seq_object, *item; 

#ifdef RPY_VERBOSE
  printf("  new SEXP for Python:%p.\n", object);
#endif 

  seq_object = PySequence_Fast(object, 
                               "Cannot create R object from non-sequence Python object.");

  if (! seq_object) {
    return NULL;
  }
  const Py_ssize_t length = PySequence_Fast_GET_SIZE(seq_object);

  Py_ssize_t i;
  switch(rType) {
  case REALSXP:
    PROTECT(sexp = NEW_NUMERIC(length));      
    for (i = 0; i < length; ++i) {
      if((item = PyNumber_Float(PySequence_Fast_GET_ITEM(seq_object, i)))) {
        REAL(sexp)[i] = PyFloat_AS_DOUBLE(item);
        Py_DECREF(item);
      }
      else {
        PyErr_Clear();
        REAL(sexp)[i] = NA_REAL;
      }
    }
    UNPROTECT(1);
    break;
  case INTSXP:
    PROTECT(sexp = NEW_INTEGER(length));
    for (i = 0; i < length; ++i) {
      if((item = PyNumber_Int(PySequence_Fast_GET_ITEM(seq_object, i)))) {
        long l = PyInt_AS_LONG(item);
        INTEGER(sexp)[i] = (l<=INT_MAX && l>=INT_MIN)?l:NA_INTEGER;
        Py_DECREF(item);
      }
      else {
        PyErr_Clear();
        INTEGER(sexp)[i] = NA_INTEGER;
      }
    }
    UNPROTECT(1);
    break;
  case LGLSXP:
    PROTECT(sexp = NEW_LOGICAL(length));
    for (i = 0; i < length; ++i) {
      int q = PyObject_IsTrue(PySequence_Fast_GET_ITEM(seq_object, i));
      if (q != -1)
        LOGICAL(sexp)[i] = q;
      else {
        PyErr_Clear();
        LOGICAL(sexp)[i] = NA_LOGICAL;
      }
    }
    UNPROTECT(1);
    break;
  case STRSXP:
    PROTECT(sexp = NEW_CHARACTER(length));
    for (i = 0; i < length; ++i) {
      if((item = PyObject_Str(PySequence_Fast_GET_ITEM(seq_object, i)))) {
        str_R = mkChar(PyString_AS_STRING(item));
        if (!str_R) {
          Py_DECREF(item);
          PyErr_NoMemory();
          sexp = NULL;
          break;
        }
        Py_DECREF(item);
        SET_STRING_ELT(sexp, i, str_R);
      }
      else if ((item = PyObject_Unicode(PySequence_Fast_GET_ITEM(seq_object, i)))) {
        str_R = mkChar(PyUnicode_AS_DATA(item));
        if (!str_R) {
          Py_DECREF(item);
          PyErr_NoMemory();
          sexp = NULL;
          break;
        }
        Py_DECREF(item);
        SET_STRING_ELT(sexp, i, str_R);
      }
      else {
        PyErr_Clear();
        SET_STRING_ELT(sexp, i, NA_STRING);
      }
    }
    UNPROTECT(1);
    break;
  case VECSXP:
    PROTECT(sexp = NEW_LIST(length));
    for (i = 0; i < length; ++i) {
      if((item = PySequence_Fast_GET_ITEM(seq_object, i))) {
        int is_PySexpObject = PyObject_TypeCheck(item, &Sexp_Type);
        if (! is_PySexpObject) {
          Py_DECREF(item);
          PyErr_Format(PyExc_ValueError, "All elements of the list must be of "
                       "type 'Sexp_Type'.");
          return NULL;
        }
        SET_ELEMENT(sexp, i, RPY_SEXP((PySexpObject *)item));
      }
    }
    UNPROTECT(1);
    break;
  case CPLXSXP:
    PROTECT(sexp = NEW_COMPLEX(length));
    for (i = 0; i < length; ++i) {
        item = PySequence_Fast_GET_ITEM(seq_object, i);
        if (PyComplex_Check(item)) {
          Py_complex cplx = PyComplex_AsCComplex(item);
          COMPLEX(sexp)[i].r = cplx.real;
          COMPLEX(sexp)[i].i = cplx.imag;
        }
        else {
          PyErr_Clear();
          COMPLEX(sexp)[i].r = NA_REAL;
          COMPLEX(sexp)[i].i = NA_REAL;
        }
    }
    UNPROTECT(1);
    break;
  default:
    PyErr_Format(PyExc_ValueError, "Cannot handle type %d", rType);
    sexp = NULL;
  }

  Py_DECREF(seq_object);

  if (sexp != NULL) {
    R_PreserveObject(sexp);
#ifdef RPY_DEBUG_PRESERVE
    preserved_robjects += 1;
    printf("  PRESERVE -- R_PreserveObject -- %p -- %i\n", 
           sexp, preserved_robjects);
#endif 
  }

#ifdef RPY_VERBOSE
  printf("  new SEXP for Python:%p is %p.\n", object, sexp);
#endif
  return sexp;
}



/* --- Find a variable in an environment --- */

/* FIXME: is this any longer useful ? */
static PySexpObject*
EmbeddedR_findVar(PyObject *self, PyObject *args)
{
  char *name;
  SEXP rho_R = R_GlobalEnv, res;
  PyObject rho;

  if (!PyArg_ParseTuple(args, "s", &name, &rho)) { 
    return NULL; 
  }

  res = findVar(install(name), rho_R);


  if (res != R_UnboundValue) {
    return newPySexpObject(res);
  }
  PyErr_Format(PyExc_LookupError, "'%s' not found", name);
  return NULL;
}
PyDoc_STRVAR(EmbeddedR_findVar_doc,
             "Find a variable in R's .GlobalEnv.");

static PyObject*
EmbeddedR_sexpType(PyObject *self, PyObject *args)
{
  /* Return the C-defined name for R types */
  int sexp_i;

  if (! PyArg_ParseTuple(args, "i", &sexp_i)) {
    /* PyErr_Format(PyExc_LookupError, "Value should be an integer"); */
    return NULL;
  }

  const char *sexp_type = validSexpType[sexp_i];

  if ((sexp_i < 0) || (sexp_i >= RPY_MAX_VALIDSEXTYPE) || (! sexp_type)) {

    PyErr_Format(PyExc_LookupError, "'%i' is not a valid SEXP value.", sexp_i);
    return NULL;
  }
  /* FIXME: store python strings when initializing validSexpType instead */
  PyObject *res = PyString_FromString(sexp_type);
  return res;

}


/* --- List of functions defined in the module --- */

static PyMethodDef EmbeddedR_methods[] = {
  {"get_initoptions",     (PyCFunction)EmbeddedR_getinitoptions,   
   METH_NOARGS,
   EmbeddedR_get_initoptions_doc},
  {"set_initoptions",     (PyCFunction)EmbeddedR_setinitoptions,   
   METH_O,
   EmbeddedR_set_initoptions_doc},
  {"initr",     (PyCFunction)EmbeddedR_init,   METH_NOARGS,
   EmbeddedR_init_doc},
  {"endr",      (PyCFunction)EmbeddedR_end,    METH_O,
   EmbeddedR_end_doc},
  {"set_interactive",   (PyCFunction)EmbeddedR_setinteractive,  METH_O,
   EmbeddedR_setinteractive_doc},
  {"set_writeconsole",   (PyCFunction)EmbeddedR_setWriteConsole,  METH_VARARGS,
   EmbeddedR_setWriteConsole_doc},
  {"get_writeconsole",   (PyCFunction)EmbeddedR_getWriteConsole,  METH_VARARGS,
   EmbeddedR_getWriteConsole_doc},
  {"set_readconsole",    (PyCFunction)EmbeddedR_setReadConsole,   METH_VARARGS,
   EmbeddedR_setReadConsole_doc},
  {"get_readconsole",    (PyCFunction)EmbeddedR_getReadConsole,   METH_VARARGS,
   EmbeddedR_getReadConsole_doc},
  {"set_flushconsole",   (PyCFunction)EmbeddedR_setFlushConsole,  METH_VARARGS,
   EmbeddedR_setFlushConsole_doc},
  {"get_flushconsole",   (PyCFunction)EmbeddedR_getFlushConsole,  METH_VARARGS,
   EmbeddedR_getFlushConsole_doc},
  {"set_showmessage",    (PyCFunction)EmbeddedR_setShowMessage,   METH_VARARGS,
   EmbeddedR_setShowMessage_doc},
  {"get_showmessage",    (PyCFunction)EmbeddedR_getShowMessage,   METH_VARARGS,
   EmbeddedR_getShowMessage_doc},
  {"set_choosefile",     (PyCFunction)EmbeddedR_setChooseFile,    METH_VARARGS,
   EmbeddedR_setChooseFile_doc},
  {"get_choosefile",     (PyCFunction)EmbeddedR_getChooseFile,    METH_VARARGS,
   EmbeddedR_getChooseFile_doc},
  {"set_showfiles",      (PyCFunction)EmbeddedR_setShowFiles,     METH_VARARGS,
   EmbeddedR_setShowFiles_doc},
  {"get_showfiles",      (PyCFunction)EmbeddedR_getShowFiles,     METH_VARARGS,
   EmbeddedR_getShowFiles_doc},
  {"set_cleanup",      (PyCFunction)EmbeddedR_setCleanUp,     METH_VARARGS,
   EmbeddedR_setCleanUp_doc},
  {"get_cleanup",      (PyCFunction)EmbeddedR_getCleanUp,     METH_VARARGS,
   EmbeddedR_getCleanUp_doc},
  {"findVarEmbeddedR",  (PyCFunction)EmbeddedR_findVar,  METH_VARARGS,
   EmbeddedR_findVar_doc},
  {"process_revents", (PyCFunction)EmbeddedR_ProcessEvents, METH_NOARGS,
   EmbeddedR_ProcessEvents_doc},
  {"str_typeint",       (PyCFunction)EmbeddedR_sexpType, METH_VARARGS,
   "Return the SEXP name tag (string) corresponding to an integer."},
  {"unserialize",       (PyCFunction)EmbeddedR_unserialize, METH_VARARGS,
   "unserialize(str, rtype)\n"
   "Unserialize an R object from its string representation."},
  {NULL,                NULL}           /* sentinel */
};




/* A. Belopolsky's callback */

/* R representation of a PyObject */

static SEXP R_PyObject_type_tag;

static SEXP
R_PyObject_decref(SEXP s)
{
        PyObject* pyo = (PyObject*)R_ExternalPtrAddr(s);
        if (pyo) {
                Py_DECREF(pyo);
                R_ClearExternalPtr(s);
        }
        return R_NilValue;
}

static SEXP
mkPyObject(PyObject* pyo)
{
        SEXP res;
        Py_INCREF(pyo);
        res = R_MakeExternalPtr(pyo, R_PyObject_type_tag, R_NilValue);
        R_RegisterCFinalizer(res, (R_CFinalizer_t)R_PyObject_decref);
        return res;
}

#define R_PyObject_TYPE_CHECK(s) \
  (TYPEOF(s) == EXTPTRSXP && R_ExternalPtrTag(s) == R_PyObject_type_tag)

static SEXP
do_Python(SEXP args)
{
  SEXP sexp = CADR(args);
  SEXP res;
  if (!R_PyObject_TYPE_CHECK(sexp)) {
    error(".Python: invalid python type");
    return R_NilValue;
  }
  /* PyTypeObject* type = R_ExternalPtrAddr(sexp); */
  args = CDDR(args);
  sexp = CAR(args);
  if (!R_PyObject_TYPE_CHECK(sexp)) {
    error(".Python: invalid function");
    return R_NilValue;
  }
  PyObject *pyf = R_ExternalPtrAddr(sexp);
  
  /* create argument list */
  PyObject *pyargs = PyList_New(0);
  PyObject *pyres;
  for (args = CDR(args); args != R_NilValue; args = CDR(args)) {
    sexp = CAR(args);
    if (R_PyObject_TYPE_CHECK(sexp)) {
      PyList_Append(pyargs, (PyObject *)R_ExternalPtrAddr(sexp));
    }
    else {
      PyList_Append(pyargs, (PyObject *)newPySexpObject(sexp));
    }
  }
  PyObject *pyargstup = PyList_AsTuple(pyargs);
  /*FIXME: named arguments are not supported yet */
  pyres = PyObject_Call(pyf, pyargstup, NULL);
  if (!pyres) {
    PyObject *exctype;
    PyObject *excvalue; 
    PyObject *exctraceback;
    PyObject *excstr;
    PyErr_Fetch(&exctype, &excvalue, &exctraceback);
    excstr = PyObject_Str(excvalue);
    if (excstr) {
      error(PyString_AS_STRING(excstr));
      Py_DECREF(excstr);
    } 
    else {
      error("Python error");
    }
    PyErr_Clear();
  }
  Py_DECREF(pyargs);
  Py_DECREF(pyargstup);
  if (PyObject_IsInstance((PyObject*)pyres, 
                          (PyObject*)&Sexp_Type)) {
    res = RPY_SEXP((PySexpObject*)pyres);
  }
  else {
    res = mkPyObject(pyres);
  }
  Py_DECREF(pyres);
  
  return res;
}

static R_ExternalMethodDef externalMethods[] = { 
        {".Python", (DL_FUNC)&do_Python, -1},
        {NULL, NULL, 0} 
};



/* --- Initialize the module ---*/
static char **validSexpType;


#define ADD_INT_CONSTANT(module, name) \
  PyModule_AddIntConstant(module, #name, name); \

#define ADD_SEXP_CONSTANT(module, name)         \
  PyModule_AddIntConstant(module, #name, name); \
  validSexpType[name] = #name ;                 \

#define PYASSERT_ZERO(code) \
  if ((code) != 0) {return ; } \


#ifndef PyMODINIT_FUNC  /* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif

PyMODINIT_FUNC
initrinterface(void)
{
  /* PyMODINIT_FUNC */
  /* RPY_RINTERFACE_INIT(void) */
  /* { */

  /* Finalize the type object including setting type of the new type
         * object; doing it here is required for portability to Windows 
         * without requiring C++. */
  if (PyType_Ready(&Sexp_Type) < 0)
    return;
  if (PyType_Ready(&ClosureSexp_Type) < 0)
    return;
  if (PyType_Ready(&VectorSexp_Type) < 0)
    return;
  if (PyType_Ready(&EnvironmentSexp_Type) < 0)
    return;
  if (PyType_Ready(&S4Sexp_Type) < 0)
    return;
  if (PyType_Ready(&LangSexp_Type) < 0)
    return;

  PyObject *m, *d;
  m = Py_InitModule3("rinterface", EmbeddedR_methods, module_doc);
  if (m == NULL)
    return;
  d = PyModule_GetDict(m);

  /* Add SXP types */
  validSexpType = calloc(RPY_MAX_VALIDSEXTYPE, sizeof(char *));
  if (! validSexpType) {
    PyErr_NoMemory();
    return;
  }

  ADD_SEXP_CONSTANT(m, NILSXP);
  ADD_SEXP_CONSTANT(m, SYMSXP);
  ADD_SEXP_CONSTANT(m, LISTSXP);
  ADD_SEXP_CONSTANT(m, CLOSXP);
  ADD_SEXP_CONSTANT(m, ENVSXP);
  ADD_SEXP_CONSTANT(m, PROMSXP);
  ADD_SEXP_CONSTANT(m, LANGSXP);
  ADD_SEXP_CONSTANT(m, SPECIALSXP);
  ADD_SEXP_CONSTANT(m, BUILTINSXP);
  ADD_SEXP_CONSTANT(m, CHARSXP);
  ADD_SEXP_CONSTANT(m, STRSXP);
  ADD_SEXP_CONSTANT(m, LGLSXP);
  ADD_SEXP_CONSTANT(m, INTSXP);
  ADD_SEXP_CONSTANT(m, REALSXP);
  ADD_SEXP_CONSTANT(m, CPLXSXP);
  ADD_SEXP_CONSTANT(m, DOTSXP);
  ADD_SEXP_CONSTANT(m, ANYSXP);
  ADD_SEXP_CONSTANT(m, VECSXP);
  ADD_SEXP_CONSTANT(m, EXPRSXP);
  ADD_SEXP_CONSTANT(m, BCODESXP);
  ADD_SEXP_CONSTANT(m, EXTPTRSXP);
  ADD_SEXP_CONSTANT(m, RAWSXP);
  ADD_SEXP_CONSTANT(m, S4SXP);

  /* longuest integer for R indexes */
  ADD_INT_CONSTANT(m, R_LEN_T_MAX);

  /* "Logical" (boolean) values */
  ADD_INT_CONSTANT(m, TRUE);
  ADD_INT_CONSTANT(m, FALSE);

  /* R_ext/Arith.h */
  /* ADD_INT_CONSTANT(m, NA_LOGICAL); */
  /* ADD_INT_CONSTANT(m, NA_INTEGER); */

  initOptions = PyTuple_New(4);

  PYASSERT_ZERO(
                PyTuple_SetItem(initOptions, 0, 
                                PyString_FromString("rpy2"))
                );
  PYASSERT_ZERO(
                PyTuple_SetItem(initOptions, 1, 
                                PyString_FromString("--quiet"))
                );
  PYASSERT_ZERO(
                PyTuple_SetItem(initOptions, 2,
                                PyString_FromString("--vanilla"))
                );
  PYASSERT_ZERO(
                PyTuple_SetItem(initOptions, 3, 
                                PyString_FromString("--no-save"))
                );

  /* Add an extra ref. It should remain impossible to delete it */
  Py_INCREF(initOptions);

  PyModule_AddObject(m, "initoptions", initOptions);
  PyModule_AddObject(m, "Sexp", (PyObject *)&Sexp_Type);
  PyModule_AddObject(m, "SexpClosure", (PyObject *)&ClosureSexp_Type);
  PyModule_AddObject(m, "SexpVector", (PyObject *)&VectorSexp_Type);
  PyModule_AddObject(m, "SexpEnvironment", (PyObject *)&EnvironmentSexp_Type);
  PyModule_AddObject(m, "SexpS4", (PyObject *)&S4Sexp_Type);
  PyModule_AddObject(m, "SexpLang", (PyObject *)&LangSexp_Type);


  if (RPyExc_RuntimeError == NULL) {
    RPyExc_RuntimeError = PyErr_NewException("rpy2.rinterface.RRuntimeError", 
                                             NULL, NULL);
    if (RPyExc_RuntimeError == NULL)
      return;
  }
  
  Py_INCREF(RPyExc_RuntimeError);
  PyModule_AddObject(m, "RRuntimeError", RPyExc_RuntimeError);

  embeddedR_isInitialized = Py_False;
  Py_INCREF(Py_False);

  if (PyModule_AddObject(m, "isInitialized", embeddedR_isInitialized) < 0)
    return;

  globalEnv = (PySexpObject *)Sexp_new(&EnvironmentSexp_Type, 
                                       Py_None, Py_None);
  RPY_SEXP(globalEnv) = R_EmptyEnv;

  if (PyDict_SetItemString(d, "globalenv", (PyObject *)globalEnv) < 0)
  {
    Py_DECREF(globalEnv);
    return;
  }
  Py_DECREF(globalEnv);

  baseNameSpaceEnv = (PySexpObject*)Sexp_new(&EnvironmentSexp_Type,
                                             Py_None, Py_None);
  RPY_SEXP(baseNameSpaceEnv) = R_EmptyEnv;
  if (PyDict_SetItemString(d, "baseenv", 
                           (PyObject *)baseNameSpaceEnv) < 0)
  {
    Py_DECREF(baseNameSpaceEnv);
    return;
  }
  Py_DECREF(baseNameSpaceEnv);

  emptyEnv = (PySexpObject*)Sexp_new(&EnvironmentSexp_Type,
                                     Py_None, Py_None);
  RPY_SEXP(emptyEnv) = R_EmptyEnv;
  if (PyDict_SetItemString(d, "emptyenv", 
                           (PyObject *)emptyEnv) < 0)
  {
    Py_DECREF(emptyEnv);
    return;
  }
  Py_DECREF(emptyEnv);

  rpy_R_MissingArg = (PySexpObject*)Sexp_new(&Sexp_Type,
                                             Py_None, Py_None);
  if (PyDict_SetItemString(d, "R_MissingArg", (PyObject *)rpy_R_MissingArg) < 0)
  {
    Py_DECREF(rpy_R_MissingArg);
    return;
  }
  Py_DECREF(rpy_R_MissingArg);  

  rpy_R_NilValue = (PySexpObject*)Sexp_new(&Sexp_Type,
					   Py_None, Py_None);
  if (PyDict_SetItemString(d, "R_NilValue", (PyObject *)rpy_R_NilValue) < 0)
  {
    Py_DECREF(rpy_R_NilValue);
    return;
  }
  Py_DECREF(rpy_R_NilValue);  

  rinterface_unserialize = PyDict_GetItemString(d, "unserialize");
  
}
