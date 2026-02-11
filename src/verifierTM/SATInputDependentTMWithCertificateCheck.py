"""
Turing Machine Specification Module
-----------------------------------

This module defines a deterministic single-tape Turing Machine used for
comparison with the improved verifier construction described in the paper.

Purpose
-------
The machine implemented here corresponds to the *original version* in which an
explicit input-validation phase is performed before the assignment procedure.
It is included only for reproducibility and comparison; the optimized machine
used in the main construction removes this phase.

Design Principles
-----------------
• The transition function is intentionally kept mathematically faithful:
      δ : Q × Γ → Q × Γ × {−1, +1}
  Therefore `delta(state, symbol)` receives no auxiliary parameters and relies
  solely on the module-internal transition table.

• Transition tables are separated semantically:
      _BASE_TRANSITIONS        : core assignment / verification behavior
      _INPUTCHECK_TRANSITIONS  : preliminary input validation phase
      _TRANSITIONS             : actual machine = union of the above

• All transition tables are private (prefixed with `_`) so external modules
  cannot accidentally alter the machine definition.  External code must use
  only the exported `delta` function.

• Parameterized states (Inc.N, Dec.N, Forward.N, etc.) are instantiated
  dynamically during execution to simulate an address register encoded in the
  state name.

Usage
-----
The module exposes only:

    delta(state, symbol)  -> (next_state, write_symbol, move)
    states(m)             -> finite state set up to address bound m

The transition tables themselves are implementation details and are not part
of the public API.

This file exists primarily as a reference implementation for the
input-dependent verifier machine described in the previous work.
"""

from . import SATInputDependentTM as baseTM

_BASE_TRANSITIONS = baseTM._TRANSITIONS
    
_INPUTCHECK_TRANSITONS={
        #Input Check
        ("InputCheck", "#"): ("CertificateCheck", "#", +1),
        ("InputCheck", "*"): ("InputCheck", "*", +1),
        ("CertificateCheck", "T"):("CertificateCheck", "T", +1),
        ("CertificateCheck", "F"):("CertificateCheck", "F", +1),
        ("CertificateCheck", "ϵ"):("BackToBeginning", "ϵ", -1),
        ("CertificateCheck", "*"):("Reject", "_", -1),
        ("BackToBeginning", "*"):("BackToBeginning", "*", -1),
        ("BackToBeginning", "ϵ"):("Check", "ϵ", +1),   
}

_TRANSITIONS= _BASE_TRANSITIONS | _INPUTCHECK_TRANSITONS 

BLANK = "ϵ"        # tape blank symbol (b)
DELIM = "_"        # structural separator in the encoding

INIT_STATE   = "InputCheck"
ACCEPT_STATE = "Accept"
REJECT_STATE = "Reject"

symbols=list("_-&#TF?!0123456789"+"ϵ")

_INPUTCHECK_STATES = [
    "InputCheck",
    "CertificateCheck",
    "BackToBeginning",
]

_STATES0 = [
    "Check","Not","Skip","Backward.T","Backward.F","Not",
    "Reject","Accept"
] + _INPUTCHECK_STATES


_states=[]

def states(m):
    global _states
    _states=_STATES0.copy()
    for j in range(0,m+1): 
        _states.append("Inc"+"."+str(j))
        _states.append("Dec"+"."+str(j))
        _states.append("Forward"+"."+str(j))
    return _states


    
def delta(state, symbol):
    action = state
    addr = ""
    altstate = None

    # --- Parse parameterized state ---
    if '.' in state:
        action, addr = state.split('.')
        altstate = action + ".N"

    # --- Build symbol matching priority ---
    symbols = [symbol]
    if symbol.isdigit():
        symbols.append('D')
    symbols.append('*')

    # --- Try direct state _TRANSITIONS ---
    for s in symbols:
        if (state, s) in _TRANSITIONS:
            next_state, output, move = _TRANSITIONS[(state, s)]
        elif altstate is not None and (altstate, s) in _TRANSITIONS:
            next_state, output, move = _TRANSITIONS[(altstate, s)]
        else:
            continue

        # --- Re-instantiate parameterized states ---
        if next_state.endswith(".D") and symbol.isdigit():
            next_state = next_state.replace(".D", "." + symbol)
            if next_state not in _states: return ("Reject", "_", -1)

        if next_state.endswith(".N"):
            next_state = next_state.replace(".N", "." + addr)

        elif next_state.endswith(".(N-1)"):
            next_state = next_state.replace(".(N-1)", "." + str(int(addr) - 1))

        elif next_state.endswith(".(10N+D)"):
            next_state = next_state.replace(
                ".(10N+D)", "." + str(int(addr) * 10 + int(symbol))
            )
            
        if next_state not in _states: return ("Reject", "_", -1)

        # --- Resolve output symbol ---
        if output == "*":
            output = symbol

        return (next_state, output, move)

    # --- No transition applicable ---
    return ("Reject", "_", -1)



