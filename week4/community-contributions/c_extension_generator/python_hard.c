#include <Python.h>
#include <stdint.h>
#include <stdlib.h>
#include <limits.h>
#include <math.h>

// LCG step with 32-bit wrap-around
static inline uint32_t lcg_next(uint32_t *state) {
    *state = (uint32_t)(1664525u * (*state) + 1013904223u);
    return *state;
}

static inline int add_overflow_int64(int64_t a, int64_t b, int64_t *res) {
    if ((b > 0 && a > INT64_MAX - b) || (b < 0 && a < INT64_MIN - b)) return 1;
    *res = a + b;
    return 0;
}

// Kadane for int64 array with overflow detection; returns PyLong or NULL (on overflow -> signal via *overflowed)
static PyObject* kadane_int64(const int64_t *arr, Py_ssize_t n, int *overflowed) {
    if (n <= 0) {
        return PyFloat_FromDouble(-INFINITY);
    }
    int64_t meh = arr[0];
    int64_t msf = arr[0];
    for (Py_ssize_t i = 1; i < n; ++i) {
        int64_t x = arr[i];
        if (meh > 0) {
            int64_t tmp;
            if (add_overflow_int64(meh, x, &tmp)) { *overflowed = 1; return NULL; }
            meh = tmp;
        } else {
            meh = x;
        }
        if (meh > msf) msf = meh;
    }
    return PyLong_FromLongLong(msf);
}

// Kadane for PyObject* integer array
static PyObject* kadane_big(PyObject **arr, Py_ssize_t n) {
    if (n <= 0) {
        return PyFloat_FromDouble(-INFINITY);
    }
    PyObject *meh = arr[0]; Py_INCREF(meh);
    PyObject *msf = arr[0]; Py_INCREF(msf);
    PyObject *zero = PyLong_FromLong(0);
    if (!zero) { Py_DECREF(meh); Py_DECREF(msf); return NULL; }

    for (Py_ssize_t i = 1; i < n; ++i) {
        int cmp = PyObject_RichCompareBool(meh, zero, Py_GT);
        if (cmp < 0) { Py_DECREF(meh); Py_DECREF(msf); Py_DECREF(zero); return NULL; }
        if (cmp == 1) {
            PyObject *t = PyNumber_Add(meh, arr[i]);
            if (!t) { Py_DECREF(meh); Py_DECREF(msf); Py_DECREF(zero); return NULL; }
            Py_DECREF(meh);
            meh = t;
        } else {
            Py_DECREF(meh);
            meh = arr[i]; Py_INCREF(meh);
        }
        int cmp2 = PyObject_RichCompareBool(meh, msf, Py_GT);
        if (cmp2 < 0) { Py_DECREF(meh); Py_DECREF(msf); Py_DECREF(zero); return NULL; }
        if (cmp2 == 1) {
            Py_DECREF(msf);
            msf = meh; Py_INCREF(msf);
        }
    }
    Py_DECREF(meh);
    Py_DECREF(zero);
    return msf; // new reference
}

// Generate int64 array fast path; returns 0 on success
static int gen_array_int64(Py_ssize_t n, uint32_t seed, int64_t min_v, int64_t max_v, int64_t *out) {
    uint32_t state = seed;
    uint64_t umax = (uint64_t)max_v;
    uint64_t umin = (uint64_t)min_v;
    uint64_t range = (umax - umin) + 1ULL; // max>=min guaranteed by caller
    for (Py_ssize_t i = 0; i < n; ++i) {
        state = lcg_next(&state);
        uint32_t r32 = state;
        uint64_t r = (range > 0x100000000ULL) ? (uint64_t)r32 : ((uint64_t)r32 % range);
        int64_t val = (int64_t)(min_v + (int64_t)r);
        out[i] = val;
    }
    return 0;
}

// Generate PyObject* int array general path using Python arithmetic
static PyObject** gen_array_big(Py_ssize_t n, uint32_t seed, PyObject *min_val, PyObject *max_val) {
    PyObject **arr = (PyObject**)PyMem_Malloc((n > 0 ? n : 1) * sizeof(PyObject*));
    if (!arr) {
        PyErr_NoMemory();
        return NULL;
    }
    PyObject *one = PyLong_FromLong(1);
    if (!one) { PyMem_Free(arr); return NULL; }
    PyObject *diff = PyNumber_Subtract(max_val, min_val);
    if (!diff) { Py_DECREF(one); PyMem_Free(arr); return NULL; }
    PyObject *range_obj = PyNumber_Add(diff, one);
    Py_DECREF(diff);
    Py_DECREF(one);
    if (!range_obj) { PyMem_Free(arr); return NULL; }

    uint32_t state = seed;
    for (Py_ssize_t i = 0; i < n; ++i) {
        state = lcg_next(&state);
        PyObject *v = PyLong_FromUnsignedLong((unsigned long)state);
        if (!v) {
            Py_DECREF(range_obj);
            for (Py_ssize_t k = 0; k < i; ++k) Py_DECREF(arr[k]);
            PyMem_Free(arr);
            return NULL;
        }
        PyObject *r = PyNumber_Remainder(v, range_obj);
        Py_DECREF(v);
        if (!r) {
            Py_DECREF(range_obj);
            for (Py_ssize_t k = 0; k < i; ++k) Py_DECREF(arr[k]);
            PyMem_Free(arr);
            return NULL;
        }
        PyObject *val = PyNumber_Add(r, min_val);
        Py_DECREF(r);
        if (!val) {
            Py_DECREF(range_obj);
            for (Py_ssize_t k = 0; k < i; ++k) Py_DECREF(arr[k]);
            PyMem_Free(arr);
            return NULL;
        }
        arr[i] = val;
    }
    Py_DECREF(range_obj);
    return arr;
}

