import mock
from ngts_zlp.submit_job import JobQueue
import pytest

@pytest.fixture
def job_queue():
    return JobQueue()

@pytest.yield_fixture
def mock_qsub(job_queue):
    with mock.patch.object(job_queue, 'qsub') as m_qsub:
        m_qsub.return_value = ['qsub_stub', '-cwd', '-N', 'mock_job',
                '-S', '/bin/bash',
                '-q', 'parallel']
        yield m_qsub

def test_qsub(job_queue):
    job_name = 'test_job_name'
    assert job_queue.qsub(job_name) == [
            'qsub', '-cwd', '-N', job_name,
                '-S', '/bin/bash',
                '-q', 'parallel']

def test_qsub_syncronous(job_queue):
    job_name = 'test_job_name'
    assert job_queue.qsub(job_name, synchronous=True) == [
            'qsub', '-cwd', '-N', job_name,
                '-S', '/bin/bash',
                '-q', 'parallel',
                '-sync', 'y']


def test_add_job_calls_qsub(mock_qsub, job_queue):
    job_queue.add_job(['ls', ], 'mock_job')
    assert mock_qsub.called_once()

def test_submit_ls_passes_ls(mock_qsub, job_queue):
    value = job_queue.add_job(['ls', ], 'mock_job')
    assert value == 'ls'

