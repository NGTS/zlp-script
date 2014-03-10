from setuptools import setup
from glob import glob

setup(name='ngts_catalogue',
        version='0.0.1',
        description='NGTS initial catalogue generation',
        author='Tom Louden',
        author_email='t.m.louden@warwick.ac.uk',
        maintainer='Simon Walker',
        maintainer_email='s.r.walker101@googlemail.com',
        url='http://github.com/NGTS/zlp-input-catalogue',
        packages=['ngts_catalogue', ],
        scripts=glob('bin/*.py'),
        long_description=open('README.markdown').read(),
        install_requires=['astropy>=0.3',
            'fitsio',
            'docopt',
            'numpy>=1.8',
            ]
        )
