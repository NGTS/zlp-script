from ngts_zlp.tasks import CreateMasterBiasTask
from ngts_zlp.submit_job import JobQueue

def test_build_master_bias_command():
    job_runner = 0
    jobname = 'test_job'
    output_dir = '/output'
    bias_list = 'biaslist.txt'

    t = CreateMasterBiasTask(job_runner, jobname)

    assert t.job_command(bias_list, output_dir) == [
            'pipebias.py', bias_list, 'test_job_MasterBias.fits',
            output_dir]

def test_submit_master_bias_job(job_queue):
    jobname = 'test_job'
    output_dir = '/output'
    bias_list = 'biaslist.txt'

    t = CreateMasterBiasTask(job_queue, jobname)

    result = t.submit(bias_list, output_dir)
    assert result == 'pipebias.py biaslist.txt test_job_MasterBias.fits /output'

