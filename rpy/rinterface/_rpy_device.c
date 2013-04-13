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
 * Copyright (C) 2008-2012 Laurent Gautier
 * Portions copyright (C) 2012-2013 Beau Benjamin Bruce
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

#include <Python.h>
#include <R.h>
#include <Rinternals.h>
#include <Rdefines.h>
#include <R_ext/GraphicsEngine.h>
#include <R_ext/GraphicsDevice.h>

#include "_rinterface.h"
#include "rpy_device.h"

/* #define RPY_DEBUG_GRDEV */

PyDoc_STRVAR(module_doc,
             "Graphical devices for R. They can be interactive "
	         "(e.g., the X11 window that open during an interactive R session),"
	         " or not (e.g., PDF or PNG files).");

static inline void rpy_on_error(void)
{
  PyObject* pythonerror = PyErr_Occurred();
  if (pythonerror != NULL) {
    /* FIXME: All R actions should be stopped since the Python callback failed,
     and the Python exception raised up. For, now print Python errror */
    PyErr_Print(); 
  }
}

static PyObject* rpy_build_gc_dict(const pGEcontext gc) 
{
  PyObject* result;
  result = Py_BuildValue("{s:l,s:l,s:d,s:d,s:i,s:i,s:i,s:d,s:d,s:d,s:d,s:i,s:s}",
						 "col",gc->col,
						 "fill",gc->fill,
						 "gamma",gc->gamma,
						 "lwd",gc->lwd,
						 "lty",gc->lty,
						 "lend",gc->lend,
						 "ljoin",gc->ljoin,
						 "lmitre",gc->lmitre,
						 "cex",gc->cex,
						 "ps",gc->ps,
						 "lineheight",gc->lineheight,
						 "fontface",gc->fontface,
						 "fontfamily",gc->fontfamily
					   );
  if(result == NULL) {
	return NULL;
  }
  
  return result;
}

/* FIXME: Is this attached to anything? */
SEXP rpy_devoff(SEXP devnum, SEXP rho)
{
  SEXP c_R, call_R, res, fun_R;

#ifdef RPY_DEBUG_GRDEV
    printf("rpy_devoff(): checking 'rho'.\n");
#endif
  if(!isEnvironment(rho)) {
#ifdef RPY_DEBUG_GRDEV
    printf("rpy_devoff(): invalid 'rho'.\n");
#endif
    error("'rho' should be an environment\n");
  }

#ifdef RPY_DEBUG_GRDEV
  printf("rpy_devoff(): Looking for dev.off()...\n");
#endif
  PROTECT(fun_R = PyRinterface_FindFun(install("dev.off"), rho));
  if (fun_R == R_UnboundValue)
    printf("dev.off() could not be found.\n");
#ifdef RPY_DEBUG_GRDEV
  printf("rpy_devoff(): found.\n");
#endif


  /* incantation to summon R */
  PROTECT(c_R = call_R = allocList(2));
  SET_TYPEOF(c_R, LANGSXP);
  SETCAR(c_R, fun_R);
  c_R = CDR(c_R);

  /* first argument is the device number to be closed */
  SETCAR(c_R, devnum);
  SET_TAG(c_R, install("which"));
  c_R = CDR(c_R);
  int error = 0;

#ifdef RPY_DEBUG_GRDEV
  printf("rpy_devoff(): R_tryEval()\n");
#endif

  PROTECT(res = R_tryEval(call_R, rho, &error));

#ifdef RPY_DEBUG_GRDEV
  printf("rpy_devoff(): unprotecting.\n");
#endif

  UNPROTECT(3);
  return res;
}


/* evaluate a generic callback to Python for device functions */
static inline void rpy_GrDev_CallBack(pDevDesc dd, char *name)
{
  PyObject *result;

  PyObject *self = (PyObject *)dd->deviceSpecific;
  if(self != NULL) {
	result = PyObject_CallMethod(self, name, NULL);
	rpy_on_error();
	Py_XDECREF(result);
  }  
}

/********************************************************************************
 * Device functions
 *
 * Implement python docstrings, 
 * default python callbacks (just tell you they are not implemented), and
 * callback wrappers (rpy_...) that interface between C and python
 * 
 * RPY_GRDEV_FULLCALLBACKSET and RPY_GRDEV_SMALLCALLBACKSET macros assist 
 ********************************************************************************/

