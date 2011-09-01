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
  const char* name;
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

static PyMethodDef xlib_display_methods[] = {
  /* {"name", (PyCFunction)Noddy_name, METH_NOARGS,
   *   "Return the name, combining the first and last name"
   * },                                                     */
  {NULL}  /* Sentinel */
};

static PyGetSetDef xlib_display_getset[] = {
  {"name", (getter)xlib_display_get_name, 0, "the display string", NULL},
  {NULL}  /* Sentinel */
};

static PyTypeObject xlib_displayType = {
  PyVarObject_HEAD_INIT(NULL, 0)
  "xlib.Display",					/* tp_name */
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
  "Xlib",
  "utils of Xlib",
  -1,
  NULL, NULL, NULL, NULL, NULL
};

PyMODINIT_FUNC PyInit_Xlib(void){
  PyObject* m;

  if(PyType_Ready(&xlib_displayType) < 0)
    return NULL;

  m = PyModule_Create(&xlibmodule);
  if(m == NULL)
    return NULL;

  Py_INCREF(&xlib_displayType);
  PyModule_AddObject(m, "Display", (PyObject *)&xlib_displayType);
  return m;
}
