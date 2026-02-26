import os
from pathlib import Path

import pytest

from app import create_app

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture()
def app(monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(FIXTURES_DIR))
    return create_app()


@pytest.fixture()
def client(app):
    return app.test_client()
