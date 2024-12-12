from setuptools import setup, find_packages

setup(
    # Needed to silence warnings (and to be a worthwhile package)
    name='Canvas Connector',
    url='https://github.com/lukekorthals/canvas-connector',
    author='Luke Korthals',
    author_email='luke-korthals@outlook.de',
    packages=find_packages(),
    install_requires=['canvasapi','beautifulsoup4', 'pandas'],
    package_data={},
    version='0.1',
    license='MIT',
    description='Some utilities for working with the Canvas API.',
    long_description=open('README.md').read(),
)