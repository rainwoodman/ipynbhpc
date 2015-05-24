from mpi4py import MPI
import sys
from sys import argv
import os.path
import cPickle as pickle

# usage:
# payload.py scriptfile vars.pickle out1 out2 out3 out4
# 
# script will be ran with a global name space populated by
# vars.pickle, 
# after it finishes
# out1, out2 , ... will be written to vars.pickle

pathfile = argv[1]
script = argv[2]
picklefile = argv[3]
varnamesout = argv[4:]

comm = MPI.COMM_WORLD
varsin = None
path = None

if comm.rank == 0:
    with file(script, 'r') as ff:
        script = ff.read()

    with file(pathfile, 'r') as ff:
        path = ff.read()

    with file(picklefile, 'r') as ff:
        varsin = ff.read()

path = comm.bcast(path)
script = comm.bcast(script)
varsin = comm.bcast(varsin)

path = pickle.loads(path)

# prepend current dir
# append the rest of the path
# this is done to avoid overriding path overridings
# of the python intepreter.
#
# for example, our python-mpi (bcast) on Edison would
# prefer to use those packages locally replicated at /dev/shm
# to avoid many file operations.  

sys.path.insert(0, path[0])
sys.path.extend(path[1:])

env = pickle.loads(varsin)

env['__file__'] = os.path.abspath(script)
env['__name__'] = "__main__"
env['MPI'] = MPI

exec(script, env)

if comm.rank == 0:
    varsout = {}
    for varname in varnamesout:
        varsout[varname] = env[varname]

    with file(picklefile, 'w') as ff:
        pickle.dump(varsout, ff, pickle.HIGHEST_PROTOCOL)

comm.barrier()

