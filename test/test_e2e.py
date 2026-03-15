#!/usr/bin/env python3

"""
End-to-end integration tests: verify mmlsyc output is valid PMD MML.

Test strategy:
1. Prepare .syr test input with all mmlsyc features
2. Compile to MML, verify output contains no mmlsyc-specific syntax
3. Verify all PMD # directives are preserved unchanged
4. Verify channel A-K output format is correct
"""

import re
import unittest
from mmlsyc.compiler import MMLSyrCompiler


class TestE2EBasicCompilation(unittest.TestCase):
    """End-to-end basic compilation tests."""

    def setUp(self):
        self.compiler = MMLSyrCompiler()

    def test_no_mmlsyr_syntax_in_output(self):
        """Verify output contains no mmlsyc-specific syntax."""
        syr_input = """
##define TEMPO 150
// This is an MMLSyr comment, should not appear in output
#Title E2E Test Song
#Composer Tester

!Kick c
!Snare d
!HiHat($n) $n

CFG [r1]4

K !Kick !Snare !HiHat(e); A cdef
B gfed // melody
"""
        result = self.compiler.compile_string(syr_input)

        # Should not contain MMLSyr-specific syntax
        self.assertNotIn('//', result, "Output should not contain // comments")
        self.assertNotIn('##', result, "Output should not contain ## directives")
        self.assertNotIn('CFG', result, "Output should not contain CFG lines")
        self.assertNotIn('MMLSyr comment', result, "Output should not contain comment text")
        self.assertNotIn('melody', result, "Output should not contain comment text")

    def test_no_macro_definitions_in_output(self):
        """Verify macro definition lines do not appear in output."""
        syr_input = """!Kick c
!Snare($v) d$v
K !Kick !Snare(+)
A cdef
"""
        result = self.compiler.compile_string(syr_input)

        # Should not contain macro definition lines (leading !Name ... definitions)
        lines = result.strip().split('\n')
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith(';'):
                # Check non-empty, non-comment lines don't start with !Name format
                macro_def = re.match(r'^!([a-zA-Z0-9_&\'-]+)(?:\([^)]*\))?\s+', stripped)
                self.assertIsNone(macro_def, 
                    f"Macro definition line should not appear in output: '{line}'")


class TestE2EPMDDirectives(unittest.TestCase):
    """Verify PMD # directives are preserved in end-to-end compilation."""

    def setUp(self):
        self.compiler = MMLSyrCompiler()

    def test_all_pmd_directives_preserved(self):
        """Verify all common PMD # directives are passed through unchanged."""
        syr_input = """#Title Test Song // song title comment
#Composer TestUser
#Arranger TestArranger
#Memo This is a test
#Zenlen 192
#Tempo 120
#Voldown 2
#PCMFile DRUMS.PPC
#Octave Reverse

A cdef
"""
        result = self.compiler.compile_string(syr_input)

        # All # directives preserved (// comment portion removed)
        self.assertIn('#Title Test Song', result)
        self.assertIn('#Composer TestUser', result)
        self.assertIn('#Arranger TestArranger', result)
        self.assertIn('#Memo This is a test', result)
        self.assertIn('#Zenlen 192', result)
        self.assertIn('#Tempo 120', result)
        self.assertIn('#Voldown 2', result)
        self.assertIn('#PCMFile DRUMS.PPC', result)
        self.assertIn('#Octave Reverse', result)

        # // comment content removed
        self.assertNotIn('song title comment', result)


class TestE2EChannelOutput(unittest.TestCase):
    """Verify channel output format correctness."""

    def setUp(self):
        self.compiler = MMLSyrCompiler()

    def test_all_channels_present(self):
        """Verify channels A-K appear correctly in output."""
        syr_input = """A o4l8 cdefgab>c
B o4l8 cdefgab>c
C o4l8 cdefgab>c
D o4l8 cdefgab>c
E o4l8 cdefgab>c
F o4l8 cdefgab>c
G o4l8 cdefgab>c
H o4l8 cdefgab>c
I o4l8 cdefgab>c
J @0 v14 o4l8 cdefgab>c
K \\b8\\s8\\b8\\s8
"""
        result = self.compiler.compile_string(syr_input)

        for ch in 'ABCDEFGHIJK':
            self.assertTrue(
                re.search(rf'^{ch}\s', result, re.MULTILINE),
                f"Channel {ch} should appear in output")

    def test_r_tracks_generated_for_k(self):
        """Verify K track macro expansion generates R tracks correctly."""
        syr_input = """!BD c
!SD d
!HH e

K !BD !SD !HH !BD !SD !HH
A cdef
"""
        result = self.compiler.compile_string(syr_input)

        # Should generate R0, R1, R2
        self.assertIn('R0', result)
        self.assertIn('R1', result)
        self.assertIn('R2', result)

        # R tracks should be defined before channel lines
        r0_pos = result.find('R0\t')
        k_pos = result.find('K ')
        a_pos = result.find('A ')
        self.assertLess(r0_pos, k_pos, "R tracks should precede K channel")
        self.assertLess(r0_pos, a_pos, "R tracks should precede A channel")

    def test_cfg_fills_undefined_channels(self):
        """Verify CFG correctly fills undefined channels."""
        syr_input = """CFG [r1]4
A o4l8 cdefgab>c
B o4l8 edcedcba
"""
        result = self.compiler.compile_string(syr_input)

        # C-H should be filled with CFG content
        for ch in 'CDEFGH':
            self.assertRegex(result, rf'{ch}\s+\[r1\]4',
                f"Channel {ch} should contain CFG default content [r1]4")

        # A, B keep original content
        self.assertIn('cdefgab>c', result)
        self.assertIn('edcedcba', result)


