#!/usr/bin/env python3

"""
MMLSyr Compiler - Main Module

Coordinates preprocessing and parsing as the main compiler.
"""

from .preprocessor import Preprocessor
from .parser import MMLSyrParser

class MMLSyrCompiler:
    """MMLSyr Compiler main class."""

    def __init__(self):
        """Initialize the compiler."""
        self.preprocessor = Preprocessor()
        self.parser = MMLSyrParser()

    def compile(self, input_file, output_file=None):
        """Compile an MMLSyr file to standard MML.
        
        Args:
            input_file (str): Input MMLSyr file path.
            output_file (str): Output MML file path.
                If None, no file is written.
        
        Returns:
            str: Compiled MML content.
        """
        # Preprocess (handle includes and syntax sugar)
        preprocessed_content = self.preprocessor.process(input_file)
        
        # Parse (handle macros, K tracks, CFG)
        compiled_content = self.parser.parse(preprocessed_content)
        
        # Write output file
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(compiled_content)
        
        return compiled_content

    def compile_string(self, content, base_path=None):
        """Compile an MMLSyr string to standard MML.
        
        Args:
            content (str): MMLSyr content to compile.
            base_path (str): Base path for resolving includes.
            
        Returns:
            str: Compiled MML content.
        """
        if base_path:
            self.preprocessor.base_path = base_path
        
        # Apply preprocessor syntax sugar to string
        preprocessed_content = self.preprocessor.process_string(content)
        
        # Parse
        compiled_content = self.parser.parse(preprocessed_content)
        
        return compiled_content
