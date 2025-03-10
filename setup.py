from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="LivelinkTransfer",
    version="0.1.0",
    author="LivelinkTransfer Team",
    description="Transfer files from iOS Live Link Face app to Windows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Maksim-Samsonov/LivelinkTransfer",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "livelinkTransfer=src.app:main",
        ],
    },
    include_package_data=True,
)