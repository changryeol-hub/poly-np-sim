"""
run_subsetsum.py

Certificate-Oblivous Fixed-state Subset-Sum Verifier Turing Machine Runner.

This script provides a Turing Machine that verifies Subset-Sum instances
using a fixed-state configuration. It is based on the formal polynomial-time
simulation framework for NP verifiers.

Key features:
- Fixed-state Subset-Sum Verifier Turing Machine: the state set and symbols
  are predefined and independent of the input size.
- Compatible with the NP verifier simulation framework.
- Supports both interactive input mode and a callable `run(tape_string)` 
  function for programmatic execution.
- Includes automated tests (`test_machine`) to validate correctness against
  predefined Subset-Sum instances (accepting and rejecting cases).

Limitations:
- Uses shared class variables in `dcg` module; multiple instances or
  multithreaded execution is not supported. Use separate processes if needed.

Usage:
    $ python run_subsetsum.py [--timeout MIN]   # interactive mode
    run(tape_string, timeout=1800)              # programmatic execution - timeout is optional (seconds)

Input format:
- The tape format is `<target>_@<elements>#<certificate>`.
- `target` is the integer sum to achieve.
- `elements` is a list of integers separated by '_'.
- `certificate` is the proposed subset (also integers separated by '_') to verify.
- Each input tape must terminate with the '#' symbol to decide NP problem.
Example:
    "28_@1_3_5_7_10_20#"   
"""
import os, sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path: sys.path.append(parent_dir)

import main.dynamicComputationGraph as dcg
from main.simulateAllCertificatePoly import *
import verifierTM.SubsetSumCOTM as TM
import main.log_ext as log_ext
log=log_ext.get_logger(__name__)

def setup_argument():
    parser = argparse.ArgumentParser()
    parser.add_argument('--timeout', type=int, default=None, help="timeout in minutes (default: no timeout)")
    log_ext.setup_logging(parser)
    args= parser.parse_args()
    if args.timeout is not None: args.timeout*=60
    return args

def run(tape_string, timeout=None):
    tape_string=tape_string.strip()
    if (tape_string.find("#")<0 or tape_string.find("@")<0):
        log.warn("Empty or Wrong Input!")
        return None
    if tape_string.endswith('#'):
        m=tape_string.find("#")-tape_string.find("@")-1;
    else: m=0
    result = SimulateVerifierForAllCertificates(tape_string, m, TM.INIT_STATE, TM.inputSymbols, TM.delta, TM.states, 
            TM.symbols, TM.ACCEPT_STATE, TM.REJECT_STATE, TM.certSymbols, timeout=timeout)
    return result

def test_machine():
    tape0="28_@1_3_5_7_10_20#1_x_x_7_xx_20"
    tape1="15_@1_3_5_7_10_20#x_3_5_7_xx_xx"
    tape2="15_@1_3_5_7_10_20#x_x_5_x_10_xx"
    tape3="20_@1_3_5_7_10_20#x_3_x_7_10_xx"
    tape4="45_@1_3_5_37_100_20#x_3_5_37_xxx_xx"
    tape5="100_@1_3_27_100#x_x_37_x45"   #Reject
    tape6="82_@1_3_37_100_45#x_x_37_xxx_45"
    tape7="18_@42_20_3_5#xx_15_3_5"   #Reject
    tape8="33_@42_20_3_5#xx_20_3_5"  #Reject
    tape9="15_@1_3_5_7_10_20#x_3_5_7_x0_x0" #Reject
    tape10="28_@42_20_3_5#"
    tape=[tape0, tape1,tape2,tape3,tape4,tape5,tape6,tape7,tape8,tape9, tape10]
    answer=[True,True,True,True,True, False, True, False, False, False, True]

    for i in range(0,len(tape)):
        if (tape[i].find("#")<0): break
        result=run(tape[i])
        assert (result=='Yes')==answer[i]
    log.info("Turing machined Confirmed.\n")

def main_interactive(timeout):
    while True:
        tape=input("Enter input of Sum of Subset(Ex:'28_@42_20_3_5#').\n")
        if "#" not in tape or '@' not in tape:
            print("Empty or Wrong Input!")
            return
        print(run(tape, timeout), "\n")

if __name__ == "__main__":
    args=setup_argument()
    if __debug__: test_machine()
    main_interactive(args.timeout)
