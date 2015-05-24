from IPython.core.magic import (Magics, magics_class, line_magic,
                                    cell_magic, line_cell_magic)

import cPickle as pickle
import cloudpickle
import os.path
import re
import PBS
import sys

class Result(object):
    def __init__(self, stdout, stderr):
        self.stdout = stdout
        self.stderr = stderr

@magics_class
class HPCMagics(Magics):
    def __init__(self, shell):
        super(HPCMagics, self).__init__(shell)
        self.spinup = os.path.join(os.path.dirname(__file__), 'spinup.py')

        self.PBS_TEMPLATE="""
#PBS -N ipynbhpcjob
#PBS -q debug
#PBS -l mppwidth=%(jobsize)d
#PBS -o %(stderr)s
#PBS -e %(stdout)s

cd $PBS_O_WORKDIR

aprun -n %(jobsize)d python-mpi %(cmdline)s

"""
        pass

    def parse(self, line):
        clauses = re.findall('(\s*(size|in|out)\(([^)]*)\))', line)
        varsin = set()
        varsout = set()
        size = 1
        for c in clauses:
            if c[1].lower() == 'size':
                size = int(c[2])
            elif c[1].lower() == 'in':
                varsin.update(set([a.strip() for a in c[2].split(',') if len(a.strip())]))
            elif c[1].lower() == 'out':
                varsout.update(set([a.strip() for a in c[2].split(',') if len(a.strip())]))
        return size, varsin, varsout
        
    @cell_magic('mpisetup')
    def mpisetup(self, line, cell):
        """ Setup the mpi magic 
            Useful substitutes are:
            
            %(jobsize)d : The number of ranks to use
            %(stdout)s : A generated location for the job stdout file.
            %(stderr)s : A generated location for the job stderr file.
            %(cmdline)s : A generated string for the command line to python
                          interpretor.

            
            Example
            -------

            >>> %%mpisetup
            #PBS -j eo
            #PBS -l mppwidth=%(jobsize)d
            #PBS -e %(stderr)s
            #PBS -o %(stdout)s

            cd $PBS_O_WORKDIR

            aprun -n %(jobsize)d python-mpi %(cmdline)s
            
        """
        for keyword in ['%(jobsize)d', '%(stderr)s', 
                    '%(stdout)s', '%(cmdline)s']:
            if keyword not in cell:
                raise ValueError('Keyword `%s` not in the job script stub'
                    % keyword)
        self.PBS_TEMPLATE = cell

    @cell_magic('mpi')
    def mpi(self, line, cell):
        payload = 'tmpjob-payload.py'
        pathfile = 'tmpjob-path.pickle'
        picklefile = 'tmpjob.pickle'
        stderrfile = 'tmpjob.err'
        stdoutfile = 'tmpjob.out'
        size, varsin, varsout = self.parse(line)

        with file(payload, 'w') as ff:
            ff.write(cell)

        # use the absolute paths in the payload
        # path is stored in a different pickle
        # because unpickling the 'in' variable may need the properly
        # setup path

        path = [os.path.abspath(os.getcwd())] + \
                    [os.path.abspath(p) for p in sys.path]

        with file(pathfile, 'w') as ff:
            cloudpickle.dump(path, ff)
            
        d = {}
        for var in varsin:
            d[var] = self.shell.user_ns[var]

        with file(picklefile, 'w') as ff:
            cloudpickle.dump(d, ff, pickle.HIGHEST_PROTOCOL)

        cmdline = "%(spinup)s %(path)s %(payload)s %(pickle)s %(varsout)s" % dict(
                path=pathfile,
                spinup=self.spinup,
                payload=payload,
                pickle=picklefile,
                varsout=" ".join(varsout))

        script = self.PBS_TEMPLATE % dict(
            stderr=stderrfile,
            stdout=stdoutfile,
            jobsize=size, cmdline=cmdline
            )

        job = PBS.submit(script)
        try:
            PBS.wait(job)
        except KeyboardInterrupt:
            PBS.delete(job)

        PBS.wait(job) 
        with file(picklefile, 'r') as ff:
            varsout = pickle.load(ff)
        for var in varsout:
            self.shell.user_ns[var] = varsout[var] 
        try:
            stderr = file(stderrfile, 'r')
            with stderr:
                errstr = stderr.read()
            self.shell.write_err(errstr)
            os.unlink(stderrfile)
        except IOError:
            errstr = None
        try:
            stdout = file(stdoutfile, 'r')
            with stdout:
                outstr = stdout.read()
            self.shell.write(outstr)
            os.unlink(stdoutfile)
        except IOError:
            outstr = None
        os.unlink(payload)
        os.unlink(picklefile)
        return Result(stderr=errstr, stdout=outstr)
