import os

from pansen.aiven.config import Config


def test_URL_CONFIG_FILE_is_absolute(config: Config):
    assert os.path.isabs(config.URL_CONFIG_FILE)
    assert os.path.isfile(config.URL_CONFIG_FILE)
