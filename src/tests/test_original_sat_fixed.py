"""
test_original_sat_fixed.py

Purpose:
- Regression test for SAT Fixed-State Turing Machine using all original modules:
    * Verifier, simulator, and computation graph are from the original implementation
- Serves as the sole original regression test file for this setup
- Intended to verify correctness of the original implementation, not for general TM testing

Input format:
    Standard SAT instance representation
    - Even for small/simple inputs, runtime can be significant because:
        * Edge extensions are unrestricted
        * Direction extensions are not applied
      → results in exhaustive verification of edges to determine possible extensions

Modes:
    Verifier mode
        Tape contains explicit certificate
        → runs fixed simulation (m = 0)

    Existence mode
        Tape contains only instance
        → enumerates all certificates (m = number of variables)

Features:
- Logs detailed results for each test case
- Designed solely for original regression testing purposes
- Not intended for performance benchmarking or general TM experimentation

Usage:
    $ python test_original_sat_fixed.py
"""
"""
test_original_sat_fixed.py

Purpose:
- Regression test for SAT Fixed-State Turing Machine using all original modules:
    * Verifier, simulator, and computation graph are from the original implementation
- Serves as the sole original regression test file for this setup
- Intended to verify correctness of the original implementation, not for general TM testing

Input format:
    Standard SAT instance representation
    - Even for small/simple inputs, runtime can be significant because:
        * Edge extensions are unrestricted
        * Direction extensions are not applied
      → results in exhaustive verification of edges to determine possible extensions

Modes:
    Verifier mode
        Tape contains explicit certificate
        → runs fixed simulation (m = 0)

    Existence mode
        Tape contains only instance
        → enumerates all certificates (m = number of variables)

Features:
- Logs detailed results for each test case
- Designed solely for original regression testing purposes
- Not intended for performance benchmarking or general TM experimentation

Usage:
    $ python test_original_sat_fixed.py
"""


import logging; log=logging.getLogger(__name__)
import os, sys

# --- path setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# --- project imports ---
import original.dynamicComputationGraph as dcg
from original.simulateAllCertificatePoly import *
import verifierTM.SATFixedStateTMWithCertificateCheck as TM
import original.log_ext as log_ext
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
        result = SimulateVerifierForAllCertificates(
            tape,
            0,  # fixed certificate mode
            TM.INIT_STATE,
            TM.symbols,
            TM.delta,
            TM.states
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
            TM.states
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