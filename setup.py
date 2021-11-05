import setuptools

setuptools.setup(
    name="boolQuery-pkg-alinajafi",
    version="0.0.1",
    author="Ali Najafi",
    author_email="alinajafilerning@gmail.com",
    description="Boolean Query Search System",
    long_description="A system for boolean query search based on IR Concepts.",
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)
