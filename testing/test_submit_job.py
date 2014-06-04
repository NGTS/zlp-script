import mock
from ngts_zlp.submit_job import JobQueue

def test_qsub():
    job_name = 'test_job_name'
    assert JobQueue().qsub(job_name) == [
            'qsub', '-cwd', '-N', job_name,
                '-S', '/bin/bash',
                '-q', 'parallel']


def test_add_job_calls_qsub():
    jq = JobQueue()

    test_job = ['ls', ]
    job_name = 'testing-ls'

    with mock.patch.object(jq, 'qsub') as mock_qsub:
        mock_qsub.return_value = ['qsub_stub', '-cwd', '-N', job_name,
                '-S', '/bin/bash',
                '-q', 'parallel']

        value = jq.add_job(test_job, job_name)

        assert mock_qsub.called_once() and value == 'ls\n'
