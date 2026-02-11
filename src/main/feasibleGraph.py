"""
feasibleGraph.py

Purpose:
- Implements routines for computing feasible subgraphs from a given dynamic computation graph (DCG),
  specifically for NP verifier simulation frameworks.
- Provides algorithms to determine cover edges, step-pendent edges, and ultimately
  the feasible graph that can be used for deterministic simulation or verification.

Main Functions:
- collectEdgesWithPath(G, C0, Ef): Collects all edges reachable via a backward path from a given edge set.
- ComputeCoverEdges(G, Ef): Computes the set of cover edges by weak ceiling adjacency propagation.
- ComputeStepPendentEdges(G, C, V0, Ef): Identifies edges that are pendent (cannot be extended) with respect to a given vertex set and cover.
- ComputeFeasibleGraph(G, V0, Ef): Computes the feasible subgraph of G by iteratively removing pendent and non-essential edges, preserving final edges.

Usage:
    Intended to be used in conjunction with dynamicComputationGraph.py and higher-level
    NP verifier simulation routines. Generates a subgraph containing only edges that
    can participate in valid computation walks starting from a set of initial vertices V0
    and ending in final edges Ef.

Notes:
- Functions make extensive use of predecessor and successor computations to propagate edge
  removals and ensure correctness.
- Designed for research-level NP verifier simulations; not intended as a general-purpose graph library.
- Maintains compatibility with the DynamicComputationGraph structures and edge/vertex representations.

Dependencies:
- dynamicComputationGraph.py
- log_ext.py
- collections, loggig
"""

from . import dynamicComputationGraph as dcg
import collections
from .log_ext import *
log=get_logger(__name__)

def collectEdgesWithPath(G,C0,Ef):
    Q=collections.deque(Ef)
    Ev=set()
    C=dcg.CellArray(dcg.CellArray.TYPE_SET)
    while len(Q)>0:
        (u,v)=e=Q.pop()
        if e in Ev: continue
        i=dcg.index(e)
        if e in C0[i]:
            C[i].add(e)
        Ev.add(e)
        Q.extend(G.incomingEdgeOf(u))
    return C

def ComputeCoverEdges(G,Ef):

    C = dcg.CellArray(dcg.CellArray.TYPE_SET)
    for f in Ef:
        C[dcg.index(f)].add(f)
    Q = collections.deque(Ef)
    while len(Q)>0:
        f=Q.popleft()
        Ec=dcg.GetWeakCeilingAdjacentEdges(G,f, Ef)
        for e in Ec:
            u,v=e; i=dcg.index(e)
            if e in C[i]: continue
            C[i].add(e); Q.append(e)
    return collectEdgesWithPath(G,C,Ef)

def GetStepPendentEdgesWithReachableGraph(G, C, V0, Ef):

    Ev=set();Er=set(); E0=set()
    for v0 in V0: 
        E0 =E0.union(G.outgoingEdgeOf(v0))  #▷ NextG(v0)
    T=collections.deque(E0)

    H=dcg.DynamicComputationGraph()
    T=collections.deque(E0)
    while (len(T)>0):
        f=T.pop()
        i=dcg.index(f)
        if H.hasEdge(f): continue
        H.addEdge(f)
        #if f in Ev: continue
        #Ev.add(f)
        u,v=f;
        if f not in C[i] and G.CountISuccedents(f)==0:
            Er.add(f)
        if v.tier()>0 and G.CountIPrecedents(f)==0:
            Er.add(f)
            
        if f not in Ef:
            En=G.getNextEdges(f); 
            if len(En)==0: Er.add(f)
            else: T.extend(En)
            
        if u not in V0:
            Eb=G.getPrevEdges(f);
            if len(Eb)==0: Er.add(f)
            else: T.extend(Eb)
            
    return H, Er
    


def ComputeFeasibleGraph(G, V0, Ef, Er_=set()):     #▷ G: non-empty computation graph
    log.log(VERBOSE,f"\t\tStart to Compute feasible graph |E(G)|={G.size()} with respect to {Ef}")   
    
    C = ComputeCoverEdges(G,Ef )        #▷ Initialize cover edge set from final edges
    H, Er = GetStepPendentEdgesWithReachableGraph(G, C, V0, Ef)

    
    Ef_=Ef.copy()         
    
    T=collections.deque(Er|Er_)
   
    log.log(VERBOSE,f"\t\tAfter Compute Step-pendent Edges |E(H)|={H.size()}")
    while len(T)>0:   #▷ Repeat until no change occurred or the graph becomes empty

        e=T.pop()
        if not H.hasEdge(e): continue
  
        if not H.isMergingEdge(e):
            E=H.getNextEdges(e); T.extend(E)

            
        Es=H.GetISuccedents(e)
        for f in Es:
            if H.CountIPrecedents(f)==1:
                T.append(f)


        Ep=H.GetIPrecedents(e)
        for f in Ep:
            i=dcg.index(f)
            if f in C[i]: continue
            if H.CountISuccedents(f)==1:
                T.append(f)
            
        if not H.isSplittingEdge(e):
            E=list(filter(lambda f: f not in Ef,H.getPrevEdges(e)));
            T.extend(E)  #Final Edge Should Not be Removed
            
        H.removeEdge(e)

        if e in Ef_:
            Ef_.remove(e)
            if len(Ef_)==0:
                return dcg.DynamicComputationGraph()
    return H
    

