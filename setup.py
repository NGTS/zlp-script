from setuptools import setup
from glob import glob
import re

package_name = 'ngts_zlp'
version_str = re.search(r'^__version__\s+=\s+[\'"]([\d.]+.*?)[\'"]',
        open('%s/version.py' % (package_name, )).read(),
        re.M).group(1)

setup(name=package_name,
        version=version_str,
        description='NGTS ZLP run script',
        author='Simon Walker',
        author_email='s.r.walker101@googlemail.com',
        url='http://github.com/NGTS/zlp-run-script',
        packages=['ngts_zlp', ],
        long_description='',
        install_requires=[
            'sh',
            ]
        )
