
#include <Python.h>

// Function to be called from Python
static PyObject* zz_hello_world(PyObject* self, PyObject* args) {
    printf("Hello, World!\n");
    Py_RETURN_NONE;
}

// Method definition structure
static PyMethodDef zz_my_methods[] = {
    {"hello_world", zz_hello_world, METH_VARARGS, "Print 'Hello, World!'"},
    {NULL, NULL, 0, NULL}  // Sentinel
};

// Module definition
static struct PyModuleDef zz_my_module = {
    PyModuleDef_HEAD_INIT,
    "zz_my_module",
    "Extension module that prints Hello, World!",
    -1,
    zz_my_methods
};

// Module initialization function
PyMODINIT_FUNC PyInit_zz_my_module(void) {
    return PyModule_Create(&zz_my_module);
}
