#!/usr/bin/env python3

"""
MMLSyr Compiler Preprocessor

Handles #include directives, path resolution, line continuations,
and syntax sugar transformations (// comments, ; line separators, ## directives).
"""

import os
import re

class Preprocessor:
    """Preprocessor for handling include directives in MMLSyr files."""

    def __init__(self, base_path=None):
        """Initialize preprocessor with base path.
        
        Args:
            base_path (str): Base path for resolving relative includes.
        """
        self.base_path = base_path or os.getcwd()
        self.included_files = set()  # To prevent circular includes

    def process(self, file_path):
        """Process a file, handling all include directives.
        
        Args:
            file_path (str): Path to the file to process.
            
        Returns:
            str: Processed content with all includes resolved.
        """
        # Normalize file path
        file_path = os.path.abspath(file_path)
        
        # Check for circular include
        if file_path in self.included_files:
            return ""  # Skip circular includes
        
        self.included_files.add(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find include file: {file_path}")
        except Exception as e:
            raise Exception(f"Error reading file {file_path}: {e}")
        
        # Process include directives
        processed_content = self._process_includes(content, file_path)
        
        # Process backslash line continuations
        processed_content = self._process_line_continuations(processed_content)
        
        # Process syntax sugar (// comments, ; line separators)
        processed_content = self._process_syntax_sugar(processed_content)
        
        return processed_content

    def process_string(self, content):
        """Process string content directly (no file I/O or includes).
        
        Args:
            content (str): Content to process.
            
        Returns:
            str: Processed content.
        """
        # Process backslash line continuations first
        content = self._process_line_continuations(content)
        return self._process_syntax_sugar(content)

    def _process_includes(self, content, current_file_path):
        """Process include directives in content.
        
        Args:
            content (str): Content to process.
            current_file_path (str): Path of the current file.
            
        Returns:
            str: Content with includes processed.
        """
        # Pattern to match include directives
        include_pattern = re.compile(r'#include\s+([^\n]+)', re.IGNORECASE)
        
        def replace_include(match):
            include_path = match.group(1).strip()
            
            # Resolve include path
            resolved_path = self._resolve_include_path(include_path, current_file_path)
            
            # Process the included file
            included_content = self.process(resolved_path)
            
            # Return processed content with a comment
            return f"\n; Include: {include_path}\n{included_content}\n; End include: {include_path}\n"
        
        # Replace all include directives
        processed_content = include_pattern.sub(replace_include, content)
        
        return processed_content

    def _resolve_include_path(self, include_path, current_file_path):
        """Resolve include path to absolute path.
        
        Args:
            include_path (str): Include path from file.
            current_file_path (str): Path of the current file.
            
        Returns:
            str: Resolved absolute path.
        """
        # Remove quotes if present
        if include_path.startswith(('"', "'")):
            include_path = include_path.strip('"\'')
            
            # Relative path
            current_dir = os.path.dirname(current_file_path)
            return os.path.abspath(os.path.join(current_dir, include_path))
        else:
            # Absolute path (already absolute)
            return include_path

    def _process_syntax_sugar(self, content):
        """Process syntax sugar: // line comments, ; inline separators, ## directives.
        
        Rules:
        - ## directives are removed (mmlsyc-specific)
        - // and everything after it is removed (line comment)
        - Non-leading ; is replaced with newline (inline separator)
        - Leading ; is preserved as PMD native comment
        
        Args:
            content (str): Content to process.
            
        Returns:
            str: Processed content.
        """
        lines = content.split('\n')
        result_lines = []
        
        for line in lines:
            # Step 0: Remove ## mmlsyc-specific directive lines
            stripped = line.lstrip()
            if stripped.startswith('##'):
                continue  # Discard entire line
            
            # Step 1: Remove // line comments
            comment_pos = line.find('//')
            if comment_pos >= 0:
                line = line[:comment_pos].rstrip()
            
            # Step 2: Process ; inline separators
            # Leading ; preserved as PMD comment, not split
            stripped = line.lstrip()
            if stripped.startswith(';'):
                # Leading ;, keep entire line as PMD comment
                result_lines.append(line)
            elif ';' in line:
                # Non-leading ;, split into multiple lines
                parts = line.split(';')
                for part in parts:
                    part_stripped = part.strip()
                    if part_stripped:
                        result_lines.append(part)
            else:
                result_lines.append(line)
        
        return '\n'.join(result_lines)

    def _process_line_continuations(self, content):
        """Process backslash line continuations: merge trailing \\ + newline into single line.
        
        Supports multi-line macro definitions:
            !Theme($key) \\
                $key4 $key8 $key8 \\
                $key2
        Becomes:
            !Theme($key)     $key4 $key8 $key8     $key2
        
        Args:
            content (str): Content to process.
            
        Returns:
            str: Processed content.
        """
        # Replace trailing \\ + newline with space (merge lines)
        return re.sub(r'\\\n\s*', ' ', content)

    def reset(self):
        """Reset preprocessor state."""
        self.included_files.clear()