RPY_GRDEV_FULLCALLBACKSET(activate,"Callback to implement: activation of the graphical device.");

RPY_GRDEV_SMALLCALLBACKSET(circle,
       "Callback to implement: draw a circle on the graphical device.\n\
	    The callback will receive the parameters x, y, radius, and gc");
static void rpy_circle(double x, double y, double r,
                       const pGEcontext gc, pDevDesc dd)
{
#ifdef RPY_DEBUG_GRDEV
  printf("Circle.\n");
#endif

  PyObject *result;

  PyObject *self = (PyObject *)dd->deviceSpecific;

  PyObject *py_gc = rpy_build_gc_dict(gc);
  result = PyObject_CallMethod(self, "circle", "dddO", x, y, r, py_gc);
  Py_DECREF(py_gc);

  rpy_on_error();
  Py_XDECREF(result);  

}

RPY_GRDEV_SMALLCALLBACKSET(clip,
             "Callback to implement: clip the graphical device.\n\
	         The callback method will receive 4 arguments (Python floats) corresponding \
	         to x0, x1, y0, y1 respectively.");
static void rpy_clip(double x0, double x1, double y0, double y1, 
		     pDevDesc dd)
{
#ifdef RPY_DEBUG_GRDEV
  printf("Clipping. %f, %f, %f, %f\n", x0, x1, y0, y1);
#endif

  PyObject *result;

  PyObject *self = (PyObject *)dd->deviceSpecific;
  result = PyObject_CallMethod(self, "clip", "dddd", x0, x1, y0, y1);

  rpy_on_error();
  Py_XDECREF(result);  
}

RPY_GRDEV_FULLCALLBACKSET(close,"Callback to implement: close the device.")

RPY_GRDEV_FULLCALLBACKSET(deactivate,"Callback to implement: deactivate the graphical device.")

RPY_GRDEV_SMALLCALLBACKSET(getEvent,
             "GetEvent is no longer used by R, but kept for back compatibility\n\
              Not implemented.");
static SEXP rpy_getEvent(SEXP rho, const char *prompt)
{
#ifdef RPY_DEBUG_GRDEV
  printf("GetEvent.\n");
#endif

  SEXP r_res = R_NilValue;

  return r_res;
}

RPY_GRDEV_SMALLCALLBACKSET(line,
            "Callback to implement: draw a line on the graphical device.\n\
	        The callback will receive the arguments x1, y1, x2, y2, and gc.");
static void rpy_line(double x1, double y1, 
                     double x2, double y2,
                     const pGEcontext gc, pDevDesc dd)
{
#ifdef RPY_DEBUG_GRDEV
  printf("Line.\n");
#endif

  PyObject *result;

  PyObject *self = (PyObject *)dd->deviceSpecific;

  PyObject *py_gc = rpy_build_gc_dict(gc);
  result = PyObject_CallMethod(self, "line", "ddddO", x1, y1, x2, y2, py_gc);
  Py_DECREF(py_gc);

  rpy_on_error();
  Py_XDECREF(result);  

}

RPY_GRDEV_SMALLCALLBACKSET(locator,
             "Callback to implement: draw a polygon on the graphical device.\n\
             Callback to implement: locator on the graphical device.\n\
             Should return 3-tuple: (x,y,done)\n\
			 done = 0 if should continue locating, done = 1 if not");
static Rboolean rpy_locator(double *x, double *y, pDevDesc dd)
{

#ifdef RPY_DEBUG_GRDEV
  printf("Locator.\n");
#endif

  PyObject *result;
  int done;
  Rboolean retbool;

  PyObject *self = (PyObject *)dd->deviceSpecific;

  result = PyObject_CallMethod(self, "locator", NULL);

  rpy_on_error();

  if (!PyTuple_Check(result) && PyTuple_Size(result) != 3) {
    PyErr_Format(PyExc_ValueError, "Callback 'locator' should return a tuple of length 3.");
    rpy_on_error();
	retbool = FALSE;
  } else {
	double rx, ry;
	PyArg_ParseTuple(result, "ddi", &rx, &ry, &done);
	*x = rx;
	*y = ry;
	if(done == 1) {
	  retbool = FALSE;
	} else {
	  retbool = TRUE;
	}
  }

  rpy_on_error();
  Py_XDECREF(result);  
  return retbool;

}

