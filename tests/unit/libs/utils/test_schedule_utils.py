import pytest
import schedule

import libs.utils.schedule_utils as schedule_utils


@pytest.fixture(scope='module')
def add_test_jobs():
    schedule.every().hour.do(print, 'Hi').tag('three', 'two')
    schedule.every().hour.do(print, 'Hi').tag('unique')
    schedule.every().hour.do(print, 'Hi').tag('three')
    schedule.every().hour.do(print, 'Hi').tag('two')
    schedule.every().hour.do(print, 'Hi').tag('non-unique')
    schedule.every().hour.do(print, 'Hi').tag('three', 'non-unique')
    yield
    schedule.clear()


@pytest.mark.parametrize('tag, expected_jobs', [
    ('three', 3),
    ('two', 2),
    ('unique', 1),
    ('non-unique', 2),
    (None, 6),
])
def test_fetch_jobs(add_test_jobs, tag, expected_jobs):
    assert len(schedule_utils.fetch_jobs(tag)) == expected_jobs


@pytest.mark.parametrize('tag', ['three', 'two', 'unique', 'non-unique', None])
def test_fetch_only_job(add_test_jobs, tag):
    if tag == 'unique':
        assert tag in schedule_utils.fetch_only_job(tag).tags
    else:
        with pytest.raises(schedule_utils.NonUniqueJobTagError):
            schedule_utils.fetch_only_job(tag)
