"""
verificationWalk.py

Purpose:
- Provides routines for verifying the existence of a computation walk within a dynamic computation graph (DCG),
  as part of deterministic NP-verifier simulations.
- Handles computing-targeted/redundant/futile edges to determine whether a valid computation path exists
  from an initial vertex v0 to a given target edge (et).

Main Functions:
- ExtendFutileWalks(G_U, G, v0): Ensures that computing-futile walks are represented in the graph by adding
  their final edges prior to pruning.
- FindFirstMergingEdgeOrFinalEdge(G, W): Finds the first merging edge in a walk or returns the final edge.
- PruneWalk(G_U, G, v0, et, W, preserveFutile): Prunes a given walk by removing non-essential edges and
  recomputing the feasible graph.
- TakeArbitraryWalk(G, v0): Extracts an arbitrary walk from the graph starting from the initial vertex v0.
- FindDisjointEdge(R, W): Finds an edge in a walk W that is disjoint from the reference graph R.
- FindTargetRedundantFutileEdge(G_U, G, v0, et): Iteratively finds either a computing-targeted edge, 
  a computing-redundant edge, or computing-futile edge for verification purposes.
- VerifyExistenceOfWalk(G_U, v0, et): Main routine that verifies whether a feasible computation walk exists
  from the initial vertex v0 to the specified target edge et.

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


def ExtendFutileWalks(G_U, G, v0):  #It should be caculated at first time before pruned
    T=collections.deque()
    T.extend(G.outgoingEdgeOf(v0))
    Eo=set()
    Ev=set()
    while len(T)>0:
        e=T.pop()
        if e in Ev: continue
        Ev.add(e)
        if G.hasEdge(e):
            T.extend(G_U.getNextEdges(e))
        elif e[1].tier()>0 and len(G.GetIPrecedents(e))>0:
            G.addEdge(e)
            Eo.add(e)           #IPrecedents() is verified when computing feasible graph
    return Eo 


def FindFirstSplittingEdgeOrFinalEdge(G, W):
    i=0;e=W[i]
    log.log(VERBOSE, f"\t\t\tFind First Splitting/Final Edge with length of W:{len(W)}")
    while i<len(W)-1:
        if G.isSplittingEdge(e):
            log.log(VERBOSE, f"\t\t\tFirst Splitting Edge:{e}")
            return e
        i=i+1;e=W[i]
    log.log(VERBOSE, f"No splitting edge, Final Edge Returned. {e}")
    return e    # ▷ It returns final edge of computation walk if no splitting edge found

def PruneWalk(G_U, G, v0, et, W, preserveFutile):
    Eo=set(); Ef={et}; V0={v0}
    
    e = FindFirstSplittingEdgeOrFinalEdge(G,W)

    if preserveFutile:
        Eo=ExtendFutileWalks(G_U, G, v0)     # ▷ Add the extended futile edges to the designated final edges
        log.debug(f"\t\tFutile Edges Extended |Eo|={len(Eo)}")
    G_U.cntPrunedWalk+=1
    log.log(VERBOSE,f"\t\tBefore Walk prunded edge by {e}. PreserveFutileWalk:{preserveFutile} |E(G)|={G.size()}")
    
    G.removeEdge(e)
    G_ = fg.ComputeFeasibleGraph(G, V0, Eo|Ef)           # ▷ Remove e′ from feasible graph
    G.addEdge(e)             # This is required to restrore original graph     
    
    for e in Eo: G.removeEdge(e)  # This is also required to restrore original graph(G is regarded as input parameter).
    log.debug(f"\t\tWalk has been pruned by edge {e}. PreserveFutileWalk:{preserveFutile} Size |E(G')|={G_.size()}")    
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

def FindDisjointEdge(R, G):   # ▷ Find disjoint edge of W from R       
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

def FindTargetRedundantFutileEdge(G_U, G, v0, et):     # v0:initial node of walks, et : the verification target edge
    Ef = {et }                              # ▷ Ef : set of verification target edges
    log.debug(f"\tStart to Find Computing-Target/Redundant/Futile Edge. Size of G:{G.size()}")   
    while G.size()>0:                       # Loop until graph empty or a computing-targeted walk is found
        W = TakeArbitraryWalk(G, v0)        # ▷ W is either a computing-tareted or a computing-futile walk
        if len(W)==0: return None, None  
        if et==W[len(W)-1] or et in W:      # ▷ et is not always at the end of W
            return et, W                    # ▷ et: verifiation target edge, W: computing-targeted edge            
        else:                        # ▷ W can be computing-embedded walk                
            H=PruneWalk(G_U, G, v0, et, W, False)
            if H.size()==0:          # ▷ After total collapse        
                G=PruneWalk(G_U, G, v0, et, W, True)
                f=FindDisjointEdge(W,G)   # R=W
                log.log(VERBOSE, f"findDisjoint Edge:{f}")
                return f, W                     # ▷ Return disjoint or redundant edge
            else: G=H          
    log.log(VERBOSE, f"Pruned to size 0")
    return None, None
    
    
def VerifyExistenceOfWalk(G_U, v0, et):      

    log.log(VERBOSE, f"Verifying walk edges et:{et}")
    
    Ef = {et }; V0={v0}
    G = fg.ComputeFeasibleGraph(G_U, V0, Ef)
    log.log(VERBOSE, f"After Initial feasible graph. et={et}")
   
    log.debug(f"Start to Verify walk. Orginal Graph G_U -> Feasible Graph G: {G_U.size()} -> {G.size()}")
    while G.size()>0:    
        e, W =FindTargetRedundantFutileEdge(G_U, G, v0, et)
        log.log(VERBOSE, f"FindTargetRedundantFutileEdge:{e}")
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







    

