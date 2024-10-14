import pytest

from main import sanitize_inputs


def test_sanitize_inputs():
    # UUID should pass
    sanitize_inputs("cf827976-b324-483a-ad15-ff29c732bab6")
    # Underscore should pass
    sanitize_inputs("Group_1")
