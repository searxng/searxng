# -*- coding: utf-8 -*-
"""Installer for SearXNG package."""

from setuptools import setup
from setuptools import find_packages

from searx.version import VERSION_TAG, GIT_URL
from searx import get_setting

with open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

with open('requirements.txt') as f:
    requirements = [ l.strip() for l in f.readlines()]

with open('requirements-dev.txt') as f:
    dev_requirements = [ l.strip() for l in f.readlines()]

setup(
    name='searxng',
    python_requires=">=3.7",
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
    author='SearXNG dev team',
    author_email='contact@searxng.org',
    license='GNU Affero General Public License',
    packages=find_packages(exclude=["tests*", "searxng_extra"]),
    zip_safe=False,
    install_requires=requirements,
    extras_require={
        'test': dev_requirements
    },
    entry_points={
        'console_scripts': [
            'searx-run = searx.webapp:run',
            'searx-checker = searx.search.checker.__main__:main'
        ]
    },
    package_data={
        'searx': [
            'settings.yml',
            '../README.rst',
            '../requirements.txt',
            '../requirements-dev.txt',
            'data/*',
            'info/*',
            'info/*/*',
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
