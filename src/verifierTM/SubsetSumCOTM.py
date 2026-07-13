"""
Deterministic certificate-oblivious Turing Machine for Subset-Sum (base-10 arithmetic version)

This module implements the concrete verifier machine used in the paper for the
Subset-Sum language.  The machine decides whether a given certificate encodes a
subset whose decimal sum equals the target value encoded in the input.

──────────────────────────────── Model Overview ────────────────────────────────
The tape encoding is divided into structured regions separated by delimiters.

    [target sum] @ [set elements] # [cerificates]

The machine repeatedly:
1. Selects a number from the multiset
2. Matches its digits against the certificate marks, unused elements (xxx) are replaced 0
3. Subtracts the number from the target sum (decimal subtraction with borrow)
4. Deletes the matched number
5. Continues until either the sum becomes 0 (accept) or mismatch occurs (reject)

All arithmetic is performed directly on the tape using digit-wise subtraction
and explicit borrow propagation.

──────────────────────────────── Alphabet ───────────────────────────────────────
BLANK = ϵ     : tape blank symbol
DELIM = _     : structural delimiter in encoding

Digits appear in two forms:
    0–9       : numeric value in the running sum
    ⓪–⑨       : marked digits belonging to a chosen subset element

Markers:
    |   : matched position marker
    ~   : erased digit placeholder
    $   : subtraction trigger
    @   : separator before sum area
    x   : represents unused elements for the sum
    #   : beginning of instance

Meta-symbols used only in transition patterns:
    M, D, Ⓜ, Ⓓ : parameterized digit classes

──────────────────────────────── States ─────────────────────────────────────────
INIT_STATE   = "Forward"
ACCEPT_STATE = "Accept"
REJECT_STATE = "Reject"

The machine operates in phases:

Forward scanning
    Locate next candidate number and digit to match

Matching phase
    FindDigitToMatch
    BackwardToMatch.k
    MatchPosition.k

Intermediate phase
    BackwardAfterMatching

Subtraction phase (decimal subtraction)
    ForwardToSubtract/BackwardToRestore
    BackwardToSubtract.k
    SumArea.k
    Subtract.k
    Borrow.0 / Borrow.1

Final validation
    CheckSum → Accept iff sum becomes 0

Parameterized states ".k" represent digit-indexed operations during matching
and subtraction.

────────────────────────────── Operational Interface ───────────────────────────
delta(state, symbol) → (next_state, write_symbol, head_move)

This is the only operational interface of the machine.
The simulator must provide the tape, head position, and halting detection.

symbols and states are exported only for simulator construction and validation;
they are not part of the transition semantics.
"""


