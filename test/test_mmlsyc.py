#!/usr/bin/env python3

"""
Test cases for MMLSyr Compiler
"""

import os
import tempfile
import unittest
from mmlsyc.compiler import MMLSyrCompiler
from mmlsyc.preprocessor import Preprocessor
from mmlsyc.parser import MMLSyrParser

class TestPreprocessor(unittest.TestCase):
    """Test cases for the Preprocessor class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.preprocessor = Preprocessor()
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary directory
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_relative_include(self):
        """Test that relative includes are properly resolved."""
        # Create included file
        included_content = "A  cdefgab>c"
        included_path = os.path.join(self.test_dir, "included.mml")
        with open(included_path, 'w', encoding='utf-8') as f:
            f.write(included_content)
        
        # Create main file with relative include
        main_content = f"#include \"included.mml\"\nK  cdef"
        main_path = os.path.join(self.test_dir, "main.mml")
        with open(main_path, 'w', encoding='utf-8') as f:
            f.write(main_content)
        
        # Process main file
        result = self.preprocessor.process(main_path)
        
        # Check that included content is present
        self.assertIn(included_content, result)
    
    def test_absolute_include(self):
        """Test that absolute includes are properly handled."""
        # Create included file
        included_content = "B  gfedcba"
        included_path = os.path.join(self.test_dir, "absolute.mml")
        with open(included_path, 'w', encoding='utf-8') as f:
            f.write(included_content)
        
        # Create main file with absolute include
        main_content = f"#include {included_path}\nA  cdef"
        main_path = os.path.join(self.test_dir, "main.mml")
        with open(main_path, 'w', encoding='utf-8') as f:
            f.write(main_content)
        
        # Process main file
        result = self.preprocessor.process(main_path)
        
        # Check that included content is present
        self.assertIn(included_content, result)
    
    def test_circular_include_protection(self):
        """Test that circular includes are properly protected against."""
        # Create file that includes itself
        main_path = os.path.join(self.test_dir, "circular.mml")
        with open(main_path, 'w', encoding='utf-8') as f:
            f.write(f"#include \"circular.mml\"\nA  cdef")
        
        # Process - should not raise an error
        result = self.preprocessor.process(main_path)
        self.assertIn("A  cdef", result)


class TestSyntaxSugar(unittest.TestCase):
    """Test cases for syntax sugar processing."""
    
    def setUp(self):
        self.preprocessor = Preprocessor()
    
    def test_line_comment_removal(self):
        """Verify // line comments are removed."""
        content = "A  cdef // this is a comment\nB  gfed"
        result = self.preprocessor.process_string(content)
        
        self.assertIn("A  cdef", result)
        self.assertNotIn("this is a comment", result)
        self.assertIn("B  gfed", result)
    
    def test_semicolon_line_split(self):
        """Verify non-leading ; is split into multiple lines."""
        content = "A  cdef; B  gfed"
        result = self.preprocessor.process_string(content)
        
        lines = result.strip().split('\n')
        a_found = any("A  cdef" in line for line in lines)
        b_found = any("B  gfed" in line for line in lines)
        self.assertTrue(a_found)
        self.assertTrue(b_found)
    
    def test_pmd_comment_preserved(self):
        """Verify leading ; is preserved as PMD comment, not split."""
        content = ";PMD comment line\nA  cdef"
        result = self.preprocessor.process_string(content)
        
        self.assertIn(";PMD comment line", result)
        self.assertIn("A  cdef", result)
    
    def test_combined_syntax_sugar(self):
        """Verify // and ; work together."""
        content = "A  cdef; B  gfed // comment"
        result = self.preprocessor.process_string(content)
        
        self.assertIn("A  cdef", result)
        self.assertNotIn("comment", result)


