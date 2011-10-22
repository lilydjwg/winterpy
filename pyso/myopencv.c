#include<Python.h>
#include<cv.h>

typedef struct {
  PyObject_HEAD
  IplImage* img;
} IplImageObject;

static PyTypeObject IplImageType;

static void IplImage_del(IplImageObject* self){
  cvReleaseImage(&(self->img));
  Py_TYPE(self)->tp_free((PyObject*)self);
}

static int IplImage_init(IplImageObject* self,
    PyObject *args, PyObject *kwds){
  const char* fpath = NULL;
  IplImage* img;
  if(!PyArg_ParseTuple(args, "z", &fpath))
    return -1;

  Py_BEGIN_ALLOW_THREADS
  img = (IplImage*)cvLoadImage(fpath, 1);
  Py_END_ALLOW_THREADS

  if(img == NULL){
    PyErr_Format(PyExc_ValueError,
	"failed to load image from file: %s",
	fpath);
    return -1;
  }
  self->img = img;

  return 0;
}

static PyObject* IplImage_getwidth(IplImageObject* self, void* data){
  return Py_BuildValue("i", self->img->width);
}

static PyObject* IplImage_getheight(IplImageObject* self, void* data){
  return Py_BuildValue("i", self->img->height);
}

static PyObject* IplImage_match(IplImageObject* self, PyObject* args){
  PyObject* pattern = NULL;
  IplImage* img;
  IplImage* pat;
  IplImage* result;
  int resultW, resultH;
  double max_interlinkage = 0;
  double min_interlinkage = 0;
  CvPoint max_point;
  CvPoint min_point;
  
  if(!PyArg_ParseTuple(args, "O!", &IplImageType, &pattern))
    return NULL;

  img = self->img;
  pat = ((IplImageObject*)pattern)->img;

  Py_BEGIN_ALLOW_THREADS

  resultW = img->width - pat->width + 1;
  resultH = img->height - pat->height + 1;
  result = cvCreateImage(cvSize(resultW, resultH), IPL_DEPTH_32F, 1);
  cvMatchTemplate(img, pat, result, CV_TM_CCOEFF_NORMED);
  cvMinMaxLoc(result, &min_interlinkage, &max_interlinkage, &min_point,
      &max_point, NULL);
  cvReleaseImage(&result);

  Py_END_ALLOW_THREADS

  return Py_BuildValue("((ii)d)", max_point.x, max_point.y, max_interlinkage);
}

static PyMethodDef IplImage_methods[] = {
  {
    "match", (PyCFunction)IplImage_match, METH_VARARGS,
    "find the most match portion for the given IplImage pattern\n" \
      "Returns a tuple: ((x, y), interlinkage)"
  },
  {NULL}  /* Sentinel */
};

static PyGetSetDef IplImage_getset[] = {
  {"width", (getter)IplImage_getwidth, 0, "the image width", NULL},
  {"height", (getter)IplImage_getheight, 0, "the image height", NULL},
  {NULL}  /* Sentinel */
};

static PyTypeObject IplImageType = {
  PyVarObject_HEAD_INIT(NULL, 0)
  "IplImage",						/* tp_name */
  sizeof(IplImageObject),				/* tp_basicsize */
  0,							/* tp_itemsize */
  (destructor)IplImage_del,				/* tp_dealloc */
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
  "OpenCV IplImage",					/* tp_doc */
  0,							/* tp_traverse */
  0,							/* tp_clear */
  0,							/* tp_richcompare */
  0,							/* tp_weaklistoffset */
  0,							/* tp_iter */
  0,							/* tp_iternext */
  IplImage_methods,	     				/* tp_methods */
  0,			     				/* tp_members */
  IplImage_getset,	     				/* tp_getset */
  0,			     				/* tp_base */
  0,			     				/* tp_dict */
  0,			     				/* tp_descr_get */
  0,			     				/* tp_descr_set */
  0,			     				/* tp_dictoffset */
  (initproc)IplImage_init,				/* tp_init */
  0,			     				/* tp_alloc */
  PyType_GenericNew,		     			/* tp_new */
};

static PyModuleDef myopencvmodule = {
  PyModuleDef_HEAD_INIT,
  "myopencv",
  "My OpenCV utils",
  -1,
  NULL, NULL, NULL, NULL, NULL
};

PyMODINIT_FUNC PyInit_myopencv(void){
  PyObject* m;

  if(PyType_Ready(&IplImageType) < 0)
    return NULL;

  m = PyModule_Create(&myopencvmodule);
  if(m == NULL)
    return NULL;

  Py_INCREF(&IplImageType);
  PyModule_AddObject(m, "Image", (PyObject *)&IplImageType);
  return m;
}
/* ===================================================================== *
 * vim modeline                                                          *
 * vim:se fdm=expr foldexpr=getline(v\:lnum)=~'^\\S.*{'?'>1'\:1:         *
 * vim: se path+=/usr/include/python3.2mu:                               *
 * ===================================================================== */
