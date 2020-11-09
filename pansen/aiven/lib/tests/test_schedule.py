from pansen.aiven.config import Config
from pansen.aiven.lib.schedule import MonitorUrlJob, Schedule


def test_get_jobs(config: Config):
    s = Schedule(config)
    parsed = s.get_jobs()
    assert 0 < len(parsed)
    assert all([isinstance(p, MonitorUrlJob) for p in parsed])