RPY_GRDEV_SMALLCALLBACKSET(metricInfo,
             "Callback to implement: metricinfo on the graphical device.\n\
              Callback recieves a character and gc.  Returns a 3-tuple of\n\
              ascent, decscent, and width.");
static void rpy_metricInfo(int c, const pGEcontext gc, 
                           double* ascent, double* descent, double *width,
                           pDevDesc dd)
{
#ifdef RPY_DEBUG_GRDEV
  printf("MetricInfo.\n");
#endif

  PyObject *result;

  PyObject *self = (PyObject *)dd->deviceSpecific;

  PyObject *py_gc = rpy_build_gc_dict(gc);
  if(c < 0) c = -c;
  result = PyObject_CallMethod(self, "metricInfo", "iO", c, py_gc);
  Py_DECREF(py_gc);

  rpy_on_error();

  if (!PyTuple_Check(result) || PyTuple_Size(result) != 3) {
    PyErr_Format(PyExc_TypeError, "Callback 'size' should return a tuple of length 3.");
  } else {
	double a, d, w;
	PyArg_ParseTuple(result, "ddd", &a, &d, &w);
	*ascent = a;
	*descent = d;
	*width = w;
	rpy_on_error();
  }

#ifdef RPY_DEBUG_GRDEV
  printf("MetricInfo: %c, %f, %f, %f\n", c, *ascent, *descent, *width);
#endif

  Py_XDECREF(result);

}

RPY_GRDEV_SMALLCALLBACKSET(mode,
      "Callback to implement: mode of the graphical device. Accepts mode as argument.");
static void rpy_mode(int mode, pDevDesc dd)
{
#ifdef RPY_DEBUG_GRDEV
  printf("Mode.\n");
#endif

  PyObject *result;

  PyObject *self = (PyObject *)dd->deviceSpecific;

  result = PyObject_CallMethod(self, "mode", "l", mode);
  rpy_on_error();
  Py_XDECREF(result);  
}

RPY_GRDEV_SMALLCALLBACKSET(newPage,
             "Callback to implement: create a new page for the graphical device.\n\
	         If the device can only handle one page,\n\
	         the callback will have to eventually terminate and clean an existing page.\n\
             Accepts gc as argument.");
static void rpy_newPage(const pGEcontext gc, pDevDesc dd)
{
#ifdef RPY_DEBUG_GRDEV
  printf("New page.\n");
#endif

  PyObject *result;

  PyObject *self = (PyObject *)dd->deviceSpecific;

  PyObject *py_gc = rpy_build_gc_dict(gc);
  result = PyObject_CallMethod(self, "newPage", "O", py_gc);
  Py_DECREF(py_gc);

  rpy_on_error();
  Py_XDECREF(result);  
}

RPY_GRDEV_SMALLCALLBACKSET(polyline,
             "Callback to implement: draw a polyline on the graphical device.\n\
              Accepts tuple of x coordinates, tuple of corresponding y coordinates,\n\
              and the gc.");
static void rpy_polyline(int n, double *x, double *y, 
                         const pGEcontext gc, pDevDesc dd)
{
#ifdef RPY_DEBUG_GRDEV
  printf("Polyline.\n");
#endif

  PyObject *result;

  PyObject *self = (PyObject *)dd->deviceSpecific;

  PyObject *py_x = PyTuple_New((Py_ssize_t)n);
  PyObject *py_y = PyTuple_New((Py_ssize_t)n);

  int i;
  for (i = 0; i < n; i++) {
    PyTuple_SET_ITEM(py_x, (Py_ssize_t)i, PyFloat_FromDouble(x[i]));
    PyTuple_SET_ITEM(py_y, (Py_ssize_t)i, PyFloat_FromDouble(y[i]));
  }

  PyObject *py_gc = rpy_build_gc_dict(gc);

  result = PyObject_CallMethod(self, "polyline", "OOO", py_x, py_y, py_gc);

  Py_DECREF(py_gc);
  Py_DECREF(py_x);
  Py_DECREF(py_y);
  
  rpy_on_error();
  Py_XDECREF(result);  
}

RPY_GRDEV_SMALLCALLBACKSET(polygon,
             "Callback to implement: draw a polygon on the graphical device.\n\
              Accepts tuple of x coordinates, tuple of corresponding y coordinates,\n\
              and the gc.");
