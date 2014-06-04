from ngts_zlp.tasks import Task

def test_assign_job_runner():
    job_runner = 12
    jobname = 'jobname'
    t = Task(job_runner, jobname)
    assert t.job_runner == job_runner
    assert t.jobname == jobname
