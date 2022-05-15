"""Setup of VW Kommi"""

import pathlib
import re
import pkg_resources
from setuptools import find_namespace_packages, setup

with open("vwkommi/__init__.py", encoding="utf8") as f:
    version = re.search(r'__version__ = "(.*?)"', f.read()).group(1)

with pathlib.Path('requirements.txt').open('r', encoding="utf-8") as requirements_txt:
    install_requires = [
        str(requirement)
        for requirement
        in pkg_resources.parse_requirements(requirements_txt)
    ]

    setup(name='vwkommi',
          version=version,
          description=(
            'VW Kommi is a simple tool to read out commission numbers of VW ID vehicles.'
          ),
          url='https://github.com/SushiTee/vwkommi',
          author='SushiTee',
          packages=find_namespace_packages(include=["vwkommi", "vwkommi.*"]),
          install_requires=install_requires,
          zip_safe=False)
