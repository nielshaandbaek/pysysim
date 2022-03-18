from setuptools import find_packages, setup

setup(
    name='pysysim',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    version='0.1.0',
    description='Python library for system simulations',
    author='Niels Haandbaek',
    license='MIT',
    install_requires=['simpy', 'pyvcd'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest==4.4.1'],
    test_suite='tests',
)
