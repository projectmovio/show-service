import os
from unittest.mock import MagicMock
import pytest

os.environ["LOG_LEVEL"] = "DEBUG"


@pytest.fixture(scope='function')
def mocked_show_db():
    import show_db

    show_db.table = MagicMock()
    show_db.client = MagicMock()

    return show_db