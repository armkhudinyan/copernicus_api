from pathlib import Path
from setuptools import setup, find_packages

VERSION = "0.1.0"
MAINTAINER = "Manvel Khudinyan"
MAINTAINER_EMAIL = "armkhudinyan@gmail.com"
URL = "https://github.com/armkhudinyan/copernicus_api"
SHORT_DESCRIPTION = ("Implementation of Python API for searching and downloadig Copernicus Sentinel mission imgaes.")
LICENSE = "MIT"
CLASSIFIERS = [
    "Intended Audience :: Research/EO applications",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3.11",
    "Topic :: Software Development",
    "Topic :: Scientific/Engineering",
    "Operating System :: Unix",
#     "Operating System :: Microsoft :: Windows",
#     "Operating System :: POSIX",
#     "Operating System :: MacOS",
]

setup(
    name="Copernicus API",
    version=VERSION,
    description=SHORT_DESCRIPTION,
    maintainer=MAINTAINER,
    maintainer_email=MAINTAINER_EMAIL,
    packages=find_packages(),
    license=LICENSE,
    long_description= (
        Path(__file__).parent / "README.md").read_text(encoding="utf8"),
    long_description_content_type="text/markdown",
    url=URL,
    classifiers=CLASSIFIERS
)