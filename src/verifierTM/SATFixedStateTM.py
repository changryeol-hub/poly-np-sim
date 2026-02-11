"""
Deterministic SAT Verifier Turing Machine (Fixed-State Version)

This module implements the fixed-state deterministic Turing machine used in the
paper to simulate a SAT verifier.  Unlike the input-dependent construction, the
state space is finite and independent of the instance size; arithmetic on
variable indices is performed symbolically on the tape.

Machine model
-------------
The machine follows the standard single-tape definition

    M = (Q, Γ, b, q0, δ, F)

where:

    δ            : implemented by `delta(state, symbol)`
    Q            : provided by `states`
    Γ            : provided by `symbols`
    b            : BLANK = "ϵ"
    q0           : INIT_STATE
    F            : {ACCEPT_STATE, REJECT_STATE}

Interface
---------
`delta` is the only operational interface.
The remaining exported objects (`symbols`, `states`, BLANK, INIT_STATE, etc.)
are descriptive components of the machine specification and are intended for
simulators or formal inspection.

Encoding conventions
--------------------
The blank symbol ϵ represents the infinite tape background.
The character '_' is NOT blank; it is a structural delimiter inside the input
encoding.

Purpose
-------
This machine serves as a comparison reference for the verifier construction
presented in the paper.  It explicitly performs certificate scanning,
literal evaluation, and backward propagation of assignments on the tape.
"""

_TRANSITIONS = {
        # Compute and Change leading 0 to _
        ("Check.S",  "_"): ("Check.S", "_", +1),
        ("Check.S",  "-"): ("CheckNot.S", "-", +1),
        ("Check.S",  "0"): ("Unknown.S","_", +1),
        ("Check.S", "D"): ("UnknownTerm.S", "D", +1),
        ("Check.S", "T"): ("Skip.S", "T", +1),
        ("Check.S", "F"): ("Check.S", "F", +1),
        ("Check.S", "&"):  ("Reject",  "_", +1),
        ("Check.S", "#"):  ("Reject",  "_", +1),
        
        ("CheckNot.S",  "_"): ("CheckNot.S", "_", +1), 
        ("CheckNot.S",  "T"): ("Check.S", "T", +1),
        ("CheckNot.S",  "D"): ("UnknownTerm.S","D", +1),
        ("CheckNot.S",  "0"): ("Unknown.S", "_", +1), 
        ("CheckNot.S",  "F"): ("Skip.S","F", +1),
        
        ("Unknown.S", "_"): ("Unknown.S", "_", +1),
        ("Unknown.S", "0"): ("Unknown.S", "_", +1),
        ("Unknown.S", "D"): ("UnknownTerm.S", "D", +1),        
        ("Unknown.S", "T"):("Skip.S", "T", +1),
        ("Unknown.S", "F"):("Unknown.S", "F", +1),
        ("Unknown.S", "-"):("UnknownNot.S","-", +1),
        ("UnknownTerm.S", "D"):("UnknownTerm.S", "D", +1),
        ("UnknownTerm.S", "_"):("Unknown.S", "_", +1),
        ("UnknownTerm.S", "&"):("Check.Free", "&", +1),
        ("UnknownTerm.S", "#"):("Fetch", "#", +1),

        ("UnknownNot.S", "T"):("Unknown.S", "T", +1),
        ("UnknownNot.S", "0"): ("Unknown.S", "_", +1),
        ("UnknownNot.S", "D"): ("UnknownTerm.S", "D", +1),
        ("UnknownNot.S", "F"):("Skip.S", "F", +1),
        ("UnknownNot.S", "_"):("UnknownNot.S", "_", +1),
        ("Unknown.S", "&"):("Check.Free", "&", +1),
        ("Unknown.S", "#"):("Fetch", "#", +1),
        
        ("Skip.Free", "&"): ("Check.Free", "&", +1),
        ("Skip.Free", "#"): ("Fetch","#", +1),
        ("Skip.Forwarded", "&"): ("Check.Forwarded", "&", +1),
        ("Skip.Forwarded",  "#"): ("Accept", "#", +1),
        ("Skip.S", "*"): ("Skip.S", "_", +1),

        
        # Check.Forwarded/Fetch
        ("Fetch",  "_"): ("Fetch", "_", +1),
        ("Fetch", "T"): ("Backward.T", "_", -1),
        ("Fetch", "F"): ("Backward.F", "_", -1),
        ("Ftech", "ϵ"): ("Reject", "ϵ", +1),
        
        
        # Backward
        ("Backward.B",  "ϵ"): ("Check.Forwarded", "ϵ", +1),
        ("BackwardInTerm.B",  "ϵ"): ("Check.Forwarded", "ϵ", +1),
        ("Backward.B", "*"):("Backward.B", "*", -1),
        ("BackwardInTerm.B",  "D"): ("BackwardInTerm.B", "D", -1),
        

        # Subtraction/Backward
        ("Backward.B", "1"): ("BackwardFrom1.B", "0", -1),
        ("Backward.B",  "0"): ("Borrow.B", "9", -1),
        ("Backward.B", "D"): ("BackwardInTerm.B", "D-1", -1),
        ("Borrow.B", "D"): ("BackwardInTerm.B", "D-1", -1),
        ("Borrow.B", "0"): ("Borrow.B", "9", -1),
        ("BackwardFrom1.B", "D"):("BackwardInTerm.B", "D", -1),        
        
        # Assign/Backward
        ("BackwardInTerm.B", "D"): ("BackwardInTerm.B", "D", -1),
        ("BackwardInTerm.B", "_"): ("Backward.B", "_", -1),
        ("BackwardInTerm.B", "&"): ("Backward.B", "&", -1),
        ("BackwardInTerm.B", "-"): ("Backward.B", "-", -1),
        ("BackwardFrom1.B", "_"):("Assign.B", "_", +1),
        ("BackwardFrom1.B", "-"):("Assign.B", "-", +1),
        ("BackwardFrom1.B", "&"):("Assign.B", "&", +1),
        ("BackwardFrom1.B", "ϵ"):("Assign.B", "ϵ", +1),
        ("Assign.B", "0"):("Backward.B", "B",-1), 
    }

symbols=list("_-&#TF0123456789"+"ϵ")
certSymbols="TF"
states=["Check.Free","CheckNot.Free","Unknown.Free", "UnknownNot.Free", "UnknownTerm.Free", "Skip.Free",
        "Check.Forwarded", "CheckNot.Forwarded", "Unknown.Forwarded", "UnknownNot.Forwarded","UnknownTerm.Forwarded", "Skip.Forwarded" ,
        "Fetch", "Backward.T","Backward.F","BackwardInTerm.T","BackwardInTerm.F",
        "Borrow.T","Borrow.F", "BackwardFrom1.T","BackwardFrom1.F","Assign.T","Assign.F","Reject","Accept"]


BLANK = "ϵ"        # tape blank symbol (b)
DELIM = "_"        # structural separator in the encoding

INIT_STATE   = "Check.Forwarded"
ACCEPT_STATE = "Accept"
REJECT_STATE = "Reject"        
        

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