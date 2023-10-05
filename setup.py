import sys
from setuptools import setup

# Version
version = "2.0.0"

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
  author                        = 'Spreaker',
  author_email                  = 'dev@spreaker.com',
  url                           = 'https://github.com/spreaker/aws-cloud-unmap',
  download_url                  = f'https://github.com/spreaker/aws-cloud-unmap/archive/{version}.tar.gz',
  keywords                      = ['aws', 'cloud map'],
  classifiers                   = [],
  python_requires               = ' >= 3.11',
  install_requires              = ["boto3==1.28.53", "python-json-logger==2.0.7", "prometheus_client==0.17.1"],
  extras_require = {
    'dev': [
      'flake8==6.1.0',
      'twine==4.0.2'
    ]
  },
  entry_points = {
    'console_scripts': [
        'aws-cloud-unmap=cloudunmap.cli:run',
    ]
  }
)
