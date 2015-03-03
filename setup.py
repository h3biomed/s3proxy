from setuptools import setup

setup(
    name='s3proxy',
    author='Nik Krumm',
    version='0.0.1',
    url='http://github.com/h3biomed/s3proxy',
    packages=['s3proxy'],
    description='S3proxy - serve S3 files simply',
    include_package_data=True,
    install_requires=[
        'PyYAML',
        'boto',
        'flask'
    ]
)