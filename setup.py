import setuptools

version = "1.0.0"

with open("README.md", "r", encoding="utf-8") as fh:
    readme = fh.read()

setuptools.setup(
    name="asyncode",
    version=version,
    author="Loïc Simon",
    author_email="loic.simon@espci.org",
    description="Emulating Python's interactive interpreter in asynchronous contexts",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/loic-simon/asyncode",
    py_modules=["asyncode"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Interpreters",
    ],
    install_requires=[],
    python_requires='>=3.5',
)

# python3 setup.py sdist bdist_wheel
# twine upload dist/*
