"""
verificationWalk.py

Purpose:
- Provides routines for verifying the existence of a computation walk within a dynamic computation graph (DCG),
  as part of deterministic NP-verifier simulations.
- Handles obsolete, disjoint, and redundant edges to determine whether a valid computation path exists
  from a set of initial vertices (V0) to a given end edge (ef).

Main Functions:
- AddFinalEdgesOfObsoleteWalks(G_U, G, Eo, Ef): Ensures that obsolete walks are represented in the graph by adding
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

def AddFinalEdgesOfObsoleteWalks(G_U, G, Eo, Ef):
    m=G_U.minEdgeIndex(); M=G_U.maxEdgeIndex()
    for i in range(m,M+1):
      for e in G_U.E[i].getAllEdges():
        u,v=e
        Vf=list(map(lambda f:f[1],Ef))
        if not G.hasEdge(e) and u not in Vf:
            if G.hasIncomingEdge(u) and (v.tier()==0 or len(G.GetIPrecedents(e))>0):
                G.addEdge(e)
                Eo.add(e)

def FindFirstMergingEdgeOrFinalEdge(G,W):
    i=0;e=W[i]
    while i<len(W)-1:
        if G.isMergingEdge(e):
            log.log(VERBOSE,"First Merging Edge:",e)
            return e
        i=i+1;e=W[i]
    log.log(VERBOSE,"No merging edge, Final Edge Returned.",e)
    return e        # ▷ It returns final edge of computation walk if no mergin edge found

def PruneWalk(G_U,G,V0,Ef,W, preserveObsolete):
    e_ = FindFirstMergingEdgeOrFinalEdge(G,W)
    Eo=set()
    if preserveObsolete:
        AddFinalEdgesOfObsoleteWalks(G_U, G, Eo, V0) #▷ Add the end of obsolete edge to final edges

    G_U.cntPrunedWalk+=1
    log.log(VERBOSE,f"\t\tBefore Walk prunded edge by {e_}. PreserveObsoleteWalk:{preserveObsolete} |E(G)|={G.size()}")
    G.removeEdge(e_)
    G_ = fg.ComputeFeasibleGraph(G,V0, Eo|Ef) #▷ Remove e′ from feasible graph
    if G_.size()>0:
        for e in Eo:
            if G_.hasEdge(e): G_.removeEdge(e)        #G[E(G)-Eo]
    log.debug(f"\t\tWalk has been pruned by edge  {e_}. PreserveObsoleteWalk:{preserveObsolete} Size Decreased(|E(G)| -> |E(G')|={G_.size()}")
    return G_

def TakeArbitraryWalk(G, V0):       # ▷Take Arbitrary Walk from Start Nodes ▷ Any consistent choice (e.g., always first edge) works; result is deterministic
    S =dcg.CellArray()              # ▷ Empty Surface
    v0=list(V0)[0]
    ES =G.outgoingEdgeOf(v0)  #▷ NextG(v0)
    assert len(ES)>0

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
 
    while i<len(W):  # For all edge of walk
        e=W[i]
        if not R.hasEdge(e):
            return e
        i+=1;
    return None   # All the walk is obsolete walk.

def FindFeasibleOrDisjointEdge(G_U, G, V0, ef): # V0:initial node of walks, ef : the end of feasible walk
    G = G.getCopyedGraph()
    Ef = {ef }                                  # ▷ Ef : set of ends of feasible or obsolete walks
    R = dcg.DynamicComputationGraph()
    log.debug(f"\tStart to Find Feasible/Disjoint/Redundant Edge. |E(G)|={G.size()}")   
    while G.size()>0:                           # Loop until only one walk remains on the graph or a feasible walk is found]
        W = TakeArbitraryWalk(G, V0)
        if len(W)==0: return None
        if ef ==W[len(W)-1] or ef in W:     # ▷ e is not obsolete walk but feasible walk
            return ef                    # ▷ W is not always at the end of W
        elif R.size()>0:                        # ▷When only one walk left, W is not feasible
            log.log(VERBOSE,"Find Disjoint Edge.")
            return FindDisjointEdge(R,W)        # ▷ Only embedded walk remains; return disjoint or redundant edge
        elif G.size()>0:                        # ▷ W can be embedded walk not obsolete walk               
            H=PruneWalk(G_U, G, V0,Ef ,W, False)
            if not any(map(lambda ef: H.hasEdge(ef), Ef)): # Add all edges and vertices of W to R
                for e in W: R.addEdge(e)
                G=PruneWalk(G_U, G, V0, Ef, W, True)
            else: G=H          
    log.log(VERBOSE,"Pruned to size 0")
    return None
    
    
def VerifyExistenceOfWalk(G0, V0, ef): 

    log.log(VERBOSE,f"Verifying walk edges ef:{ef}")
    
    Ef = {ef }
    G = fg.ComputeFeasibleGraph(G0, V0, Ef)
    log.log(VERBOSE,f"After Initial feasible graph ef:{len(Ef)}")
   
    log.debug(f"Start to Verify walk. Orginal Graph G0 -> Feasible Graph G: {G0.size()} -> {G.size()}")
    while G.size()>0:    
        e=FindFeasibleOrDisjointEdge(G0, G, V0, ef)
        log.log(VERBOSE,f"DisjointEdgeOrFinalEdge:{e}")
        if e in Ef:
            log.log(VERBOSE,f"Walk Verified ending at {e}")
            return True
        elif e is None:
            log.log(VERBOSE,f"Walk not verified NIL returned.")
            return False
        G0.cntRemovedDisjointEdge+=1
        G.removeEdge(e)
        G = fg.ComputeFeasibleGraph(G, V0, Ef)
        log.debug(f"\tRemoved disjoint edge:",e, "Size Decreased(G0->G):{G0.size()}->{G.size()}")
    log.log(VERBOSE,"No walk! empty feasible graph!")
    return False







    

