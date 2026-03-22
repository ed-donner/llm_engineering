
from setuptools import setup, Extension

module = Extension(
    'zz_my_module',
    sources=['zz_my_module.c'],
)

setup(
    name='zz_my_module',
    version='1.0',
    description='This is a custom C extension module.',
    ext_modules=[module]
)
