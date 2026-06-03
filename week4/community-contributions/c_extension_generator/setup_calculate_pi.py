from setuptools import setup, Extension
import sys
import os

extra_compile_args = []
extra_link_args = []

if os.name == 'nt':
    extra_compile_args.extend(['/O2', '/fp:precise'])
else:
    extra_compile_args.extend(['-O3', '-fno-strict-aliasing'])

module = Extension(
    'calculate_pi',
    sources=['calculate_pi.c'],
    extra_compile_args=extra_compile_args,
    extra_link_args=extra_link_args,
)

setup(
    name='calculate_pi',
    version='1.0.0',
    description='High-performance C extension for computing pi via the Leibniz series',
    ext_modules=[module],
)
