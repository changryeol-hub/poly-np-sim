"""
subsetsum_cotm_test_cases.py

Purpose:
- Provides test cases for the Certificate-Oblivious Subset-Sum Turing Machine
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
    - 'x' : mask symbol for unused elements
    Example: "28_@1_3_5_7_10_20#1_x_x_7_xx_20"

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
    ("120_@19_120_47_14_34_12_43_12_22#xx_120_xx_xx_xx_xx_xx_xx_xx",True),
    ("28_@1_3_5_7_10_20#1_x_x_7_xx_20", True),
    ("15_@1_3_5_7_10_20#x_3_5_7_xx_xx", True),
    ("15_@1_3_5_7_10_20#x_x_5_x_10_xx", True),
    ("20_@1_3_5_7_10_20#x_3_x_7_10_xx", True),
    ("45_@1_3_5_37_100_20#x_3_5_37_xxx_xx", True),
    ("100_@1_3_27_100#x_x_37_xxx", False),
    ("47_@1_3_37_10_45#x_x_37_1x_xx", False),
    ("18_@42_20_3_5#xx_10_3_5", False),
    ("23_@42_20_3_5#xx_20_3_x_", False),
    ("15_@1_3_5_7_10_20#x_3_5_7_x0_xx", False),
    ("28_@42_20_3_5#xx_20_3_5", True),
]

# ∃w V(x,w)
sat_tests = [
    ("10_@3_4_12#",False),
    ("28_@42_20_3_5#", True),
]

def get_certificate_length(tape: str) -> int:
    # T@a_b_c_d#
    return tape.find("#")-tape.find("@")-1
    