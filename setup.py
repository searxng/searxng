# SPDX-License-Identifier: AGPL-3.0-or-later
"""Installer for SearXNG package."""

from setuptools import setup, find_packages

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
    python_requires=">=3.8",
    version=VERSION_TAG,
    description="A privacy-respecting, hackable metasearch engine",
    long_description=long_description,
    url=get_setting('brand.docs_url'),
    project_urls={
        "Code": GIT_URL,
        "Issue tracker": get_setting('brand.issue_url')
    },
    classifiers=[
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
    packages=find_packages(
        include=[
            'searx', 'searx.*', 'searx.*.*', 'searx.*.*.*',
        ]
    ),
    install_requires=requirements,
    extras_require={
        'test': dev_requirements
    },
    entry_points={
        'console_scripts': [
            'searxng-run = searx.webapp:run',
            'searxng-checker = searx.search.checker.__main__:main'
        ]
    },
    package_data={
        'searx': [
            'settings.yml',
            '*.toml',
            '*.msg',
            'search/checker/scheduler.lua',
            'data/*.json',
            'data/*.txt',
            'data/*.ftz',
            'infopage/*/*',
            'static/themes/simple/css/*',
            'static/themes/simple/css/*/*',
            'static/themes/simple/img/*',
            'static/themes/simple/js/*',
            'templates/*/*',
            'templates/*/*/*',
            'translations/*',
            'translations/*/*',
            'translations/*/*/*',
        ],
    },
)
