from setuptools import find_packages, setup

from flask_mongodb.about import (__author__, __author_email__, __description__,
                               __url__, __version__)

with open('README.md', 'r') as readme_file:
    long_description = readme_file.read()

setup(
    name='flask_mongodb',
    version=__version__,
    description=__description__,
    long_description=long_description,
    url=__url__,
    author=__author__,
    author_email=__author_email__,
    license='BSD-2-Clause License',
    packages=find_packages(),
    install_requires=[
        'Flask==2.0.3', 
        'pymongo==4.0.2', 
        'WTForms==3.0.1', 
        'email-validator==1.1.3'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Environment :: Web Environment',
        'Framework :: Flask',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython'
    ]
)
