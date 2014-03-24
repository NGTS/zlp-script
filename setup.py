from setuptools import setup
from glob import glob
import re

package_name = 'ngts_catalogue'
version_str = re.search(r'^__version__\s+=\s+[\'"]([\d.]+)[\'"]',
        open('%s/version.py' % (package_name, )).read(),
        re.M).group(1)

setup(name=package_name,
        version=version_str,
        description='NGTS initial catalogue generation',
        author='Tom Louden',
        author_email='t.m.louden@warwick.ac.uk',
        maintainer='Simon Walker',
        maintainer_email='s.r.walker101@googlemail.com',
        url='http://github.com/NGTS/zlp-input-catalogue',
        packages=['ngts_catalogue', ],
        entry_points={
            'console_scripts': ['ZLP_create_cat.py = ngts_catalogue.main:main'],
            },
        long_description=open('README.markdown').read(),
        install_requires=['astropy>=0.3',
            'fitsio',
            'docopt',
            'numpy>=1.8',
            ]
        )
