"""CORS_ORIGINS is documented as comma-separated; a JSON array also works.

Getting this wrong only shows up at boot on a real server, with a SettingsError
that names no value — cheap to pin down here.
"""
from app.core.config import Settings


def test_comma_separated(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://a.com, https://b.com")
    assert Settings(_env_file=None).cors_origins == ["https://a.com", "https://b.com"]


def test_json_array(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", '["https://a.com","https://b.com"]')
    assert Settings(_env_file=None).cors_origins == ["https://a.com", "https://b.com"]


def test_single_value(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://only.com")
    assert Settings(_env_file=None).cors_origins == ["https://only.com"]
