import os

from setuptools import setup, find_packages

import pholcidae2

setup(
    name='pholcidae2',
    version=pholcidae2.__version__,
    packages=find_packages(os.path.dirname(os.path.abspath(__file__)))
)
