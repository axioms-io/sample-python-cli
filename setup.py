from setuptools import setup, find_packages

setup(
    name='sample-python-cli',
    version='0.0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'halo'
    ],
    entry_points={
        "console_scripts": [
            "ax = cli.scripts.main:cli",
            "axioms = cli.scripts.main:cli",
        ],
    },
)