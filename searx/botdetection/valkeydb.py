# SPDX-License-Identifier: AGPL-3.0-or-later
"""Providing a Valkey database for the botdetection methods."""

from __future__ import annotations

import valkey

__all__ = ["set_valkey_client", "get_valkey_client"]

CLIENT: valkey.Valkey | None = None
"""Global Valkey DB connection (Valkey client object)."""


def set_valkey_client(valkey_client: valkey.Valkey):
    global CLIENT  # pylint: disable=global-statement
    CLIENT = valkey_client


def get_valkey_client() -> valkey.Valkey:
    if CLIENT is None:
        raise ValueError("No connection to the Valkey database has been established.")
    return CLIENT
