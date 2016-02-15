#include<curses.h>
#include<Python.h>

static PyObject* py_newterm(PyObject *self, PyObject *args){
  int fd;
  SCREEN *screen;
  if (!PyArg_ParseTuple(args, "i", &fd))
    return NULL;

  Py_BEGIN_ALLOW_THREADS
  FILE *fp = fdopen(fd, "w+");
  screen = newterm(NULL, fp, fp);
  Py_END_ALLOW_THREADS

  return PyLong_FromVoidPtr(screen);
}

static PyObject* py_set_term(PyObject *self, PyObject *args){
  SCREEN *screen;
  if (!PyArg_ParseTuple(args, "l", &screen))
    return NULL;

  Py_BEGIN_ALLOW_THREADS
  screen = set_term(screen);
  Py_END_ALLOW_THREADS

  return PyLong_FromVoidPtr(screen);
}

static PyMethodDef mytermutil_methods[] = {
  {"newterm", py_newterm, METH_VARARGS},
  {"set_term", py_set_term, METH_VARARGS},
  {NULL, NULL}    /* Sentinel */
};

#if PY_MAJOR_VERSION >= 3
static PyModuleDef mytermutil = {
  PyModuleDef_HEAD_INIT,
  "mytermutil",
  "My terminal utils",
  -1,
  mytermutil_methods,
  NULL, NULL, NULL, NULL
};
#endif

#if PY_MAJOR_VERSION >= 3
PyMODINIT_FUNC PyInit_mytermutil(void){
  PyObject* m;

  m = PyModule_Create(&mytermutil);
  if(m == NULL)
    return NULL;
  return m;
#else
PyMODINIT_FUNC initmytermutil(void){
  Py_InitModule("mytermutil", mytermutil_methods);
#endif
}
