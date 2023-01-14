# -*- coding: utf-8 -*-
"""Installer for SearXNG package."""

from setuptools import setup, find_packages

with open('README.rst', encoding='utf-8') as f:
    long_description = f.read()


def version_yyyymmdd_tag():
    from setuptools_scm.version import ScmVersion

    def custom_version_scheme(version: ScmVersion):
        return f"{version.node_date.year}.{version.node_date.month}.{version.node_date.day}+{version.node}"

    def custom_local_scheme(version: ScmVersion):
        return '.dirty' if version.dirty else ''

    return {
        'write_to': 'searx/_version.py',
        'version_scheme': custom_version_scheme,
        'local_scheme': custom_local_scheme
    }


setup(
    name='searxng',
    python_requires=">=3.7",
    description="A privacy-respecting, hackable metasearch engine",
    long_description=long_description,
    use_scm_version=version_yyyymmdd_tag,
    url='https://docs.searxng.org/',
    project_urls={
        "Code": 'https://github.com/searxng/searxng',
        "Documentation": 'https://docs.searxng.org/',
        "Issue tracker": 'https://github.com/searxng/searxng/issues',
        "New issue": 'https://github.com/searxng/searxng/issues/new',
        'Public instances': 'https//searx.space',
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
    packages=find_packages(exclude=["tests*", "searxng_extra*"]),
    zip_safe=False,
    install_requires=[
        'certifi==2022.12.7',
        'babel==2.11.0',
        'flask-babel==3.0.1',
        'flask==2.2.2',
        'jinja2==3.1.2',
        'lxml==4.9.2',
        'pygments==2.14.0',
        'python-dateutil==2.8.2',
        'pyyaml==6.0',
        'httpx[http2]==0.21.2',
        'Brotli==1.0.9',
        'uvloop==0.17.0',
        'httpx-socks[asyncio]==0.7.2',
        'setproctitle==1.3.2',
        'redis==4.5.1',
        'markdown-it-py==2.1.0',
        'typing_extensions==4.4.0',
        'fasttext-predict==0.9.2.1',
    ],
    entry_points={
        'console_scripts': [
            'searxng = searx.webapp:run',
            'searxng-checker = searx.search.checker.__main__:main'
        ]
    },
    package_data={
        'searx': [
            'settings.yml',
            '../README.rst',
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
            'translations/*/*/*'
        ],
    },

)
