"""
cnf_sat_runner.py

Purpose:
- Run the Fixed-State SAT Verifier Turing Machine on benchmark SAT instances.
- Supports both standard CNF files and fixed-format SAT tape strings.
- Intended for performance/validation on small to medium SAT instances.

Usage:
    $ python cnf_sat_runner.py path_to_file --loglevel DEBUG

Input formats:
1. DIMACS CNF format (.cnf):
   - Clauses end with '0', file may optionally end with '%\n0'.
   - This script converts the CNF into a SAT verifier tape string.

2. Fixed-format tape string:
   - Lines with '&' as separators between clauses and '_' as separators between symbols.
   - Each tape must terminate with the '#' symbol.
   - Example: "-1_3_5&5_2_1&7_9_10&-6_1_-4&2_-6_1#"
"""

import logging as log
import os, sys, argparse

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path: sys.path.append(parent_dir)

import main.dynamicComputationGraph as dcg
from main.simulateAllCertificatePoly import *
import verifierTM.SATFixedStateTM as TM
import sys, argparse, os, logging as log

def setup_logging():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help="Path to CNF or tape string format file")
    parser.add_argument('--loglevel', default='INFO', choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'])
    args = parser.parse_args()
    
    numeric_level = log.getLevelNamesMapping().get(args.loglevel.upper(), log.INFO)
    log.basicConfig(level=numeric_level)
    return args

def read_file(filename):
    with open(filename,'r') as f:
        lines = f.readlines()

    # Strip lines containing comments (c), while preserving the 'p cnf' header.
    content_lines = [line for line in lines if not line.startswith('c')]
    first_line = content_lines[0] if content_lines else ''
    content = ''.join(content_lines[1:])
    return first_line, content


def parse_input(filename):
    first_line, content = read_file(filename)

    # Identify CNF format: Check for .cnf extension or 'p cnf' in the header line.
    if filename.lower().endswith('.cnf') or 'p cnf' in first_line.lower():
        log.info("Detected CNF file format")
        # Process CNF file
        tape = content.replace("0\n%\n0","").replace("0\n","&").strip()+'#'
        tape = tape.replace(" ","_").replace("_&","&")
    else:
        log.info("Recarded as fixed-format tape")
        tape = content.strip()
        if '#' not in tape:
            raise ValueError("Invalid tape format: missing '#' terminator")
        tape = tape.replace(" ","_").replace("_&","&")

    return tape


def main():
    args = setup_logging()
    filename = args.filename

    tape_string = parse_input(filename)
    temp = tape_string.rstrip('#').replace('-','').replace('&','_').split('_')
    m = max(map(int,filter(lambda x: x.isdecimal(), temp)))
    log.info(f"Processing {filename} with m={m}")
    result = SimulateVerifierForAllCertificates(tape_string, m,TM.INIT_STATE, TM.symbols, TM.delta, TM.states, TM.certSymbols)
    print(result)

    if result=='Yes':
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
