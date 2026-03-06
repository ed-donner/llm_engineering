#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <math.h>
#include <float.h>
#include <limits.h>
#include <stdint.h>

static PyObject* leibniz_pi(PyObject* self, PyObject* args) {
    PyObject* iterations_obj;
    if (!PyArg_ParseTuple(args, "O", &iterations_obj)) {
        return NULL;
    }

    long long n_signed;
    int overflow = 0;
    n_signed = PyLong_AsLongLongAndOverflow(iterations_obj, &overflow);
    if (n_signed == -1 && PyErr_Occurred() && overflow == 0) {
        return NULL;
    }

    unsigned long long n = 0ULL;
    if (overflow < 0) {
        n = 0ULL;
    } else if (overflow > 0) {
        unsigned long long tmp = PyLong_AsUnsignedLongLong(iterations_obj);
        if (tmp == (unsigned long long)-1 && PyErr_Occurred()) {
            return NULL;
        }
        n = tmp;
    } else {
        if (n_signed <= 0) {
            n = 0ULL;
        } else {
            n = (unsigned long long)n_signed;
        }
    }

    double result = 1.0;
    if (n == 0ULL) {
        return PyFloat_FromDouble(result * 4.0);
    }

    Py_BEGIN_ALLOW_THREADS
    for (unsigned long long i = 1ULL; i <= n; ++i) {
        double jd1;
        if (i <= ULLONG_MAX / 4ULL) {
            unsigned long long j1 = i * 4ULL - 1ULL;
            jd1 = (double)j1;
        } else {
            jd1 = (double)i * 4.0 - 1.0;
        }
        result -= 1.0 / jd1;

        double jd2;
        if (i <= (ULLONG_MAX - 1ULL) / 4ULL) {
            unsigned long long j2 = i * 4ULL + 1ULL;
            jd2 = (double)j2;
        } else {
            jd2 = (double)i * 4.0 + 1.0;
        }
        result += 1.0 / jd2;
    }
    Py_END_ALLOW_THREADS

    return PyFloat_FromDouble(result * 4.0);
}

static PyMethodDef CalculatePiMethods[] = {
    {"leibniz_pi", leibniz_pi, METH_VARARGS, "Compute pi using the Leibniz series with the given number of iterations."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef calculate_pimodule = {
    PyModuleDef_HEAD_INIT,
    "calculate_pi",
    "High-performance Leibniz pi calculation.",
    -1,
    CalculatePiMethods
};

PyMODINIT_FUNC PyInit_calculate_pi(void) {
    return PyModule_Create(&calculate_pimodule);
}
