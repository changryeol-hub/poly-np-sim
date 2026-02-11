"""
simulateAllCertificatePoly.py

Purpose:
- Implements a deterministic simulation of an NP verifier Turing Machine over all possible
  computation paths for a given input string.
- Uses a dynamic computation graph (DCG) to represent vertices (configurations) and edges
  (transitions) of the verifier.
- Determines whether the verifier accepts the input by exhaustively exploring all
  feasible computation walks using the verificationWalk and feasibleGraph modules.

Main Classes:
- NPDynamicComputationGraph(dcg.DynamicComputationGraph):
    Extends the base dynamic computation graph to include Turing Machine-specific structures:
    states Q, input tape L, transition function δ, alphabet Σ, start state q0, and accepting/rejecting states F.
    Provides methods to generate next edges, floor edges, and all vertices for a given configuration.

Main Functions:
- CollectBoundaryEdges(G, H): Collects edges on the current boundary of feasible graph H
  that may extend the graph in valid ways.
- ExtendByVerifiableEdges(V0, Q, H, Ev): Attempts to extend H along candidate edges Q,
  verifying each walk's feasibility via VerifyExistenceOfWalk.
- IsAcceptedOnFootmarks(G, H, v0): Determines whether there exists a feasible walk
  starting from vertex v0 that reaches an accepting state.
- SimulateVerifierForAllCertificates(L, m, q0, Σ, δ, Q): Constructs the NPDynamicComputationGraph
  for the given input and TM, initializes the computation graph, and returns 'Yes' if any
  computation path leads to acceptance, 'No' otherwise.

Usage:
- Supports deterministic simulation of NP-verifiers for any given instance L.
- Works in conjunction with verificationWalk.py to ensure only feasible computation walks
  are considered.
- Designed for experimental demonstration of polynomial-time simulation of NP verifiers.

Notes:
- Feasible walks are verified incrementally by extending boundary edges and pruning
  invalid or obsolete walks.
- Floor edges (tier 0) and non-floor edges are handled separately to respect TM tape indexing.
- Logging is provided to trace extension and verification of edges during simulation.

Dependencies:
- dynamicComputationGraph.py
- verificationWalk.py
- log_ext.py
"""

from . import dynamicComputationGraph as dcg
from . import verificationWalk as vw
from .log_ext import *
log=get_logger(__name__)

class NPDynamicComputationGraph(dcg.DynamicComputationGraph):
    def __init__(self,L,m, q0 , Q,Σ,δ,F):
        super().__init__()
        self.q0=q0
        self.L=L
        self.m=m
        self.Q=Q
        self.δ=δ
        self.Γ=set(Σ) | {'ϵ'}
        self.F=F        
        dcg.initialize(self.Q, self.Γ, self.δ)

    def getAllVerticesIn(self, T):
        V=set()
        if T.tier>0:
            for q in self.Q:
                for s in self.Γ:
                    v=T.vertex(self.V[T.index][T.tier-1][q][s])
                    V.add(v)
        else: v=T.vertex(None); V.add(v)
        return V
        
        
    def GetNextEdges(self,u,h):
        E = self.GetFloorNextEdges(u)
        E_ = self.GetNonFloorNextEdges(u,h)
        return E | E_

    def GetNonFloorNextEdges(self,v,h):
        E=set()
        (i_, q_) = (v.next_index(), v.next_state())
        for s_ in self.Γ:
            for t_ in range(1,h+2):
                V=self.getAllVerticesIn(self.V[i_][t_][q_][s_])
                for w in V:
                    E.add((v,w))
        return E

    def GetFloorNextEdges(self,v): #should check no outgoing edge from it
        L,V=self.L,self.V
        E=set()

        (i_, q_) = (v.next_index(), v.next_state())
        assert q_ in self.Q
        if(i_<0): log.log(VERBOSE, f"Negative index {i_} accessed!")

        if i_ < 0 or i_ > len(L) + self.m:
            log.debug(f"Empty String Area accessed index:{i_}")
            s_='ϵ'; v_=V[i_][0][q_][s_].vertex(None)
            E.add((v, v_))
        elif 0<= i_<len(L):
            s_=L[i_]; v_ = V[i_][0][q_][s_].vertex(None)
            E.add((v,v_))
        else:
            for s_ in self.Γ:
                v_ = v_=V[i_][0][q_][s_].vertex(None)
                E.add((v, v_))
        return E

def CollectBoundaryEdges(G,H):
    Q=set()             # the empty set of edges
    if H.size()==0: return Q
    m=H.minEdgeIndex(); M=H.maxEdgeIndex()
    for i in range(m,M+2):
        for elist in list(H.E[i].edges.values()):
            v=elist.at
            h=len(H.V[v.next_index()])-1
            E=G.GetNextEdges(v,h)
            for e in E:
                if e[1].tier()==0 or len(H.GetIPrecedents(e))>0:
                    if not H.hasEdge(e): Q.add(e)
    return Q
    
def ExtendByVerifiableEdges(V0, Q, H, Ev):
    i=0
    for e in Q:
        H.addEdge(e)
        log.debug(f"Verifying edge:{e}")
        i+=1 
        if vw.VerifyExistenceOfWalk(H, V0, e):
            Ev.add(e)
            log.info(f"Extended:{e}, Candidate edges remained:{len(Q)-i}")

        else:
            H.removeEdge(e)
            log.debug(f"Not Extended:{e} - Candidate edges remained:{len(Q)-i}")
           

def IsAcceptedOnFootmarks(G,H, V0):     # ▷ qacc, qrej is a constance
    Q = CollectBoundaryEdges(G,H)
    log.debug(f"Collected boundary edges:{len(Q)}")
    while len(Q)>0:# ▷ Extend H by valid computation edges
        Ev=set()
        ExtendByVerifiableEdges(V0, Q, H, Ev) #▷ Ev: verified extension edges
        if len(Ev)==0:                  #▷ No feasible edge extended
            return False
        elif any(map(lambda e:e[1].state()=='Accept',Ev)):   #there exist state(v) = qacc for some (u, v) ∈ Ev then
            return True
        Q=CollectBoundaryEdges(G,H)    #▷ Eb: newly collected boundary edges
        log.debug(f"Collected boundary edges:{len(Q)}")
    return False

def SimulateVerifierForAllCertificates(L, m, q0,Σ, δ,Q):
    F={'Accept','Reject'}
    G=NPDynamicComputationGraph(L, m, q0,Q,Σ, δ,F)
    #G.Initialize(L, m, q0,Σ | {ϵ}, δ,Q)
    s = L[0]                #▷ Problem Instance is not empty string
    v0 =G.V[0][0][q0][s].vertex(None)   #▷ v0: vertex at index 0, tier 0, state q0, symbol s
    E0 =G.GetFloorNextEdges(v0)  #▷ NextG(v0)
    V0={v0}
    H = dcg.DynamicComputationGraph() #▷ Computation Graph
    for e in E0: H.addEdge(e)
    if IsAcceptedOnFootmarks(G, H, V0): # ▷ v0:Initial vertex where state(v0) = q0
        return 'Yes'
    return 'No'






