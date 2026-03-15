#!/usr/bin/env python3

"""
MMLSyr Compiler Parser

Parses MMLSyr content, collects macro definitions (with parameterized macros),
processes K track macro calls, expands macros in A-J channels, and fills CFG defaults.
"""

import re

class MMLSyrParser:
    """Parser for MMLSyr content."""

    def __init__(self):
        """Initialize the parser."""
        # Mapping: macro_name -> {'content': macro body, 'params': [param names]}
        self.macros = {}
        self.r_counter = 0  # Generated R track counter
        self.r_mapping = {}  # Macro call signature -> R track name mapping
        self.generated_r = []  # List of generated R track definitions

    def parse(self, content):
        """Parse content, collecting macros and processing tracks.
        
        Args:
            content (str): Content to parse.
            
        Returns:
            str: Parsed content with macros expanded and tracks processed.
        """
        # Reset state
        self.macros.clear()
        self.r_counter = 0
        self.r_mapping.clear()
        self.generated_r.clear()
        
        # Collect macro definitions and remove definition lines from content
        self._collect_macros(content)
        content = self._remove_macro_definitions(content)
        
        # Collect CFG channel defaults
        self.cfg_content = self._collect_cfg(content)
        
        # Process K tracks
        processed_content = self._process_k_tracks(content)
        
        # Expand macros in A-J channels (Phase 8: multi-channel macro expansion)
        processed_content = self._expand_macros_in_channels(processed_content)
        
        # Apply CFG defaults to undefined channels
        processed_content = self._apply_cfg_defaults(processed_content)
        
        # Insert generated R tracks
        final_content = self._insert_r_tracks(processed_content)
        
        return final_content

    def _collect_macros(self, content):
        """Collect macro definitions from content.
        
        Supports two formats:
        - No params:       !MacroName   content
        - Parameterized:   !MacroName($p1, $p2)   content_using_$p1_and_$p2
        
        Args:
            content (str): Content to parse.
        """
        # Match parameterized macros: !Name($p1, $p2)  content
        param_macro_pattern = re.compile(
            r'^\s*!([a-zA-Z0-9_&\'-]+)\(([^)]+)\)\s+([^\n]+)', re.MULTILINE
        )
        # Match simple macros: !Name  content
        simple_macro_pattern = re.compile(
            r'^\s*!([a-zA-Z0-9_&\'-]+)\s+([^\n]+)', re.MULTILINE
        )
        
        # Collect parameterized macros first
        param_matches = param_macro_pattern.findall(content)
        for macro_name, params_str, macro_content in param_matches:
            param_list = [p.strip() for p in params_str.split(',')]
            self.macros[macro_name] = {
                'content': macro_content.strip(),
                'params': param_list
            }
        
        # Then collect simple macros (skip those already collected as parameterized)
        simple_matches = simple_macro_pattern.findall(content)
        for macro_name, macro_content in simple_matches:
            if macro_name not in self.macros:
                self.macros[macro_name] = {
                    'content': macro_content.strip(),
                    'params': []
                }

    def _remove_macro_definitions(self, content):
        """Remove macro definition lines from content.
        
        Macro definition lines (leading !Name... syntax) are not standard PMD MML
        and must be removed before output. Only removes leading definitions,
        does not affect macro calls within K track lines.
        
        Args:
            content (str): Content containing macro definitions.
            
        Returns:
            str: Content with macro definition lines removed.
        """
        # Match leading macro definition lines (both parameterized and simple)
        # Note: !Name calls within K tracks are not at line start, won't be matched
        macro_def_pattern = re.compile(
            r'^\s*!([a-zA-Z0-9_&\'-]+)(?:\([^)]*\))?\s+[^\n]*\n?', re.MULTILINE
        )
        return macro_def_pattern.sub('', content)

    def _process_k_tracks(self, content):
        """Process K tracks, replacing macro calls with R track references.
        
        Args:
            content (str): Content with K tracks to process.
            
        Returns:
            str: Content with processed K tracks.
        """
        # Pattern to match K track lines
        k_pattern = re.compile(r'^(\s*K\s+)([^\n]+)', re.MULTILINE)
        
        def replace_k_track(match):
            k_prefix = match.group(1)
            k_content = match.group(2)
            
            # Process macro calls in K content
            processed_k_content, generated_r = self._process_k_content(k_content)
            
            # Add generated R tracks to list
            self.generated_r.extend(generated_r)
            
            # Return updated K track line
            return f"{k_prefix}{processed_k_content}"
        
        # Replace all K track lines
        processed_content = k_pattern.sub(replace_k_track, content)
        
        return processed_content

    def _process_k_content(self, k_content):
        """Process macro calls within K track content.
        
        Supports two call formats:
        - No params:       !MacroName
        - Parameterized:   !MacroName(arg1, arg2)
        
        Args:
            k_content (str): K track content.
            
        Returns:
            tuple: (processed_k_content, generated_r_tracks)
        """
        generated_r = []
        processed_content = k_content
        
        # Match parameterized macro calls: !Name(arg1, arg2)
        param_call_pattern = re.compile(r'!([a-zA-Z0-9_&\'-]+)\(([^)]+)\)')
        # Match simple macro calls: !Name
        simple_call_pattern = re.compile(r'!([a-zA-Z0-9_&\'-]+)(?!\()')
        
        # Step 1: Process parameterized macro calls
        def replace_param_call(match):
            macro_name = match.group(1)
            args_str = match.group(2)
            
            if macro_name not in self.macros:
                return match.group(0)  # Undefined macro, keep as-is
            
            macro_info = self.macros[macro_name]
            args = [a.strip() for a in args_str.split(',')]
            
            # Replace formal params with actual args
            # Sort by param name length descending to avoid prefix conflicts
            # (e.g., $r accidentally replacing prefix of $root)
            expanded = macro_info['content']
            param_arg_pairs = sorted(
                zip(macro_info['params'], args),
                key=lambda x: len(x[0]),
                reverse=True
            )
            for param, arg in param_arg_pairs:
                expanded = expanded.replace(param, arg)
            
            # Generate R track for each unique expansion
            # Use macro name + args as signature to avoid duplicates
            call_signature = f"{macro_name}({args_str})"
            if call_signature in self.r_mapping:
                return self.r_mapping[call_signature]
            
            r_name = f"R{self.r_counter}"
            self.r_counter += 1
            self.r_mapping[call_signature] = r_name
            # Recursively expand nested macros (Phase 6.1)
            expanded = self._expand_nested_macros(expanded)
            generated_r.append(f"{r_name}\t{expanded}")
            return r_name
        
        processed_content = param_call_pattern.sub(replace_param_call, processed_content)
        
        # Step 2: Process simple macro calls
        def replace_simple_call(match):
            macro_name = match.group(1)
            
            if macro_name not in self.macros:
                return match.group(0)  # Undefined macro, keep as-is
            
            macro_info = self.macros[macro_name]
            
            # Calling a parameterized macro without args: expand raw content
            call_signature = macro_name
            if call_signature in self.r_mapping:
                return self.r_mapping[call_signature]
            
            r_name = f"R{self.r_counter}"
            self.r_counter += 1
            self.r_mapping[call_signature] = r_name
            # Recursively expand nested macros (Phase 6.1)
            expanded_content = self._expand_nested_macros(macro_info['content'])
            generated_r.append(f"{r_name}\t{expanded_content}")
            return r_name
        
        processed_content = simple_call_pattern.sub(replace_simple_call, processed_content)
        
        # Process complex patterns (e.g., [macro_call]n)
        processed_content = self._process_complex_patterns(processed_content)
        
        return processed_content, generated_r

    def _expand_nested_macros(self, content, depth=0):
        """Recursively expand nested macro calls within content.
        
        Supports macros referencing other macros. Recursion depth limited
        to 10 to prevent infinite loops.
        
        Args:
            content (str): Content to expand.
            depth (int): Current recursion depth.
            
        Returns:
            str: Expanded content.
        """
        if depth > 10:
            return content  # Prevent infinite recursion
        
        # Match parameterized macro calls: !Name(arg1, arg2)
        param_call_pattern = re.compile(r'!([a-zA-Z0-9_&\'-]+)\(([^)]+)\)')
        # Match simple macro calls: !Name
        simple_call_pattern = re.compile(r'!([a-zA-Z0-9_&\'-]+)(?!\()')
        
        changed = False
        
        # Expand parameterized macros
        def replace_param(match):
            nonlocal changed
            macro_name = match.group(1)
            args_str = match.group(2)
            if macro_name not in self.macros:
                return match.group(0)
            changed = True
            macro_info = self.macros[macro_name]
            args = [a.strip() for a in args_str.split(',')]
            expanded = macro_info['content']
            param_arg_pairs = sorted(
                zip(macro_info['params'], args),
                key=lambda x: len(x[0]),
                reverse=True
            )
            for param, arg in param_arg_pairs:
                expanded = expanded.replace(param, arg)
            return expanded
        
        content = param_call_pattern.sub(replace_param, content)
        
        # Expand simple macros
        def replace_simple(match):
            nonlocal changed
            macro_name = match.group(1)
            if macro_name not in self.macros:
                return match.group(0)
            changed = True
            return self.macros[macro_name]['content']
        
        content = simple_call_pattern.sub(replace_simple, content)
        
        # If replacements occurred, recurse (may produce new macro calls)
        if changed:
            content = self._expand_nested_macros(content, depth + 1)
        
        return content

    def _process_complex_patterns(self, content):
        """Process complex patterns like [macro_call]n and convert to R tracks.
        
        Args:
            content (str): Content to process.
            
        Returns:
            str: Processed content.
        """
        # Pattern to match [content]n patterns
        pattern = re.compile(r'\[([^\]]+)\](\d+)')
        
        def replace_pattern(match):
            pattern_content = match.group(1)
            pattern_count = match.group(2)
            
            # Generate new R track for this pattern
            r_name = f"R{self.r_counter}"
            self.r_counter += 1
            
            # Create R track definition
            r_def = f"{r_name}\t[{pattern_content}]{pattern_count}"
            self.generated_r.append(r_def)
            
            # Return R track reference
            return r_name
        
        # Replace all patterns
        processed_content = pattern.sub(replace_pattern, content)
        
        return processed_content

    def _expand_macros_in_channels(self, content):
        """Expand macro calls in A-J channel lines.
        
        Non-K channel macros are expanded inline (no R tracks generated),
        directly replacing the macro call with expanded content.
        Supports both parameterized and simple macro calls.
        
        Args:
            content (str): Content to process.
            
        Returns:
            str: Processed content.
        """
        if not self.macros:
            return content
        
        # Match A-J channel lines (not K, which is handled by _process_k_tracks)
        channel_pattern = re.compile(r'^(\s*[A-J]\s+)(.*)', re.MULTILINE)
        
        def expand_channel_line(match):
            prefix = match.group(1)
            line_content = match.group(2)
            # Use recursive expansion for inline macro calls
            expanded = self._expand_nested_macros(line_content)
            return prefix + expanded
        
        return channel_pattern.sub(expand_channel_line, content)

    def _collect_cfg(self, content):
        """Collect CFG channel default content.
        
        CFG line format: CFG  content
        
        Args:
            content (str): Content to parse.
            
        Returns:
            str or None: CFG content, or None if no CFG lines found.
        """
        cfg_pattern = re.compile(r'^\s*CFG\s+([^\n]+)', re.MULTILINE)
        cfg_parts = []
        
        for match in cfg_pattern.finditer(content):
            cfg_parts.append(match.group(1).strip())
        
        if cfg_parts:
            return ' '.join(cfg_parts)
        return None
    
    def _apply_cfg_defaults(self, content):
        """Apply CFG default content to undefined channels.
        
        Detects which A-H channels are already defined, and inserts
        CFG content for undefined ones. Also removes CFG lines.
        
        Args:
            content (str): Content to process.
            
        Returns:
            str: Processed content.
        """
        if not self.cfg_content:
            return content
        
        # Remove CFG lines
        cfg_line_pattern = re.compile(r'^\s*CFG\s+[^\n]*\n?', re.MULTILINE)
        content = cfg_line_pattern.sub('', content)
        
        # Detect defined channels (A-K, PMD standard channel range)
        channel_pattern = re.compile(r'^\s*([A-K])\s+', re.MULTILINE)
        defined_channels = set()
        for match in channel_pattern.finditer(content):
            defined_channels.add(match.group(1))
        
        # Insert CFG content for undefined channels
        missing_channels = [ch for ch in 'ABCDEFGH' if ch not in defined_channels]
        
        if not missing_channels:
            return content
        
        # Append undefined channels with CFG default content
        cfg_lines = []
        for ch in missing_channels:
            cfg_lines.append(f"{ch}\t{self.cfg_content}")
        
        return content.rstrip() + '\n' + '\n'.join(cfg_lines) + '\n'

    def _insert_r_tracks(self, content):
        """Insert generated R tracks into content.
        
        Args:
            content (str): Content to insert R tracks into.
            
        Returns:
            str: Content with R tracks inserted.
        """
        if not self.generated_r:
            return content
        
        # Detect first channel line (A-K, PMD standard channel range)
        channel_pattern = re.compile(r'^(\s*[A-K]\s+)', re.MULTILINE)
        match = channel_pattern.search(content)
        
        if match:
            # Insert before first channel line
            insert_pos = match.start()
            r_tracks_content = '\n'.join(self.generated_r) + '\n\n'
            return content[:insert_pos] + r_tracks_content + content[insert_pos:]
        else:
            # Insert at end if no channel lines found
            return content + '\n' + '\n'.join(self.generated_r)
