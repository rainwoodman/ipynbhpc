from IPython.core.magic import (Magics, magics_class, line_magic,
                                    cell_magic, line_cell_magic)
import cPickle as pickle
import os.path
import re
import PBS

@magics_class
class HPCMagics(Magics):
    def __init__(self, shell):
        super(HPCMagics, self).__init__(shell)
        self.spinup = os.path.join(os.path.dirname(__file__), 'spinup.py')

        self.setup()
    def setup(self):
        self.PBS_TEMPLATE="""
#PBS -j eo
#PBS -N ipynbhpcjob
#PBS -e %(logfile)s
#PBS -q debug
#PBS -l mppwidth=%(jobsize)d

cd $PBS_O_WORKDIR

aprun -n %(jobsize)d python-mpi %(spinup)s %(payload)s %(pickle)s %(varsout)s

"""
        pass

    def parse(self, line):
        clauses = re.findall('(\s*(size|in|out)\(([^)]*)\))', line)
        varsin = None
        varsout = None
        size = 1
        for c in clauses:
            if c[1].lower() == 'size':
                size = int(c[2])
            elif c[1].lower() == 'in':
                if varsin is None:
                    varsin = set()
                varsin.update(set([a.strip() for a in c[2].split(',') if len(a.strip())]))
            elif c[1].lower() == 'out':
                if varsout is None:
                    varsout = set()
                varsout.update(set([a.strip() for a in c[2].split(',') if len(a.strip())]))
        return size, varsin, varsout
        
    @cell_magic('qsub')
    def qsub(self, line, cell):
        payload = 'tmpjob.py'
        picklefile = 'tmpjob.pickle'
        logfile = 'tmpjob.log'
        size, varsin, varsout = self.parse(line)

        with file(payload, 'w') as ff:
            ff.write(cell)

        d = {}
        for var in varsin:
            d[var] = self.shell.user_ns[var]

        with file(picklefile, 'w') as ff:
            pickle.dump(d, ff, pickle.HIGHEST_PROTOCOL)

        script = self.PBS_TEMPLATE % dict(
            logfile='tmpjob.log',
            jobsize=size,
            spinup=self.spinup,
            payload=payload,
            pickle=picklefile,
            varsout=" ".join(varsout))

        job = PBS.submit(script)
        PBS.wait(job)
        with file(picklefile, 'r') as ff:
            varsout = pickle.load(ff)
        for var in varsout:
            self.shell.user_ns[var] = varsout[var] 
        with file(logfile, 'r') as ff:
            return ff.read()

# In order to actually use these magics, you must register them with a
# running IPython.  This code must be placed in a file that is loaded
# once
# IPython is up and running:
ip = get_ipython()
# You can register the class itself without instantiating it.  IPython
# will
# call the default constructor on it.
ip.register_magics(HPCMagics)
