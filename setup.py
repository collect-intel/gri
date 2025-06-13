"""
Setup configuration for the Global Representativeness Index (GRI) package.
"""

from setuptools import setup, find_packages

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="gri",
    version="2.0.0",
    author="GRI Project Contributors",
    author_email="contact@gri-project.org",
    description="Global Representativeness Index calculation toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/gri",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*", "notebooks"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=22.0",
            "isort>=5.0",
            "flake8>=4.0",
            "mypy>=0.900",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=1.0",
            "nbsphinx>=0.8",
        ],
    },
    entry_points={
        "console_scripts": [
            "gri-process-data=scripts.process_data:main",
            "gri-calculate=scripts.calculate_gri_config:main",
        ],
    },
    include_package_data=True,
    package_data={
        "gri": ["../config/*.yaml", "../data/processed/*.csv"],
    },
)