static void rpy_polygon(int n, double *x, double *y, 
                        const pGEcontext gc, pDevDesc dd)
{
#ifdef RPY_DEBUG_GRDEV
  printf("Polygon.\n");
#endif 

  PyObject *result;

  PyObject *self = (PyObject *)dd->deviceSpecific;

  PyObject *py_x = PyTuple_New((Py_ssize_t)n);
  PyObject *py_y = PyTuple_New((Py_ssize_t)n);

  int i;
  for (i = 0; i < n; i++) {
    PyTuple_SET_ITEM(py_x, (Py_ssize_t)i, PyFloat_FromDouble(x[i]));
    PyTuple_SET_ITEM(py_y, (Py_ssize_t)i, PyFloat_FromDouble(y[i]));
  }

  PyObject *py_gc = rpy_build_gc_dict(gc);

  result = PyObject_CallMethod(self, "polygon", "OOO", py_x, py_y, py_gc);

  Py_DECREF(py_gc);
  Py_DECREF(py_x);
  Py_DECREF(py_y);

  rpy_on_error();
  Py_DECREF(result);  
}

RPY_GRDEV_SMALLCALLBACKSET(rect,
  "Callback to implement: draw a rectangle on the graphical device.\n\
   The callback will receive 5 parameters x0, x1, y0, y1, and the gc.");
static void rpy_rect(double x0, double x1, double y0, double y1,
                     const pGEcontext gc, pDevDesc dd)
{
#ifdef RPY_DEBUG_GRDEV
  printf("Rect.\n");
#endif

  PyObject *result;

  PyObject *self = (PyObject *)dd->deviceSpecific;

  PyObject *py_gc = rpy_build_gc_dict(gc);
  result = PyObject_CallMethod(self, "rect", "ddddO", x0, x1, y0, y1, py_gc);
  Py_DECREF(py_gc);

  rpy_on_error();
  Py_XDECREF(result);  

}

RPY_GRDEV_SMALLCALLBACKSET(size,
             "Callback to implement: set the size of the graphical device.\n\
              The callback must return a tuple of 4 Python float (C double).\n\
	          These could be:\n\
	          left = 0\nright= <WindowWidth>\nbottom = <WindowHeight>\ntop=0\n"
	         );
static void rpy_size(double *left, double *right, 
                     double *bottom, double *top,
                     pDevDesc dd)
{
#ifdef RPY_DEBUG_GRDEV
  printf("Sizing device.\n");
  printf("Size in: %f, %f, %f, %f\n", *left, *right, *bottom, *top);
#endif

  PyObject *result;

  PyObject *self = (PyObject *)dd->deviceSpecific;

  result = PyObject_CallMethod(self, "size", NULL);
  rpy_on_error();

  if (!PyTuple_Check(result) || PyTuple_Size(result) != 4) {
    PyErr_Format(PyExc_TypeError, "Callback 'size' should return a tuple of length 4.");
  } else {
	double l, r, b, t;
	PyArg_ParseTuple(result, "dddd", &l, &r, &b, &t);
	*left = l;
	*right = r;
    *bottom = b;
	*top = t;
	rpy_on_error();
  }

#ifdef RPY_DEBUG_GRDEV
  printf("Size out: %f, %f, %f, %f\n", *left, *right, *bottom, *top);
#endif

  Py_XDECREF(result);  
}

RPY_GRDEV_SMALLCALLBACKSET(strWidth, 
	     "Callback to implement: strwidth(text) -> width\n\
          Width (in pixels) of a text when represented on the graphical device.\n\
          String and gc passed as arguments.\n\
	      The callback will return a Python float (C double).");
static double rpy_strWidth(const char *str, const pGEcontext gc, pDevDesc dd)
{
#ifdef RPY_DEBUG_GRDEV
  printf("String width.\n");
#endif 

  PyObject *result;

  PyObject *self = (PyObject *)dd->deviceSpecific;

  PyObject *py_gc = rpy_build_gc_dict(gc);
  result = PyObject_CallMethod(self, "strWidth", "sO", str, py_gc);
  Py_DECREF(py_gc);

  rpy_on_error();

  if (!PyFloat_Check(result)) {
    PyErr_Format(PyExc_TypeError,
				 "The value returned by strwidth must be a float");
  }

  double out = PyFloat_AsDouble(result);

  Py_DECREF(result);  

  return out;
}

RPY_GRDEV_SMALLCALLBACKSET(text,
  "Callback to implement: display text on the device.\n\
  The callback will receive the parameters:\n				\
  x, y (position), string, rot (angle in degrees), hadj (horizontal adj), and gc");
