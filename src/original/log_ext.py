"""
log_ext.py

Purpose:
- Provides centralized logging configuration and utilities for the project
- Defines a custom VERBOSE logging level (numeric value 5) below DEBUG
- Offers short-name module loggers to keep log output concise

Features:
- Logging level configurable via command-line argument '--loglevel'
- Defaults to DEBUG in development mode (__debug__ is True), otherwise INFO
- get_logger(__name__) returns a shortened module-specific logger name
- Helper function for safely truncating long tape/language strings in logs

Typical usage:
    from log_ext import setup_logging, get_logger
    setup_logging()
    log = get_logger(__name__)
"""

import logging, argparse

VERBOSE = 5

_MAX_TAPE_LOG_LEN = 40

if logging.getLevelName(VERBOSE) == f"Level {VERBOSE}":
    logging.addLevelName(VERBOSE, "VERBOSE")
    
    
def setup_logging():
    parser = argparse.ArgumentParser()
    parser.add_argument('--loglevel',
        default='INFO',
        choices=['VERBOSE', 'DEBUG','INFO','WARNING','ERROR','CRITICAL'])
    args = parser.parse_args()
    level=args.loglevel
    
    if level=="":
        numeric_level=logging.DEBUG if __debug__ else logging.INFO
    else :
        numeric_level = logging.getLevelNamesMapping().get(level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level)

def get_inputlog_str(language):
    if '#' not in language:
        return language
    else:
        parts = language.split('#')
        logstr = parts[0][:_MAX_TAPE_LOG_LEN]+'...#'+parts[1]
        return logstr
    
    
_NAME_MAP = {

    # ===== Graph / structure =====
    "dynamicComputationGraph": "dcg",
    "feasibleGraph": "fg",

    # ===== Verification walk =====
    "verificationWalk": "ver",

    # ===== Certificate enumeration =====
    "simulateAllCertificatePoly": "sim",

    # ===== Turing Machines =====
    "SATFixedStateTM": "tm",
    "SATInputDependentTM": "tm",
    "SATFixedStateTMWithCertificateCheck": "tm",
    "SubsetSumTM": "tm",

    # ===== Problem meaning layer =====
    "sat_test_cases": "sat",
    "subsetsum_test_cases": "ss",

    # ===== Runners =====
    "run_sat_fixed": "run",
    "run_sat_dynamic": "run",
    "run_subsetsum": "run",
    "cnf_file_runner": "run",

    # ===== Input / helpers =====
    "input": "input",

    # ===== Tests =====
    "test_main_sat_fixed": "test",
    "test_main_sat_dynamic": "test",
    "test_main_subsetsum": "test",
    "test_original_sat_fixed": "test",
    "test_hybrid_fixed(original_feasible)": "test",
    "test_hybrid_dynamic(main_feasible)": "test",
    "test_hybrid_subsetsum(orginal_feasible)": "test",
}

_DEFAULT = "misc"

def get_logger(module_name):
    leaf = module_name.rsplit('.', 1)[-1]
    short = _NAME_MAP.get(leaf, _DEFAULT)
    return logging.getLogger(short)
