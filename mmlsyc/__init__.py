#!/usr/bin/env python3

"""
MMLSyr Compiler

A compiler for MMLSyr language, which extends MML with features like:
- // line comments and ; inline separators
- Parameterized macros with nested expansion
- Backslash line continuations for multi-line macros
- K track macro calls with automatic R track generation
- A-J channel inline macro expansion
- CFG default channel filling
- ## mmlsyc-specific directives
- PMD # directive passthrough
- Relative path #include support
"""

from .compiler import MMLSyrCompiler
from .preprocessor import Preprocessor
from .parser import MMLSyrParser

__all__ = [
    'MMLSyrCompiler',
    'Preprocessor',
    'MMLSyrParser'
]

__version__ = "0.3.0"
__author__ = "Syruph-dot"
__license__ = "MIT"