static void rpy_text(double x, double y, const char *str,
                     double rot, double hadj,
		             const pGEcontext gc, pDevDesc dd)
{
#ifdef RPY_DEBUG_GRDEV
  printf("Text.\n");
#endif

  PyObject *result;

  PyObject *self = (PyObject *)dd->deviceSpecific;

  PyObject *py_gc = rpy_build_gc_dict(gc);
  result = PyObject_CallMethod(self, "text", "ddsddO", x, y, str, rot, hadj, py_gc);
  Py_DECREF(py_gc);

  rpy_on_error();
  Py_XDECREF(result);  
}

/********************************************************************************
 * rpy_resize notify regarding a resize from within python
 ********************************************************************************/
static PyObject* rpy_resize(PyObject *self, PyObject *args)
{
#ifdef RPY_DEBUG_GRDEV
  printf("Resizing device.\n");
#endif

  GEDevDesc *gd = GEgetDevice(curDevice());
  if (gd) {
	pDevDesc dd = gd->dev;
	if (dd) {
	  dd->size(&(dd->left), &(dd->right), &(dd->bottom), &(dd->top), dd);
	  GEplayDisplayList(gd);
	  }
  }
  Py_RETURN_NONE;
}

void configureDevice(pDevDesc dd, PyObject *self)
{
#ifdef RPY_DEBUG_GRDEV
  printf("Configuring device.\n");
#endif

  /* setup structure */
  dd->deviceSpecific = (void *) self;
  dd->close = rpy_close;
  dd->activate = rpy_activate;
  dd->deactivate = rpy_deactivate;
  dd->size = rpy_size;
  dd->newPage = rpy_newPage;
  dd->clip = rpy_clip;
  /* Next two are unused */
  dd->strWidth = rpy_strWidth;
  dd->text = rpy_text;
  dd->rect = rpy_rect;
  dd->circle = rpy_circle;
  dd->line = rpy_line;
  dd->polyline = rpy_polyline;
  dd->polygon = rpy_polygon;
  dd->locator = rpy_locator;
  dd->mode = rpy_mode;
  dd->metricInfo = rpy_metricInfo;
  /* add path, raster, cap functions -- see GraphicsDevice.h */
  dd->getEvent = rpy_getEvent;
  dd->holdflush = NULL; // new in 2.14.0 - can be left unimplemented as NULL (GraphicsDevice.h)
  /* FIXME: initialization from self.attribute */
  dd->hasTextUTF8 = TRUE; /*PyObject_GetAttrString(self, ); */
  dd->wantSymbolUTF8 = TRUE;   /* FIXME: initialization from self.attribute */
  dd->strWidthUTF8 = rpy_strWidth;
  dd->textUTF8 = rpy_text;

  dd->left = dd->clipLeft = 0;   /* FIXME: initialization from self.attribute */
  dd->right = dd->clipRight = 720;   /* FIXME: initialization from self.attribute */
  dd->bottom = dd->clipBottom = 720;   /* FIXME: initialization from self.attribute */
  dd->top = dd->clipTop = 0;   /* FIXME: initialization from self.attribute */

  /* starting parameters */
  dd->startfont = 1; 
  dd->startps = 15.0; /* ps *  */
  dd->startcol = R_RGB(0, 0, 0);
  dd->startfill = R_TRANWHITE;
  dd->startlty = LTY_SOLID; 
  dd->startgamma = 1.0;
        
  dd->cra[0] = 0.9*15.0;
  dd->cra[1] = 1.2*15.0;
        
  /* character addressing offsets */
  dd->xCharOffset = 0.4900;
  dd->yCharOffset = 0.3333;
  dd->yLineBias = 0.1;

  /* inches per raster unit */
  dd->ipr[0] = 1.0/72.0;
  dd->ipr[1] = 1.0/72.0;

  /* device capabilities */
  dd->canClip = TRUE;         /* flag for clipping capability */
  dd->canHAdj = 0; /* text adjustment 0, 1, or 2 */
  dd->canChangeGamma = FALSE; /* flag for if device handles gamma correction */

  dd->canGenMouseDown = TRUE; /* can the device generate mousedown events */
  dd->canGenMouseMove = TRUE; /* can the device generate mousemove events */
  dd->canGenMouseUp = TRUE;   /* can the device generate mouseup events */
  
  dd->canGenKeybd = TRUE;     /* can the device generate keyboard events */
    
  dd->displayListOn = TRUE;

  /* finish */
}

