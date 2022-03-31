from setuptools import find_packages, setup

from flask_mongodb.about import (__author__, __author_email__, __description__,
                               __url__, __version__)

setup(
    name='flask_mongodb',
    version=__version__,
    description=__description__,
    url=__url__,
    author=__author__,
    author_email=__author_email__,
    license='BSD-2-Clause License',
    packages=find_packages(),
    install_requires=['flask', 'pymongo', 'flask-wtf', 'wtform', 'email-validator'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Environment :: Web Environment',
        'Framework :: Flask',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: CPython'
    ]
)
