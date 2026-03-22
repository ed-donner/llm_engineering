from setuptools import setup, Extension
import sys

extra_compile_args = []
extra_link_args = []
if sys.platform == 'win32':
    extra_compile_args = ['/O2', '/Ot', '/GL', '/fp:fast']
    extra_link_args = ['/LTCG']
else:
    extra_compile_args = ['-O3', '-march=native']

module = Extension(
    name='python_hard',
    sources=['python_hard.c'],
    extra_compile_args=extra_compile_args,
    extra_link_args=extra_link_args,
    language='c'
)

setup(
    name='python_hard',
    version='1.0.0',
    description='High-performance C extension reimplementation',
    ext_modules=[module]
)
