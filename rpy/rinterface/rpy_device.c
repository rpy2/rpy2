
/* Copyright Laurent Gautier - 2009-2010 */

#include <Python.h>
#include <R.h>
#include <Rinternals.h>
#include <Rdefines.h>
#include <R_ext/GraphicsEngine.h>
#include <R_ext/GraphicsDevice.h>

#include "rpy_rinterface.h"
#include "rpy_device.h"


PyDoc_STRVAR(module_doc,
             "Graphical output devices for R.");

static inline void rpy_printandclear_error(void)
{
  PyObject* pythonerror = PyErr_Occurred();
  if (pythonerror != NULL) {
    /* All R actions should be stopped since the Python callback failed,
     and the Python exception raised up.*/
    /* FIXME: Print the exception in the meanwhile */
    PyErr_Print();
    PyErr_Clear();
  }
}

static inline void rpy_GrDev_CallBack(pDevDesc dd, PyObject *name)
{
  PyObject *result;

  /* Restore the Python handler */
  /* FIXME */
  /* PyOS_setsig(SIGINT, python_sighandler); */

  PyObject *self = (PyObject *)dd->deviceSpecific;
  result = PyObject_CallMethodObjArgs(self, name, NULL);

  rpy_printandclear_error();

  Py_XDECREF(result);  
}

static PyObject *GrDev_close_name;
static void rpy_Close(pDevDesc dd)
{
  rpy_GrDev_CallBack(dd, GrDev_close_name);
}

PyDoc_STRVAR(GrDev_close_doc,
             "Close the graphical output device.");