_TRANSITIONS = {
        #Find the digit to match           
        ("Forward", "#"):("FindDigitToMatch", "#", +1),
        ("Forward", "*"):("Forward", "*", +1),
        ("FindDigitToMatch", "~"):("FindDigitToMatch", "~", +1),
        ("FindDigitToMatch", "M"):("BackwardToMatch.M", "~", -1),
        ("FindDigitToMatch", "_"):("BackwardToMatch.Delim", "~",-1),
        ("FindDigitToMatch", "x"):("BackwardToMatch.X", "~",-1),
        ("FindDigitToMatch", "*"):("Rejct", "~",-1),
        ("FindDigitToMatch", "ϵ"):("BackwardAfterMatching", "ϵ", -1),
     
        # match the single digit       
        ("BackwardToMatch.M", "*"): ("BackwardToMatch.M", "*", -1),
        ("BackwardToMatch.X", "*"): ("BackwardToMatch.X", "*", -1),
        ("BackwardToMatch.Delim", "*"): ("BackwardToMatch.Delim", "*", -1),
        ("BackwardToMatch.M","|"):("MatchPosition.M","_", +1),
        ("BackwardToMatch.M", "Ⓓ"):("MatchPosition.M","D", +1),
        ("BackwardToMatch.M", "x"):("Reject", "_", +1),
        ("BackwardToMatch.M", "@"):("MatchPosition.M", "@",+1),

        ("BackwardToMatch.Delim","|"):("MatchPosition.Delim","_", +1),
        ("BackwardToMatch.Delim", "Ⓓ"):("MatchPosition.Delim","D", +1),
        ("BackwardToMatch.Delim", "x"):("MatchPosition.Delim","0", +1),
        ("BackwardToMatch.Delim", "@"):("MatchPosition.Delim","@", +1),
        ("BackwardToMatch.X","|"):("MatchPosition.X","_", +1),
        ("BackwardToMatch.X", "Ⓓ"):("Reject","_", +1),
        ("BackwardToMatch.X", "x"):("MatchPosition.X","0", +1),
        ("BackwardToMatch.X", "@"):("MatchPosition.X","@", +1),
        
        ("MatchPosition.Delim", "_"):("Forward","|", +1),
        ("MatchPosition.M", "M"):("Forward","Ⓜ", +1),
        ("MatchPosition.X", "D"):("Forward","x", +1),

        ("BackwardToSubtract.M", "*"):("BackwardToSubtract.M", "*", -1),
        ("ForwardToSubtract",'$'):("SbtractionDigit", "~",-1),
        ("ForwardToSubtract",'*'):("ForwardToSubtract", "*",+1),
        
        # Subtract digits after matching confired.
        ("BackwardToSubtract.M",'@'):("SumArea.M", "@",-1),
        ("SbtractionDigit", "M"):("BackwardToSubtract.M", "$", -1),
        ("SbtractionDigit", "_"):("BackwardToRestore", "$", -1),
        ("SbtractionDigit", "@"):("CheckSum", "@", -1),

        # Remove Matched Number and Recover Symbol After matching
        ("BackwardAfterMatching", "*"):("BackwardAfterMatching", "*", -1),
        ("BackwardAfterMatching", "Ⓜ"):("BackwardToSubtract.M", "$", -1),
        ("BackwardAfterMatching", "x"):("BackwardToSubtract.0", "$", -1),
        ("BackwardToRestore", "Ⓓ"):("BackwardToRestore", "D", -1),
        ("BackwardToRestore", "|"):("BackwardToRestore", "_", -1),
        ("BackwardToRestore", "*"):("BackwardToRestore", "*", -1),
        ("BackwardToRestore","ϵ"):("ForwardToSubtract", "ϵ", +1),

        #Check Sum 0
        ("CheckSum", "|"): ("CheckSum", "_", -1),
        ("CheckSum", "0"): ("CheckSum", "_", -1),
        ("CheckSum", "⓪"): ("CheckSum", "_", -1),
        ("CheckSum", "*"): ("Reject", "_", -1),
        ("CheckSum", "ϵ"): ("Accept", "_", +1),
        
        #Subtract matched number
        ("SumArea.M", "D"): ("SumArea.M", "D", -1),
        ("SumArea.M", "|"): ("SumArea.M", "|", -1),
        ("SumArea.M", "_"): ("Subtract.M", "|", -1),
        ("SumArea.M", "Ⓓ"): ("Subtract.M", "D", -1),
        ("Subtract.M", "D"): ("Borrow.B", "Ⓓ-Ⓜ", -1),   #B: !- Borrow: _, No Borrow

        ("Subtract.0", "ϵ"): ("ForwardToSubtract", "ϵ", +1),
        ("Borrow.0", "ϵ"):("ForwardToSubtract", "ϵ", +1),
        ("Borrow.1", "ϵ"):("Reject", "~", +1),
        
        ("Borrow.0","D"):("Borrow.0", "D", -1),
        ("Borrow.0","*"):("Reject", "~", -1),
        ("Borrow.1", "0"):("Borrow.1", "9", -1),
        ("Borrow.1", "D"):("Borrow.0", "D-1", -1),
        ("Borrow.1","*"):("Reject", "~", -1),
    }
    
