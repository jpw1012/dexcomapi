import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dexcomapi",
    version="0.4.1",
    author="Jim Walsh",
    author_email="jim@walshfamily.email",
    description="Uses Dexcom APIs to download blood glucose data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jpw1012/dexcomapi",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)