static PyObject* GrDev_close(PyObject *self)
{
  PyErr_Format(PyExc_NotImplementedError, "Device closing not implemented.");
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject* GrDev_activate_name;
static void rpy_Activate(pDevDesc dd)
{
  rpy_GrDev_CallBack(dd, GrDev_activate_name);
}

PyDoc_STRVAR(GrDev_activate_doc,
             "Activate the graphical output device.");
static PyObject* GrDev_activate(PyObject *self)
{
  /* error("Not implemented."); */
  PyErr_Format(PyExc_NotImplementedError, "Device activation not implemented.");
  /* printf("done.\n"); */
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject* GrDev_deactivate_name;
static void rpy_Deactivate(pDevDesc dd)
{
  rpy_GrDev_CallBack(dd, GrDev_deactivate_name);
}

PyDoc_STRVAR(GrDev_deactivate_doc,
             "Deactivate the graphical output device.");
static PyObject* GrDev_deactivate(PyObject *self)
{
  PyErr_Format(PyExc_NotImplementedError, "Device deactivation not implemented.");
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject* GrDev_size_name;
static void rpy_Size(double *left, double *right, 
                     double *bottom, double *top,
                     pDevDesc dd)
{
  PyObject *result;

  /* Restore the Python handler */
  /* FIXME */
  /* PyOS_setsig(SIGINT, python_sighandler); */
  printf("FIXME: size(left=%f, right=%f, bottom=%f, top=%f)\n", 
         *left, *right, *bottom, *top);

  PyObject *self = (PyObject *)dd->deviceSpecific;

  PyObject *lrbt = Py_BuildValue("(dddd)", *left, *right, *bottom, *top);
  result = PyObject_CallMethodObjArgs(self, GrDev_size_name, 
                                      lrbt, NULL);
  rpy_printandclear_error();

  if (! PyTuple_Check(result) ) {
    PyErr_Format(PyExc_ValueError, "Callback 'size' should return a tuple.");
    rpy_printandclear_error();
  } else if (PyTuple_Size(result) != 4) {
    PyErr_Format(PyExc_ValueError, "Callback 'size' should return a tuple of length 4.");
    rpy_printandclear_error();    
  } else {
    *left = PyFloat_AsDouble(PyTuple_GetItem(result, 0));
    *right = PyFloat_AsDouble(PyTuple_GetItem(result, 1));
    *bottom = PyFloat_AsDouble(PyTuple_GetItem(result, 2));
    *top = PyFloat_AsDouble(PyTuple_GetItem(result, 3));
  }

  Py_XDECREF(result);  
}

PyDoc_STRVAR(GrDev_size_doc,
             "Set the size of the graphical device.");
static PyObject* GrDev_size(PyObject *self, PyObject *args)
{
  PyErr_Format(PyExc_NotImplementedError, 
               "Device size not implemented.\n"
               "[ expected signature is ((left, right, bottom, top)) \n]"
               "[ should return a tuple of length 4]");
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject* GrDev_newpage_name;
static void rpy_NewPage(const pGEcontext gc, pDevDesc dd)
{
  PyObject *result;

  /* Restore the Python handler */
  /* FIXME */
  /* PyOS_setsig(SIGINT, python_sighandler); */

  /* FIXME give the callback access to gc */
  PyObject *self = (PyObject *)dd->deviceSpecific;
  result = PyObject_CallMethodObjArgs(self, GrDev_newpage_name, NULL);

  rpy_printandclear_error();

  Py_XDECREF(result);  
}

PyDoc_STRVAR(GrDev_newpage_doc,
             "Create a new page for the graphical device.");
static PyObject* GrDev_newpage(PyObject *self, PyObject *args)
{
  printf("FIXME: newpage.\n");
  /* PyErr_Format(PyExc_NotImplementedError, "Not implemented."); */
  Py_INCREF(Py_None);
  printf("  done.\n");
  return Py_None;
}

static PyObject* GrDev_clip_name;
static void rpy_Clip(double x0, double x1, double y0, double y1, pDevDesc dd)
{
  PyObject *result;

  /* Restore the Python handler */
  /* FIXME */
  /* PyOS_setsig(SIGINT, python_sighandler); */

  PyObject *self = (PyObject *)dd->deviceSpecific;
  /* FIXME optimize ? */
  PyObject *py_x0 = PyFloat_FromDouble(x0);
  PyObject *py_x1 = PyFloat_FromDouble(x1);
  PyObject *py_y0 = PyFloat_FromDouble(y0);
  PyObject *py_y1 = PyFloat_FromDouble(y1);
  result = PyObject_CallMethodObjArgs(self, GrDev_clip_name, 
                                      py_x0, py_x1,
                                      py_y0, py_y1,
                                      NULL);

  rpy_printandclear_error();
  Py_XDECREF(result);
}

PyDoc_STRVAR(GrDev_clip_doc,
             "Clip the graphical device.");
static PyObject* GrDev_clip(PyObject *self, PyObject *args)
{
  PyErr_Format(PyExc_NotImplementedError, "Device clip not implemented.");
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject* GrDev_strwidth_name;
static double rpy_StrWidth(const char *str, const pGEcontext gc, pDevDesc dd)
{
  PyObject *result;

  /* Restore the Python handler */
  /* FIXME */
  /* PyOS_setsig(SIGINT, python_sighandler); */

  /* FIXME give the callback access to gc */
  PyObject *self = (PyObject *)dd->deviceSpecific;
  PyObject *py_str = PyString_FromString(str);
  result = PyObject_CallMethodObjArgs(self, GrDev_strwidth_name, py_str);

  rpy_printandclear_error();

  double r_res = PyFloat_AsDouble(result);
  Py_DECREF(result);  

  return r_res;
}

PyDoc_STRVAR(GrDev_strwidth_doc,
             "String width on the graphical device.");
static PyObject* GrDev_strwidth(PyObject *self, PyObject *args)
{
  PyErr_Format(PyExc_NotImplementedError, "Device strwidth not implemented.");
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject* GrDev_text_name;
static void rpy_Text(double x, double y, const char *str,
                     double rot, double hadj, const pGEcontext gc, pDevDesc dd)
{
    PyObject *result;

  /* Restore the Python handler */
  /* FIXME */
  /* PyOS_setsig(SIGINT, python_sighandler); */

  PyObject *self = (PyObject *)dd->deviceSpecific;
  /* FIXME optimize ? */
  PyObject *py_x = PyFloat_FromDouble(x);
  PyObject *py_y = PyFloat_FromDouble(y);
  PyObject *py_str = PyString_FromString(str);
  PyObject *py_rot = PyFloat_FromDouble(rot);
  PyObject *py_hadj = PyFloat_FromDouble(hadj);
  /* FIXME pass gc ? */
  result = PyObject_CallMethodObjArgs(self, GrDev_text_name, 
                                      py_x, py_y,
                                      py_str, py_rot, py_hadj,
                                      NULL);

  rpy_printandclear_error();

  Py_DECREF(result);  
}

PyDoc_STRVAR(GrDev_text_doc,
             "String width on the graphical device.");
static PyObject* GrDev_text(PyObject *self, PyObject *args)
{
  PyErr_Format(PyExc_NotImplementedError, "Device text not implemented.");
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject* GrDev_rect_name;
static void rpy_Rect(double x0, double x1, double y0, double y1,
                     const pGEcontext gc, pDevDesc dd)
{
  PyObject *result;

  /* Restore the Python handler */
  /* FIXME */
  /* PyOS_setsig(SIGINT, python_sighandler); */

  PyObject *self = (PyObject *)dd->deviceSpecific;
  /* FIXME optimize ? */
  PyObject *py_x0 = PyFloat_FromDouble(x0);
  PyObject *py_x1 = PyFloat_FromDouble(x1);
  PyObject *py_y0 = PyFloat_FromDouble(y0);
  PyObject *py_y1 = PyFloat_FromDouble(y1);
  /* FIXME pass gc ? */
  result = PyObject_CallMethodObjArgs(self, GrDev_rect_name, 
                                      py_x0, py_x1,
                                      py_y0, py_y1,
                                      NULL);

  rpy_printandclear_error();

  Py_DECREF(result);  
}

PyDoc_STRVAR(GrDev_rect_doc,
             "Draw a rectangle on the graphical device.");
static PyObject* GrDev_rect(PyObject *self, PyObject *args)
{
  PyErr_Format(PyExc_NotImplementedError, "Device rect not implemented.");
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject* GrDev_circle_name;
static void rpy_Circle(double x, double y, double r,
                       const pGEcontext gc, pDevDesc dd)
{
  PyObject *result;

  /* Restore the Python handler */
  /* FIXME */
  /* PyOS_setsig(SIGINT, python_sighandler); */

  PyObject *self = (PyObject *)dd->deviceSpecific;
  /* FIXME optimize ? */
  PyObject *py_x = PyFloat_FromDouble(x);
  PyObject *py_y = PyFloat_FromDouble(y);
  PyObject *py_r = PyFloat_FromDouble(r);
  /* FIXME pass gc ? */
  result = PyObject_CallMethodObjArgs(self, GrDev_circle_name, 
                                      py_x, py_y, py_r,
                                      NULL);

  rpy_printandclear_error();
  Py_DECREF(result);  
}

PyDoc_STRVAR(GrDev_circle_doc,
             "Draw a circle on the graphical device.");
static PyObject* GrDev_circle(PyObject *self, PyObject *args)
{
  PyErr_Format(PyExc_NotImplementedError, "Device circle not implemented.");
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject* GrDev_line_name;
static void rpy_Line(double x1, double y1, 
                     double x2, double y2,
                     const pGEcontext gc, pDevDesc dd)
{
  PyObject *result;

  /* Restore the Python handler */
  /* FIXME */
  /* PyOS_setsig(SIGINT, python_sighandler); */

  PyObject *self = (PyObject *)dd->deviceSpecific;
  /* FIXME optimize ? */
  PyObject *py_x1 = PyFloat_FromDouble(x1);
  PyObject *py_y1 = PyFloat_FromDouble(y1);
  PyObject *py_x2 = PyFloat_FromDouble(x2);
  PyObject *py_y2 = PyFloat_FromDouble(y2);
  /* FIXME pass gc ? */
  result = PyObject_CallMethodObjArgs(self, GrDev_line_name, 
                                      py_x1, py_y1, py_x2, py_y2,
                                      NULL);

  rpy_printandclear_error();
  Py_DECREF(result);  
}

PyDoc_STRVAR(GrDev_line_doc,
             "Draw a line on the graphical device.");
static PyObject* GrDev_line(PyObject *self, PyObject *args)
{
  PyErr_Format(PyExc_NotImplementedError, 
               "Device line not implemented.\n"
               "[expected signature is (x1, y1, x2, y2)]");
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject* GrDev_polyline_name;
static void rpy_PolyLine(int n, double *x, double *y, 
                         const pGEcontext gc, pDevDesc dd)
{
  PyObject *result;

  /* Restore the Python handler */
  /* FIXME */
  /* PyOS_setsig(SIGINT, python_sighandler); */

  PyObject *self = (PyObject *)dd->deviceSpecific;
  /* FIXME optimize ? */
  #ifdef RPY_DEBUG_GRDEV
  printf("FIXME: PolyLine.\n");
  #endif
  PyObject *py_x = PyFloat_FromDouble(*x);
  PyObject *py_y = PyFloat_FromDouble(*y);
  /* FIXME pass gc ? */
  result = PyObject_CallMethodObjArgs(self, GrDev_polyline_name, 
                                      py_x, py_y,
                                      NULL);

  rpy_printandclear_error();
  Py_DECREF(result);  
}

PyDoc_STRVAR(GrDev_polyline_doc,
             "Draw a polyline on the graphical device.");
static PyObject* GrDev_polyline(PyObject *self, PyObject *args)
{
  PyErr_Format(PyExc_NotImplementedError, "Device polyline not implemented.");
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject* GrDev_polygon_name;
static void rpy_Polygon(int n, double *x, double *y, 
                        const pGEcontext gc, pDevDesc dd)
{
  PyObject *result;

  /* Restore the Python handler */
  /* FIXME */
  /* PyOS_setsig(SIGINT, python_sighandler); */

  PyObject *self = (PyObject *)dd->deviceSpecific;
  /* FIXME optimize ? */
#ifdef RPY_DEBUG_GRDEV
  printf("FIXME: Polygon.\n");
#endif
  PyObject *py_x = PyFloat_FromDouble(*x);
  PyObject *py_y = PyFloat_FromDouble(*y);
  /* FIXME pass gc ? */
  result = PyObject_CallMethodObjArgs(self, GrDev_polygon_name, 
                                      py_x, py_y,
                                      NULL);
  rpy_printandclear_error();
  Py_DECREF(result);  
}

PyDoc_STRVAR(GrDev_polygon_doc,
             "Draw a polygon on the graphical device.");
static PyObject* GrDev_polygon(PyObject *self, PyObject *args)
{
  PyErr_Format(PyExc_NotImplementedError, "Device polygon not implemented.");
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject* GrDev_locator_name;
static Rboolean rpy_Locator(double *x, double *y, pDevDesc dd)
{
  PyObject *result;

  /* Restore the Python handler */
  /* FIXME */
  /* PyOS_setsig(SIGINT, python_sighandler); */

  PyObject *self = (PyObject *)dd->deviceSpecific;
  /* FIXME optimize ? */
#ifdef RPY_DEBUG_GRDEV
  printf("FIXME: Locator.\n");
#endif
  PyObject *py_x = PyFloat_FromDouble(*x);
  PyObject *py_y = PyFloat_FromDouble(*y);
  /* FIXME: pass gc ? */
  /* FIXME: test !dd->dev->locator before proceed ? */
  result = PyObject_CallMethodObjArgs(self, GrDev_locator_name, 
                                      py_x, py_y,
                                      NULL);

  rpy_printandclear_error();

  if (! PyTuple_Check(result) ) {
    PyErr_Format(PyExc_ValueError, "Callback 'size' should return a tuple.");
    rpy_printandclear_error();
  } else if (PyTuple_Size(result) != 2) {
    PyErr_Format(PyExc_ValueError, "Callback 'size' should return a tuple of length 2.");
    rpy_printandclear_error();    
  } else {
    *x = PyFloat_AsDouble(PyTuple_GetItem(result, 0));
    *y = PyFloat_AsDouble(PyTuple_GetItem(result, 1));
  }

  Rboolean res_r = TRUE;
  printf("FIXME: return TRUE or FALSE");
  Py_DECREF(result);
  return res_r;
}

PyDoc_STRVAR(GrDev_locator_doc,
             "Locator on the graphical device.");
static PyObject* GrDev_locator(PyObject *self, PyObject *args)
{
  PyErr_Format(PyExc_NotImplementedError, "Device locator not implemented.");
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject* GrDev_mode_name;
static void rpy_Mode(int mode, pDevDesc dd)
{
  PyObject *result;

  /* Restore the Python handler */
  /* FIXME */
  /* PyOS_setsig(SIGINT, python_sighandler); */

  PyObject *self = (PyObject *)dd->deviceSpecific;
  PyObject *py_mode = PyInt_FromLong((long)mode);
  result = PyObject_CallMethodObjArgs(self, GrDev_mode_name, 
                                      py_mode,
                                      NULL);
  rpy_printandclear_error();
  Py_DECREF(result);  
}

PyDoc_STRVAR(GrDev_mode_doc,
             "Mode on the graphical device.");
static PyObject* GrDev_mode(PyObject *self)
{
  PyErr_Format(PyExc_NotImplementedError, "Device mode not implemented.");
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject* GrDev_metricinfo_name;
static void rpy_MetricInfo(int c, const pGEcontext gc, 
                           double* ascent, double* descent, double *width,
                           pDevDesc dd)
{
  PyObject *result;

  /* Restore the Python handler */
  /* FIXME */
  /* PyOS_setsig(SIGINT, python_sighandler); */
  
  PyObject *self = (PyObject *)dd->deviceSpecific;
  /* FIXME optimize ? */
#ifdef RPY_DEBUG_GRDEV
  printf("FIXME: MetricInfo.\n");
#endif
  PyObject *py_c = PyInt_FromLong((long)c);
  PyObject *py_ascent = PyFloat_FromDouble(*ascent);
  PyObject *py_descent = PyFloat_FromDouble(*descent);
  PyObject *py_width = PyFloat_FromDouble(*width);
  /* FIXME pass gc ? */
  result = PyObject_CallMethodObjArgs(self, GrDev_metricinfo_name, 
                                      py_c,
                                      py_ascent, py_descent, py_width,
                                      NULL);

  rpy_printandclear_error();


  if (! PyTuple_Check(result) ) {
    PyErr_Format(PyExc_ValueError, "Callback 'size' should return a tuple.");
    rpy_printandclear_error();
  } else if (PyTuple_Size(result) != 3) {
    PyErr_Format(PyExc_ValueError, "Callback 'metricinfo' should return a tuple of length 3.");
    rpy_printandclear_error();    
  } else {
    *ascent = PyFloat_AsDouble(PyTuple_GetItem(result, 0));
    *descent = PyFloat_AsDouble(PyTuple_GetItem(result, 1));
    *width = PyFloat_AsDouble(PyTuple_GetItem(result, 2));
  }
  Py_DECREF(result);

}

PyDoc_STRVAR(GrDev_metricinfo_doc,
             "MetricInfo on the graphical device.");
static PyObject* GrDev_metricinfo(PyObject *self, PyObject *args)
{
  PyErr_Format(PyExc_NotImplementedError, "Device metricinfo not implemented.");
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject* GrDev_getevent_name;
static SEXP rpy_GetEvent(SEXP rho, const char *prompt)
{
  SEXP r_res = R_NilValue;
  PyObject *result;

  pGEDevDesc dd = GEcurrentDevice();
  /* Restore the Python handler */
  /* FIXME */
  /* PyOS_setsig(SIGINT, python_sighandler); */

  PyObject *self = (PyObject *)dd->dev->deviceSpecific;
  /* FIXME optimize ? */
#ifdef RPY_DEBUG_GRDEV
  printf("FIXME: MetricInfo.\n");
#endif
  PyObject *py_prompt = PyString_FromString(prompt);
  /* FIXME pass gc ? */
  result = PyObject_CallMethodObjArgs(self, GrDev_getevent_name,
                                      py_prompt,
                                      NULL);

  rpy_printandclear_error();
  /* FIXME: check that the method only returns PySexp ? */
  printf("FIXME: check that only PySexp returned.\n");

  r_res = RPY_SEXP((PySexpObject *)result);
  /* FIXME: handle refcount and protection of the resulting r_res */
  printf("FIXME: handle refcount and protection of the resulting r_res");
  Py_DECREF(result);
  return r_res;
}

PyDoc_STRVAR(GrDev_getevent_doc,
             "Get even on the graphical device.");
static PyObject* GrDev_getevent(PyObject *self, PyObject *args)
{
  PyErr_Format(PyExc_NotImplementedError, "Device getevent not implemented.");
  Py_INCREF(Py_None);
  return Py_None;
}



void configureDevice(pDevDesc dd, PyObject *self)
{
  /* setup structure */
  dd->deviceSpecific = (void *) self;
  dd->close = rpy_Close;
  dd->activate = rpy_Activate;
  dd->deactivate = rpy_Deactivate;
  dd->size = rpy_Size;
  dd->newPage = rpy_NewPage;
  dd->clip = rpy_Clip;
  /* Next two are unused */
  dd->strWidth = rpy_StrWidth;
  dd->text = rpy_Text;
  dd->rect = rpy_Rect;
  dd->circle = rpy_Circle;
  dd->line = rpy_Line;
  dd->polyline = rpy_PolyLine;
  dd->polygon = rpy_Polygon;
  dd->locator = rpy_Locator;
  dd->mode = rpy_Mode;
  dd->metricInfo = rpy_MetricInfo;
  dd->getEvent = rpy_GetEvent;
  /* FIXME: initialization from self.attribute */
  dd->hasTextUTF8 = TRUE; /*PyObject_GetAttrString(self, ); */
  dd->wantSymbolUTF8 = TRUE;   /* FIXME: initialization from self.attribute */
  dd->strWidthUTF8 = rpy_StrWidth;
  dd->textUTF8 = rpy_Text;

  dd->left = 0;   /* FIXME: initialization from self.attribute */
  dd->right = 100;   /* FIXME: initialization from self.attribute */
  dd->bottom = 100;   /* FIXME: initialization from self.attribute */
  dd->top = 0;   /* FIXME: initialization from self.attribute */

  /* starting parameters */
  dd->startfont = 1; 
  dd->startps = 12.0; /* ps *  */
  dd->startcol = R_RGB(0, 0, 0);
  dd->startfill = R_TRANWHITE;
  dd->startlty = LTY_SOLID; 
  dd->startgamma = 1;
        
  /* dd->cra[0] = 0.9 * 12; */
  /* dd->cra[1] = 1.2 * 12; */
        
  /* character addressing offsets */
  dd->xCharOffset = 0.4900;
  dd->yCharOffset = 0.3333;
  dd->yLineBias = 0.1;

  /* inches per raster unit */
  dd->ipr[0] = 1;
  dd->ipr[1] = 1;

  /* device capabilities */
  dd->canClip = FALSE;
  dd->canHAdj = 0; /* text adjustment 0, 1, or 2 */
  dd->canChangeGamma = FALSE; /* FIXME: what is this ? */

  dd->canGenMouseDown = TRUE; /* can the device generate mousedown events */
  dd->canGenMouseMove = TRUE; /* can the device generate mousemove events */
  dd->canGenMouseUp = TRUE;   /* can the device generate mouseup events */
  
  dd->canGenKeybd = TRUE;     /* can the device generate keyboard events */
    
  dd->displayListOn = TRUE;
        
  /* finish */
}

static void
GrDev_clear(PyGrDevObject *self)
{
  /* FIXME */
  printf("FIXME: Clearing GrDev.\n");
  printf("  done.\n");
}

static void
GrDev_dealloc(PyGrDevObject *self)
{
  /* FIXME */
#ifdef RPY_DEBUG_GRDEV
  printf("FIXME: Deallocating GrDev.\n");
#endif
  R_ReleaseObject(self->devnum);
  PyMem_Free(((PyGrDevObject *)self)->grdev);
  self->ob_type->tp_free((PyObject*)self);
#ifdef RPY_DEBUG_GRDEV
  printf("  done.\n");
#endif
}

static PyObject*
GrDev_repr(PyObject *self)
{
  pDevDesc devdesc = ((PyGrDevObject *)self)->grdev;
  return PyString_FromFormat("<%s - Python:\%p / R graphical device:\%p>",
                             self->ob_type->tp_name,
                             self,
                             devdesc);
}

static PyMethodDef GrDev_methods[] = {
  {"close", (PyCFunction)GrDev_close, METH_NOARGS,
   GrDev_close_doc},
  {"activate", (PyCFunction)GrDev_activate, METH_NOARGS,
   GrDev_activate_doc},
  {"deactivate", (PyCFunction)GrDev_deactivate, METH_NOARGS,
   GrDev_deactivate_doc},
  {"size", (PyCFunction)GrDev_size, METH_VARARGS,
   GrDev_size_doc},
  {"newpage", (PyCFunction)GrDev_newpage, METH_VARARGS,
   GrDev_newpage_doc},
  {"clip", (PyCFunction)GrDev_clip, METH_VARARGS,
   GrDev_clip_doc},
  {"strwidth", (PyCFunction)GrDev_strwidth, METH_VARARGS,
   GrDev_strwidth_doc},
  {"text", (PyCFunction)GrDev_text, METH_VARARGS,
   GrDev_text_doc},
  {"rect", (PyCFunction)GrDev_rect, METH_VARARGS,
   GrDev_rect_doc},
  {"circle", (PyCFunction)GrDev_circle, METH_VARARGS,
   GrDev_circle_doc},
  {"line", (PyCFunction)GrDev_line, METH_VARARGS,
   GrDev_line_doc},
  {"polyline", (PyCFunction)GrDev_polyline, METH_VARARGS,
   GrDev_polyline_doc},
  {"polygon", (PyCFunction)GrDev_polygon, METH_VARARGS,
   GrDev_polygon_doc},
  {"locator", (PyCFunction)GrDev_locator, METH_VARARGS,
   GrDev_locator_doc},
  {"mode", (PyCFunction)GrDev_mode, METH_VARARGS,
   GrDev_mode_doc},
  {"metricinfo", (PyCFunction)GrDev_metricinfo, METH_VARARGS,
   GrDev_metricinfo_doc},
  {"getevent", (PyCFunction)GrDev_getevent, METH_VARARGS,
   GrDev_getevent_doc},
  /* */
  {NULL, NULL}          /* sentinel */
};


PyDoc_STRVAR(GrDev_hasTextUTF8_doc,
             "UTF8 capabilities of the device.");
static PyObject*
GrDev_hasTextUTF8_get(PyObject *self)
{
  PyObject *res;
  if (((PyGrDevObject *)self)->grdev->hasTextUTF8 == TRUE) {
    res = Py_True;
  } else {
    res = Py_False;
  }
  Py_INCREF(res);
  return res;
}
static int
GrDev_hasTextUTF8_set(PyObject *self, PyObject *value)
{
  if (value == NULL) {
    PyErr_SetString(PyExc_TypeError, 
                    "The attribute hasTextUTF8 cannot be deleted");
    return -1;
  }
  if (! PyBool_Check(value)) {
    PyErr_SetString(PyExc_TypeError, 
                    "The attribute hasTextUTF8 must be a boolean");
    return -1;
  }
  if (value == Py_True) {
    ((PyGrDevObject *)self)->grdev->hasTextUTF8 = TRUE;    
  } else if (value == Py_False) {
    ((PyGrDevObject *)self)->grdev->hasTextUTF8 = FALSE;
  } else {
    PyErr_SetString(PyExc_TypeError,
                    "Mysterious error when setting the attribute hasTextUTF8.");
    return -1;
  }
  return 0;
}

PyDoc_STRVAR(GrDev_wantSymbolUTF8_doc,
             "UTF8 capabilities of the device.");
static PyObject*
GrDev_wantSymbolUTF8_get(PyObject *self)
{
  PyObject *res;
  if (((PyGrDevObject *)self)->grdev->wantSymbolUTF8 == TRUE) {
    res = Py_True;
  } else {
    res = Py_False;
  }
  Py_INCREF(res);
  return res;
}
static int
GrDev_wantSymbolUTF8_set(PyObject *self, PyObject *value)
{
  if (value == NULL) {
    PyErr_SetString(PyExc_TypeError, 
                    "The attribute wantSymbolUTF8 cannot be deleted");
    return -1;
  }
  if (! PyBool_Check(value)) {
    PyErr_SetString(PyExc_TypeError, 
                    "The attribute wantSymbolUTF8 must be a boolean");
    return -1;
  }
  if (value == Py_True) {
    ((PyGrDevObject *)self)->grdev->wantSymbolUTF8 = TRUE;    
  } else if (value == Py_False) {
    ((PyGrDevObject *)self)->grdev->wantSymbolUTF8 = FALSE;
  } else {
    PyErr_SetString(PyExc_TypeError,
                    "Mysterious error when setting the attribute hasTextUTF8.");
    return -1;
  }
  return 0;
}

PyDoc_STRVAR(GrDev_left_doc,
             "Left coordinate.");
static PyObject*
GrDev_left_get(PyObject *self)
{
  PyObject *res;
  res = PyFloat_FromDouble(((PyGrDevObject *)self)->grdev->left);
  return res;
}
static int
GrDev_left_set(PyObject *self, PyObject *value)
{
  if (value == NULL) {
    PyErr_SetString(PyExc_TypeError, 
                    "The attribute left cannot be deleted");
    return -1;
  }
  if (! PyFloat_Check(value)) {
    PyErr_SetString(PyExc_TypeError, 
                    "The attribute left must be a float");
    return -1;
  }
  ((PyGrDevObject *)self)->grdev->left = PyFloat_AsDouble(value);    
  return 0;
}


PyDoc_STRVAR(GrDev_right_doc,
             "Right coordinate.");
static PyObject*
GrDev_right_get(PyObject *self)
{
  PyObject *res;
  res = PyFloat_FromDouble(((PyGrDevObject *)self)->grdev->right);
  return res;
}
static int
GrDev_right_set(PyObject *self, PyObject *value)
{
  if (value == NULL) {
    PyErr_SetString(PyExc_TypeError, 
                    "The attribute right cannot be deleted");
    return -1;
  }
  if (! PyFloat_Check(value)) {
    PyErr_SetString(PyExc_TypeError, 
                    "The attribute right must be a float");
    return -1;
  }
  ((PyGrDevObject *)self)->grdev->right = PyFloat_AsDouble(value);    
  return 0;
}

PyDoc_STRVAR(GrDev_top_doc,
             "Top coordinate.");
static PyObject*
GrDev_top_get(PyObject *self)
{
  PyObject *res;
  res = PyFloat_FromDouble(((PyGrDevObject *)self)->grdev->top);
  return res;
}
static int
GrDev_top_set(PyObject *self, PyObject *value)
{
  if (value == NULL) {
    PyErr_SetString(PyExc_TypeError, 
                    "The attribute top cannot be deleted");
    return -1;
  }
  if (! PyFloat_Check(value)) {
    PyErr_SetString(PyExc_TypeError, 
                    "The attribute top must be a float");
    return -1;
  }
  ((PyGrDevObject *)self)->grdev->top = PyFloat_AsDouble(value);    
  return 0;
}

PyDoc_STRVAR(GrDev_bottom_doc,
             "Bottom coordinate.");
static PyObject*
GrDev_bottom_get(PyObject *self)
{
  PyObject *res;
  res = PyFloat_FromDouble(((PyGrDevObject *)self)->grdev->bottom);
  return res;
}
static int
GrDev_bottom_set(PyObject *self, PyObject *value)
{
  if (value == NULL) {
    PyErr_SetString(PyExc_TypeError, 
                    "The attribute bottom cannot be deleted");
    return -1;
  }
  if (! PyFloat_Check(value)) {
    PyErr_SetString(PyExc_TypeError, 
                    "The attribute bottom must be a float");
    return -1;
  }
  ((PyGrDevObject *)self)->grdev->bottom = PyFloat_AsDouble(value);    
  return 0;
}

PyDoc_STRVAR(GrDev_canGenMouseDown_doc,
             "Ability to generate mouse down events.");
static PyObject*
GrDev_canGenMouseDown_get(PyObject *self)
{
  PyObject *res;
  if (((PyGrDevObject *)self)->grdev->canGenMouseDown == TRUE) {
    res = Py_True;
  } else {
    res = Py_False;
  }
  Py_INCREF(res);
  return res;
}
static int
GrDev_canGenMouseDown_set(PyObject *self, PyObject *value)
{
  if (value == NULL) {
    PyErr_SetString(PyExc_TypeError, 
                    "The attribute canGenMouseDown cannot be deleted");
    return -1;
  }
  if (! PyBool_Check(value)) {
    PyErr_SetString(PyExc_TypeError, 
                    "The attribute canGenMouseDown must be a boolean");
    return -1;
  }
  if (value == Py_True) {
    ((PyGrDevObject *)self)->grdev->canGenMouseDown = TRUE;    
  } else if (value == Py_False) {
    ((PyGrDevObject *)self)->grdev->canGenMouseDown = FALSE;
  } else {
    PyErr_SetString(PyExc_TypeError,
                    "Mysterious error when setting the attribute canGenMouseDown.");
    return -1;
  }
  return 0;
}


PyDoc_STRVAR(GrDev_canGenMouseMove_doc,
             "Ability to generate mouse move events.");
static PyObject*
GrDev_canGenMouseMove_get(PyObject *self)
{
  PyObject *res;
  if (((PyGrDevObject *)self)->grdev->canGenMouseMove == TRUE) {
    res = Py_True;
  } else {
    res = Py_False;
  }
  Py_INCREF(res);
  return res;
}
static int
GrDev_canGenMouseMove_set(PyObject *self, PyObject *value)
{
  if (value == NULL) {
    PyErr_SetString(PyExc_TypeError, 
                    "The attribute canGenMouseMove cannot be deleted");
    return -1;
  }
  if (! PyBool_Check(value)) {
    PyErr_SetString(PyExc_TypeError, 
                    "The attribute canGenMouseMove must be a boolean");
    return -1;
  }
  if (value == Py_True) {
    ((PyGrDevObject *)self)->grdev->canGenMouseMove = TRUE;    
  } else if (value == Py_False) {
    ((PyGrDevObject *)self)->grdev->canGenMouseMove = FALSE;
  } else {
    PyErr_SetString(PyExc_TypeError,
                    "Mysterious error when setting the attribute canGenMouseMove.");
    return -1;
  }
  return 0;
}


PyDoc_STRVAR(GrDev_canGenMouseUp_doc,
             "Ability to generate mouse up events.");
static PyObject*
GrDev_canGenMouseUp_get(PyObject *self)
{
  PyObject *res;
  if (((PyGrDevObject *)self)->grdev->canGenMouseUp == TRUE) {
    res = Py_True;
  } else {
    res = Py_False;
  }
  Py_INCREF(res);
  return res;
}
static int
GrDev_canGenMouseUp_set(PyObject *self, PyObject *value)
{
  if (value == NULL) {
    PyErr_SetString(PyExc_TypeError, 
                    "The attribute canGenMouseUp cannot be deleted");
    return -1;
  }
  if (! PyBool_Check(value)) {
    PyErr_SetString(PyExc_TypeError, 
                    "The attribute canGenMouseUp must be a boolean");
    return -1;
  }
  if (value == Py_True) {
    ((PyGrDevObject *)self)->grdev->canGenMouseUp = TRUE;    
  } else if (value == Py_False) {
    ((PyGrDevObject *)self)->grdev->canGenMouseUp = FALSE;
  } else {
    PyErr_SetString(PyExc_TypeError,
                    "Mysterious error when setting the attribute canGenMouseUp.");
    return -1;
  }
  return 0;
}


PyDoc_STRVAR(GrDev_canGenKeybd_doc,
             "Ability to generate keyboard events.");
static PyObject*
GrDev_canGenKeybd_get(PyObject *self)
{
  PyObject *res;
  if (((PyGrDevObject *)self)->grdev->canGenKeybd == TRUE) {
    res = Py_True;
  } else {
    res = Py_False;
  }
  Py_INCREF(res);
  return res;
}
static int
GrDev_canGenKeybd_set(PyObject *self, PyObject *value)
{
  if (value == NULL) {
    PyErr_SetString(PyExc_TypeError, 
                    "The attribute canGenKeydb cannot be deleted");
    return -1;
  }
  if (! PyBool_Check(value)) {
    PyErr_SetString(PyExc_TypeError, 
                    "The attribute canGenKeybd must be a boolean");
    return -1;
  }
  if (value == Py_True) {
    ((PyGrDevObject *)self)->grdev->canGenKeybd = TRUE;    
  } else if (value == Py_False) {
    ((PyGrDevObject *)self)->grdev->canGenKeybd = FALSE;
  } else {
    PyErr_SetString(PyExc_TypeError,
                    "Mysterious error when setting the attribute canGenKeybd.");
    return -1;
  }
  return 0;
}

PyDoc_STRVAR(GrDev_displayListOn_doc,
             "Status of the display list.");
static PyObject*
GrDev_displayListOn_get(PyObject *self)
{
  PyObject *res;
  if (((PyGrDevObject *)self)->grdev->displayListOn == TRUE) {
    res = Py_True;
  } else {
    res = Py_False;
  }
  Py_INCREF(res);
  return res;
}
static int
GrDev_displayListOn_set(PyObject *self, PyObject *value)
{
  if (value == NULL) {
    PyErr_SetString(PyExc_TypeError, 
                    "The attribute displayListOn cannot be deleted");
    return -1;
  }
  if (! PyBool_Check(value)) {
    PyErr_SetString(PyExc_TypeError, 
                    "The attribute displayListOn must be a boolean");
    return -1;
  }
  if (value == Py_True) {
    ((PyGrDevObject *)self)->grdev->displayListOn = TRUE;    
  } else if (value == Py_False) {
    ((PyGrDevObject *)self)->grdev->displayListOn = FALSE;
  } else {
    PyErr_SetString(PyExc_TypeError,
                    "Mysterious error when setting the attribute displayListOn.");
    return -1;
  }
  return 0;
}


PyDoc_STRVAR(GrDev_devnum_doc,
             "Device number.");
static PyObject* GrDev_devnum_get(PyObject* self)
{
  PyObject* res;
  if ( ((PyGrDevObject *)self)->devnum == R_NilValue) {
    Py_INCREF(Py_None);
    res = Py_None;
  } else {
    res = PyInt_FromLong((long)RPY_DEV_NUM(self));
  }
  return res;

}

 
static PyGetSetDef GrDev_getsets[] = {
  {"hasTextUTF8", 
   (getter)GrDev_hasTextUTF8_get,
   (setter)GrDev_hasTextUTF8_set,
   GrDev_hasTextUTF8_doc},
  {"wantSymbolUTF8", 
   (getter)GrDev_wantSymbolUTF8_get,
   (setter)GrDev_wantSymbolUTF8_set,
   GrDev_wantSymbolUTF8_doc},
  {"left", 
   (getter)GrDev_left_get,
   (setter)GrDev_left_set,
   GrDev_left_doc},
  {"right", 
   (getter)GrDev_right_get,
   (setter)GrDev_right_set,
   GrDev_right_doc},
  {"top", 
   (getter)GrDev_top_get,
   (setter)GrDev_top_set,
   GrDev_top_doc},
  {"bottom", 
   (getter)GrDev_bottom_get,
   (setter)GrDev_bottom_set,
   GrDev_bottom_doc},
  {"canGenMouseDown", 
   (getter)GrDev_canGenMouseDown_get,
   (setter)GrDev_canGenMouseDown_set,
   GrDev_canGenMouseDown_doc},
  {"canGenMouseMove", 
   (getter)GrDev_canGenMouseMove_get,
   (setter)GrDev_canGenMouseMove_set,
   GrDev_canGenMouseMove_doc},
  {"canGenMouseUp", 
   (getter)GrDev_canGenMouseUp_get,
   (setter)GrDev_canGenMouseUp_set,
   GrDev_canGenMouseUp_doc},
  {"canGenKeybd", 
   (getter)GrDev_canGenKeybd_get,
   (setter)GrDev_canGenKeybd_set,
   GrDev_canGenKeybd_doc},
  {"displayListOn", 
   (getter)GrDev_displayListOn_get,
   (setter)GrDev_displayListOn_set,
   GrDev_displayListOn_doc},
  /* */
  {"devnum",
   (getter)GrDev_devnum_get,
   NULL,
   GrDev_devnum_doc},
  /* */
  {NULL, NULL, NULL, NULL}          /* sentinel */
};


static PyObject*
GrDev_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{

  /* FIXME: should this be checked and raise an exception if necessary ? */
  /* R_CheckDeviceAvailable(); */

#ifdef RPY_DEBUG_GRDEV
  printf("FIXME: New GrDev\n");
#endif
  PyGrDevObject *self;
  self = (PyGrDevObject *)type->tp_alloc(type, 0);

  if (! self)
    PyErr_NoMemory();

  self->grdev = (pDevDesc)PyMem_Malloc(1 * sizeof(DevDesc));
  /* FIXME: fallback if memory allocation error ? */
  self->devnum = R_NilValue;
#ifdef RPY_DEBUG_GRDEV
  printf("  done.\n");
#endif
  return(PyObject *)self;
}


static int
GrDev_init(PyObject *self, PyObject *args, PyObject *kwds)
{
#ifdef RPY_DEBUG_GRDEV
  printf("FIXME: Initializing GrDev\n");
#endif
  pDevDesc dd = ((PyGrDevObject *)self)->grdev;

  configureDevice(dd, self);
  pGEDevDesc gdd = GEcreateDevDesc(dd);

  GEaddDevice2(gdd, self->ob_type->tp_name);

  ((PyGrDevObject *)self)->devnum = ScalarInteger(ndevNumber(dd) + 1);
  R_PreserveObject(((PyGrDevObject *)self)->devnum);
  /* FIXME: protect device number ? */
  /* allocate memory for the pDevDesc structure ? */
  /* pDevDesc grdev = malloc(); */
  /* FIXME: handle allocation error */
  /* self->grdev = grdev; */
  printf("  done.\n");
  return 0;
}

/*
 * Generic graphical device.
 */
static PyTypeObject GrDev_Type = {
        /* The ob_type field must be initialized in the module init function
         * to be portable to Windows without using C++. */
        PyObject_HEAD_INIT(NULL)
        0,                      /*ob_size*/
        "rpy2.rinterface.GraphicalDevice",   /*tp_name*/
        sizeof(PyGrDevObject),  /*tp_basicsize*/
        0,                      /*tp_itemsize*/
        /* methods */
        (destructor)GrDev_dealloc, /*tp_dealloc*/
        0,                      /*tp_print*/
        0,                      /*tp_getattr*/
        0,                      /*tp_setattr*/
        0,                      /*tp_compare*/
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
        0,                      /*tp_doc*/
        0,                      /*tp_traverse*/
        0,/*(inquiry)Sexp_clear, tp_clear*/
        0,                      /*tp_richcompare*/
        0,                      /*tp_weaklistoffset*/
        0,                      /*tp_iter*/
        0,                      /*tp_iternext*/
        GrDev_methods,           /*tp_methods*/
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
};

static PyMethodDef rpydevice_methods[] = {
  {NULL,                NULL}           /* sentinel */
};



#ifndef PyMODINIT_FUNC  /* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif

PyMODINIT_FUNC
initrpy_device(void)
{

  GrDev_close_name = PyString_FromString("close");
  GrDev_activate_name = PyString_FromString("activate");
  GrDev_deactivate_name = PyString_FromString("deactivate");
  GrDev_size_name = PyString_FromString("size");
  GrDev_newpage_name = PyString_FromString("newpage");
  GrDev_clip_name = PyString_FromString("clip");
  GrDev_strwidth_name = PyString_FromString("strwidth");
  GrDev_text_name = PyString_FromString("text");
  GrDev_rect_name = PyString_FromString("rect");
  GrDev_circle_name = PyString_FromString("circle");
  GrDev_line_name = PyString_FromString("line");
  GrDev_polyline_name = PyString_FromString("polyline");
  GrDev_polygon_name = PyString_FromString("polygon");
  GrDev_locator_name = PyString_FromString("locator");
  GrDev_mode_name = PyString_FromString("mode");
  GrDev_metricinfo_name = PyString_FromString("metricinfo");
  GrDev_getevent_name = PyString_FromString("getevent");

  if (PyType_Ready(&GrDev_Type) < 0)
    return;
  
  PyObject *m, *d;
  m = Py_InitModule3("rpy_device", rpydevice_methods, module_doc);
  if (m == NULL)
    return;
  d = PyModule_GetDict(m);

  PyModule_AddObject(m, "GraphicalDevice", (PyObject *)&GrDev_Type);  
}
