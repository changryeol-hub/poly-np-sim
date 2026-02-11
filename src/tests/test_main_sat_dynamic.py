"""
test_main_sat_dynamic.py

Purpose:
- Regression test for SAT Fixed-State Turing Machine
- Separates:
    1) Verifier correctness  : V(x, w)
    2) SAT existence search : ∃w V(x, w)

Usage:
    $ python test_main_sat_dynamic.py
"""

import logging as log
import os, sys

# --- path setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# --- project imports ---
import main.dynamicComputationGraph as dcg
from main.simulateAllCertificatePoly import SimulateVerifierForAllCertificates
import verifierTM.SATInputDependentTM as TM
import main.log_ext as log_ext

import sat_test_cases 

verifier_tests=sat_test_cases.verifier_tests
sat_tests=sat_test_cases.sat_tests

# ============================================================
# Run Verifier Tests
# ============================================================

def run_verifier_tests():
    log.info("==== Verifier correctness tests ====")
    ok = True

    for i, (tape, expected_bool) in enumerate(verifier_tests):
        n=sat_test_cases.get_variable_count(tape) # Used for state-space size, not certificate length

        result = SimulateVerifierForAllCertificates(
            tape,
            0,  # fixed certificate mode
            TM.INIT_STATE,
            TM.symbols,
            TM.delta,
            TM.states(n),
            TM.certSymbols
        )

        if (result == 'Yes') != expected_bool:
            log.error(f"[Verifier] Test {i} FAILED: {tape} -> {result}")
            ok = False
        else:
            log.info(f"[Verifier] Test {i} passed.")

    return ok


# ============================================================
# Run SAT Search Tests
# ============================================================

def run_sat_tests():
    log.info("==== SAT existence tests ====")
    ok = True

    for i, (tape, expected_bool) in enumerate(sat_tests):
        m = sat_test_cases.get_variable_count(tape)

        result = SimulateVerifierForAllCertificates(
            tape,
            m,  # enumerate certificates
            TM.INIT_STATE,
            TM.symbols,
            TM.delta,
            TM.states(m),
            TM.certSymbols
        )

        if (result == 'Yes') != expected_bool:
            log.error(f"[SAT] Test {i} FAILED: {tape} -> {result}")
            ok = False
        else:
            log.info(f"[SAT] Test {i} passed.")

    return ok


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    log_ext.setup_logging()

    verifier_ok = run_verifier_tests()
    sat_ok = run_sat_tests()

    if verifier_ok and sat_ok:
        print("All tests passed.")
        sys.exit(0)
    else:
        print("Some tests failed.")
        sys.exit(1)
