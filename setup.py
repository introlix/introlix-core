from setuptools import setup
import setuptools

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="introlix_api",
    version="0.0.1",
    author="Satyam Mishra",
    author_email="tubex998@gmail.com",
    description="Introlix API offers a comprehensive suite of tools and APIs utilized in Introlix Feed.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.10",
)