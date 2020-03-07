from setuptools import setup
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='imagiz',
      version='0.5',
      description='Live video streaming over network with OpenCV and (ZMQ or TCP)',
      url='https://github.com/jmowlaei/imagiz',
      author='Jafar Mowlaei',
      author_email='jmowlaei@gmail.com',
      license='MIT',
      packages=['imagiz'],
      install_requires=[
          'zmq',
      ],
      zip_safe=False,
      long_description=long_description,
      long_description_content_type='text/markdown'
      
      )