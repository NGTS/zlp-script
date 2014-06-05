from ngts_zlp.tasks import CreateInputListTask

def test_build_input_list_command():
    job_runner = 0
    jobname = 'test_job'
    image_dirs = 'imagedirs'

    t = CreateInputListTask(job_runner, jobname=jobname)

    assert t.job_command(image_dirs) == ['createlists.py',
            image_dirs, 'IMAGE', 'fits', jobname]

def test_submit_input_list_job(job_queue):
    jobname = 'test_job'
    image_dirs = 'imagedirs'

    t = CreateInputListTask(job_queue, jobname)

    result = t.submit(image_dirs)
    assert result == 'createlists.py imagedirs IMAGE fits test_job'

