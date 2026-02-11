"""
test_hybrid_fixed(original_feasible).py

Purpose:
- Regression test for SAT Fixed-State Turing Machine using a hybrid setup:
    * Feasible graph module from original implementation
    * All other modules (verifier, simulator, computation graph, logging) from main implementation
- Designed to verify correctness of the hybrid setup
- Slightly slower than the pure main implementation due to using original feasible graph
- Not intended for general TM testing or performance benchmarking

Input format:
    Standard SAT instance representation

Modes:
    Verifier mode
        Tape contains explicit certificate
        → runs fixed simulation (m = 0)

    Existence mode
        Tape contains only instance
        → enumerates all certificates (m = number of variables)

Features:
- Creates a temporary library snapshot package combining main modules with original feasible graph
- Logs detailed results for each test case
- Cleans up temporary package after execution
- Focused on verifying hybrid implementation correctness with original feasible graph

Usage:
    $ python test_hybrid_fixed(original_feasible).py
"""

import logging as log
import os, sys, shutil
from pathlib import Path
import importlib
# ============================================================
# Prepare TEMP package (library snapshot test)
# ============================================================

ROOT = Path(__file__).resolve().parent.parent
TEMP = ROOT / "temp"

def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

def prepare_temp_package():
    print(f"[temp] using workspace: {TEMP}")
    if TEMP.exists():
        shutil.rmtree(TEMP)

    # --- copy from main ---
    copy(ROOT/"main"/"verificationWalk.py",        TEMP/"verificationWalk.py")
    copy(ROOT/"main"/"simulateAllCertificatePoly.py", TEMP/"simulateAllCertificatePoly.py")
    copy(ROOT/"main"/"dynamicComputationGraph.py", TEMP/"dynamicComputationGraph.py")
    
    # --- copy from original ---
    copy(ROOT/"original"/"feasibleGraph.py",           TEMP/"feasibleGraph.py")
    copy(ROOT/"original"/"log_ext.py",                 TEMP/"log_ext.py")
    #copy(ROOT/"original"/"__init__.py",                TEMP/"__init__.py")
    (TEMP / "__init__.py").write_text("# temp package\n")

    importlib.invalidate_caches()  

prepare_temp_package()

# --- path setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# --- project imports ---
import temp.dynamicComputationGraph as dcg
from temp.simulateAllCertificatePoly import SimulateVerifierForAllCertificates
import verifierTM.SATFixedStateTMWithCertificateCheck as TM
import temp.log_ext as log_ext

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
        
        dcg.TierArray.symbols = TM.symbols
        dcg.TierArray.states = TM.states
        dcg.TransitionCase.delta = TM.delta
        
        result = SimulateVerifierForAllCertificates(
            tape,
            0,  # fixed certificate mode
            TM.INIT_STATE,
            TM.symbols,
            TM.delta,
            TM.states,
            TM.symbols
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
        
        dcg.TierArray.symbols = TM.symbols
        dcg.TierArray.states = TM.states
        dcg.TransitionCase.delta = TM.delta

        result = SimulateVerifierForAllCertificates(
            tape,
            m,  # enumerate certificates
            TM.INIT_STATE,
            TM.symbols,
            TM.delta,
            TM.states,
            TM.symbols
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
        shutil.rmtree(TEMP)
        sys.exit(0)
    else:
        print("Some tests failed.")
        sys.exit(1)
