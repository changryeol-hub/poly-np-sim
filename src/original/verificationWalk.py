"""
verificationWalk.py

Purpose:
- Provides routines for verifying the existence of a computation walk within a dynamic computation graph (DCG),
  as part of deterministic NP-verifier simulations.
- Handles computing-targeted/redundant/futile edges to determine whether a valid computation path exists
  from a set of initial vertices (V0) to a given target edge (et).

Main Functions:
- ExtendFutileWalks(G_U, G, Eo, Ef): Ensures that computing-futile walks are represented in the graph by adding
  their final edges prior to pruning.
- FindFirstSplittingEdgeOrFinalEdge(G, W): Finds the first splitting edge in a walk or returns the final edge.
- PruneWalk(G_U, G, V0, et, W, preserveFutile): Prunes a given walk by removing non-essential edges and
  recomputing the feasible graph.
- TakeArbitraryWalk(G, V0): Extracts an arbitrary walk from the graph starting from initial vertices V0.
- FindDisjointEdge(R, W): Finds an edge in a walk W that is disjoint from the reference graph R.
- FindTargetRedundantFutileEdge(G_U, G, V0, et): Iteratively finds either a computing-targeted edge, 
  a computing-redundant edge, or computing-futile edge for verification purposes.
- VerifyExistenceOfWalk(G_U, V0, et): Main routine that verifies whether a feasible computation walk exists
  from the initial vertices V0 to the specified target edge et.

Usage:
- Intended to work together with dynamicComputationGraph.py and feasibleGraph.py.
- Can be used to simulate NP verifier computation paths, prune non-feasible walks, and confirm
  deterministic feasibility of walks in polynomial time.

Notes:
- Makes extensive use of feasible graph computation, predecessor/successor tracking, and walk pruning.
- Designed for research-level simulations of deterministic NP-verifier algorithms.
- Maintains internal counters for statistics on pruning, removed edges, and extended walks.
- Walk selection is deterministic but arbitrary, typically taking the first available edge at each step.

Dependencies:
- dynamicComputationGraph.py
- feasibleGraph.py
- log_ext.py
- collections
"""

from . import feasibleGraph as fg
from . import dynamicComputationGraph as dcg
import collections
from .log_ext import *
log=get_logger(__name__)

def ExtendFutileWalks(G_U, G, Eo, Ef):
    m=G_U.minEdgeIndex(); M=G_U.maxEdgeIndex()
    for i in range(m,M+1):
      for e in G_U.E[i].getAllEdges():
        u,v=e
        Vf=list(map(lambda f:f[1],Ef))
        if not G.hasEdge(e) and u not in Vf:
            if G.hasIncomingEdge(u) and (v.tier()==0 or len(G.GetIPrecedents(e))>0):
                G.addEdge(e)
                Eo.add(e)

def FindFirstSplittingEdgeOrFinalEdge(G, W):
    i=0;e=W[i]
    while i<len(W)-1:
        if G.isSplittingEdge(e):
            log.log(VERBOSE,"First Splitting Edge:",e)
            return e
        i=i+1;e=W[i]
    log.log(VERBOSE,"No splitting edge, Final Edge Returned.",e)
    return e        # ▷ It returns final edge of computation walk if no splitting edge found

def PruneWalk(G_U, G, v0, et, W, preserveFutile):
    Eo=set(); Ef={et}; V0={v0}
    e_ = FindFirstSplittingEdgeOrFinalEdge(G,W)
    if preserveFutile:
        ExtendFutileWalks(G_U, G, Eo, Ef) #▷ Add the end of computing-futile edge to final edges

    G_U.cntPrunedWalk+=1
    log.log(VERBOSE,f"\t\tBefore Walk prunded edge by {e_}. preserveFutileWalk:{preserveFutile} |E(G)|={G.size()}")

    G.removeEdge(e_)
    G_ = fg.ComputeFeasibleGraph(G, V0, Eo|Ef)           # ▷ Remove e′ from feasible graph
    if preserveFutile: log.debug(f"\t\tWalk has been pruned by edge {e_}. |E(G')| with extended edges={G_.size()}")
    G.addEdge(e_)             # This is required to restrore original graph     
    
    for e in Eo: G.removeEdge(e)  # This is also required to restrore original graph(G is regarded as input parameter).     
    
    if G_.size()>0:
        for e in Eo:
            if G_.hasEdge(e): G_.removeEdge(e)        #G[E(G)-Eo]
    log.debug(f"\t\tWalk has been pruned by edge  {e_}. preserveFutileWalk:{preserveFutile} Size Decreased(|E(G)| -> |E(G')|={G_.size()}")
    return G_