BLANK = "ϵ"        # tape blank symbol (b)
DELIM = "_"        # structural separator in the encoding

INIT_STATE   = "Forward"
ACCEPT_STATE = "Accept"
REJECT_STATE = "Reject"

certSymbols="_0123456789x"
inputSymbols=list("#_@0123456789x")
symbols=inputSymbols+list("⓪①②③④⑤⑥⑦⑧⑨|$~ϵ")

states=["Forward", "FindDigitToMatch", "ForwardToSubtract", 
        "BackwardAfterMatching", "BackwardToRestore",
        "BackwardToMatch.Delim", "BackwardToMatch.X",
        "MatchPosition.Delim", "MatchPosition.X",         
        "SbtractionDigit", "CheckSum","Borrow.0", "Borrow.1",
        "Reject","Accept"]
        
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
    
    
def _tryTransition(TRANSITIONS, state, altstate, addr, symbol, s):
    M=D=None
    if (state, s) in TRANSITIONS:
        (next_state,output,move)=TRANSITIONS[(state, s)]
    elif (altstate, s) in TRANSITIONS:
        if altstate.endswith(".M") and s=='M':
            if addr!=symbol: return None
        (next_state,output,move)=TRANSITIONS[(altstate, s)]
        if altstate.endswith("M") and addr.isdecimal():
            M=int(addr)                          
    else: return None
    
    if s=='M' and symbol.isdecimal():
        M=int(symbol)
    elif s=='Ⓜ' and (symbol=='⓪' or ('①'<=symbol<='⑨')): 
        M=0 if symbol=='⓪' else ord(symbol)-ord('①')+1    
    elif s=='D' and symbol.isdecimal():
        D=int(symbol)
    elif s=='Ⓓ' and (symbol=='⓪' or ('①'<=symbol<='⑨')):
        D=0 if symbol=='⓪' else ord(symbol)-ord('①')+1   
        
    if next_state.endswith('M') and M is not None:
        next_state=next_state.replace(".M","."+str(M))
    elif next_state.endswith('B') and  output=="Ⓓ-Ⓜ" and D is not None and M is not None:
        n=(10+D-M)%10; B=1 if D-M<0 else 0
        output='⓪' if n==0 else chr(ord('①')+n-1)
        next_state=next_state.replace(".B", "."+str(B))
        return (next_state,output,move)
    
    if output=="Ⓜ":
        output='⓪' if M==0 else chr(ord('①')+int(M)-1)
    elif output=='D' and D is not None:
        output=str(D)
    elif output=="D-1" and D is not None:
        output=str(D-1)
    elif output=="Ⓓ" and D is not None:
        output='⓪' if D==0 else chr(ord('①')+D-1)
    
    elif output=="*": output=symbol
       
    assert output not in('Ⓜ','Ⓓ','D','M'), f"{state}, {symbol}, {addr}, {altstate}, {output}"
    return (next_state,output,move)

_DELTA=dict()

def delta(state,symbol):
    if (state,symbol) in _DELTA: return _DELTA[(state,symbol)]
    action=state; addr=""; altsymbol=""; altstate=""
    if '.' in state:
        (action,addr)=state.split('.')
        if addr.isdecimal(): altstate=action+".M"
    symbols=[symbol]
    if symbol.isdecimal(): symbols+=['M','D']
    elif  symbol=='⓪' or ('①'<=symbol<='⑨'): symbols+=['Ⓜ','Ⓓ']
    symbols.append('*')

    for s in symbols:
        result=_tryTransition(_TRANSITIONS, state, altstate, addr, symbol, s)
        if result is not None:
            _DELTA[(state,symbol)]=result
            return result
    
    _DELTA[(state,symbol)]=("Reject","_",+1)
    return ("Reject","_",+1)
    



