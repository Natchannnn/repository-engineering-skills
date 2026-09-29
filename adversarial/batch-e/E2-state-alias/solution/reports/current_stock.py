# Copyright (c) 2026 Example Fixture. MIT License.
"""Stock report: reads through the live shared view."""

from catalog import state


def held_view():
    return state.view()


def current():
    return dict(state.view())
