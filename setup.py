import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("src/xml_encoder/VERSION", "r", encoding="utf-8") as fh:
    version = fh.read()

setuptools.setup(
    name="xml-encoder",
    version=version,
    author="John Carter",
    author_email="jfcarter2358@gmail.com",
    description="A package for reading Jenkinsfile-like pipeline files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jfcarter2358/xml-encoder",
    project_urls={
        "Bug Tracker": "https://github.com/jfcarter2358/xml-encoder/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)
