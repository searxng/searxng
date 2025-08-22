# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=,missing-module-docstring,missing-class-docstring

import importlib
import logging
import os
import shlex
import subprocess

# fallback values
# if there is searx.version_frozen module, and it is not possible to get the git tag
VERSION_STRING: str = "1.0.0"
VERSION_TAG: str = "1.0.0"
DOCKER_TAG: str = "1.0.0"
GIT_URL: str = "unknown"
GIT_BRANCH: str = "unknown"

logger = logging.getLogger("searx")

SUBPROCESS_RUN_ENV = {
    "PATH": os.environ["PATH"],
    "LC_ALL": "C",
    "LANGUAGE": "",
}


def subprocess_run(args: str | list[str] | tuple[str], **kwargs) -> str:  # type: ignore
    """Call :py:func:`subprocess.run` and return (striped) stdout.  If returncode is
    non-zero, raise a :py:func:`subprocess.CalledProcessError`.
    """
    if not isinstance(args, (list, tuple)):
        args = shlex.split(args)

    kwargs["env"] = kwargs.get("env", SUBPROCESS_RUN_ENV)  # type: ignore
    kwargs["encoding"] = kwargs.get("encoding", "utf-8")  # type: ignore
    kwargs["stdout"] = subprocess.PIPE
    kwargs["stderr"] = subprocess.PIPE
    # raise CalledProcessError if returncode is non-zero
    kwargs["check"] = True
    # pylint: disable=subprocess-run-check
    proc = subprocess.run(args, **kwargs)  # type: ignore
    return proc.stdout.strip()  # type: ignore


def get_git_url_and_branch():
    # handle GHA directly
    if "GITHUB_REPOSITORY" in os.environ and "GITHUB_REF_NAME" in os.environ:
        git_url = f"https://github.com/{os.environ['GITHUB_REPOSITORY']}"
        git_branch = os.environ["GITHUB_REF_NAME"]
        return git_url, git_branch

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


def get_git_version() -> tuple[str, str, str]:
    git_commit_date_hash: str = subprocess_run(r"git show -s --date='format:%Y.%m.%d' --format='%cd+%h'")
    # Remove leading zero from minor and patch level / replacement of PR-2122
    # which depended on the git version: '2023.05.06+..' --> '2023.5.6+..'
    git_commit_date_hash = git_commit_date_hash.replace('.0', '.')
    tag_version: str = git_commit_date_hash
    git_version: str = git_commit_date_hash
    docker_tag: str = git_commit_date_hash.replace("+", "-")

    # add "+dirty" suffix if there are uncommitted changes except searx/settings.yml
    try:
        subprocess_run("git diff --quiet -- . ':!searx/settings.yml' ':!utils/brand.env'")
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            git_version += "+dirty"
        else:
            logger.warning('"%s" returns an unexpected return code %i', e.returncode, e.cmd)

    return git_version, tag_version, docker_tag


def get_information() -> tuple[str, str, str, str, str]:
    version_string: str = VERSION_STRING
    version_tag: str = VERSION_TAG
    docker_tag: str = DOCKER_TAG
    git_url: str = GIT_URL
    git_branch: str = GIT_BRANCH

    try:
        version_string, version_tag, docker_tag = get_git_version()
    except subprocess.CalledProcessError as ex:
        logger.error("Error while getting the version: %s", ex.stderr)
    try:
        git_url, git_branch = get_git_url_and_branch()
    except subprocess.CalledProcessError as ex:
        logger.error("Error while getting the git URL & branch: %s", ex.stderr)

    return version_string, version_tag, docker_tag, git_url, git_branch


try:
    vf = importlib.import_module('searx.version_frozen')
    VERSION_STRING, VERSION_TAG, DOCKER_TAG, GIT_URL, GIT_BRANCH = (
        str(vf.VERSION_STRING),
        str(vf.VERSION_TAG),
        str(vf.DOCKER_TAG),
        str(vf.GIT_URL),
        str(vf.GIT_BRANCH),
    )
except ImportError:
    VERSION_STRING, VERSION_TAG, DOCKER_TAG, GIT_URL, GIT_BRANCH = get_information()

logger.info("version: %s", VERSION_STRING)

if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 2 and sys.argv[1] == "freeze":
        VERSION_STRING, VERSION_TAG, DOCKER_TAG, GIT_URL, GIT_BRANCH = get_information()

        # freeze the version (to create an archive outside a git repository)
        python_code = f"""# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring
# this file is generated automatically by searx/version.py

VERSION_STRING = "{VERSION_STRING}"
VERSION_TAG = "{VERSION_TAG}"
DOCKER_TAG = "{DOCKER_TAG}"
GIT_URL = "{GIT_URL}"
GIT_BRANCH = "{GIT_BRANCH}"
"""
        path = os.path.join(os.path.dirname(__file__), "version_frozen.py")
        with open(path, "w", encoding="utf8") as f:
            f.write(python_code)
            print(f"{f.name} created")

        # set file timestamp to commit timestamp
        commit_timestamp = int(subprocess_run("git show -s --format=%ct"))
        os.utime(path, (commit_timestamp, commit_timestamp))
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
