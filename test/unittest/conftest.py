import os
from unittest.mock import MagicMock
import pytest

os.environ["LOG_LEVEL"] = "DEBUG"


@pytest.fixture(scope='function')
def mocked_shows_db():
    import shows_db

    shows_db.table = MagicMock()
    shows_db.client = MagicMock()

    return shows_db


@pytest.fixture(scope='function')
def mocked_episodes_db():
    import episodes_db

    episodes_db.table = MagicMock()

    return episodes_db
