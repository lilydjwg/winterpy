#include<Python.h>
#include<X11/Xlib.h>

typedef struct {
  PyObject_HEAD
  Display *dpy;
} xlib_displayObject;

static void xlib_display_del(xlib_displayObject* self){
  Display* dpy;
  if(self->dpy){
    dpy = self->dpy;
    Py_BEGIN_ALLOW_THREADS
    XCloseDisplay(dpy);
    Py_END_ALLOW_THREADS
  }
  Py_TYPE(self)->tp_free((PyObject*)self);
}

static int xlib_display_init(xlib_displayObject* self,
    PyObject *args, PyObject *kwds){
  const char* name = NULL;
  Display* dpy;
  if(!PyArg_ParseTuple(args, "|z", &name))
    return -1;

  Py_BEGIN_ALLOW_THREADS
  dpy = XOpenDisplay(name);
  Py_END_ALLOW_THREADS

  if(dpy == NULL){
    PyErr_SetString(PyExc_ValueError, "failed to open display");
    return -1;
  }
  self->dpy = dpy;

  return 0;
}

static PyObject* xlib_display_get_name(xlib_displayObject* self, void* data){
  return Py_BuildValue("s", DisplayString(self->dpy));
}

PyObject* xlib_flush(xlib_displayObject* self){
  Display *dpy;
  dpy = self->dpy;
  Py_BEGIN_ALLOW_THREADS
  /* XXX: what does the returned value do? */
  XFlush(dpy);
  Py_END_ALLOW_THREADS

  Py_RETURN_NONE;
}

PyObject* xlib_getpos(xlib_displayObject* self){
  Display *dpy;
  XEvent event;
  dpy = self->dpy;

  Py_BEGIN_ALLOW_THREADS
  /* get info about current pointer position */
  XQueryPointer(dpy, RootWindow(dpy, DefaultScreen(dpy)),
      &event.xbutton.root, &event.xbutton.window,
      &event.xbutton.x_root, &event.xbutton.y_root,
      &event.xbutton.x, &event.xbutton.y,
      &event.xbutton.state);
  Py_END_ALLOW_THREADS

  return Py_BuildValue("ii", event.xbutton.x, event.xbutton.y);
}

static PyObject *xtest_motion(xlib_displayObject* self, PyObject* args){
  Display *dpy;
  dpy = self->dpy;
  int x, y;
  unsigned long delay = 0;
  int screen = -1;
  if(!PyArg_ParseTuple(args, "ii|ki", &x, &y, &delay, &screen))
    return NULL;

  Py_BEGIN_ALLOW_THREADS
  XTestFakeMotionEvent(dpy, screen, x, y, delay);
  Py_END_ALLOW_THREADS

  Py_RETURN_NONE;
}

static PyObject *xtest_button(xlib_displayObject* self, PyObject* args){
  Display *dpy;
  dpy = self->dpy;
  unsigned int button = 1;
  int is_press = -1;
  unsigned long delay = 0;
  if(!PyArg_ParseTuple(args, "|iik", &button, &is_press, &delay))
    return NULL;
  if(is_press < -1 || is_press > 1)
    PyErr_SetString(PyExc_ValueError, "is_press should be bool or -1");

  Py_BEGIN_ALLOW_THREADS
  if(is_press == -1){
    XTestFakeButtonEvent(dpy, button, 1, delay);
    XTestFakeButtonEvent(dpy, button, 0, delay);
  }else{
    XTestFakeButtonEvent(dpy, button, is_press, delay);
  }
  Py_END_ALLOW_THREADS

  Py_RETURN_NONE;
}

static PyMethodDef xlib_display_methods[] = {
  {
    "motion", (PyCFunction)xtest_motion, METH_VARARGS,
    "moves the mouse cursor\n" \
      "Arguments are (x, y, delay, screen_number). The latter two are optional."
  },
  {
    "button", (PyCFunction)xtest_button, METH_VARARGS,
    "click the mouse\n" \
      "Arguments are (button, is_press, delay), and all are optional." \
      "button defaults to left button, and delay 0." \
      "is_press defaults to -1, meaning press and release."
  },
  {
    "flush", (PyCFunction)xlib_flush, METH_NOARGS,
    "flush X display"
  },
  {
    "getpos", (PyCFunction)xlib_getpos, METH_NOARGS,
    "get the mouse cursor position"
  },
  {NULL}  /* Sentinel */
};

static PyGetSetDef xlib_display_getset[] = {
  {"name", (getter)xlib_display_get_name, 0, "the display string", NULL},
  {NULL}  /* Sentinel */
};

static PyTypeObject xlib_displayType = {
  PyVarObject_HEAD_INIT(NULL, 0)
  "x.Display",					/* tp_name */
  sizeof(xlib_displayObject),				/* tp_basicsize */
  0,							/* tp_itemsize */
  (destructor)xlib_display_del,				/* tp_dealloc */
  0,							/* tp_print */
  0,							/* tp_getattr */
  0,							/* tp_setattr */
  0,							/* tp_reserved */
  0,							/* tp_repr */
  0,							/* tp_as_number */
  0,							/* tp_as_sequence */
  0,							/* tp_as_mapping */
  0,							/* tp_hash  */
  0,							/* tp_call */
  0,							/* tp_str */
  0,							/* tp_getattro */
  0,							/* tp_setattro */
  0,							/* tp_as_buffer */
  Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,		/* tp_flags */
  "X Display",						/* tp_doc */
  0,							/* tp_traverse */
  0,							/* tp_clear */
  0,							/* tp_richcompare */
  0,							/* tp_weaklistoffset */
  0,							/* tp_iter */
  0,							/* tp_iternext */
  xlib_display_methods,	     				/* tp_methods */
  0,			     				/* tp_members */
  xlib_display_getset,	     				/* tp_getset */
  0,			     				/* tp_base */
  0,			     				/* tp_dict */
  0,			     				/* tp_descr_get */
  0,			     				/* tp_descr_set */
  0,			     				/* tp_dictoffset */
  (initproc)xlib_display_init,				/* tp_init */
  0,			     				/* tp_alloc */
  PyType_GenericNew,		     			/* tp_new */
};

static PyModuleDef xlibmodule = {
  PyModuleDef_HEAD_INIT,
  "X",
  "utils from Xlib and the like",
  -1,
  NULL, NULL, NULL, NULL, NULL
};

PyMODINIT_FUNC PyInit_X(void){
  PyObject* m;

  if(PyType_Ready(&xlib_displayType) < 0)
    return NULL;

  m = PyModule_Create(&xlibmodule);
  if(m == NULL)
    return NULL;

  Py_INCREF(&xlib_displayType);
  PyModule_AddObject(m, "Display", (PyObject *)&xlib_displayType);
  PyModule_AddObject(m, "LEFT_BUTTON", PyLong_FromLong(1));
  PyModule_AddObject(m, "MIDDLE_BUTTON", PyLong_FromLong(2));
  PyModule_AddObject(m, "RIGHT_BUTTON", PyLong_FromLong(3));
  PyModule_AddObject(m, "WHEEL_UP", PyLong_FromLong(4));
  PyModule_AddObject(m, "WHEEL_DOWN", PyLong_FromLong(5));
  return m;
}
/* vim: se path+=/usr/include/python3.2mu: */
