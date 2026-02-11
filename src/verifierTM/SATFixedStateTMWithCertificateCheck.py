"""
Deterministic SAT Verifier Turing Machine (Input-Checking Variant)

This module defines the deterministic single-tape Turing machine used in the
paper as the *input-validated* version of the fixed-state SAT verifier.  It
extends the base verifier machine with a preliminary certificate format check
before evaluation begins.

Formal model
------------
The machine corresponds to

    M = (Q, Γ, b, q0, δ, F)

where:

    δ : implemented by `delta(state, symbol)`
    Q : `states`
    Γ : `symbols`
    b : BLANK = "ϵ"
    q0: INIT_STATE
    F : {ACCEPT_STATE, REJECT_STATE}

Interface
---------
`delta` is the only operational interface of the machine.
All other exported objects (`states`, `symbols`, BLANK, INIT_STATE, etc.)
describe the formal specification and are intended for simulators or analysis.

Structure
---------
The transition function is composed of two layers:

    _BASE_TRANSITIONS        – core SAT verification procedure
    _INPUTCHECK_TRANSITIONS  – certificate format validation

They are merged into `_TRANSITIONS`, yielding a machine that first verifies the
well-formedness of the input and then performs deterministic evaluation.

Encoding conventions
--------------------
ϵ : true tape blank symbol (background of the infinite tape)
_ : structural delimiter inside the encoded instance (not blank)

Purpose
-------
This machine is provided as a comparison reference showing the original verifier
including explicit input validation.  The paper later removes this phase to
demonstrate that the verification procedure itself does not depend on the
pre-checking stage.
"""

from . import SATFixedStateTM as baseTM
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
        ("BackToBeginning", "ϵ"):("Check.Forwarded", "ϵ", +1),   
}

_TRANSITIONS= _BASE_TRANSITIONS | _INPUTCHECK_TRANSITONS 

BLANK = "ϵ"        # tape blank symbol (b)
DELIM = "_"        # structural separator in the encoding

INIT_STATE   = "InputCheck"
ACCEPT_STATE = "Accept"
REJECT_STATE = "Reject"

symbols=list("_-&#TF0123456789"+"ϵ")

_INPUTCHECK_STATES = [
    "InputCheck",
    "CertificateCheck",
    "BackToBeginning",
]

states=["Check.Free","CheckNot.Free","Unknown.Free", "UnknownNot.Free", "UnknownTerm.Free", "Skip.Free",
        "Check.Forwarded", "CheckNot.Forwarded", "Unknown.Forwarded", "UnknownNot.Forwarded","UnknownTerm.Forwarded", "Skip.Forwarded" ,
        "Fetch", "Backward.T","Backward.F","BackwardInTerm.T","BackwardInTerm.F",
        "Borrow.T","Borrow.F", "BackwardFrom1.T","BackwardFrom1.F","Assign.T","Assign.F","Reject","Accept"] + _INPUTCHECK_STATES

def delta(state,symbol):
    action=state; sub=""; altsymbol=""; altstate=""
    if '.' in state:
        (action,sub)=state.split('.')
        if sub.isdigit(): altstate=action+".D"
        elif sub in "TF": altstate=action+".B"
        else: altstate=action+".S"
    symbols=[symbol]
    if symbol.isdigit():
        symbols.append('D')
    elif symbol in 'TF': 
        symbols.append('B')
    symbols.append('*')
    for s in symbols:
        if (state, s) in _TRANSITIONS:
            (next_state,output,move)=_TRANSITIONS[(state, s)]
        elif altstate is not None and (altstate, s) in _TRANSITIONS:
            (next_state,output,move)=_TRANSITIONS[(altstate, s)]
            if altstate.endswith(".B") and next_state.endswith(".B"): next_state=next_state.replace(".B","."+sub)
            if altstate.endswith(".B") and output=="B" and sub in 'TF': output=sub
        else: continue

        if next_state.endswith(".B") and symbol in 'TF': next_state=next_state.replace(".B","."+symbol)
        elif next_state.endswith(".S") : next_state=next_state.replace(".S","."+sub)
        if output=='D' and symbol.isdigit(): output=symbol
        elif output=="D-1" and symbol.isdigit(): output=str(int(symbol)-1)
        if output=="*": output=symbol

        return (next_state,output,move)
    
    return ("Reject","_",+1)