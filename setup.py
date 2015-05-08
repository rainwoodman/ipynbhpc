from distutils.core import setup

setup(
    name="ipynbhpc", version="0.1pre",
    author="Yu Feng",
    author_email="rainwoodman@gmail.com",
    url="http://github.com/rainwoodman/ipynbhpc",
    description="IPython Notebook Cells as HPC jobs",
    zip_safe = False,
    packages= ['ipynbhpc'],
    requires=['ipython'],
)
