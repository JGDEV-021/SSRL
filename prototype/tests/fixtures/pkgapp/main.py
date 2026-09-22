"""pkgapp — synthetic test fixture for SSRL MVP tests (deterministic)."""


def main():
    return greeting()


def greeting():
    return "hello"


def _private_helper():
    return 42