from setuptools import setup, find_packages

setup(
    name="mmlsyc",
    version="0.3.0",
    description="MMLSyr Compiler - Preprocessor from MMLSyr extended syntax to standard PMD MML",
    long_description="""MMLSyr Compiler compiles MMLSyr extended syntax into standard PMD MML.

Features:
- // line comments and ; inline separators (C-style)
- Parameterized macros !Name($p1, $p2) with nested macro expansion
- Backslash \\ multi-line macro continuation
- K track macro calls with automatic R track generation
- A-J channel inline macro expansion
- CFG default channel filling
- ## mmlsyc-specific directives
- PMD # directive passthrough
- #include with relative path support
""",
    author="Syruph-dot",
    license="MIT",
    packages=find_packages(exclude=["test", "test.*"]),
    entry_points={
        "console_scripts": [
            "mmlsyc = mmlsyc.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Sound/Audio :: Sound Synthesis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.10",
)