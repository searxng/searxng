# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Configuration class :py:class:`Config` with deep-update, schema validation
and deprecated names.

The :py:class:`Config` class implements a configuration that is based on
structured dictionaries.  The configuration schema is defined in a dictionary
structure and the configuration data is given in a dictionary structure.
"""
from __future__ import annotations
from typing import Any

import copy
import typing
import logging
import pathlib
import pytomlpp as toml

__all__ = ['Config', 'UNSET', 'SchemaIssue']

log = logging.getLogger(__name__)


class FALSE:
    """Class of ``False`` singelton"""

    # pylint: disable=multiple-statements
    def __init__(self, msg):
        self.msg = msg

    def __bool__(self):
        return False

    def __str__(self):
        return self.msg

    __repr__ = __str__


UNSET = FALSE('<UNSET>')


class SchemaIssue(ValueError):
    """Exception to store and/or raise a message from a schema issue."""

    def __init__(self, level: typing.Literal['warn', 'invalid'], msg: str):
        self.level = level
        super().__init__(msg)

    def __str__(self):
        return f"[cfg schema {self.level}] {self.args[0]}"


class Config:
    """Base class used for configuration"""

    UNSET = UNSET

    @classmethod
    def from_toml(cls, schema_file: pathlib.Path, cfg_file: pathlib.Path, deprecated: dict) -> Config:

        # init schema

        log.debug("load schema file: %s", schema_file)
        cfg = cls(cfg_schema=toml.load(schema_file), deprecated=deprecated)
        if not cfg_file.exists():
            log.warning("missing config file: %s", cfg_file)
            return cfg

        # load configuration

        log.debug("load config file: %s", cfg_file)
        try:
            upd_cfg = toml.load(cfg_file)
        except toml.DecodeError as exc:
            msg = str(exc).replace('\t', '').replace('\n', ' ')
            log.error("%s: %s", cfg_file, msg)
            raise

        is_valid, issue_list = cfg.validate(upd_cfg)
        for msg in issue_list:
            log.error(str(msg))
        if not is_valid:
            raise TypeError(f"schema of {cfg_file} is invalid!")
        cfg.update(upd_cfg)
        return cfg

    def __init__(self, cfg_schema: typing.Dict, deprecated: typing.Dict[str, str]):
        """Construtor of class Config.

        :param cfg_schema: Schema of the configuration
        :param deprecated: dictionary that maps deprecated configuration names to a messages

        These values are needed for validation, see :py:obj:`validate`.

        """
        self.cfg_schema = cfg_schema
        self.deprecated = deprecated
        self.cfg = copy.deepcopy(cfg_schema)

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def validate(self, cfg: dict):
        """Validation of dictionary ``cfg`` on :py:obj:`Config.SCHEMA`.
        Validation is done by :py:obj:`validate`."""

        return validate(self.cfg_schema, cfg, self.deprecated)

    def update(self, upd_cfg: dict):
        """Update this configuration by ``upd_cfg``."""

        dict_deepupdate(self.cfg, upd_cfg)

    def default(self, name: str):
        """Returns default value of field ``name`` in ``self.cfg_schema``."""
        return value(name, self.cfg_schema)

    def get(self, name: str, default: Any = UNSET, replace: bool = True) -> Any:
        """Returns the value to which ``name`` points in the configuration.

        If there is no such ``name`` in the config and the ``default`` is
        :py:obj:`UNSET`, a :py:obj:`KeyError` is raised.
        """

        parent = self._get_parent_dict(name)
        val = parent.get(name.split('.')[-1], UNSET)
        if val is UNSET:
            if default is UNSET:
                raise KeyError(name)
            val = default

        if replace and isinstance(val, str):
            val = val % self
        return val

    def set(self, name: str, val):
        """Set the value to which ``name`` points in the configuration.

        If there is no such ``name`` in the config, a :py:obj:`KeyError` is
        raised.
        """
        parent = self._get_parent_dict(name)
        parent[name.split('.')[-1]] = val

    def _get_parent_dict(self, name):
        parent_name = '.'.join(name.split('.')[:-1])
        if parent_name:
            parent = value(parent_name, self.cfg)
        else:
            parent = self.cfg
        if (parent is UNSET) or (not isinstance(parent, dict)):
            raise KeyError(parent_name)
        return parent

    def path(self, name: str, default=UNSET):
        """Get a :py:class:`pathlib.Path` object from a config string."""

        val = self.get(name, default)
        if val is UNSET:
            if default is UNSET:
                raise KeyError(name)
            return default
        return pathlib.Path(str(val))

    def pyobj(self, name, default=UNSET):
        """Get python object refered by full qualiffied name (FQN) in the config
        string."""

        fqn = self.get(name, default)
        if fqn is UNSET:
            if default is UNSET:
                raise KeyError(name)
            return default
        (modulename, name) = str(fqn).rsplit('.', 1)
        m = __import__(modulename, {}, {}, [name], 0)
        return getattr(m, name)


# working with dictionaries


def value(name: str, data_dict: dict):
    """Returns the value to which ``name`` points in the ``dat_dict``.

    .. code: python

        >>> data_dict = {
                "foo": {"bar": 1 },
                "bar": {"foo": 2 },
                "foobar": [1, 2, 3],
            }
        >>> value('foobar', data_dict)
        [1, 2, 3]
        >>> value('foo.bar', data_dict)
        1
        >>> value('foo.bar.xxx', data_dict)
        <UNSET>

    """

    ret_val = data_dict
    for part in name.split('.'):
        if isinstance(ret_val, dict):
            ret_val = ret_val.get(part, UNSET)
        if ret_val is UNSET:
            break
    return ret_val


def validate(
    schema_dict: typing.Dict, data_dict: typing.Dict, deprecated: typing.Dict[str, str]
) -> typing.Tuple[bool, list]:

    """Deep validation of dictionary in ``data_dict`` against dictionary in
    ``schema_dict``.  Argument deprecated is a dictionary that maps deprecated
    configuration names to a messages::

        deprecated = {
            "foo.bar" : "config 'foo.bar' is deprecated, use 'bar.foo'",
            "..."     : "..."
        }

    The function returns a python tuple ``(is_valid, issue_list)``:

    ``is_valid``:
      A bool value indicating ``data_dict`` is valid or not.

    ``issue_list``:
      A list of messages (:py:obj:`SchemaIssue`) from the validation::

          [schema warn] data_dict: deprecated 'fontlib.foo': <DEPRECATED['foo.bar']>
          [schema invalid] data_dict: key unknown 'fontlib.foo'
          [schema invalid] data_dict: type mismatch 'fontlib.foo': expected ..., is ...

    If ``schema_dict`` or ``data_dict`` is not a dictionary type a
    :py:obj:`SchemaIssue` is raised.

    """
    names = []
    is_valid = True
    issue_list = []

    if not isinstance(schema_dict, dict):
        raise SchemaIssue('invalid', "schema_dict is not a dict type")
    if not isinstance(data_dict, dict):
        raise SchemaIssue('invalid', f"data_dict issue{'.'.join(names)} is not a dict type")

    is_valid, issue_list = _validate(names, issue_list, schema_dict, data_dict, deprecated)
    return is_valid, issue_list


def _validate(
    names: typing.List,
    issue_list: typing.List,
    schema_dict: typing.Dict,
    data_dict: typing.Dict,
    deprecated: typing.Dict[str, str],
) -> typing.Tuple[bool, typing.List]:

    is_valid = True

    for key, data_value in data_dict.items():

        names.append(key)
        name = '.'.join(names)

        deprecated_msg = deprecated.get(name)
        # print("XXX %s: key %s //   data_value: %s" % (name, key, data_value))
        if deprecated_msg:
            issue_list.append(SchemaIssue('warn', f"data_dict '{name}': deprecated - {deprecated_msg}"))

        schema_value = value(name, schema_dict)
        # print("YYY %s: key %s // schema_value: %s" % (name, key, schema_value))
        if schema_value is UNSET:
            if not deprecated_msg:
                issue_list.append(SchemaIssue('invalid', f"data_dict '{name}': key unknown in schema_dict"))
                is_valid = False

        elif type(schema_value) != type(data_value):  # pylint: disable=unidiomatic-typecheck
            issue_list.append(
                SchemaIssue(
                    'invalid',
                    (f"data_dict: type mismatch '{name}':" f" expected {type(schema_value)}, is: {type(data_value)}"),
                )
            )
            is_valid = False

        elif isinstance(data_value, dict):
            _valid, _ = _validate(names, issue_list, schema_dict, data_value, deprecated)
            is_valid = is_valid and _valid
        names.pop()

    return is_valid, issue_list


def dict_deepupdate(base_dict: dict, upd_dict: dict, names=None):
    """Deep-update of dictionary in ``base_dict`` by dictionary in ``upd_dict``.

    For each ``upd_key`` & ``upd_val`` pair in ``upd_dict``:

    0. If types of ``base_dict[upd_key]`` and ``upd_val`` do not match raise a
       :py:obj:`TypeError`.

    1. If ``base_dict[upd_key]`` is a dict: recursively deep-update it by ``upd_val``.

    2. If ``base_dict[upd_key]`` not exist: set ``base_dict[upd_key]`` from a
       (deep-) copy of ``upd_val``.

    3. If ``upd_val`` is a list, extend list in ``base_dict[upd_key]`` by the
       list in ``upd_val``.

    4. If ``upd_val`` is a set, update set in ``base_dict[upd_key]`` by set in
       ``upd_val``.
    """
    # pylint: disable=too-many-branches
    if not isinstance(base_dict, dict):
        raise TypeError("argument 'base_dict' is not a ditionary type")
    if not isinstance(upd_dict, dict):
        raise TypeError("argument 'upd_dict' is not a ditionary type")

    if names is None:
        names = []

    for upd_key, upd_val in upd_dict.items():
        # For each upd_key & upd_val pair in upd_dict:

        if isinstance(upd_val, dict):

            if upd_key in base_dict:
                # if base_dict[upd_key] exists, recursively deep-update it
                if not isinstance(base_dict[upd_key], dict):
                    raise TypeError(f"type mismatch {'.'.join(names)}: is not a dict type in base_dict")
                dict_deepupdate(
                    base_dict[upd_key],
                    upd_val,
                    names
                    + [
                        upd_key,
                    ],
                )

            else:
                # if base_dict[upd_key] not exist, set base_dict[upd_key] from deepcopy of upd_val
                base_dict[upd_key] = copy.deepcopy(upd_val)

        elif isinstance(upd_val, list):

            if upd_key in base_dict:
                # if base_dict[upd_key] exists, base_dict[up_key] is extended by
                # the list from upd_val
                if not isinstance(base_dict[upd_key], list):
                    raise TypeError(f"type mismatch {'.'.join(names)}: is not a list type in base_dict")
                base_dict[upd_key].extend(upd_val)

            else:
                # if base_dict[upd_key] doesn't exists, set base_dict[key] from a deepcopy of the
                # list in upd_val.
                base_dict[upd_key] = copy.deepcopy(upd_val)

        elif isinstance(upd_val, set):

            if upd_key in base_dict:
                # if base_dict[upd_key] exists, base_dict[up_key] is updated by the set in upd_val
                if not isinstance(base_dict[upd_key], set):
                    raise TypeError(f"type mismatch {'.'.join(names)}: is not a set type in base_dict")
                base_dict[upd_key].update(upd_val.copy())

            else:
                # if base_dict[upd_key] doesn't exists, set base_dict[upd_key] from a copy of the
                # set in upd_val
                base_dict[upd_key] = upd_val.copy()

        else:
            # for any other type of upd_val replace or add base_dict[upd_key] by a copy
            # of upd_val
            base_dict[upd_key] = copy.copy(upd_val)
