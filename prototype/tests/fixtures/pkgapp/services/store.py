""":mod:`pkgapp.services` — service orchestration."""
from ..db import save


def store(item):
    """Validate and persist an item (flow entry)."""
    return save(item)