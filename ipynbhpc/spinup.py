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

script = argv[1]
picklefile = argv[2]
varnamesout = argv[3:]

sys.path.insert(0, os.path.abspath(os.getcwd()))

comm = MPI.COMM_WORLD
varsin = None

if comm.rank == 0:
    with file(script, 'r') as ff:
        script = ff.read()

    with file(picklefile, 'r') as ff:
        varsin = ff.read()
script = comm.bcast(script)
varsin = comm.bcast(varsin)

env = pickle.loads(varsin)

env['__file__'] = os.path.abspath(script)
env['__name__'] = "__main__"

exec(script, env)

if comm.rank == 0:
    varsout = {}
    for varname in varnamesout:
        varsout[varname] = env[varname]

    with file(picklefile, 'w') as ff:
        pickle.dump(varsout, ff, pickle.HIGHEST_PROTOCOL)

comm.barrier()

