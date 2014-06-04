import mock
from ngts_zlp.submit_job import JobQueue
import pytest

@pytest.fixture
def job_queue():
    return JobQueue()

def test_qsub(job_queue):
    job_name = 'test_job_name'
    assert job_queue.qsub(job_name) == [
            'qsub', '-cwd', '-N', job_name,
                '-S', '/bin/bash',
                '-q', 'parallel']

def test_add_job_calls_qsub(job_queue):
    test_job = ['ls', ]
    job_name = 'testing-ls'

    with mock.patch.object(job_queue, 'qsub') as mock_qsub:
        mock_qsub.return_value = ['qsub_stub', '-cwd', '-N', job_name,
                '-S', '/bin/bash',
                '-q', 'parallel']

        job_queue.add_job(test_job, job_name)

        assert mock_qsub.called_once()

def test_submit_ls_passes_ls(job_queue):
    test_job = ['ls', ]
    job_name = 'testing-ls'

    with mock.patch.object(job_queue, 'qsub') as mock_qsub:
        mock_qsub.return_value = ['qsub_stub', '-cwd', '-N', job_name,
                '-S', '/bin/bash',
                '-q', 'parallel']

        value = job_queue.add_job(test_job, job_name)
        assert value == 'ls\n'

