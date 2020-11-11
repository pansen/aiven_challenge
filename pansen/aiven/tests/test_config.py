import os
from urllib import parse

from pansen.aiven.config import Config


def test_URL_CONFIG_FILE_is_absolute(config: Config):
    assert os.path.isabs(config.URL_CONFIG_FILE)
    assert os.path.isfile(config.URL_CONFIG_FILE)


def test_config_postgres_url_parse(config: Config):
    urlparse = parse.urlparse(config.POSTGRES_URL)
    assert urlparse.hostname
    assert urlparse.port
    assert urlparse.username
    assert urlparse.password
    assert urlparse.path.lstrip("/")

    assert urlparse.hostname == config.POSTGRES_CONNECTION_ARGS["host"]
    assert urlparse.port == config.POSTGRES_CONNECTION_ARGS["port"]
    assert urlparse.username == config.POSTGRES_CONNECTION_ARGS["user"]
    assert urlparse.password == config.POSTGRES_CONNECTION_ARGS["password"]
    assert urlparse.path.lstrip("/") == config.POSTGRES_CONNECTION_ARGS["database"]