static void
GrDev_dealloc(PyGrDevObject *self)
{
#ifdef RPY_DEBUG_GRDEV
  printf("Deallocating graphics device (GrDev_dealloc)\n");
#endif

  pGEDevDesc dd = GEgetDevice(RPY_DEV_NUM(self)-1); 

  // Need to preserve error state as we enter callbacks
  PyObject *err_type, *err_value, *err_traceback;
  int have_error = PyErr_Occurred() ? 1 : 0;

  if (have_error)
	PyErr_Fetch(&err_type, &err_value, &err_traceback);
  
  /* Caution: GEkillDevice calls free for self->grdev
     and the method "close()" for the the device. 
     (See GrDev_close for details) */
  if (dd) GEkillDevice(dd);

  if (have_error)
	PyErr_Restore(err_type, err_value, err_traceback);

#if (PY_VERSION_HEX < 0x03010000)
  self->ob_type->tp_free((PyObject*)self);
#else
  Py_TYPE(self)->tp_free((PyObject*)self);
#endif

#ifdef RPY_DEBUG_GRDEV
  printf("GrDev_dealloc done.\n");
#endif
}

static PyObject*
GrDev_repr(PyObject *self)
{
  pDevDesc devdesc = ((PyGrDevObject *)self)->grdev;
#if (PY_VERSION_HEX < 0x03010000)
  return PyString_FromFormat("<%s - Python:\%p / R graphical device:\%p>",
                             self->ob_type->tp_name,
                             self,
                             devdesc);
#else
  return PyUnicode_FromFormat("<%s - Python:\%p / R graphical device:\%p>",
			      Py_TYPE(self)->tp_name,
			      self,
			      devdesc);
#endif
}

/**********************************************************************
 * Expose methods
 **********************************************************************/
static PyMethodDef GrDev_methods[] = {
  RPY_GRDEV_METHOD(activate,NO),
  RPY_GRDEV_METHOD(circle,VAR),
  RPY_GRDEV_METHOD(clip,VAR),
  RPY_GRDEV_METHOD(close,NO),
  RPY_GRDEV_METHOD(deactivate,NO),
  RPY_GRDEV_METHOD(getEvent,VAR),
  RPY_GRDEV_METHOD(line,VAR),
  RPY_GRDEV_METHOD(locator,VAR),
  RPY_GRDEV_METHOD(metricInfo,VAR),
  RPY_GRDEV_METHOD(mode,VAR),
  RPY_GRDEV_METHOD(polyline,VAR),
  RPY_GRDEV_METHOD(polygon,VAR),
  RPY_GRDEV_METHOD(rect,VAR),
  RPY_GRDEV_METHOD(size,VAR),
  RPY_GRDEV_METHOD(strWidth,VAR),
  RPY_GRDEV_METHOD(text,VAR),
  RPY_GRDEV_METHOD(newPage,VAR),
  {"resize", (PyCFunction)rpy_resize, METH_VARARGS,
   "request a resize"},
  /* */
  {NULL, NULL, 0, NULL}          /* sentinel */
};

/**********************************************************************
 * Getters/setters for NewDevDesc structure (GraphicsDevice.h)
 **********************************************************************/
RPY_GRDEV_FLOAT_GETSET(self,left,"Left coordinate.");
RPY_GRDEV_FLOAT_GETSET(self,right,"Right coordinate.");
RPY_GRDEV_FLOAT_GETSET(self,top,"Top coordinate.");
RPY_GRDEV_FLOAT_GETSET(self,bottom,"Bottom coordinate.");

RPY_GRDEV_FLOAT_GETSET(self,clipLeft,"Left clip coordinate.");
RPY_GRDEV_FLOAT_GETSET(self,clipRight,"Right clip coordinate.");
RPY_GRDEV_FLOAT_GETSET(self,clipTop,"Top clip coordinate.");
RPY_GRDEV_FLOAT_GETSET(self,clipBottom,"Bottom clip coordinate.");

RPY_GRDEV_FLOAT_GETSET(self,xCharOffset,"X character addressing offset (unused).");
RPY_GRDEV_FLOAT_GETSET(self,yCharOffset,"Y character addressing offset.");
RPY_GRDEV_FLOAT_GETSET(self,yLineBias,"1/2 interline space as frac of line height.");

