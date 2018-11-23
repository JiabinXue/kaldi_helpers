from setuptools import setup, find_packages

requirements = [
    'pytest',
    'pympi-ling',
    'numpy',
    'langid',
    'nltk',
    'praatio',
    'pydub',
]

setup(
    name='kaldi_helpers',
    version='0.3',
    packages=find_packages(),
    url='https://github.com/CoEDL/kaldi-helpers',
    install_requires=requirements,
    include_package_data=True,
    license='',
    author='CoEDL',
    author_email='n.lambourne@uq.edu.au',
    description='Scripts for preparing language data for use with Kaldi ASR',
    entry_points={
    },
)
