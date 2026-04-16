from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", "r") as f:
    requirements = [
        line.strip()
        for line in f
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="retaillang",
    version="0.1.0",
    author="Your Name",
    author_email="your@email.com",
    description="A DSL for retail business analytics — natural language to Pandas/SQL/charts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/retaillang",
    packages=find_packages(exclude=["tests*", "docs*", "examples*"]),
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "retaillang=main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Compilers",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
)