RPY_GRDEV_BOOL_GETSET(hasTextUTF8,"UTF8 capabilities of the device.")
RPY_GRDEV_BOOL_GETSET(wantSymbolUTF8,"UTF8 capabilities of the device.")

RPY_GRDEV_BOOL_GETSET(displayListOn,"Status of the display list.")

RPY_GRDEV_BOOL_GETSET(canGenMouseDown,"Ability to generate mouse down events.")
RPY_GRDEV_BOOL_GETSET(canGenMouseMove,"Ability to generate mouse move events.")
RPY_GRDEV_BOOL_GETSET(canGenMouseUp,"Ability to generate mouse up events.")
RPY_GRDEV_BOOL_GETSET(canGenKeybd,"Ability to generate keyboard events.")


PyDoc_STRVAR(GrDev_devnum_doc,
             "Device number.");
static PyObject* GrDev_devnum_get(PyObject* self)
{
  PyObject* res;
  if ( RPY_DEV_NUM(self) == 0) {
    Py_INCREF(Py_None);
    res = Py_None;
  } else {
#if (PY_VERSION_HEX < 0x03010000)
    res = PyInt_FromLong((long)RPY_DEV_NUM(self));
#else
    res = PyLong_FromLong((long)RPY_DEV_NUM(self));
#endif
  }
  return res;

}

static PyGetSetDef GrDev_getsets[] = {
  RPY_GRDEV_GETSET(left),
  RPY_GRDEV_GETSET(right),
  RPY_GRDEV_GETSET(top),
  RPY_GRDEV_GETSET(bottom),
  RPY_GRDEV_GETSET(clipLeft),
  RPY_GRDEV_GETSET(clipRight),
  RPY_GRDEV_GETSET(clipTop),
  RPY_GRDEV_GETSET(clipBottom),
  RPY_GRDEV_GETSET(xCharOffset),
  RPY_GRDEV_GETSET(yCharOffset),
  RPY_GRDEV_GETSET(yLineBias),
  RPY_GRDEV_GETSET(hasTextUTF8),
  RPY_GRDEV_GETSET(wantSymbolUTF8),
  RPY_GRDEV_GETSET(canGenMouseDown),
  RPY_GRDEV_GETSET(canGenMouseUp),
  RPY_GRDEV_GETSET(canGenMouseMove),
  RPY_GRDEV_GETSET(canGenKeybd),
  RPY_GRDEV_GETSET(displayListOn),
  /* */
  {"devnum",
   (getter)GrDev_devnum_get,
   NULL,
   GrDev_devnum_doc},
  /* */
  {NULL}          /* sentinel */
};


static PyObject*
GrDev_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{

#ifdef RPY_DEBUG_GRDEV
  printf("Allocating graphics device (GrDev_new)\n");
#endif

  PyGrDevObject *self;

  if (!PyRinterface_IsInitialized()) {
    PyErr_Format(PyExc_RuntimeError, 
                 "R must be initialized before graphical device instances can be created.");
    return NULL;
  }

  self = (PyGrDevObject *)type->tp_alloc(type, 0);

  if (self != NULL) {
	self->grdev = (pDevDesc)calloc(1, sizeof(DevDesc));
	if (self->grdev == NULL) {
	  PyErr_Format(PyExc_RuntimeError, 
				   "Could not allocate memory for an R device description.");
	  Py_DECREF(self);
	  return NULL;
	}
  } else {	
    PyErr_NoMemory();
  }

#ifdef RPY_DEBUG_GRDEV
  printf("GrDev_new done.\n");
#endif
  
  return(PyObject *)self;
}


static int
GrDev_init(PyObject *self, PyObject *args, PyObject *kwds)
{

#ifdef RPY_DEBUG_GRDEV
  printf("Initializing graphics device (GrDev_init)\n");
#endif

  if (!PyRinterface_IsInitialized()) {
    PyErr_Format(PyExc_RuntimeError, 
                 "R must be initialized before graphical device instances can be created.");
    return -1;
  }

  if (R_CheckDeviceAvailableBool() != TRUE) {
    PyErr_Format(PyExc_RuntimeError, 
                 "Too many open R devices.");
    return -1;
  }

  pDevDesc dev = ((PyGrDevObject *)self)->grdev;

  configureDevice(dev, self);

  pGEDevDesc gdd = GEcreateDevDesc(dev);

#if (PY_VERSION_HEX < 0x03010000)
  GEaddDevice2(gdd, self->ob_type->tp_name);
#else
  GEaddDevice2(gdd, Py_TYPE(self)->tp_name);
#endif

#ifdef RPY_DEBUG_GRDEV
  printf("GrDev_init done.\n");
#endif
  
  return 0;
}


