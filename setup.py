import sys
from setuptools import setup

# Version
version = "1.0.4"

# Requires Python 3
if sys.version_info.major < 3:
    raise RuntimeError('Installing requires Python 3 or newer')

# Read the long description from README.md
with open('README.md') as file:
    long_description = file.read()

setup(
  name                          = 'aws-cloud-unmap',
  packages                      = ['cloudunmap'],
  version                       = version,
  description                   = 'Remove terminated EC2 instances from AWS CloudMap service',
  long_description              = long_description,
  long_description_content_type = 'text/markdown',
  author                        = 'Marco Pracucci',
  author_email                  = 'marco@pracucci.com',
  url                           = 'https://github.com/spreaker/aws-cloud-unmap',
  download_url                  = f'https://github.com/spreaker/aws-cloud-unmap/archive/{version}.tar.gz',
  keywords                      = ['aws', 'cloud map'],
  classifiers                   = [],
  python_requires               = ' >= 3',
  install_requires              = ["boto3==1.9.123", "python-json-logger==0.1.10"],
  extras_require = {
    'dev': [
      'flake8==3.7.7',
      'twine==1.13.0'
    ]
  },
  entry_points = {
    'console_scripts': [
        'aws-cloud-unmap=cloudunmap.cli:run',
    ]
  }
)
