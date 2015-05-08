from mpi4py import MPI
from sys import argv
import cPickle as pickle

# usage:
# payload.py scriptfile vars.pickle out1 out2 out3 out4
# 
# script will be ran with a global name space populated by
# vars.pickle, 
# after it finishes
# out1, out2 , ... will be written to vars.pickle

script = argv[1]
comm = MPI.COMM_WORLD
varsin = None

if comm.rank == 0:
    with file(script, 'r') as ff:
        script = ff.read()

    with file(argv[2], 'r') as ff:
        varsin = pickle.load(ff)

script = comm.bcast(script)
varsin = comm.bcast(varsin)

varnamesout = argv[3:]

exec(script, varsin)

if comm.rank == 0:
    varsout = {}
    for varname in varnamesout:
        varsout[varname] = varsin[varname]

    with file(argv[2], 'w') as ff:
        pickle.dump(varsout, ff, pickle.HIGHEST_PROTOCOL)

comm.barrier()

