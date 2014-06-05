import pytest
from ngts_zlp.submit_job import JobQueue

@pytest.fixture
def job_queue():
    '''
    Constructs a default job_queue, with the stub qsub script
    '''
    return JobQueue(qsub_command='qsub_stub')

