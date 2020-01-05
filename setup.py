from setuptools import setup
def readme():
    with open('README.rst') as f:
        return f.read()
# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='imagiz',
      version='0.3',
      description='Live video streaming over network with OpenCV and ZMQ',
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