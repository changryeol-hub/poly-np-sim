
# NP Verifier Simulation Framework

## MIT License

```
Copyright (c) 2026 Changryeol Lee

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Academic and Research Use Notice

This software and associated scripts are released for purely academic and research purposes, primarily to enable verification, reproduction, and exploration of the results presented in the accompanying **P=NP proof and implementation study**.

The implementation is intended for **experimental validation and educational use**, and is not yet optimized for practical SAT/Subset-Sum solving or commercial applications.

By releasing this code, the authors aim to support **transparency, peer verification, and further research** in computational complexity and Turing Machine simulations.

## Folder Structure

```
project_root/
│
├─ .gitignore                                  # Git ignore settings
├─ License                                     # Project license
├─ README.md                                   # Project documentation
│
└─ src/                                        # All source codes and resources
    │
    ├─ main/                                   # Core logic (Main implementation)
    │   ├─ log_ext.py
    │   ├─ dynamicComputationGraph.py
    │   ├─ simulateAllCertificatePoly.py
    │   ├─ verificationWalk.py
    │   └─ feasibleGraph.py
    │
    ├─ original/                               # Legacy/Original version codes
    │   ├─ log_ext.py
    │   ├─ dynamicComputationGraph.py
    │   ├─ simulateAllCertificatePoly.py
    │   ├─ verificationWalk.py
    │   └─ feasibleGraph.py
    │
    ├─ verifierTM/                             # Turing Machine (TM) verifiers
    │   ├─ SATFixedStateTM.py
    │   ├─ SATFixedStateTMWithCertificateCheck.py
    │   ├─ SATInputDependentTM.py
    │   ├─ SATInputDependentTMWithCertificateCheck.py
    │   ├─ SubsetSumTM.py
    │   └─ SubsetSumTMWithCertificateCheck.py
    │
    ├─ runners/                                # Execution scripts and data
    │   ├─ run_sat_fixed.py
    │   ├─ run_subsetsum.py
    │   ├─ run_sat_dynamic.py
    │   ├─ cnf_file_runner.py
    │   └─ input/                              # Input files (CNF, Tape, etc.)
    │       ├─ sample0.cnf ~ sample50.cnf      # SAT/CNF benchmark instances
    │       ├─ uf20-01.cnf, uuf20-100.cnf      # Standard benchmark instances
    │       ├─ input(cnf).txt                  # CNF tape inputs
    │       └─ input(sumofsubset).txt          # Subset-Sum tape inputs
    │
    └─ tests/                                  # Test and validation scripts
        ├─ sat_test_cases.py
        ├─ subsetsum_test_cases.py
        ├─ test_original_sat_fixed.py
        ├─ test_hybrid_fixed(original_feasible).py
        ├─ test_hybrid_dynamic(main_feasible).py
        ├─ test_main_sat_fixed*.py
        ├─ test_main_sat_dynamic*.py
        └─ test_main_subsetsum*.py

```

## Key Features

### Fixed-State SAT Verifier
- Constant state set, independent of input size.
- Fully compatible with the feasible-graph verification framework.
- `run_sat_fixed.py` provides both interactive and programmatic usage.

### Input-Dependent SAT Verifier
- State set depends on the maximum value in the input tape.
- Allows testing on larger or specially structured SAT instances.
- Accessible via `run_sat_dynamic.py`.

### Subset-Sum Verifier
- Handles classic Subset-Sum instances in the fixed-state framework.
- `run_subsetsum.py` supports programmatic and interactive execution.

### Benchmark Runner
- `cnf_file_runner.py` can process standard DIMACS CNF files or legacy tape files.
- Automatically detects file type and constructs a verifier tape string.

### Original Test Scripts
- Located in the `tests/` folder.
- Based entirely on the original (pre-main) implementation.
- Used primarily for **TM verification and regression** on small test cases.
- These scripts are **not optimized for runtime**, especially on larger inputs.


## Usage

### Logging (`log_ext.py`)
- Provides reusable logging setup for all runners and tests.
- Supports standard levels: CRITICAL, ERROR, WARNING, INFO, DEBUG.
- Adds custom VERBOSE level (numeric 5).
- **Note:** `log_ext.py` exists in both `original/` and `main/feasible/` directories for modular snapshots, but scripts can simply `import log_ext` for unified usage.  
- Intended for **import in scripts**, not standalone execution.

All runners accept a `--loglevel` argument to control logging:

```bash
python run_sat_fixed.py --loglevel DEBUG
python run_subsetsum.py --loglevel INFO
python run_sat_dynamic.py --loglevel WARNING
python cnf_file_runner.py path/to/file.cnf --loglevel DEBUG

```

### Tape Input Format
- Tape symbols use `_` to separate numbers and `&` to separate elements.
- Each tape must end with `#`.

**Example:**
```
-1_3_5&5_2_1&7_9_10&-6_1_-4&2_-6_1#
```

### CNF Input Format
- Standard DIMACS CNF format.
- Clauses end with `0`.
- File may optionally end with `%`.
- `cnf_file_runner.py` converts CNF files into a SAT verifier tape automatically.

### Sample Inputs
- `input/` folder contains small example files for SAT, Subset-Sum, and CNF.
- Original legacy tape inputs for testing and comparison are included.

### Notes
- **Multithreading:** Not supported due to shared class variables. Multiple runs can be executed in separate processes if needed.
- **Python Version:** Tested on Python 3.10+.
- **Dependencies:** Only standard library modules are required (`argparse`, `logging`, `sys`, `os`).

### Python Example
```python
from run_sat_fixed import run

tape = "-1_3_5&5_2_1&7_9_10&-6_1_-4&2_-6_1#"
result = run(tape)
print(result)  # 'Yes' or 'No'
```

### Run a Benchmark CNF File
```bash
python cnf_file_runner.py input/sample.cnf --loglevel DEBUG
```
**Output:** `'Yes'` (SAT) or `'No'` (UNSAT)
