from setuptools import find_packages, setup

from flask_mongodb.about import (AUTHOR, AUTHOR_EMAIL, DESCRIPTION,
                               URL, VERSION)

with open('README.md', 'r') as readme_file:
    long_description = readme_file.read()

setup(
    name='flask_mongodb',
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    url=URL,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    maintainer=AUTHOR,
    maintainer_email=AUTHOR_EMAIL,
    license='BSD-2-Clause License',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'flask-mongodb = flask_mongodb.cli.cli:main'
        ]
    },
    install_requires=[
        'Flask>=2,<3', 
        'pymongo<4.4', 
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
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: CPython'
    ]
)
