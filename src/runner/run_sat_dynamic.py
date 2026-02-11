"""
run_sat_dynamic.py

Input-dependent SAT Verifier Turing Machine Runner.

This script provides a SAT verifier Turing Machine whose states depend
on the input size. It is based on the formal polynomial-time simulation 
framework for NP verifiers.

Key features:
- Input-dependent SAT Verifier Turing Machine: the state set is generated
  dynamically based on the input instance.
- Compatible with the feasible-graph verification framework.
- Supports both interactive input mode and a callable `run(tape_string)` 
  function for programmatic execution.
- Includes automated tests (`test_machine`) to validate correctness
  against predefined SAT and UNSAT instances.

Limitations:
- Uses shared class variables in the `dcg` module; multithreaded execution
  is not supported. For parallel runs, use separate processes.

Usage:
    $ python run_sat_dynamic.py          # interactive mode
    run(tape_string)                     # programmatic execution

Input format:
- Tape symbols are encoded using '_' as separators between numbers and
  '&' as separators between elements. Each input tape must terminate
  with the '#' symbol.
Example:
    "-1_3_5&5_2_1&7_9_10&-6_1_-4&2_-6_1#"
"""


import logging as log
import os, sys, argparse

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path: sys.path.append(parent_dir)

import main.dynamicComputationGraph as dcg
from main.simulateAllCertificatePoly import *
import verifierTM.SATInputDependentTM as TM

import main.log_ext as log_ext


def run(tape_string):
    if (tape_string.find("#")<0): 
        log.warn("Empty or Wrong Input!")
        return None
    m=max(map(int,tape_string.rstrip("#").strip("_").replace('&','_').replace('__','_').split("_")))
    result=SimulateVerifierForAllCertificates(tape_string, m,TM.INIT_STATE, TM.symbols, TM.delta, TM.states(m), TM.certSymbols)
    return result

def test_machine():
    tape1="1_2_3&4_5_6&7_8_9&-9_10_1&-2_6_1&3_5_1&-4_2_10#"  # 1. SAT
    tape2="1&-1&2_3&4_5&7#"                                  # 2. UNSAT
    tape3="1_2_3&4_5_6&7_8_9&-9_10_1&-2_6_1&3_5_1&4_2_10#"   # 3. SAT
    tape4="2&-2&1_3_1&4_6_5&-9_10#"                          # 4. UNSAT
    tape5="-1_3_5&5_2_1&7_9_10&-6_1_-4&2_-6_1#"              # 5. SAT
    tape6="1_3_5&5_2_1&7_9_10&-6_1_-4&2_-6_1#"               # 6.SAT
    tape7="4_-18_19_&3_18_-5_&-5_-8_-15_&-20_7_-16_&10_-13_-7_&-12_-9_17_&17_19_5_&-16_9_15_&"\
          +"11_-5_-14_&18_-10_13_&-3_11_12_&-6_-17_-8_&-18_14_1_&-19_-15_10_&12_18_-19_&-8_4_7_&"\
          +"-8_-9_4_&7_17_-15_&12_-7_-14_&-10_-11_8_&2_-15_-11_&9_6_1_&-11_20_-17#" #7.SAT

    tape=[tape1,tape2,tape3,tape4,tape5,tape6]
    answer=[True, False, True, False ,True, True, True]

    for i in range(0,len(tape)):
        if (tape[i].find("#")<0): break
        result=run(tape[i])
        assert (result=='Yes')==answer[i]
    log.info("Turing machined Confirmed.\n")

def main_interactive():
    while True:
        tape=input("Enter input of SAT(Ex:'-1_3_5&5_2_1&7_9_10&-6_1_-4&2_-6_1#').\n")
        if "#" not in tape:
            print("Empty or Wrong Input!")
            return
        print(run(tape))

if __name__ == "__main__":
    log_ext.setup_logging()
    if __debug__: test_machine()
    main_interactive()


