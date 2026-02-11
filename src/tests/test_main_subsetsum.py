"""
test_main_subsetsum.py

Purpose:
- Regression test for Subset-Sum Turing Machine
- Separates:
    1) Verifier correctness  : V(x, w)
    2) Solution existence    : ∃w V(x, w)

Input format:
    Target_@_a_b_c_d#certificate_;
        Example: 28_@_1_3_5_7_10_20#1_20_7_;

    - '_' : separator
    - '@' : separates target value and set elements
    - '#' : begins certificate section
    - ';' : terminates certificate
    - certificate is a selected subset written as numbers

Modes:
    Verifier mode
        Tape contains explicit certificate ending with ';'
        → runs fixed simulation (m = 0)

    Existence mode
        Tape ends with '#'
        → enumerates all certificates (m = number of elements)

Usage:
    $ python test_main_subsetsum_fixed.py
"""


import logging as log
import os, sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import main.dynamicComputationGraph as dcg
from main.simulateAllCertificatePoly import SimulateVerifierForAllCertificates
import verifierTM.SubsetSumTM as TM
import main.log_ext as log_ext

import subsetsum_test_cases as tc

# ============================================================
# Verifier tests
# ============================================================

def run_verifier_tests():
    log.info("==== SubsetSum Verifier tests ====")
    ok = True

    for i, (tape, expected_bool) in enumerate(tc.verifier_tests):

        result = SimulateVerifierForAllCertificates(
            tape,
            0,
            TM.INIT_STATE,
            TM.symbols,
            TM.delta,
            TM.states,
            TM.certSymbols
        )

        if (result == 'Yes') != expected_bool:
            log.error(f"[Verifier] Test {i} FAILED: {tape} -> {result}")
            ok = False
        else:
            log.info(f"[Verifier] Test {i} passed.")

    return ok


# ============================================================
# SAT search tests
# ============================================================

def run_sat_tests():
    log.info("==== SubsetSum existence tests ====")
    ok = True

    for i, (tape, expected_bool) in enumerate(tc.sat_tests):

        m = tc.get_certificate_length(tape)

        result = SimulateVerifierForAllCertificates(
            tape,
            m,
            TM.INIT_STATE,
            TM.symbols,
            TM.delta,
            TM.states,
            TM.certSymbols
        )

        if (result == 'Yes') != expected_bool:
            log.error(f"[SAT] Test {i} FAILED: {tape} -> {result}")
            ok = False
        else:
            log.info(f"[SAT] Test {i} passed.")

    return ok


if __name__ == "__main__":

    if not log.getLogger().handlers:
        log_ext.setup_logging()

    verifier_ok = run_verifier_tests()
    sat_ok = run_sat_tests()

    if verifier_ok and sat_ok:
        print("All tests passed.")
        sys.exit(0)
    else:
        print("Some tests failed.")
        sys.exit(1)

