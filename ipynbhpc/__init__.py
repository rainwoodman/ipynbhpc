def setup():
    from IPython import get_ipython
    from magics import HPCMagics
    ip = get_ipython()
    ip.register_magics(HPCMagics)
    
