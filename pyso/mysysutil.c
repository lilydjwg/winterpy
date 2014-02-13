#include<sys/prctl.h>
#include<Python.h>

static PyObject* subreap(PyObject *self, PyObject *args){
  PyObject* pyreaping;
  int reaping;
  int result;

  if (!PyArg_ParseTuple(args, "O!", &PyBool_Type, &pyreaping))
    return NULL;
  reaping = pyreaping == Py_True;

  Py_BEGIN_ALLOW_THREADS
  result = prctl(PR_SET_CHILD_SUBREAPER, reaping); 
  Py_END_ALLOW_THREADS

  if(result != 0){
    return PyErr_SetFromErrno(Py_None);
  }else{
    Py_RETURN_NONE;
  }
}

static PyMethodDef mysysutil_methods[] = {
  {"subreap", subreap, METH_VARARGS},
  {NULL, NULL}    /* Sentinel */
};

static PyModuleDef mysysutil = {
  PyModuleDef_HEAD_INIT,
  "mysysutil",
  "My system utils",
  -1,
  mysysutil_methods,
  NULL, NULL, NULL, NULL
};

PyMODINIT_FUNC PyInit_mysysutil(void){
  PyObject* m;

  m = PyModule_Create(&mysysutil);
  if(m == NULL)
    return NULL;
  return m;
}
