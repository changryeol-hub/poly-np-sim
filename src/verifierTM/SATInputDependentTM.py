"""
Deterministic Verifier Turing Machine (Core Version)
---------------------------------------------------

This module specifies the Turing Machine actually used in the construction
presented in the paper.  Unlike the comparison version, this machine omits the
explicit input-validation phase and operates directly on the encoded instance
and certificate.

Conceptual Role
---------------
The machine implements the assignment-propagation verifier that underlies the
feasible-graph simulation.  It deterministically scans the certificate region,
interprets variable indices encoded in decimal form, and propagates truth
values back to the corresponding literal occurrences in the formula region.

Formally, the exported function

        delta : Q × Γ → Q × Γ × {−1, +1}

is a direct realization of the transition function of the verifier TM.
No auxiliary parameters or external state are used; the machine definition is
entirely contained in this module.

State Encoding
--------------
Parameterized states (Inc.N, Dec.N, Forward.N) simulate a finite control
register holding a decimal address N:

    Inc.N        : parse a variable index
    Forward.N    : move to the certificate cell
    Dec.N        : count down while scanning certificate symbols
    Backward.T/F : propagate assignment back to the formula

The address value is not stored on tape but encoded in the state name and
expanded dynamically during execution.

Design Constraints
------------------
• The transition table is private and must not be modified externally.
• `delta` is the only operational interface of the machine.
• The sets `states` and `symbols` are provided only for descriptive purposes.
• The machine is deterministic and single-tape.
• This implementation corresponds exactly to the verifier described in the
  formal construction (no preprocessing or input checking stage).
• The machine uses an explicit blank symbol distinct from the delimiter used in the input encoding.

Public Interface
----------------
    delta(state, symbol)  -> (next_state, write_symbol, move)
    states(m)             -> finite state set up to address bound m

The module therefore acts as a self-contained specification of the verifier TM
used in the feasible-graph simulation.
"""

_TRANSITIONS = {
        # Assign.Check
        ("Check",  "_"): ("Check", "_", +1),
        ("Check",  "-"): ("Not", "-", +1),
        ("Check",  "D"): ("Inc.D","?", +1),
        ("Not",  "D"): ("Inc.D","!", +1),
        ("Skip",  "&"): ("Check", "_", +1),
        ("Skip", "#"): ("Accept","_", +1),
        ("Skip", "*"): ("Skip", "_", +1),  
        ("Check", "&"):  ("Reject",  "_", +1),
        ("Check", "#"):  ("Reject",  "_", +1),


        # Assign.Inc
        ("Inc.N",  "_"): ("Forward.N", "_", +1),
        ("Inc.N",  "&"): ("Forward.N", "&", +1),
        ("Inc.N",  "#"): ("Dec.(N-1)", "#", +1),
        ("Inc.N",  "D"): ("Inc.(10N+D)", "_", +1),

        # Assign.Forward
        ("Forward.N",  "*"): ("Forward.N", "*", +1),
        ("Forward.N",  "#"): ("Dec.(N-1)",  "#", +1),

        # Assign.Dec
        ("Dec.N", "T"): ("Dec.(N-1)", "T", +1),
        ("Dec.N", "F"): ("Dec.(N-1)", "F", +1),
        ("Dec.0", "T"): ("Backward.T", "T", -1),
        ("Dec.0", "F"): ("Backward.F", "F", -1),

        # Assign.Backward
        ("Backward.T", "*"): ("Backward.T", "*", -1),
        ("Backward.F", "*"): ("Backward.F", "*", -1),
        ("Backward.T",  "?"): ("Skip", "_", +1),
        ("Backward.F", "?"): ("Check", "_", +1),
        ("Backward.T",  "!"): ("Check", "_", +1),
        ("Backward.F", "!"): ("Skip", "_", +1),
        
    }

symbols="_-&#TF?!0123456789"+"ϵ"
certSymbols="TF"
_STATES0=["Check","Not", "Skip", "Backward.T","Backward.F","Not",
        "Reject","Accept"]

BLANK = "ϵ"        # tape blank symbol (b)
DELIM = "_"        # structural separator in the encoding

INIT_STATE   = "Check"
ACCEPT_STATE = "Accept"
REJECT_STATE = "Reject"

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

        if next_state.endswith(".N"):
            next_state = next_state.replace(".N", "." + addr)

        elif next_state.endswith(".(N-1)"):
            next_state = next_state.replace(".(N-1)", "." + str(int(addr) - 1))

        elif next_state.endswith(".(10N+D)"):
            next_state = next_state.replace(
                ".(10N+D)", "." + str(int(addr) * 10 + int(symbol))
            )
        
        if next_state not in _states:
            return ("Reject", "_", -1)

        # --- Resolve output symbol ---
        if output == "*":
            output = symbol

        return (next_state, output, move)

    # --- No transition applicable ---
    return ("Reject", "_", -1)



