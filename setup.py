from setuptools import setup

def readme():
  with open("README.md") as f:
    return f.read()

setup(
  name = "yModel",
  version = "0.0.1",
  description = "Marshmallow subclasses with extended features",
  long_description = readme(),
  classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Plugins",
    "Framework :: ySanic",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Topic :: Database"
  ],
  keywords = "data schema marshmallow trees materialized_paths mongodb",
  url = "https://github.com/Garito/yModel",
  author = "Garito",
  author_email = "garito@gmail.com",
  license = "MIT",
  packages = ["yModel"],
  install_requires = [
    "marshmallow",
    "motor",
    "python-slugify"
  ],
  test_suite = "unittest"
)
