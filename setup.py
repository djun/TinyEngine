# coding=utf-8

from setuptools import setup, find_packages

setup(
    name='Tiny Engine',
    version=0.1,
    description=(
        'A DIY scripting engine supporting most common customizations. '
        'The script format in engine is based on Json/Json5 file format.'
    ),
    long_description=open('README.rst').read(),
    author='DJun',
    author_email='djunxp@gmail.com',
    maintainer='DJun',
    maintainer_email='djunxp@gmail.com',
    license='GNU General Public License',
    packages=find_packages(),
    platforms=["all"],
    url='https://github.com/djunxp/TinyEngine',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License',
        'Programming Language :: Python',
        'Programming Language :: Python :: Implementation',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries',
    ],
    install_requires=[
        'json5',
        'jsonpath',
        'lxml',
        'cssselect',
    ],
)