def TakeArbitraryWalk(G, v0):       # ▷Take Arbitrary Walk from Start Nodes ▷ Any consistent choice (e.g., always first edge) works; result is deterministic
    S =dcg.CellArray()              # ▷ Empty Surface
    ES=[]
    ES.extend(G.outgoingEdgeOf(v0))        # ▷ NextG(v0)
    if len(ES)==0:
        log.warning("The initial edge is missing. Empty walk returned!")
    
    e=ES[0] if len(ES)>0 else None
    W=[]
    while e is not None:
        u,v=e
        S[u.index()]=u.T            # ▷ Update surface S[index(u)] with the transition case to which node u belongs
        W.append(e)
        next_index=v.next_index()
        EN=list(filter(lambda f:(S[next_index] is None and f[1].tier()==0) 
                        or G.IPrecedent(f[1])==S[next_index], G.getNextEdges(e)))
        e=EN[0] if len(EN)>0 else None
    return W

def FindDisjointEdge(R, G):          # ▷ Find disjoint edge of W from R
    i=0
 
    while i<len(R):     # For all edge of walk
        u,v=e=R[i]
        if not G.hasEdge(e):
            EN=G.outgoingEdgeOf(u)
            if len(EN)==0: return None
            log.debug(f"DisjointEdge Detected:{EN[0]}")
            return EN[0]
        i+=1;
    log.debug(f"No disjoint edge exists. |R|={len(R)}, |G|={G.size()}")
    return None         # All the walk is Futile walk.


def FindTargetRedundantFutileEdge(G_U, G, v0, et): # v0:initial node of walks, et : the verification target edge
    Ef = {et }                                  # ▷ Ef : set of verification target edges
    log.debug(f"\tStart to Find Target/Redundant/Futile Edge. |E(G)|={G.size()}")   
    while G.size()>0:                           # Loop until graph empty or a computing-targeted walk is found
        W = TakeArbitraryWalk(G, v0)            # ▷ W is either a computing-tareted or a computing-futile walk
        if len(W)==0: return None
        if et==W[len(W)-1] or et in W:    # ▷ et is not always at the end of W
            return et                      # ▷ et is a verifiation target edge    
        else:                        # ▷ W can be computing-embedded walk               
            H=PruneWalk(G_U, G, v0, et, W, False)
            if H.size()==0:          # ▷ After total collapse               
                G=PruneWalk(G_U, G, v0, et, W, True)
                f=FindDisjointEdge(W,G)        # R=W
                log.log(VERBOSE,"Find Disjoint Edge.", f)
                return f 
            else: G=H          
    log.log(VERBOSE,"Pruned to size 0")
    return None
    
    
def VerifyExistenceOfWalk(G_U, v0, et): 

    log.log(VERBOSE,f"Verifying walk edges et:{et}")
    
    Ef = {et }; V0={v0}
    G = fg.ComputeFeasibleGraph(G_U, V0, Ef)
    log.log(VERBOSE,f"After Initial feasible graph et:{et}")
   
    log.debug(f"Start to Verify walk. Orginal Graph G_U -> Feasible Graph G: {G_U.size()} -> {G.size()}")
    while G.size()>0:    
        e=FindTargetRedundantFutileEdge(G_U, G, v0, et)
        log.log(VERBOSE,f"FindTargetRedundantFutileEdge:{e}")
        if e in Ef:
            log.log(VERBOSE,f"Walk Verified ending at {e}")
            return True
        elif e is None:
            log.log(VERBOSE,f"Walk not verified NIL returned.")
            return False
        G_U.cntRemovedRedundantFutileEdge+=1
        G.removeEdge(e)
        G = fg.ComputeFeasibleGraph(G, V0, Ef)
        log.debug(f"\tRemoved disjoint edge:{e} Size Decreased(G_U->G):{G_U.size()}->{G.size()}")
    log.log(VERBOSE,"No walk! empty feasible graph!")
    return False







    

