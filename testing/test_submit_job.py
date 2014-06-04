from ngts_zlp.submit_job import JobQueue

def test_add_job():
    jq = JobQueue()

    test_job = ['ls', ]
    job_name = 'testing-ls'

    jq.add_job(test_job, job_name)