class TestE2EFullSong(unittest.TestCase):
    """Full song end-to-end compilation tests."""

    def setUp(self):
        self.compiler = MMLSyrCompiler()

    def test_full_song_compilation(self):
        """Simulate full PMD song compilation, verify all features work together."""
        syr_input = r"""#Title Syr Test Song
#Composer mmlsyc
#Zenlen 192
#Tempo 150
#PCMFile DRUMS.PPC

// === Macro Definitions ===
!Intro($k) o4 v12 l8 $k $k $k $k
!Verse($k,$o) o$o v10 l8 $k4 $k8 $k8 \
    $k2

// === CFG: Default silence ===
##soundbank default.ff
CFG [r1]4

// === Channels ===
A !Intro(c); B !Intro(e)
K !Verse(c,4) !Verse(d,5)
J @0 v14 o4 l1 c
"""
        result = self.compiler.compile_string(syr_input)

        # 1. PMD directives preserved
        self.assertIn('#Title Syr Test Song', result)
        self.assertIn('#Composer mmlsyc', result)
        self.assertIn('#Zenlen 192', result)
        self.assertIn('#Tempo 150', result)
        self.assertIn('#PCMFile DRUMS.PPC', result)

        # 2. No MMLSyr syntax remaining
        self.assertNotIn('//', result)
        self.assertNotIn('##', result)
        self.assertNotIn('CFG', result)
        self.assertNotIn('=== Macro', result)
        self.assertNotIn('=== CFG', result)
        self.assertNotIn('=== Channels', result)

        # 3. A, B channels macro expansion
        lines = result.split('\n')
        a_line = next((l for l in lines if l.strip().startswith('A ')), None)
        b_line = next((l for l in lines if l.strip().startswith('B ')), None)
        self.assertIsNotNone(a_line)
        self.assertIsNotNone(b_line)
        # A should contain Intro(c) expanded content
        self.assertIn('o4', a_line)
        # B should contain Intro(e) expanded content
        self.assertIn('o4', b_line)

        # 4. K track macros expanded to R tracks
        self.assertIn('K ', result)
        # Continuation macro Verse should be correctly merged
        self.assertTrue(
            any('R' in l and 'c4' in l for l in lines),
            "Should have R track with expanded Verse(c,4) content"
        )

        # 5. J channel preserved
        self.assertIn('@0 v14 o4 l1 c', result)

        # 6. CFG filled undefined channels
        defined = set()
        for line in lines:
            m = re.match(r'^\s*([A-K])\s+', line)
            if m:
                defined.add(m.group(1))
        # C-H should be filled by CFG
        for ch in 'CDEFGH':
            self.assertIn(ch, defined,
                f"Channel {ch} should be filled by CFG")

    def test_output_is_valid_pmd_text(self):
        """Verify output contains only valid PMD characters and structures."""
        syr_input = """#Title Valid Check
!Pat c4d4e4f4
K !Pat
A o4l8 cdefgab>c
"""
        result = self.compiler.compile_string(syr_input)

        # Each line should be one of:
        # 1. Empty line
        # 2. ; PMD comment (starts with ;)
        # 3. # PMD directive (starts with #)
        # 4. Channel line (starts with A-K or R+digit)
        valid_line_pattern = re.compile(
            r'^(\s*$|;.*|#\w.*|[A-K]\s+.*|R\d+\s+.*)')

        lines = result.split('\n')
        for i, line in enumerate(lines):
            if line.strip():
                self.assertRegex(line.strip(), valid_line_pattern,
                    f"Line {i+1} is not valid PMD MML format: '{line}'")


if __name__ == '__main__':
    unittest.main()
