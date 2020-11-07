import inspect
import os

import pytest
from starlette.testclient import TestClient
from vcr import VCR

from pansen.aiven.config import Config, configure
from pansen.aiven.main import app


@pytest.fixture(scope="function")
def config() -> Config:
    return configure(app)


@pytest.fixture(scope="function")
def test_client(config) -> TestClient:
    c = TestClient(app)
    return c


def _build_vcr_cassette_yaml_path_from_func_using_module(function):
    return os.path.join(os.path.dirname(inspect.getfile(function)), function.__name__ + ".yaml")


cast_vcr = VCR(
    func_path_generator=_build_vcr_cassette_yaml_path_from_func_using_module,
    decode_compressed_response=True,
    # https://vcrpy.readthedocs.io/en/latest/advanced.html#filter-sensitive-data-from-the-request
    # filter_headers=['authorization'],
    # 'new_episodes' | 'once'
    record_mode="once",
)
