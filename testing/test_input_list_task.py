from ngts_zlp.tasks import CreateInputListTask

def test_build_input_list_command():
    job_runner = 0
    jobname = 'test_job'
    image_dirs = 'imagedirs'

    t = CreateInputListTask(job_runner, jobname=jobname)

    assert t.job_command(image_dirs) == ['create_lists.py',
            image_dirs, 'IMAGE', 'fits', jobname]

