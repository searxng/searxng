# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=,missing-module-docstring,missing-class-docstring

import os
import shlex
import subprocess
import logging
import importlib

# fallback values
# if there is searx.version_frozen module, and it is not possible to get the git tag
VERSION_STRING = "1.0.0"
VERSION_TAG = "1.0.0"
GIT_URL = "unknow"
GIT_BRANCH = "unknow"

logger = logging.getLogger("searx")

SUBPROCESS_RUN_ENV = {
    "PATH": os.environ["PATH"],
    "LC_ALL": "C",
    "LANGUAGE": "",
}


def subprocess_run(args, **kwargs):
    """Call :py:func:`subprocess.run` and return (striped) stdout.  If returncode is
    non-zero, raise a :py:func:`subprocess.CalledProcessError`.
    """
    if not isinstance(args, (list, tuple)):
        args = shlex.split(args)

    kwargs["env"] = kwargs.get("env", SUBPROCESS_RUN_ENV)
    kwargs["encoding"] = kwargs.get("encoding", "utf-8")
    kwargs["stdout"] = subprocess.PIPE
    kwargs["stderr"] = subprocess.PIPE
    # raise CalledProcessError if returncode is non-zero
    kwargs["check"] = True
    proc = subprocess.run(args, **kwargs)  # pylint: disable=subprocess-run-check
    return proc.stdout.strip()


def get_git_url_and_branch():
    try:
        ref = subprocess_run("git rev-parse --abbrev-ref @{upstream}")
    except subprocess.CalledProcessError:
        ref = subprocess_run("git rev-parse --abbrev-ref master@{upstream}")
    origin, git_branch = ref.split("/", 1)
    git_url = subprocess_run(["git", "remote", "get-url", origin])

    # get https:// url from git@ url
    if git_url.startswith("git@"):
        git_url = git_url.replace(":", "/", 2).replace("git@", "https://", 1)
    if git_url.endswith(".git"):
        git_url = git_url.replace(".git", "", 1)

    return git_url, git_branch


def get_git_version():
    git_commit_date_hash = subprocess_run(r"git show -s --date='format:%Y.%m.%d' --format='%cd+%h'")
    # Remove leading zero from minor and patch level / replacement of PR-2122
    # which depended on the git version: '2023.05.06+..' --> '2023.5.6+..'
    git_commit_date_hash = git_commit_date_hash.replace('.0', '.')
    tag_version = git_version = git_commit_date_hash

    # add "+dirty" suffix if there are uncommited changes except searx/settings.yml
    try:
        subprocess_run("git diff --quiet -- . ':!searx/settings.yml' ':!utils/brand.env'")
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            git_version += "+dirty"
        else:
            logger.warning('"%s" returns an unexpected return code %i', e.returncode, e.cmd)
    docker_tag = git_version.replace("+", "-")
    return git_version, tag_version, docker_tag


try:
    vf = importlib.import_module('searx.version_frozen')
    VERSION_STRING, VERSION_TAG, DOCKER_TAG, GIT_URL, GIT_BRANCH = (
        vf.VERSION_STRING,
        vf.VERSION_TAG,
        vf.DOCKER_TAG,
        vf.GIT_URL,
        vf.GIT_BRANCH,
    )
except ImportError:
    try:
        try:
            VERSION_STRING, VERSION_TAG, DOCKER_TAG = get_git_version()
        except subprocess.CalledProcessError as ex:
            logger.error("Error while getting the version: %s", ex.stderr)
        try:
            GIT_URL, GIT_BRANCH = get_git_url_and_branch()
        except subprocess.CalledProcessError as ex:
            logger.error("Error while getting the git URL & branch: %s", ex.stderr)
    except FileNotFoundError as ex:
        logger.error("%s is not found, fallback to the default version", ex.filename)


logger.info("version: %s", VERSION_STRING)

if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 2 and sys.argv[1] == "freeze":
        # freeze the version (to create an archive outside a git repository)
        python_code = f"""# SPDX-License-Identifier: AGPL-3.0-or-later
# this file is generated automatically by searx/version.py

VERSION_STRING = "{VERSION_STRING}"
VERSION_TAG = "{VERSION_TAG}"
DOCKER_TAG = "{DOCKER_TAG}"
GIT_URL = "{GIT_URL}"
GIT_BRANCH = "{GIT_BRANCH}"
"""
        with open(os.path.join(os.path.dirname(__file__), "version_frozen.py"), "w", encoding="utf8") as f:
            f.write(python_code)
            print(f"{f.name} created")
    else:
        # output shell code to set the variables
        # usage: eval "$(python -m searx.version)"
        shell_code = f"""
VERSION_STRING="{VERSION_STRING}"
VERSION_TAG="{VERSION_TAG}"
DOCKER_TAG="{DOCKER_TAG}"
GIT_URL="{GIT_URL}"
GIT_BRANCH="{GIT_BRANCH}"
"""
        print(shell_code)
