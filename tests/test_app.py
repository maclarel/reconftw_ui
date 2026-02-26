"""
Smoke tests – verify the application starts and all routes respond without errors.

These tests use an empty example.com fixture directory. All parsers handle
missing files gracefully, so every route should return 200 with empty data.
"""

import pytest
from flask import Flask

DOMAIN = "example.com"
DOMAIN_PREFIX = f"/domain/{DOMAIN}"


def test_create_app_returns_flask_instance(app):
    assert isinstance(app, Flask)


def test_index(client):
    r = client.get("/")
    assert r.status_code == 200


@pytest.mark.parametrize("path", [
    f"/domain/{DOMAIN}/",
    f"/domain/{DOMAIN}/overview",
    f"/domain/{DOMAIN}/subdomains",
    f"/domain/{DOMAIN}/webs",
    f"/domain/{DOMAIN}/hosts",
    f"/domain/{DOMAIN}/osint",
    f"/domain/{DOMAIN}/vulnerabilities",
    f"/domain/{DOMAIN}/fuzzing",
    f"/domain/{DOMAIN}/screenshots",
    f"/domain/{DOMAIN}/js",
])
def test_domain_routes_200(client, path):
    r = client.get(path)
    assert r.status_code == 200


def test_unknown_domain_returns_404(client):
    r = client.get("/domain/nonexistent.invalid/")
    assert r.status_code == 404


@pytest.mark.parametrize("path", [
    "/domain/../etc/",
    "/domain/example.com/../other/",
])
def test_path_traversal_returns_404(client, path):
    r = client.get(path)
    assert r.status_code == 404


def test_fuzzing_valid_status_filter(client):
    r = client.get(f"{DOMAIN_PREFIX}/fuzzing?status=200")
    assert r.status_code == 200


def test_fuzzing_out_of_range_status_filter(client):
    """Status filter outside 200-399 should be silently reset, not raise."""
    r = client.get(f"{DOMAIN_PREFIX}/fuzzing?status=500")
    assert r.status_code == 200


def test_fuzzing_non_numeric_status_filter(client):
    r = client.get(f"{DOMAIN_PREFIX}/fuzzing?status=abc")
    assert r.status_code == 200
