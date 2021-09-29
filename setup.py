# -*- coding: utf-8 -*-
"""Installer for Searxng package."""

from setuptools import setup
from setuptools import find_packages

from searxng.version import VERSION_TAG, GIT_URL
from searxng import get_setting

with open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

with open('requirements.txt') as f:
    requirements = [ l.strip() for l in f.readlines()]

with open('requirements-dev.txt') as f:
    dev_requirements = [ l.strip() for l in f.readlines()]

setup(
    name='searxng',
    version=VERSION_TAG,
    description="A privacy-respecting, hackable metasearch engine",
    long_description=long_description,
    url=get_setting('brand.docs_url'),
    project_urls={
        "Code": GIT_URL,
        "Issue tracker": get_setting('brand.issue_url')
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python",
        "Topic :: Internet",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        'License :: OSI Approved :: GNU Affero General Public License v3'
    ],
    keywords='metasearch searchengine search web http',
    author='Adam Tauber',
    author_email='asciimoo@gmail.com',
    license='GNU Affero General Public License',
    packages=find_packages(exclude=["tests*", "searxng_extra"]),
    zip_safe=False,
    install_requires=requirements,
    extras_require={
        'test': dev_requirements
    },
    entry_points={
        'console_scripts': [
            'searxng-run = searxng.webapp:run',
            'searxng-checker = searxng.search.checker.__main__:main'
        ]
    },
    package_data={
        'searxng': [
            'settings.yml',
            '../README.rst',
            '../requirements.txt',
            '../requirements-dev.txt',
            'data/*',
            'plugins/*/*',
            'static/*.*',
            'static/*/*.*',
            'static/*/*/*.*',
            'static/*/*/*/*.*',
            'static/*/*/*/*/*.*',
            'templates/*/*.*',
            'templates/*/*/*.*',
            'tests/*',
            'tests/*/*',
            'tests/*/*/*',
            'translations/*/*/*'
        ],
    },

)
