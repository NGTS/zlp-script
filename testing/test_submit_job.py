from ngts_zlp.submit_job import JobQueue
import pytest

@pytest.fixture
def job_queue():
    '''
    Constructs a default job_queue, with the stub qsub script
    '''
    return JobQueue(qsub_command='qsub_stub')

def test_qsub(job_queue):
    job_name = 'test_job_name'
    assert job_queue.qsub(job_name) == [
            'qsub_stub', '-cwd', '-N', job_name,
                '-S', '/bin/bash',
                '-q', 'parallel']

def test_qsub_syncronous(job_queue):
    job_name = 'test_job_name'
    assert job_queue.qsub(job_name, synchronous=True) == [
            'qsub_stub', '-cwd', '-N', job_name,
                '-S', '/bin/bash',
                '-q', 'parallel',
                '-sync', 'y']


def test_submit_ls_passes_ls(job_queue):
    value = job_queue.add_job(['ls', ], 'mock_job')
    assert value == 'ls'

