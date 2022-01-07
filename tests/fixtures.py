import os

import pytest

from squirrel.squirrel import _main


@pytest.fixture
def test_directory(tmp_path):
    cwd = os.getcwd()
    d = tmp_path / 'test_directory'
    d.mkdir()
    os.chdir(str(d))

    yield True

    #teardown
    os.chdir(cwd)


@pytest.fixture
def initialized(test_directory):
    _main(['init'])