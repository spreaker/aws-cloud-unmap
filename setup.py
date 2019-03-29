import sys
from setuptools import setup

if sys.version_info.major < 3:
    raise RuntimeError('Installing requires Python 3 or newer')

# Read the long description from README.md
with open('README.md') as file:
    long_description = file.read()

# Read requirements
with open('requirements.txt') as file:
    requirements = list(filter(lambda r: r, file.read().split("\n")))

setup(
  name             = 'aws-cloud-unmap',
  packages         = ['cloudunmap'],
  version          = '1.0.0',
  description      = 'Remove terminated EC2 instances from AWS CloudMap service',
  long_description = long_description,
  author           = 'Marco Pracucci',
  author_email     = 'marco@pracucci.com',
  url              = 'https://github.com/spreaker/aws-cloud-unmap',
  download_url     = 'https://github.com/spreaker/aws-cloud-unmap/archive/1.0.0.tar.gz',
  keywords         = ['aws', 'cloud map'],
  classifiers      = [],
  python_requires  = ' >= 3',
  install_requires = [requirements],
  entry_points     = {
    'console_scripts': [
        'aws-cloud-unmap=cloudunmap.cli:main',
    ]
  }
)
