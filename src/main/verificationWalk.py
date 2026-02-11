"""
verificationWalk.py

Purpose:
- Provides routines for verifying the existence of a computation walk within a dynamic computation graph (DCG),
  as part of deterministic NP-verifier simulations.
- Handles obsolete, disjoint, and redundant edges to determine whether a valid computation path exists
  from a set of initial vertices (V0) to a given end edge (ef).

Main Functions:
- AddFinalEdgesOfObsoleteWalks(G_U, G, V0): Ensures that obsolete walks are represented in the graph by adding
  their final edges prior to pruning.
- FindFirstMergingEdgeOrFinalEdge(G, W): Finds the first merging edge in a walk or returns the final edge.
- PruneWalk(G_U, G, V0, Ef, W, preserveObsolete): Prunes a given walk by removing non-essential edges and
  recomputing the feasible graph.
- TakeArbitraryWalk(G, V0): Extracts an arbitrary walk from the graph starting from initial vertices V0.
- FindDisjointEdge(R, W): Finds an edge in a walk W that is disjoint from the reference graph R.
- FindFeasibleOrDisjointEdge(G_U, G, V0, ef): Iteratively finds either a feasible edge, a disjoint edge,
  or redundant edge for verification purposes.
- VerifyExistenceOfWalk(G0, V0, ef): Main routine that verifies whether a feasible computation walk exists
  from the initial vertices V0 to the specified end edge ef.

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


def AddFinalEdgesOfObsoleteWalks(G_U,G, V0):#it should be caculated at first time before pruned
    ES =set()
    Eo=set()
    for v0 in V0: ES=ES | set(G_U.outgoingEdgeOf(v0))
    T=collections.deque(ES)
    Ev =set()
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

def PruneWalk(G_U,G,V0,Ef,W, preserveObsolete):
    e_ = FindFirstMergingEdgeOrFinalEdge(G,W)
    Eo=set()
    if preserveObsolete:
        Eo=AddFinalEdgesOfObsoleteWalks(G_U, G, V0)     # ▷ Add the end of obsolete edge to final edges
        log.debug(f"\t\tObsolete Edges Extended |Eo|={len(Eo)}")
    G_U.cntPrunedWalk+=1
    log.log(VERBOSE,f"\t\tBefore Walk prunded edge by {e_}. PreserveObsoleteWalk:{preserveObsolete} |E(G)|={G.size()}")
    G.removeEdge(e_)
    G_ = fg.ComputeFeasibleGraph(G,V0, Eo|Ef)           # ▷ Remove e′ from feasible graph
    G.addEdge(e_)
    if preserveObsolete: log.debug(f"\t\tWalk has been pruned by edge {e_}. |E(G')| with extended edges={G_.size()}")
    if G_.size()>0 and any(map(lambda f_: G.hasEdge(f_), Ef)):
        for e in Eo:
            if G_.hasEdge(e): G_.removeEdge(e)          # G[E(G)-Eo]
    log.debug(f"\t\tWalk has been pruned by edge {e_}. PreserveObsoleteWalk:{preserveObsolete} Size Decreased(|E(G)| -> |E(G')|={G_.size()}")
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

def FindDisjointEdge(R,W):          # ▷ Check indirect precedents, To make orphaned walks, ceiling edges of another walk need
    i=0
    while i<len(W):     # For all edge of walk
        e=W[i]
        if not R.hasEdge(e):
            return e
        i+=1;
    return None         # All the walk is obsolete walk.

def FindFeasibleOrDisjointEdge(G_U, G, V0, ef):     # V0:initial node of walks, ef : the end of feasible walk
    G = G.getCopyedGraph()
    Ef = {ef }                              # ▷ Ef : set of ends of feasible or obsolete walks
    R = dcg.DynamicComputationGraph()
    log.debug(f"\tStart to Find Feasible/Disjoint/Redundant Edge. Size of G:{G.size()}")   
    while G.size()>0:                       # Loop until a feasible walk/disjoint edge found
        W = TakeArbitraryWalk(G, V0)        # ▷ W is either a feasible or an obsolete walk
        if len(W)==0: return None, None  
        if ef==W[len(W)-1] or ef in W:     # ▷ e is not obsolete walk but feasible walk
            return ef, W                    # ▷ W is not always at the end of W
        elif R.size()>0:                    # ▷ When only one walk left, W is not feasible
            f=FindDisjointEdge(R,W)
            log.log(VERBOSE, f"findDisjoint Edge:{f}")
            return f, W                     # ▷ Only embedded walk remains; return disjoint or redundant edge
        elif G.size()>0:                    # ▷ W can be embedded walk not obsolete walk               
            H=PruneWalk(G_U, G, V0, Ef, W, False)
            if H.size()==0:             # Add all edges and vertices of W to R
                for e in W: R.addEdge(e)
                G=PruneWalk(G_U, G, V0, Ef, W, True)
            else: G=H          
    log.log(VERBOSE, f"Pruned to size 0")
    return None, None
    
    
def VerifyExistenceOfWalk(G0, V0, ef): # Wrong Original version is right Since obsolete edge should contain rejected path

    log.log(VERBOSE, f"Verifying walk edges ef:{ef}")
    
    Ef = {ef }
    G = fg.ComputeFeasibleGraph(G0, V0, Ef)
    log.log(VERBOSE, f"After Initial feasible graph. ef={ef}")
   
    log.debug(f"Start to Verify walk. Orginal Graph G0 -> Feasible Graph G: {G0.size()} -> {G.size()}")
    while G.size()>0:    
        e, W =FindFeasibleOrDisjointEdge(G0, G, V0, ef)
        log.log(VERBOSE, f"DisjointEdgeOrFinalEdge: {e}")
        if e in Ef:
            log.log(VERBOSE,f"Walk Verified ending at {e}")
            return W
        elif e is None:
            log.log(VERBOSE, f"Walk not verified NIL returned")
            return None
        G0.cntRemovedDisjointEdge+=1
        G.removeEdge(e)
        G = fg.ComputeFeasibleGraph(G, V0, Ef)
        log.debug(f"\tRemoved disjoint edge:{e} Size Decreased(G0->G):{G0.size()}->{G.size()}")
    log.log(VERBOSE, f"No walk! empty feasible graph!")
    return None







    