class TestParser(unittest.TestCase):
    """Test cases for the MMLSyrParser class."""
    
    def setUp(self):
        """Set up test environment."""
        self.parser = MMLSyrParser()
    
    def test_macro_collection(self):
        """Test that macros are properly collected."""
        content = "!Kick  c\n!Snare  d\nK  !Kick !Snare"
        self.parser.parse(content)
        
        self.assertIn("Kick", self.parser.macros)
        self.assertIn("Snare", self.parser.macros)
        self.assertEqual(self.parser.macros["Kick"]["content"], "c")
        self.assertEqual(self.parser.macros["Snare"]["content"], "d")
    
    def test_k_track_processing(self):
        """Test that K tracks are processed correctly."""
        content = """!Kick  c
!Snare  d

K  !Kick 8 !Snare 8
A  cdefgab>c
"""
        result = self.parser.parse(content)
        
        # Verify R tracks are generated
        self.assertIn("R0", result)
        self.assertIn("R1", result)
        # Verify K track references R tracks
        self.assertIn("K  R0 8 R1 8", result)
    
    def test_parameterized_macro(self):
        """Verify parameterized macros expand correctly."""
        content = """!Note($pitch,$vol)  o4v$vol $pitch
K  !Note(c,12) !Note(d,10)
A  cdef
"""
        result = self.parser.parse(content)
        
        self.assertIn("o4v12 c", result)
        self.assertIn("o4v10 d", result)
    
    def test_parameterized_macro_prefix_conflict(self):
        """Verify param substitution uses longest-first to avoid prefix conflicts."""
        content = """!Chord($root,$r)  $root$r
K  !Chord(ce,df+) !Chord(df+,c)
A  cdef
"""
        result = self.parser.parse(content)
        
        # R0 should be cedf+ (not corrupted by $r replacing prefix of $root)
        self.assertIn("cedf+", result)
        # R1 should be df+c
        self.assertIn("df+c", result)
    
    def test_parameterized_macro_with_different_args(self):
        """Verify different args produce different R tracks."""
        content = """!Pat($n)  $n4$n8$n8
K  !Pat(c) !Pat(d) !Pat(c)
A  cdef
"""
        result = self.parser.parse(content)
        
        # R0=c4c8c8, R1=d4d8d8, second !Pat(c) reuses R0
        self.assertIn("R0", result)
        self.assertIn("R1", result)
        self.assertIn("c4c8c8", result)
        self.assertIn("d4d8d8", result)
    
    def test_undefined_macro_kept(self):
        """Verify undefined macro calls are kept as-is."""
        content = """!Kick  c
K  !Kick !Unknown
A  cdef
"""
        result = self.parser.parse(content)
        
        self.assertIn("R0", result)
        self.assertIn("!Unknown", result)


class TestCFG(unittest.TestCase):
    """CFG default channel filling tests."""
    
    def setUp(self):
        self.parser = MMLSyrParser()
    
    def test_cfg_fills_missing_channels(self):
        """Verify CFG fills undefined channels C-H."""
        content = """CFG  [r1]4
A  cdef
B  gfed
"""
        result = self.parser.parse(content)
        
        for ch in 'CDEFGH':
            self.assertIn(f"{ch}\t[r1]4", result,
                f"Channel {ch} should contain CFG default content")
        self.assertNotIn("CFG", result)
    
    def test_cfg_does_not_override(self):
        """Verify CFG does not override existing channels."""
        content = """CFG  [r1]4
A  cdef
B  gfed
C  abcd
"""
        result = self.parser.parse(content)
        
        self.assertIn("C  abcd", result)
    
    def test_cfg_absent(self):
        """Verify behavior is unchanged without CFG."""
        content = "A   cdef\nB   gfed\n"
        result = self.parser.parse(content)
        
        self.assertIn("A   cdef", result)
        self.assertIn("B   gfed", result)
        # No extra channels should be inserted
        self.assertNotIn("C\t", result)

class TestExtendedChannels(unittest.TestCase):
    """Extended channel name tests."""
    
    def setUp(self):
        self.parser = MMLSyrParser()
    
    def test_extended_channel_names(self):
        """Verify PMD standard channels I-K are recognized."""
        content = """!Pat  cdef
I   efga
J   gabc
K  !Pat
A  cdef
"""
        result = self.parser.parse(content)
        
        # I and J channels should be preserved
        self.assertIn("I   efga", result)
        self.assertIn("J   gabc", result)
        # K track macros should be expanded
        self.assertIn("R0", result)

class TestNestedMacros(unittest.TestCase):
    """Phase 6.1: Nested macro call tests."""

    def setUp(self):
        self.parser = MMLSyrParser()

    def test_nested_macro_expansion(self):
        """Verify macros referencing other macros are recursively expanded."""
        content = """!Step($n) $n
!Chord($r,$t) !Step($r)!Step($t)
K !Chord(c,e) !Chord(d,f+)
A cdef
"""
        result = self.parser.parse(content)
        # R0 should be ce (!Step(c) -> c, !Step(e) -> e)
        self.assertIn('ce', result)
        # R1 should be df+
        self.assertIn('df+', result)

    def test_nested_simple_macro(self):
        """Verify simple macros nested expansion."""
        content = """!Base c4d4e4f4
!Verse !Base !Base
K !Verse
A cdef
"""
        result = self.parser.parse(content)
        # Verse should contain Base content twice
        self.assertIn('c4d4e4f4', result)
        # Find the R track containing Verse content
        lines = result.split('\n')
        verse_r_content = None
        for line in lines:
            if line.startswith('R') and '\t' in line:
                _, track_content = line.split('\t', 1)
                if 'c4d4e4f4' in track_content:
                    verse_r_content = track_content
                    break
        self.assertIsNotNone(verse_r_content, "Should find R track with Base content")
        # Check it contains Base content twice (!Base !Base -> c4d4e4f4c4d4e4f4)
        self.assertEqual(verse_r_content.count('c4d4e4f4'), 2)


