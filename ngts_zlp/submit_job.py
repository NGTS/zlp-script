import subprocess as sp

class JobQueue(object):
    def __init__(self, qsub_command='qsub'):
        self.qsub_command = qsub_command

    def qsub(self, jobname, queue='parallel', synchronous=False):
        cmd = [self.qsub_command, '-cwd', '-N', jobname,
                '-S', '/bin/bash',
                '-q', queue]
        if synchronous:
            cmd += ['-sync', 'y']

        return cmd

    def add_job(self, cmd, jobname, synchronous=False):
        p = sp.Popen(self.qsub(jobname, synchronous=synchronous),
                stdout=sp.PIPE, stdin=sp.PIPE)
        return p.communicate(input=' '.join(cmd))[0].strip('\n')