/*
 * Generic graphical device.
 */
PyDoc_STRVAR(GrDev_doc,
             "Python-defined graphical device for R.");

static PyTypeObject GrDev_Type = {
        /* The ob_type field must be initialized in the module init function
         * to be portable to Windows without using C++. */
#if (PY_VERSION_HEX < 0x03010000)
        PyObject_HEAD_INIT(NULL)
        0,                      /*ob_size*/
#else
	PyVarObject_HEAD_INIT(NULL, 0)
#endif
        "rpy2.rinterface.GraphicalDevice",   /*tp_name*/
        sizeof(PyGrDevObject),  /*tp_basicsize*/
        0,                      /*tp_itemsize*/
        /* methods */
        (destructor)GrDev_dealloc, /*tp_dealloc*/
        0,                      /*tp_print*/
        0,                      /*tp_getattr*/
        0,                      /*tp_setattr*/
#if (PY_VERSION_HEX < 0x03010000)
        0,                      /*tp_compare*/
#else
        0,                      /*tp_reserved*/
#endif
        GrDev_repr,             /*tp_repr*/
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
        GrDev_doc,                      /*tp_doc*/
        0,                      /*tp_traverse*/
        0,/*(inquiry)Sexp_clear, tp_clear*/
        0,                      /*tp_richcompare*/
        0,                      /*tp_weaklistoffset*/
        0,                      /*tp_iter*/
        0,                      /*tp_iternext*/
        GrDev_methods,          /*tp_methods*/
        0,                      /*tp_members*/
        GrDev_getsets,            /*tp_getset*/
        0,                      /*tp_base*/
        0,                      /*tp_dict*/
        0,                      /*tp_descr_get*/
        0,                      /*tp_descr_set*/
        0,                      /*tp_dictoffset*/
        (initproc)GrDev_init,    /*tp_init*/
        0,                      /*tp_alloc*/
        GrDev_new,               /*tp_new*/
        0,                      /*tp_free*/
        0,                      /*tp_is_gc*/
#if (PY_VERSION_HEX < 0x03010000)
#else
	0,                      /*tp_bases*/
	0,                      /*tp_mro*/
	0,                      /*tp_cache*/
	0,                      /*tp_subclasses*/
	0                       /*tp_weaklist*/
#endif
};

/* Additional methods for RpyDevice */
static PyMethodDef rpydevice_methods[] = {
  {NULL, NULL, 0, NULL}          /* sentinel */
};

#ifndef PyMODINIT_FUNC  /* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif

#if (PY_VERSION_HEX < 0x03010000)
#else
static struct PyModuleDef rpydevicemodule = {
   PyModuleDef_HEAD_INIT,
   "_rpy_device",           /* name of module */
   module_doc,             /* module documentation, may be NULL */
   -1,                     /* size of per-interpreter state of the module */
   NULL, NULL, NULL, NULL, NULL
 };
#endif

PyMODINIT_FUNC
#if (PY_VERSION_HEX < 0x03010000)
init_rpy_device(void)
#else
PyInit__rpy_device(void)
#endif
{
  if (PyType_Ready(&GrDev_Type) < 0) {
#if (PY_VERSION_HEX < 0x03010000)
    return;
#else
    return NULL;
#endif
  }
  
  PyObject *m;
#if (PY_VERSION_HEX < 0x03010000)
  m = Py_InitModule3("_rpy_device", rpydevice_methods, module_doc);
#else
  m = PyModule_Create(&rpydevicemodule);
#endif
  if (m == NULL) {
#if (PY_VERSION_HEX < 0x03010000)
    return;
#else
    return NULL;
#endif
  }

  if (import_rinterface() < 0)
#if (PY_VERSION_HEX < 0x03010000)
    return;
#else
    return NULL;
#endif

  PyObject *d;
  d = PyModule_GetDict(m);
  PyModule_AddObject(m, "GraphicalDevice", (PyObject *)&GrDev_Type);  
#if (PY_VERSION_HEX < 0x03010000)
#else
  return m;
#endif
}
