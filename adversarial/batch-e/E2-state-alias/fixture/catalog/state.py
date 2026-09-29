# Copyright (c) 2026 Example Fixture. MIT License.
"""Shared catalog state. Consumers hold live views (MappingProxyType)."""

from types import MappingProxyType

STATE = {"sku": 1}


def view():
    return MappingProxyType(STATE)


def reset():
    STATE.clear()
    STATE.update({"sku": 1})
