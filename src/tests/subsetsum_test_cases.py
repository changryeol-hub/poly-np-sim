"""
subsetsum_test_cases.py

Purpose:
- Provides test cases for the Subset-Sum Fixed-State Turing Machine
- Separates tests into:
    1) Verifier correctness tests (`verifier_tests`): checks V(x, w)
    2) Existence tests (`sat_tests`): checks ∃w V(x, w)

Input format for tapes:
    target_@_a_b_c_d#certificate_;
    - target: integer target sum
    - '_' : separator between numbers
    - '@' : separates target value from set elements
    - '#' : marks beginning of certificate section
    - certificate: subset of elements selected as witness
    - ';' : terminates certificate
    Example: "28_@_1_3_5_7_10_20#1_20_7_;"

Verifier tests (`verifier_tests`):
- Each tuple is (tape, expected_bool)
- Checks whether the provided certificate correctly satisfies the Subset-Sum instance

SAT/existence tests (`sat_tests`):
- Each tuple is (tape, expected_bool)
- Checks whether there exists a certificate that satisfies the Subset-Sum instance

Utility function:
- get_certificate_length(tape: str) -> int
    * Computes the number of elements in the certificate section of a tape
    * Formula: number of characters between '@' and '#' in the tape string

Usage:
- Import this module in test scripts to run verifier and SAT existence tests
- Example:
    from subsetsum_test_cases import verifier_tests, sat_tests, get_certificate_length
"""



# verifier: V(x,w)
verifier_tests = [
    ("28_@_1_3_5_7_10_20#1_20_7_;", True),
    ("15_@_1_3_5_7_10_20#3_5_7_;", True),
    ("15_@_1_3_5_7_10_20#5_10_;", True),
    ("20_@_1_3_5_7_10_20#3_10_7_;", True),
    ("45_@_1_3_5_37_100_20#3_5_37_;", True),
    ("100_@_1_3_27_100#37_45_;", False),
    ("82_@_1_3_37_100_45#37_45_;", True),
    ("18_@_42_20_3_5#5_3_15_;", False),
    ("33_@_42_20_3_5#5_5_3_20_;", False),
    ("15_@_1_3_5_7_10_20#3_5_07_;", False),
    ("28_@_42_20_3_5#20_5_3_42;", False),
]

# ∃w V(x,w)
sat_tests = [
    ("10_@_3_4_12#",False),
    ("28_@_42_20_3_5#", True),
]

def get_certificate_length(tape: str) -> int:
    # T@a_b_c_d#
    return tape.find("#")-tape.find("@")-1
    