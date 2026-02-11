"""
feasibleGraph.py

Purpose:
- Implements routines to compute the feasible subgraph of a dynamic computation graph (DCG),
  given a set of initial vertices (V0) and final edges (Ef).
- Feasible edges are determined by ceiling/cover adjacency, tier constraints, and index-based propagation.
- Supports stepwise upward and downward edge expansion to ensure all edges in the feasible graph
  maintain consistency with the original computation walk structure.

Main Functions:
- ComputeCoverEdges(G, Ef): Computes the set of cover edges starting from Ef using weak ceiling adjacency
  and path existence checks.
- ComputeFeasibleGraph(G, V0, Ef): Computes the feasible graph by sweeping edges iteratively
  from left-to-right and right-to-left, updating edges according to StepUp and StepDown propagation.
- SweepEdges(G, C, V0, Ef, i, d): Performs a directional sweep across edges of index i in direction d,
  updating feasible edges in H.
- StepUpEdges(G, H, Es, Hs, V0, Ef): Expands edges upward from a set of floor edges, adding edges
  that are consistent with adjacency and index-predecessor conditions.
- StepDownEdges(G, H, I, C): Expands edges downward from a set I, adding edges that are in the cover set C.

Usage:
- Intended to be used with dynamicComputationGraph.py to generate feasible graphs for NP-verifier
  simulations or other deterministic walk verification procedures.
- Works in conjunction with verificationWalk.py to verify existence of feasible walks.
- Supports debug printing to trace edge propagation and feasible graph construction.

Notes:
- Edge propagation uses index-predecessor/index-successor relations and index adjacency to ensure correctness.
- The feasible graph is updated iteratively until a fixed point is reached (no change in graph size).
- Designed for research-level simulations of deterministic NP-verifier algorithms.

Dependencies:
- dynamicComputationGraph.py
- log_ext.py
- collections
"""

from . import dynamicComputationGraph as dcg
import collections
from .log_ext import *
log=get_logger(__name__)

def ComputeCoverEdges(G,Ef):
    C = set()
    for u,v in Ef: C.add((u,v))
    Q = collections.deque(Ef)
    while len(Q)>0:
        f=Q.popleft()
        Ec=dcg.GetWeakCeilingAdjacentEdges(G,f, Ef)
        for e in Ec:
            u,v=e; 
            if e in C: continue
            if dcg.areAdjacent(e, f) or G.existsPathAvodingStartIndex(e,f):
                C.add(e); Q.append(e)
    return C
    
def ComputeFeasibleGraph(G, V0,Ef):     #▷ G: non-empty computation graph
    log.log(VERBOSE,f"\t\tStart feasible graph |E(G)|={G.size()} with respect to {Ef}")                             
    C = ComputeCoverEdges(G,Ef )        #▷ Initialize cover edge set from final edges
    H=G; n=0                            #▷ Initialize feasible graph as the input graph
    log.log(VERBOSE,f"\t\tCover Edge Computed |C|={len(C)} with respect to {Ef}")  
    while H.size()>0 and n!=H.size():   #▷ Repeat until no change occurred or the graph becomes empty
        n = H.size()#▷ Number of edges before sweep
        i = H.minEdgeIndex()
        log.log(VERBOSE,f"\t\tBefore Sweep from left to right; minIndex, |E(H)|:{i},{H.size()}")
        H = SweepEdges(H,C, V0,Ef , i, +1)  #▷ Update the graph by sweeping edges from left to right
        if H.size()==0: return H
        i = H.maxEdgeIndex()
        log.log(VERBOSE,f"\t\tBefore Sweep from right to left; maxIndex, |E(H)|:{i},{H.size()}")
        H = SweepEdges(H,C, V0,Ef , i,-1)   #▷ Update the graph by sweeping edges from right to left
    log.log(VERBOSE,f"Feasible Graph computed:{H.size()}")
    return H   
 
def SweepEdges(G,C, V0,Ef, i, d):
    H = dcg.DynamicComputationGraph()   #▷ Initialize empty graph to store feasible edges

    Ei=G.E[i]
    log.log(VERBOSE,f"Start SweepEdges: i={i}, |E(G)|={G.size()}, |E(H)|={H.size()}")
    while Ei.size()>0:                   #▷ While there are edges in G with index i
        Ej=H.E[i-d]
        I = StepUpEdges(G,H,Ei, Ej, V0, Ef)    #▷ Expand edges upward from previous index layer
        log.log(VERBOSE,f"Before StepDownEdges i={i}, |E(G)|={G.size()}, |E(H)|={H.size()}")
        H = StepDownEdges(G, H, I,C)           #▷ Add edges downward to form feasible graph
        log.log(VERBOSE,f"After StepDownEdges i={i}, |E(G)|={G.size()}, |E(H)|={H.size()}")
        i = i + d                           #▷ Move to the next index in direction d
        Ei=G.E[i]
    log.log(VERBOSE,f"End SweepEdges i={i}, |E(G)|={G.size()}, |E(H)|={H.size()}")
    return H

def StepDownEdges(G, H, I, C):
  
    Q= collections.deque()
    for e in I:
        if e in C: Q.append(e)
    Ev = set(); I_=set()
     
    log.log(VERBOSE,f"Start of StepDownEdges: |I|={len(I)}, |E(H)|={H.size()}")
    while len(Q)>0:                         #▷ Step downward
        e=Q.popleft(); Ev.add(e)
        I_.add(e)
        Q.extend((G.GetIPrecedents(e)& I)-Ev)       #Enqueue all the edges of IPrecI (e) \ Ev to Q
    for f in I_: H.addEdge(f)
    log.log(VERBOSE,f"End of StepDownEdges: |I'|={len(I_)}, |E(H)|={H.size()}")
    return H

def StepUpEdges(G, H, Es, Hs, V0, Ef ):     #▷ E ⊂ E(G)
    Eb=Es.getFloorEdges()                   #▷ all the edges e = (u, v) ∈ E such that tier(v) = 0)
    Q= collections.deque(Eb)                #▷ Add all floor edge first,
 
    Ev=set(); I = set()
    log.log(VERBOSE,f"Strat of StepUpEdges i={Es.index}, (Floor Edge Size)=: {len(Eb)}")
    while len(Q)>0:         #▷ Step upward
        e=Q.popleft();
        Ev.add(e)
        if dcg.IsIndexAdjacent(G, e, Hs, Ef, V0):
            I.add(e) 
            S=G.GetISuccedents(e)
            Q.extend(G.GetISuccedents(e)-Ev)
    log.log(VERBOSE,f"End of StepUpEdges i={Es.index}, |I|={len(I)}.")

    return I

