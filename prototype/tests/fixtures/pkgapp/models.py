""":mod:`pkgapp.models` — domain models."""


class Item:
    """A domain item."""

    def validate(self):
        return True


def looks_valid(item):
    return item.x > 0