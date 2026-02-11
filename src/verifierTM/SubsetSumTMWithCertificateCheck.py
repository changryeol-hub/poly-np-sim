"""
Deterministic Turing Machine for Subset-Sum with Input Validation Phase

This module specifies the concrete verifier machine used in the feasible-graph
simulation framework for the Subset-Sum language.  Compared to the base machine,
this version includes an explicit input-sanity phase (InputCheck) ensuring the
certificate region is well-formed before arithmetic verification begins.

──────────────────────────────── Overall Behaviour ─────────────────────────────
The machine decides whether the certificate encodes a subset of the given
multiset whose decimal sum equals the target value.

Execution proceeds in two logically separated stages:

1) Input validation
   Ensures the certificate region contains only digits and delimiters and
   returns the head to the beginning of the instance.

2) Arithmetic verification
   Iteratively:
      • select a marked element
      • match its digits
      • subtract it from the running sum
      • delete the element
   Accept iff the running sum becomes zero.

──────────────────────────────── Tape Structure ─────────────────────────────────
The encoding divides the tape into structured zones:

    # <numbers> @ <target-sum> ; <workspace>

Markers and working symbols are introduced during execution and later removed.

BLANK = ϵ     : tape blank
DELIM = _     : structural delimiter

Important markers
    |  matched position
    ~  erased digit placeholder
    $  subtraction trigger
    @  separator before sum area
    ;  end of number list

Digit representations
    0–9       : numeric digits in the running sum
    ⓪–⑨       : digits belonging to a chosen subset element

Meta-classes (transition patterns only)
    D, M, Ⓓ, Ⓜ : digit categories used for parameterized transitions

──────────────────────────────── State Phases ───────────────────────────────────

Input validation phase
    InputCheck → CertificateCheck → BackToBeginning → Forward

Matching phase
    Forward → FindDigitToMatch → BackwardToMatch.k → MatchPosition.k

Verification phase
    BackwardToCheckMatch → MatchedDigits

Arithmetic subtraction (decimal with borrow)
    BackwardToSubtract.k → SumArea.k → Subtract.k → Borrow.{0,1}

Final validation
    BackwardToCheckSum → CheckSum → Accept / Reject

Parameterized states ".k" denote digit-indexed operations.

────────────────────────────── Operational Interface ───────────────────────────
delta(state, symbol) → (next_state, write_symbol, head_move)

This is the only operational interface required by the simulator.

The exported alphabets and state lists exist only for machine construction and
consistency checking and are not part of the transition semantics.
"""

#from .SubsetSumTM import _TRANSITIONS as _BASE_TRANSITIONS
from . import SubsetSumTM as baseTM

_BASE_TRANSITIONS = baseTM._TRANSITIONS

_INPUTCHECK_TRANSITONS = {
        ("InputCheck", "#"): ("CertificateCheck", "#", +1),
        ("InputCheck", "*"): ("InputCheck", "*", +1),
        ("CertificateCheck", "D"):("CertificateCheck", "D", +1),
        ("CertificateCheck", "_"):("CertificateCheck", "_", +1),
        ("CertificateCheck", ";"):("BackToBeginning", ";", -1),
        ("CertificateCheck", "*"):("Reject", "_", -1),
        ("BackToBeginning", "*"):("BackToBeginning", "*", -1),
        ("BackToBeginning", "ϵ"):("Forward", "ϵ", +1),      
}
    
_TRANSITIONS= _BASE_TRANSITIONS | _INPUTCHECK_TRANSITONS 

BLANK = "ϵ"        # tape blank symbol (b)
DELIM = "_"        # structural separator in the encoding

INIT_STATE   = "InputCheck"
ACCEPT_STATE = "Accept"
REJECT_STATE = "Reject"

_INPUTCHECK_STATES = [
    "InputCheck",
    "CertificateCheck",
    "BackToBeginning",
]

certSymbols=";_0123456789"
symbols=list("#$;|_~@0123456789⓪①②③④⑤⑥⑦⑧⑨"+"ϵ")
states=["Forward","FindDigitToMatch", "SbtractionDigit","DigitToMatch","CheckMatchBackward","MatchedDigits","BackwardAfterMatching",
        "Forward","CheckForward","BackwardToCheckMatch", "CheckSum","BackwardToCheckSum","Borrow.0", "Borrow.1",
        "Reject","Accept"]+_INPUTCHECK_STATES 
        
for i in range(0,10): 
    states.append("Backward"+"."+str(i))
    states.append("BackwardToMatch"+"."+str(i))
    states.append("MatchPosition"+"."+str(i))
    states.append("BackwardToSubtract"+"."+str(i))
    states.append("SumArea"+"."+str(i))
    states.append("Subtract"+"."+str(i))

for key in _TRANSITIONS:
    state, symbol=key
    state=state.replace(".M",".1")
    if state not in states: assert False, state

def delta(state,symbol):
    action=state; addr=""; altsymbol=""; altstate=""
    if '.' in state:
        (action,addr)=state.split('.')
        if addr.isdecimal(): altstate=action+".M"
    symbols=[symbol]
    if symbol.isdecimal(): symbols+=['M','D']
    elif  symbol=='⓪' or ('①'<=symbol<='⑨'): symbols+=['Ⓜ','Ⓓ']
    symbols.append('*')


    for s in symbols:
        result=baseTM._tryTransition(_TRANSITIONS, state, altstate, addr, symbol, s)
        if result is not None:
            return result
        
    return ("Reject","_",-1)
    