class TestLineContinuation(unittest.TestCase):
    """Phase 6.2: Backslash line continuation tests."""

    def setUp(self):
        self.preprocessor = Preprocessor()
        self.parser = MMLSyrParser()
        self.compiler = MMLSyrCompiler()

    def test_backslash_line_continuation(self):
        """Verify \\ continuation merges lines in preprocessing."""
        content = "!Theme($key) \\\n    $key4 $key8 $key8 \\\n    $key2\nK !Theme(c)\nA cdef\n"
        result = self.preprocessor.process_string(content)
        # Continuation should merge into single line
        self.assertNotIn('\\\n', result)
        # Macro definition should be on one line
        self.assertIn('!Theme', result)

    def test_continuation_in_full_compile(self):
        """Verify continuation macros expand correctly in full compilation."""
        content = "!Theme($key) \\\n    $key4 $key8 $key8 \\\n    $key2\nK !Theme(c)\nA cdef\n"
        result = self.compiler.compile_string(content)
        # Expanded result should contain c4 c8 c8 c2
        self.assertIn('c4', result)
        self.assertIn('c8', result)
        self.assertIn('c2', result)


class TestMultiChannelMacro(unittest.TestCase):
    """Phase 8: Multi-channel macro expansion tests (A-J channels)."""

    def setUp(self):
        self.parser = MMLSyrParser()

    def test_macro_in_fm_channel(self):
        """Verify FM channels can use simple macros."""
        content = """!Verse o4v12l8 cdefgab>c
A !Verse
B !Verse
K cdef
"""
        result = self.parser.parse(content)
        # A and B should contain expanded macro content
        self.assertIn('o4v12l8 cdefgab>c', result)
        lines = result.split('\n')
        a_found = False
        b_found = False
        for line in lines:
            if line.strip().startswith('A') and 'o4v12l8' in line:
                a_found = True
            if line.strip().startswith('B') and 'o4v12l8' in line:
                b_found = True
        self.assertTrue(a_found, "Channel A should contain expanded macro content")
        self.assertTrue(b_found, "Channel B should contain expanded macro content")

    def test_parameterized_macro_in_channel(self):
        """Verify parameterized macros expand in channels."""
        content = """!Scale($o) o$o l8 cdefgab>c
A !Scale(4)
B !Scale(5)
K cdef
"""
        result = self.parser.parse(content)
        # A should contain o4, B should contain o5
        lines = result.split('\n')
        a_has_o4 = any(line.strip().startswith('A') and 'o4' in line for line in lines)
        b_has_o5 = any(line.strip().startswith('B') and 'o5' in line for line in lines)
        self.assertTrue(a_has_o4, "Channel A should contain o4")
        self.assertTrue(b_has_o5, "Channel B should contain o5")


class TestDirectivePassthrough(unittest.TestCase):
    """Phase 7: # directive passthrough and ## directive tests."""

    def setUp(self):
        self.compiler = MMLSyrCompiler()

    def test_pmd_directives_preserved(self):
        """Verify PMD # directives are passed through unchanged."""
        content = """#Title Test Song
#Composer TestUser
#PCMFile DRUMS.PPC
#Tempo 120
A cdef
"""
        result = self.compiler.compile_string(content)
        self.assertIn('#Title Test Song', result)
        self.assertIn('#Composer TestUser', result)
        self.assertIn('#PCMFile DRUMS.PPC', result)
        self.assertIn('#Tempo 120', result)

    def test_pmd_directive_with_comment(self):
        """Verify // comments in # directive lines are removed."""
        content = """#Title My Song // song title
A cdef
"""
        result = self.compiler.compile_string(content)
        self.assertIn('#Title My Song', result)
        self.assertNotIn('song title', result)

    def test_double_hash_directive_removed(self):
        """Verify ## mmlsyc-specific directives are removed from output."""
        content = """##define VOL 12
##soundbank drums.ff
A cdef
"""
        result = self.compiler.compile_string(content)
        # ## directives should be removed
        self.assertNotIn('##define', result)
        self.assertNotIn('##soundbank', result)
        # A channel preserved
        self.assertIn('A cdef', result)


class TestCompiler(unittest.TestCase):
    """Test cases for the MMLSyrCompiler class."""
    
    def setUp(self):
        """Set up test environment."""
        self.compiler = MMLSyrCompiler()
    
    def test_compile_string(self):
        """Test that compile_string works correctly."""
        content = """!Kick  c
!Snare  d

K  !Kick 8 !Snare 8
A  cdefgab>c
"""
        result = self.compiler.compile_string(content)
        
        # Check that result contains processed content
        self.assertIn("R0", result)
        self.assertIn("R1", result)
        self.assertIn("K  R0 8 R1 8", result)
        self.assertIn("A  cdefgab>c", result)
    
    def test_full_compilation(self):
        """Test the full compilation process with a temporary file."""
        with tempfile.TemporaryDirectory() as test_dir:
            # Create test file
            test_content = """!Kick  c
!Snare  d

K  !Kick 8 !Snare 8
A  cdefgab>c
"""
            test_path = os.path.join(test_dir, "test.mml")
            with open(test_path, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            # Compile file
            result = self.compiler.compile(test_path)
            
            # Check that result contains processed content
            self.assertIn("R0", result)
            self.assertIn("R1", result)
            self.assertIn("K  R0 8 R1 8", result)
            self.assertIn("A  cdefgab>c", result)

if __name__ == '__main__':
    unittest.main()