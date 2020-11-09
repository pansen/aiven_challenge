from pansen.aiven.config import Config
from pansen.aiven.lib.schedule import Schedule
from pansen.aiven.lib.http import MonitorUrlJob


def test_get_jobs(config: Config):
    s = Schedule(config)
    parsed = s.get_jobs()
    assert 0 < len(parsed)
    assert all([isinstance(p, MonitorUrlJob) for p in parsed])

    # We operate with a special test config `test_url_config.yaml`, thus we can assert particular
    # contents.
    assert 2 == len(parsed)
    assert "http://httpbin.org/post?a=1" == parsed[0].url
    assert "http://httpbin.org/get?a=1" == parsed[1].url
