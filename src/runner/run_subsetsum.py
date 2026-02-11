"""
run_subsetsum.py

Fixed-state Subset-Sum Verifier Turing Machine Runner.

This script provides a Turing Machine that verifies Subset-Sum instances
using a fixed-state configuration. It is based on the formal polynomial-time
simulation framework for NP verifiers.

Key features:
- Fixed-state Subset-Sum Verifier Turing Machine: the state set and symbols
  are predefined and independent of the input size.
- Compatible with the feasible-graph verification framework.
- Supports both interactive input mode and a callable `run(tape_string)` 
  function for programmatic execution.
- Includes automated tests (`test_machine`) to validate correctness against
  predefined Subset-Sum instances (accepting and rejecting cases).

Limitations:
- Uses shared class variables in `dcg` module; multiple instances or
  multithreaded execution is not supported. Use separate processes if needed.

Usage:
    $ python run_subsetsum.py            # interactive mode
    run(tape_string)                     # programmatic execution

Input format:
- The tape format is `<target>_@_<elements>#<certificate>`.
- `target` is the integer sum to achieve.
- `elements` is a list of integers separated by '_'.
- `certificate` is the proposed subset (also integers separated by '_') to verify.
- Each input tape must terminate with the '#' symbol.
Example:
    "28_@_1_3_5_7_10_20#1_20_7_;"
"""
import logging as log
import os, sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path: sys.path.append(parent_dir)

import main.dynamicComputationGraph as dcg
from main.simulateAllCertificatePoly import *
import verifierTM.SubsetSumTM as TM
import main.log_ext as log_ext


def run(tape_string):
    if (tape_string.find("#")<0 or tape_string.find("@")<0):
        log.warn("Empty or Wrong Input!")
        return None
    m=tape_string.find("#")-tape_string.find("@");
    result=SimulateVerifierForAllCertificates(tape_string, m,TM.INIT_STATE, TM.symbols, TM.delta, TM.states, TM.certSymbols)
    return result

def test_machine():
    tape0="28_@_1_3_5_7_10_20#1_20_7_;"
    tape1="15_@_1_3_5_7_10_20#3_5_7_;"
    tape2="15_@_1_3_5_7_10_20#5_10_;"
    tape3="20_@_1_3_5_7_10_20#3_10_7_;"
    tape4="45_@_1_3_5_37_100_20#3_5_37_;"
    tape5="100_@_1_3_27_100#37_45_;"   #Reject
    tape6="82_@_1_3_37_100_45#37_45_;"
    tape7="18_@_42_20_3_5#5_3_15_;"   #Reject
    tape8="33_@_42_20_3_5#5_5_3_20_;"  #Reject
    tape9="15_@_1_3_5_7_10_20#3_5_07_;" #Reject
    tape10="28_@_42_20_3_5#"
    tape=[tape0, tape1,tape2,tape3,tape4,tape5,tape6,tape7,tape8,tape9, tape10]
    answer=[True,True,True,True,True, False, True, False, False, False, True]

    for i in range(0,len(tape)):
        if (tape[i].find("#")<0): break
        result=run(tape[i])
        assert (result=='Yes')==answer[i]
    log.info("Turing machined Confirmed.\n")

def main_interactive():
    while True:
        tape=input("Enter input of Sum of Subset(Ex:'28_@_42_20_3_5#').\n")
        if "#" not in tape or '@' not in tape:
            print("Empty or Wrong Input!")
            return
        print(run(tape))

if __name__ == "__main__":
    log_ext.setup_logging()
    if __debug__: test_machine()
    main_interactive()
