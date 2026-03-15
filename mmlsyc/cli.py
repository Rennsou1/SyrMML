#!/usr/bin/env python3

"""
MMLSyr Compiler CLI
"""

import argparse
import sys
from .compiler import MMLSyrCompiler

def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description='MMLSyr Compiler - Compile MMLSyr files to standard PMD MML'
    )
    
    # Input file
    parser.add_argument('input', help='Input MMLSyr file path')
    
    # Output file (optional)
    parser.add_argument('-o', '--output', help='Output MML file path')
    
    # Version
    parser.add_argument(
        '-v', '--version', action='version', 
        version='MMLSyr Compiler 0.3.0'
    )
    
    # Verbose mode
    parser.add_argument(
        '-V', '--verbose', action='store_true',
        help='Show compilation details'
    )
    
    # Syntax check only
    parser.add_argument(
        '--check', action='store_true',
        help='Check syntax only, do not output compiled result'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    try:
        # Create compiler instance
        compiler = MMLSyrCompiler()
        
        if args.verbose:
            print(f"[mmlsyc] Compiling: {args.input}", file=sys.stderr)
        
        # Compile file
        compiled_content = compiler.compile(args.input, args.output)
        
        if args.verbose:
            # Output compilation stats
            lines = compiled_content.strip().split('\n')
            print(f"[mmlsyc] Done: {len(lines)} lines output", file=sys.stderr)
        
        if args.check:
            # Check-only mode, do not output content
            print("Syntax check passed.", file=sys.stderr)
        elif not args.output:
            # No output file specified, print to stdout
            print(compiled_content)
            
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()