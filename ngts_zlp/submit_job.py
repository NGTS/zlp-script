import subprocess as sp

class JobQueue(object):
    def qsub(self, jobname, queue='parallel', synchronous=False):
        cmd = ['qsub', '-cwd', '-N', jobname,
                '-S', '/bin/bash',
                '-q', queue]
        if synchronous:
            cmd += ['-sync', 'y']

        return cmd

    def add_job(self, cmd, jobname):
        p = sp.Popen(self.qsub(jobname), stdout=sp.PIPE, stdin=sp.PIPE)
        return p.communicate(input=' '.join(cmd))[0].strip('\n')

