#include<Python.h>
#include<X11/Xlib.h>
#include<X11/keysym.h>
#include<X11/extensions/XTest.h>
#include<X11/extensions/scrnsaver.h>

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

static PyObject *xtest_motion(xlib_displayObject* self, PyObject* args, PyObject* kwds){
  Display *dpy;
  dpy = self->dpy;
  int x, y;
  unsigned long delay = 0;
  int screen = -1;
  static char *kwlist[] = {"x", "y", "delay", "screen", "relative", NULL};
  PyObject* rel;
  int is_rel = 0;

  if(!PyArg_ParseTupleAndKeywords(args, kwds, "ii|kiO!", kwlist, &x, &y,
	&delay, &screen, &PyBool_Type, &rel))
    return NULL;
  is_rel = rel == Py_True;

  Py_BEGIN_ALLOW_THREADS
  if(is_rel){
    /* NOTE: only four args here; the doc is wrong. */
    XTestFakeRelativeMotionEvent(dpy, x, y, delay);
  }else{
    XTestFakeMotionEvent(dpy, screen, x, y, delay);
  }
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
  if(is_press < -1 || is_press > 1){
    PyErr_SetString(PyExc_ValueError, "is_press should be bool or -1");
    return NULL;
  }

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

static PyObject *xtest_key(xlib_displayObject* self, PyObject* args){
  Display *dpy;
  dpy = self->dpy;
  unsigned int keycode = 1;
  int is_press = -1;
  unsigned long delay = 0;
  PyObject* key;
  PyObject* obj;
  const char* keystr;
  KeySym keysym, key_lower, key_upper;
  KeyCode shiftkeycode = 0;

  if(!PyArg_ParseTuple(args, "O|ik", &key, &is_press, &delay))
    return NULL;
  Py_INCREF(key);
  if(PyUnicode_Check(key)){
    obj = PyUnicode_EncodeFSDefault(key);
    Py_DECREF(key);
    keystr = PyBytes_AsString(obj);
    Py_BEGIN_ALLOW_THREADS
    keysym = XStringToKeysym(keystr);
    if(keysym == NoSymbol){
      keycode = 0;
    }else{
      keycode = XKeysymToKeycode(dpy, keysym);
    }
    Py_END_ALLOW_THREADS
    if(keycode == 0){/* invalid */
      PyErr_Format(PyExc_ValueError, "invalid keysym name: %s", keystr);
      Py_DECREF(obj);
      return NULL;
    }
    Py_DECREF(obj);
  }else if(PyLong_Check(key)){
    keycode = PyLong_AsUnsignedLong(key);
    Py_DECREF(key);
  }else{
    obj = PyObject_Type(key);
    Py_DECREF(key);
    key = PyObject_GetAttrString(obj, "__name__");
    Py_DECREF(obj);
    PyErr_Format(PyExc_TypeError, "int or str expected, but got: %S", key);
    Py_DECREF(key);
    return NULL;
  }
  if(is_press < -1 || is_press > 1){
    PyErr_SetString(PyExc_ValueError, "is_press should be bool or -1");
    return NULL;
  }

  Py_BEGIN_ALLOW_THREADS
  if(is_press == -1){
    XConvertCase(keysym, &key_lower, &key_upper);
    if(keysym == key_upper && keysym != key_lower){
      shiftkeycode = XKeysymToKeycode(dpy, XK_Shift_L);
      XTestFakeKeyEvent(dpy, shiftkeycode, 1, delay);
    }
  }
  if(is_press == -1){
    /*
     * FIXME: if delay specified, keypress will be repeated several times after
     * the correct one after a small delay. */
    XTestFakeKeyEvent(dpy, keycode, 1, delay);
    XTestFakeKeyEvent(dpy, keycode, 0, delay);
    if(shiftkeycode != 0){
      XTestFakeKeyEvent(dpy, shiftkeycode, 0, delay);
    }
  }else{
    XTestFakeKeyEvent(dpy, keycode, is_press, delay);
  }
  Py_END_ALLOW_THREADS

  Py_RETURN_NONE;
}

static PyObject *scrnsaver_idletime(xlib_displayObject* self){
  Display *display = self->dpy;
  XScreenSaverInfo *info;

  Py_BEGIN_ALLOW_THREADS
  info = XScreenSaverAllocInfo();
  XScreenSaverQueryInfo(display, DefaultRootWindow(display), info);
  Py_END_ALLOW_THREADS

  return PyLong_FromUnsignedLong(info->idle);
}

static PyObject* scrnsaver_state(xlib_displayObject* self){
  /*
   * In my practice, ScreenSaverDisabled iPyUnicode_AS_DATAs got if the monitor is on, and
   * ScreenSaverOn if it is off. `kind` is always ScreenSaverBlanked.
   */
  Display *dpy;
  XScreenSaverInfo *info;
  int ss_event, ss_error;
  int state, kind;
  dpy = self->dpy;

  if(XScreenSaverQueryExtension(dpy, &ss_event, &ss_error)){
    Py_BEGIN_ALLOW_THREADS
    info = XScreenSaverAllocInfo();
    XScreenSaverQueryInfo(dpy, DefaultRootWindow(dpy), info);
    state = info->state;
    kind = info->kind;
    XFree(info);
    switch(state){
      case ScreenSaverOff:
	state = 0;
	break;
      case ScreenSaverOn:
	state = 1;
	break;
      case ScreenSaverDisabled:
	state = -1;
	break;
      default:
	state = -2;
    }
    Py_END_ALLOW_THREADS
    return Py_BuildValue("ii", state, kind);
  }else{
    PyErr_SetString(PyExc_RuntimeError, "XScreeSaver not supported");
    return NULL;
  }
}

static PyMethodDef xlib_display_methods[] = {
  {
    "button", (PyCFunction)xtest_button, METH_VARARGS,
    "click the mouse\n" \
      "Arguments are (button, is_press, delay), and all are optional.\n" \
      ".button. defaults to left button, and delay 0. " \
      "`is_press` defaults to -1, meaning press and release."
  },
  {
    "flush", (PyCFunction)xlib_flush, METH_NOARGS,
    "flush X display"
  },
  {
    "getpos", (PyCFunction)xlib_getpos, METH_NOARGS,
    "get the mouse cursor position"
  },
  {
    "idletime", (PyCFunction)scrnsaver_idletime, METH_NOARGS,
    "get user idle time in milliseconds"
  },
  {
    "key", (PyCFunction)xtest_key, METH_VARARGS,
    "press the keyboard\n" \
      "Arguments are (key, is_press, delay), the latter two are optional.\n" \
      "`key` can be keycode or keysym name. `delay` defaults to 0. " \
      "`is_press` defaults to -1, meaning press and release."
  },
  {
    "motion", (PyCFunction)xtest_motion, METH_VARARGS | METH_KEYWORDS,
    "moves the mouse cursor\n" \
      "Arguments are (x, y, delay, screen, relative). The latter three are optional.\n" \
      "`relative` is a boolean indicating if the motion is relative."
  },
  {
    "screensaver_state", (PyCFunction)scrnsaver_state, METH_NOARGS,
    "get the screensaver state, returns a tuple of (state, kind)\n" \
      "`state` can be 0 for off, 1 for on, -1 for disabled, and -2 for others"
  },
  {NULL}  /* Sentinel */
};

static PyGetSetDef xlib_display_getset[] = {
  {"name", (getter)xlib_display_get_name, 0, "the display string", NULL},
  {NULL}  /* Sentinel */
};

static PyTypeObject xlib_displayType = {
  PyVarObject_HEAD_INIT(NULL, 0)
  "Display",            /* tp_name */
  sizeof(xlib_displayObject),       /* tp_basicsize */
  0,              /* tp_itemsize */
  (destructor)xlib_display_del,       /* tp_dealloc */
  0,              /* tp_print */
  0,              /* tp_getattr */
  0,              /* tp_setattr */
  0,              /* tp_reserved */
  0,              /* tp_repr */
  0,              /* tp_as_number */
  0,              /* tp_as_sequence */
  0,              /* tp_as_mapping */
  0,              /* tp_hash  */
  0,              /* tp_call */
  0,              /* tp_str */
  0,              /* tp_getattro */
  0,              /* tp_setattro */
  0,              /* tp_as_buffer */
  Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,   /* tp_flags */
  "X Display",            /* tp_doc */
  0,              /* tp_traverse */
  0,              /* tp_clear */
  0,              /* tp_richcompare */
  0,              /* tp_weaklistoffset */
  0,              /* tp_iter */
  0,              /* tp_iternext */
  xlib_display_methods,             /* tp_methods */
  0,                  /* tp_members */
  xlib_display_getset,              /* tp_getset */
  0,                  /* tp_base */
  0,                  /* tp_dict */
  0,                  /* tp_descr_get */
  0,                  /* tp_descr_set */
  0,                  /* tp_dictoffset */
  (initproc)xlib_display_init,        /* tp_init */
  0,                  /* tp_alloc */
  PyType_GenericNew,              /* tp_new */
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
/* ===================================================================== *
 * vim modeline                                                          *
 * vim:se fdm=expr foldexpr=getline(v\:lnum)=~'^\\S.*{'?'>1'\:1:         *
 * vim: se path+=/usr/include/python3.2mu:                               *
 * ===================================================================== */
