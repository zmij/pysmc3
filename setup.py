from distutils.core import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="smc3",  # How you named your package folder (MyLib)
    packages=["smc3"],  # Chose the same as "name"
    version="0.1.1",  # Start with a small number and increase it with every change you make
    license="Apache-2.0",  # Chose a license from here: https://help.github.com/articles/licensing-a-repository
    description="Simulation Motor Controller interface",  # Give a short description about your library
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Sergei A. Fedorov",  # Type in your name
    author_email="sergei.a.fedorov@gmail.com",  # Type in your E-Mail
    url="https://github.com/zmij/pysmc3",  # Provide either the link to your github or to your website
    download_url="https://github.com/zmij/pysmc3/archive/refs/tags/v0.1.tar.gz",  # I explain this later on
    keywords=[
        "motion simulation",
        "motor control",
        "diagnostic tools",
    ],
    install_requires=[  # I get to this in a second
        "pyserial-asyncio",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",  # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        "Intended Audience :: Developers",
        "Topic :: Games/Entertainment :: Simulation",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
)
