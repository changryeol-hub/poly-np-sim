"""
verificationWalk.py

Purpose:
- Provides routines for verifying the existence of a computation walk within a dynamic computation graph (DCG),
  as part of deterministic NP-verifier simulations.
- Handles computing-targeted/redundant/futile edges to determine whether a valid computation path exists
  from a set of initial vertices (V0) to a given target edge (et).

Main Functions:
- ExtendFutileWalks(G_U, G, V0): Ensures that computing-futile walks are represented in the graph by adding
  their final edges prior to pruning.
- FindFirstMergingEdgeOrFinalEdge(G, W): Finds the first merging edge in a walk or returns the final edge.
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


def ExtendFutileWalks(G_U,G, V0):  #It should be caculated at first time before pruned
    T=collections.deque()
    for v0 in V0: T.extend(G.outgoingEdgeOf(v0))
    Eo=set()
    Ev=set()
    while len(T)>0:
        e=T.pop()
        if e in Ev: continue
        Ev.add(e)
        if G.hasEdge(e):
            T.extend(G_U.getNextEdges(e))
        elif e[1].tier()>0 and G.CountIPrecedents(e)>0:
            G.addEdge(e)
            Eo.add(e)           #IPrecedents() is verified when computing feasible graph
    return Eo 


def FindFirstMergingEdgeOrFinalEdge(G,W):
    i=0;e=W[i]
    log.log(VERBOSE, f"\t\t\tFind First Merging/Final Edge with length of W:{len(W)}")
    while i<len(W)-1:
        if G.isMergingEdge(e):
            log.log(VERBOSE, f"\t\t\tFirst Merging Edge:{e}")
            return e
        i=i+1;e=W[i]
    log.log(VERBOSE, f"No merging edge, Final Edge Returned. {e}")
    return e    # ▷ It returns final edge of computation walk if no mergin edge found

def PruneWalk(G_U,G,V0,et,W, preserveFutile):
    Eo=set(); Ef={et}
    e_ = FindFirstMergingEdgeOrFinalEdge(G,W)
    if preserveFutile:
        Eo=ExtendFutileWalks(G_U, G, V0)     # ▷ Add the extended futile edges to the designated final edges
        log.debug(f"\t\tFutile Edges Extended |Eo|={len(Eo)}")
    G_U.cntPrunedWalk+=1
    log.log(VERBOSE,f"\t\tBefore Walk prunded edge by {e_}. PreserveFutileWalk:{preserveFutile} |E(G)|={G.size()}")
    G.removeEdge(e_)
    G_ = fg.ComputeFeasibleGraph(G,V0, Eo|Ef)           # ▷ Remove e′ from feasible graph
    G.addEdge(e_)            # this is required to restrore original graph 
    if preserveFutile: log.debug(f"\t\tWalk has been pruned by edge {e_}. |E(G')| with extended edges={G_.size()}")
    if G_.size()>0 and any(map(lambda f_: G.hasEdge(f_), Ef)):
        for e in Eo:
            if G_.hasEdge(e): G_.removeEdge(e)          # G[E(G)-Eo]
    log.debug(f"\t\tWalk has been pruned by edge {e_}. PreserveFutileWalk:{preserveFutile} Size Decreased(|E(G)| -> |E(G')|={G_.size()}")
    return G_

def TakeArbitraryWalk(G, V0):       # ▷Take Arbitrary Walk from Start Nodes ▷ Any consistent choice (e.g., always first edge) works; result is deterministic
    S =dcg.CellArray()              # ▷ Empty Surface
    v0=list(V0)[0]
    ES =G.outgoingEdgeOf(v0)        # ▷ NextG(v0)
    if len(ES)==0:
        log.warning("The initial edge is missing. Empty walk returned!")
    
    e=ES[0] if len(ES)>0 else None
    W=[]
    while e is not None:
        u,v=e
        S[u.index()]=u.T            # ▷ Update surface S[index(u)] with the transition case to which node u belongs
        W.append(e)
        EN=list(filter(lambda e:e[1].tier()==0 or G.IPrecedent(e[1])==S[e[1].index()], G.getNextEdges(e)))
        e=EN[0] if len(EN)>0 else None
    return W

def FindDisjointEdge(R,W):   # ▷ Find disjoint edge of W from R       
    i=0
    while i<len(W):     # For all edge of walk
        e=W[i]
        if not R.hasEdge(e):
            return e
        i+=1;
    return None         # All the walk is Futile walk.

def FindTargetRedundantFutileEdge(G_U, G, V0, et):     # V0:initial node of walks, et : the verification target edge
    Ef = {et }                              # ▷ Ef : set of verification target edges
    R = dcg.DynamicComputationGraph()
    log.debug(f"\tStart to Find Computing-Target/Redundant/Futile Edge. Size of G:{G.size()}")   
    while G.size()>0:                       # Loop until graph empty or a computing-targeted walk is found
        W = TakeArbitraryWalk(G, V0)        # ▷ W is either a computing-tareted or a computing-futile walk
        if len(W)==0: return None, None  
        if et==W[len(W)-1] or et in W:      # ▷ et is not always at the end of W
            return et, W                    # ▷ et: verifiation target edge, W: computing-targeted edge
        elif R.size()>0:                    # ▷ After total collapse 
            f=FindDisjointEdge(R,W)
            log.log(VERBOSE, f"findDisjoint Edge:{f}")
            return f, W                     # ▷ Return disjoint or redundant edge
        else:                        # ▷ W can be computing-embedded walk                
            H=PruneWalk(G_U, G, V0, et, W, False)
            if H.size()==0:                 
                for e in W: R.addEdge(e)    # Add all edges and vertices of W to R
                G=PruneWalk(G_U, G, V0, et, W, True)
            else: G=H          
    log.log(VERBOSE, f"Pruned to size 0")
    return None, None
    
    
def VerifyExistenceOfWalk(G_U, V0, et):      

    log.log(VERBOSE, f"Verifying walk edges et:{et}")
    
    Ef = {et }
    G = fg.ComputeFeasibleGraph(G_U, V0, Ef)
    log.log(VERBOSE, f"After Initial feasible graph. et={et}")
   
    log.debug(f"Start to Verify walk. Orginal Graph G_U -> Feasible Graph G: {G_U.size()} -> {G.size()}")
    while G.size()>0:    
        e, W =FindTargetRedundantFutileEdge(G_U, G, V0, et)
        log.log(VERBOSE, f"FindTargetRedundantFutileEdge: {e}")
        if e in Ef:
            log.log(VERBOSE,f"Walk Verified ending at {e}")
            return W
        elif e is None:
            log.log(VERBOSE, f"Walk not verified NIL returned")
            return None
        G_U.cntRemovedRedundantFutileEdge+=1
        G.removeEdge(e)
        G = fg.ComputeFeasibleGraph(G, V0, Ef)
        log.debug(f"\tRemoved disjoint edge:{e} Size Decreased(G_U->G):{G_U.size()}->{G.size()}")
    log.log(VERBOSE, f"No walk! empty feasible graph!")
    return None







    

