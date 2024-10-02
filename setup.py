from setuptools import find_packages, setup

setup(
    name="wlogging_util",
    version="0.0.1",
    description="A custom logging utility for Python",
    package_dir={"": "./wlogging_util"},
    packages=find_packages(where="wlogging_util"),
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/wobYY/wlogging_util",
    author="wobY",
    author_email="wobybusiness@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    install_requires=["concurrent-log-handler==0.9.25"],
    extras_require={"dev": ["twine", "wheel"]},
    python_requires=">=3.12",
)
