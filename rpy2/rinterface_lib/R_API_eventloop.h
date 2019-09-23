/* cffi_source-begin */
# include <sys/select.h> /* for fd_set */
/* cffi_source-end */

typedef void (*InputHandlerProc)(void *userData);
typedef struct _InputHandler InputHandler;
typedef struct _InputHandler {
  
  int activity;
  int fileDescriptor;
  InputHandlerProc handler;
  
  struct _InputHandler *next;
  
  /* Whether we should be listening to this file descriptor or not. */
  int active;
  
  /* Data that can be passed to the routine as its only argument.
     This might be a user-level function or closure when we implement
     a callback to R mechanism. 
  */
  void *userData;
  
} InputHandler;

extern InputHandler *initStdinHandler(void);

extern InputHandler *addInputHandler(InputHandler *handlers,
				     int fd, InputHandlerProc handler,
				     int activity);
extern InputHandler *getInputHandler(InputHandler *handlers, int fd);
extern int           removeInputHandler(InputHandler **handlers, InputHandler *it);
extern InputHandler *R_InputHandlers;
extern void (* R_PolledEvents)(void);
extern int R_wait_usec;

/* cffi_source-begin */
/* The definitions below require fd_set, which is only defined through
 * the include of sys/select.h . */
extern InputHandler *getSelectedHandler(InputHandler *handlers, fd_set *mask);
extern fd_set *R_checkActivity(int usec, int ignore_stdin);
extern fd_set *R_checkActivityEx(int usec, int ignore_stdin, void (*intr)(void));
extern void R_runHandlers(InputHandler *handlers, fd_set *mask);

extern int R_SelectEx(int  n,  fd_set  *readfds,  fd_set  *writefds,
		      fd_set *exceptfds, struct timeval *timeout,
		      void (*intr)(void));
/* cffi_source-end */
