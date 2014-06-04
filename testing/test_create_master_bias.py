from ngts_zlp.tasks import CreateMasterBiasTask

def test_build_master_bias_command():
    job_runner = 0
    jobname = 'test_job'
    output_dir = '/output'
    bias_list = 'biaslist.txt'

    t = CreateMasterBiasTask(job_runner, jobname)

    assert t.job_command(bias_list, output_dir) == [
            'pipebias.py', bias_list, 'test_job_MasterBias.fits',
            output_dir]

