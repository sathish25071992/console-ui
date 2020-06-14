import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="cui-sathish25071992",
    version="0.0.1",
    author="Sathish V",
    author_email="sathish25071992@gmail.com",
    description="Console Based UI with task management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sathish25071992/console-ui",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.4',
)