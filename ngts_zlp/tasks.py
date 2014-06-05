class Task(object):
    def __init__(self, job_runner, jobname):
        self.job_runner = job_runner
        self.jobname = jobname

    def submit(self, *args, **kwargs):
        job_command = self.job_command(*args, **kwargs)
        return self.job_runner.add_job(job_command, self.jobname,
                synchronous=self.synchronous)


class CreateInputListTask(Task):
    script_name = 'createlists.py'
    synchronous = True

    def job_command(self, image_dirs):
        return [self.script_name, image_dirs, 'IMAGE', 'fits', self.jobname]

class CreateMasterBiasTask(Task):
    script_name = 'pipebias.py'
    synchronous = True

    def output_file(self):
        return '{jobname}_MasterBias.fits'.format(jobname=self.jobname)

    def job_command(self, bias_list, output_dir):
        return [self.script_name, bias_list, self.output_file(), output_dir]

