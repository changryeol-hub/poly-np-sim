"""
sat_test_cases.py

Purpose:
- Provides SAT test cases for Fixed-State and Input-Dependent Turing Machines
- Separates tests into:
    1) Verifier correctness (`verifier_tests` / `simple_verifier_tests`): checks V(x, w)
    2) SAT existence (`sat_tests` / `simple_sat_tests`): checks ∃w V(x, w)
- Includes both full regression tests and simple small-variable tests for quick verification

Input format for formulas:
    Standard SAT CNF-like representation with certificate (for verifier tests)
    - '&' : separates clauses
    - '_' : separates variables within clauses
    - '-' : negation of a variable
    - '#' : begins certificate section (T/F string) or indicates SAT existence
    - Examples:
        Verifier: "1_2&-1_3#TFT" → certificate w = T F T
        SAT existence: "1_2&-1_3#" → asks whether a satisfying assignment exists

Verifier tests:
- `verifier_tests`: full regression set for correctness checking
- `simple_verifier_tests`: small-variable tests (≤5 variables) for quick verification
- Each tuple: (formula_with_certificate, expected_bool)

SAT existence tests:
- `sat_tests`: full regression set
- `simple_sat_tests`: small-variable tests
- Each tuple: (formula, expected_bool)

Utility function:
- get_variable_count(formula_with_hash: str) -> int
    * Returns the highest variable index in the formula (ignores negation)
    * Used to determine the number of variables for certificate enumeration

Usage:
- Import this module in SAT TM test scripts
- Example:
    from sat_test_cases import verifier_tests, sat_tests, get_variable_count
"""


# ============================================================
# Test Set 1 : Verifier correctness  V(x, w)
# ============================================================
verifier_tests = [
    ("1_2_3&4_5_6&7_8_9&-9_10_1&-2_6_1&3_5_1&-4_2_10#TTFFTFTFFT", True),
    ("1&-1&2_3&4_5&7#TTTTTTT", False),
    ("-1_3_5&5_2_1&7_9_10&-6_1_-4&2_-6_1#TTTFTFTFTF", True),
    ("1_3_5&5_2_1&7_9_10&-6_1_-4&2_-6_1#TTTFTFTFTF", True),
    ("2&-2&1_3_1&4_6_5&-9_10#FFFFFFFFFF", False),
]


# ============================================================
# Test Set 2 : SAT existence  ∃w V(x,w)
# ============================================================
sat_tests = [
    ("1_2_3&4_5_6&7_8_9&-9_10_1&-2_6_1&3_5_1&-4_2_10#", True),
    ("1&-1&2_3&4_5&7#", False),
    ("-1_3_5&5_2_1&7_9_10&-6_1_-4&2_-6_1#", True),
    ("1_3_5&5_2_1&7_9_10&-6_1_-4&2_-6_1#", True),
    ("2&-2&1_3_1&4_6_5&-9_10#", False),
]


# ============================================================
# Simple Test : Verifier correctness  V(x, w)
# variables ≤ 5
# ============================================================
simple_verifier_tests = [

    # satisfiable
    # (x1 ∨ x2) ∧ (¬x1 ∨ x3)
    # w = T F T
    ("1_2&-1_3#TFT", True),

    # unsatisfiable
    # x1 ∧ ¬x1
    # any certificate fails
    ("1&-1#T", False),

]

# ============================================================
# Simple Test : SAT existence  ∃w V(x,w)
# ============================================================
simple_sat_tests = [

    # satisfiable
    # (x1 ∨ x2) ∧ (¬x1 ∨ x3)
    ("1_2&-1_3#", True),

    # unsatisfiable
    # x1 ∧ ¬x1
    ("1&-1#", False),

]




# ============================================================
# Helpers
# ============================================================

def get_variable_count(formula_with_hash: str) -> int:
    """Extract max variable index m from formula#"""
    if formula_with_hash.find('#')>=0:        
        formula=formula_with_hash.split('#')[0]
    else:
        formula=formula_with_hash
    temp = formula.replace('-', '').replace('&', '_').strip('_').split('_')
    return max(map(int, temp))