static PyObject* max_subarray_sum_internal(Py_ssize_t n, uint32_t seed, PyObject *min_val, PyObject *max_val) {
    if (n <= 0) {
        return PyFloat_FromDouble(-INFINITY);
    }

    if (PyLong_Check(min_val) && PyLong_Check(max_val)) {
        int overflow1 = 0, overflow2 = 0;
        long long min64 = PyLong_AsLongLongAndOverflow(min_val, &overflow1);
        if (overflow1) goto BIGINT_PATH;
        long long max64 = PyLong_AsLongLongAndOverflow(max_val, &overflow2);
        if (overflow2) goto BIGINT_PATH;
        if (max64 >= min64) {
            int64_t *arr = (int64_t*)PyMem_Malloc((size_t)n * sizeof(int64_t));
            if (!arr) { PyErr_NoMemory(); return NULL; }
            if (gen_array_int64(n, seed, (int64_t)min64, (int64_t)max64, arr) != 0) {
                PyMem_Free(arr);
                return NULL;
            }
            int overflowed = 0;
            PyObject *res = kadane_int64(arr, n, &overflowed);
            if (!res && overflowed) {
                // fallback to big-int Kadane
                PyObject **arr_obj = (PyObject**)PyMem_Malloc((size_t)n * sizeof(PyObject*));
                if (!arr_obj) { PyMem_Free(arr); PyErr_NoMemory(); return NULL; }
                for (Py_ssize_t i = 0; i < n; ++i) {
                    arr_obj[i] = PyLong_FromLongLong(arr[i]);
                    if (!arr_obj[i]) {
                        for (Py_ssize_t k = 0; k < i; ++k) Py_DECREF(arr_obj[k]);
                        PyMem_Free(arr_obj);
                        PyMem_Free(arr);
                        return NULL;
                    }
                }
                PyObject *bires = kadane_big(arr_obj, n);
                for (Py_ssize_t i = 0; i < n; ++i) Py_DECREF(arr_obj[i]);
                PyMem_Free(arr_obj);
                PyMem_Free(arr);
                return bires;
            }
            PyMem_Free(arr);
            return res;
        }
    }
BIGINT_PATH: ;
    PyObject **arr_obj = gen_array_big(n, seed, min_val, max_val);
    if (!arr_obj) return NULL;
    PyObject *res = kadane_big(arr_obj, n);
    for (Py_ssize_t i = 0; i < n; ++i) Py_DECREF(arr_obj[i]);
    PyMem_Free(arr_obj);
    return res;
}

static PyObject* py_max_subarray_sum(PyObject *self, PyObject *args) {
    Py_ssize_t n;
    PyObject *seed_obj, *min_val, *max_val;
    if (!PyArg_ParseTuple(args, "nOOO", &n, &seed_obj, &min_val, &max_val)) return NULL;
    if (n < 0) n = 0;
    uint32_t seed = (uint32_t)(PyLong_AsUnsignedLongLongMask(seed_obj) & 0xFFFFFFFFULL);
    if (PyErr_Occurred()) return NULL;
    return max_subarray_sum_internal(n, seed, min_val, max_val);
}

static PyObject* py_total_max_subarray_sum(PyObject *self, PyObject *args) {
    Py_ssize_t n;
    PyObject *init_seed_obj, *min_val, *max_val;
    if (!PyArg_ParseTuple(args, "nOOO", &n, &init_seed_obj, &min_val, &max_val)) return NULL;
    if (n < 0) n = 0;
    uint32_t state = (uint32_t)(PyLong_AsUnsignedLongLongMask(init_seed_obj) & 0xFFFFFFFFULL);
    if (PyErr_Occurred()) return NULL;

    PyObject *total = PyLong_FromLong(0);
    if (!total) return NULL;

    for (int i = 0; i < 20; ++i) {
        uint32_t seed = lcg_next(&state);
        PyObject *part = max_subarray_sum_internal(n, seed, min_val, max_val);
        if (!part) { Py_DECREF(total); return NULL; }
        PyObject *new_total = PyNumber_Add(total, part);
        Py_DECREF(part);
        if (!new_total) { Py_DECREF(total); return NULL; }
        Py_DECREF(total);
        total = new_total;
    }
    return total;
}

static PyMethodDef module_methods[] = {
    {"max_subarray_sum", (PyCFunction)py_max_subarray_sum, METH_VARARGS, "Compute maximum subarray sum using LCG-generated array."},
    {"total_max_subarray_sum", (PyCFunction)py_total_max_subarray_sum, METH_VARARGS, "Compute total of maximum subarray sums over 20 LCG seeds."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "python_hard",
    NULL,
    -1,
    module_methods,
    NULL,
    NULL,
    NULL,
    NULL
};

PyMODINIT_FUNC PyInit_python_hard(void) {
    return PyModule_Create(&moduledef);
}
