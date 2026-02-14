"""
simulateAllCertificatePoly.py

Purpose:
- Provides a deterministic, polynomial-time simulation framework for NP verifier Turing Machines.
- Implements dynamic computation graphs, edge extension, and verification walks to simulate all possible certificates.
- Supports both subset-sum and SAT fixed-state or dynamic verifier machines.
- Includes statistics tracking for edges extended, verification attempts, and computation walk lengths.

Main Classes/Functions:
- NPDynamicComputationGraph: Extends DynamicComputationGraph for NP verification with certificate handling.
- SimulateVerifierForAllCertificates(L, m, q0, Σ, δ, Q, certSymbols=""): 
    Simulates the verifier on input string L with certificate length m and returns 'Yes' or 'No'.
- ExtendEdgeDirectlyWithWalk, ExtendByVerifiableEdges, IsAcceptedOnFootmarks:
    Core routines for traversing and extending the computation graph along feasible walks.
- printStat(H, sec): Prints statistics of computation graph usage and timing.

Usage:
    Import and call SimulateVerifierForAllCertificates with appropriate parameters for the target NP verifier.

Notes:
- Requires `main.dynamicComputationGraph`, `verificationWalk`, and `feasibleGraph` modules.
- Designed for research and verification of P=NP framework; not optimized for general SAT/Subset-Sum performance.
"""

import collections
import copy, time, datetime

from . import dynamicComputationGraph as dcg
from . import verificationWalk as vw
from . import feasibleGraph as fg
from .log_ext import *
log=get_logger(__name__)

class NPDynamicComputationGraph(dcg.DynamicComputationGraph):
    def __init__(self,L,m, q0, Q,Σ,δ,F, certSymbols=""):
        super().__init__()
        self.q0=q0
        self.L=L
        self.m=m
        self.Q=Q
        self.δ=δ
        self.Γ=set(Σ) | {'ϵ'}
        self.F=F
        if certSymbols=="": self.CertSymbols=list(Σ)
        else: self.CertSymbols=certSymbols

        dcg.initialize(self.Q, self.Γ, self.δ)

    def ISuccessorWith(self, u, q):

        v=self.V[u.index()][u.tier()+1][q][u.output()].vertex(u.transitionCase())
        return v

    
    def GetNextEdgesAbovePreds(self, u, Ep):
        En=set()
        for e in Ep:
            if e is None:
                En=En | self.GetFloorNextEdges(u);
                continue
            v,w=e
            assert w.index()==u.index() and u.next_index()==v.index(), "Not the IPrecedent u,v,w:"+str(u)+str(v)+str(w)
            i,t,q,s=v.index(),v.tier()+1, u.next_state(), v.output()
            assert self.V[i][t][q][s] is not None, f"{i},{t},{q},{s}"
            z=self.V[i][t][q][s].vertex(v.transitionCase())
            En.add((u,z))
            assert abs(u.index()-z.index())==1, "Index difference assertion"+str(u)+","+str((v,w))+str(Ep)
        return En
        

    def GetNonFloorNextEdge(self,u,Es):
        E=set()
        (i_, q_) = (u.next_index(), u.next_state())
        for e in Es.getAllEdges():
            v,w = e
            if v.index() != u.next_index() or u.tier()<w.tier() or (u.tier()==w.tier() and u!=w): continue
            if u.tier()==w.tier()+1 and not (w.state()==u.laste_state() and w.symbol()==u.last_symbol()): continue
            s=self.ISuccessorWith(v, u.next_state())
            E.add((u,s))
        return E

    def GetFloorNextEdges(self,v): #should check no outgoing edge from it
        L,V=self.L,self.V
        E=set()

        (i_, q_) = (v.next_index(), v.next_state())
        if(i_<0): log.log(VERBOSE, f"Negative index {i_} accessed!")

        if i_ < 0 or i_ >= len(L) + self.m:
            log.debug(f"Empty String Area accessed with index:{i_}")
            s_='ϵ'; v_=V[i_][0][q_][s_].vertex(None)
            E.add((v, v_))
        elif 0<= i_<len(L):
            s_=L[i_]; v_ = V[i_][0][q_][s_].vertex(None)
            E.add((v,v_))
        else:
            for s_ in self.CertSymbols :
                v_ = v_=V[i_][0][q_][s_].vertex(None)
                E.add((v, v_))
        return E
        
      
def AddExtendableEdgeOnCeilingEdges(H, S, Ev):
    for e in S:
        if e is None: continue
        u,v=e
        if H.isMergingEdge(e) or H.isPseudoCombiningEdge(e) or H.isCombiningEdge(e): #should consider combined edge
            Q=set(H.ISuccedent(v))
            while len(Q)>0:
                w=Q.pop()
                if H.isFoldingNode(w):
                    Q.update(H.ISuccedent(w))
                elif w.next_index()==u.index():
                    Ec=dcg.filterWithPathForward(H,e,H.incomingEdgeOf(w))
                    for ec in Ec: Ev.add((e,ec))
            
def ExtendEdgeDirectlyWithWalk(G, H, W, Ev):
    
    S=dcg.CellArray()
    R=dcg.CellArray()
    T=collections.deque(); 
    for e in W:
        u,v=e
        if u.tier()==0: R[u.index()]=u.symbol()
        if not H.hasEdge(e):
            if e!=W[-1]: log.info(f"Extended edge {e} is a merging edge.")
            break
        S[min(u.index(),v.index())]=(u,v)

    T.append((e, S, R))

    while len(T)>0:   #should add any edge if its succedent is folding node
        e,S,R=T.pop()
        u,v=e
        
        if H.hasEdge(e): continue
 
        log.debug(f"Restarted from:{e}")
        walkLength=0
        while(True):
            isNewEdge=False
            if not H.hasEdge(e):
                H.addEdge(e); 
                isNewEdge=True
            u,v=e
            S[min(u.index(),v.index())]=e;
            if v.tier()==0: R[v.index()]=v.symbol()

            if isNewEdge and H.isMergingEdge(e) :
                AddExtendableEdgeOnCeilingEdges(H,S,Ev)

            walkLength+=1
            if v.state() in ['Accept','Reject']:
                H.cntHaltingEdge+=1
                break

            ep=S[min(v.index(),v.next_index())]

            if isNewEdge and ep is not None and v.next_index()!=u.index():
                if H.isMergingEdge(ep) or H.isPseudoCombiningEdge(ep) or H.isCombiningEdge(ep):
                    Ev.add((None,e))
            #log.log(VERBOSE, f"{e}")
            Ep={ep}
            En=G.GetNextEdgesAbovePreds(v, Ep)
            e=En.pop()
            if len(En)>0:
                for f in En:
                    if not H.hasEdge(f):
                        log.debug(f"Splitted:{f}")
                        T.append((f, copy.copy(S),copy.copy(R)))

        
        H.cntExtendedComputationWalk+=1
        H.cntSumOfComputationWalkLength+=walkLength
        if v.state()=='Accept':
            log.info(f"Accepted Edge:{e}")
            return R
        elif v.state()=='Reject': 
            language=''.join(R).strip('ϵ')
            if language.find('#')<0: log.info(f"End of Walk:{e}, Rejected:{language}")
            else: log.info(f"End of Walk:{e}, Rejected:{get_inputlog_str(language)}")
    return None



def CollectRestrictedBoundaryEdges(G,H, Ev):
    Q=set()             # the empty set of edges

    log.log(VERBOSE, f"Collecting For:{len(Ev)}")
    
    for ep,e in Ev:        #▷ For all last extended edges
        u,v=e; 
        if v.next_index()==u.index() or v.state() in ['Reject', 'Accept']:
            continue
        if ep is None:
            Ep=dcg.GetForwardWeakCeilingAdjacentEdges(H,e)
            Ep=dcg.filterWithPathBackward(H, e, Ep)
        else: Ep={ep}
        En=G.GetNextEdgesAbovePreds(v, Ep)
        for f in En:
            if not H.hasEdge(f): Q.add(f);

    return Q



def ExtendByVerifiableEdges(G, V0, Q0, H, Ev):
    Ef=set()
    
    Q=collections.deque(Q0)
    while len(Q)>0:
        ef=Q.popleft()
        if H.hasEdge(ef): continue
        
        H.addEdge(ef)
        H.cntCandiateForVerificaition+=1
        W=vw.VerifyExistenceOfWalk(H, V0, ef)
        H.removeEdge(ef)
        if W is not None:
            log.info(f"Extended:{ef}, Candidate edges remained:{len(Q)}")
            H.cntExtendedByVerification+=1
            R=ExtendEdgeDirectlyWithWalk(G,H,W,Ev)
            if R is not None:   #there exist state(v) = qacc for some (u, v) ∈ Ev then
                return R
        else:
            log.debug(f"Not Extended:{ef} - Candidate edges remained:{len(Q)}")
    
    
def IsAcceptedOnFootmarks(G,H, V0):     # ▷ qacc, qrej is a constance
    Ev=set()
    Q=set()
    for v0 in V0:
        Q.update(G.GetFloorNextEdges(v0))

    while len(Q)>0:# ▷ Extend H by valid computation edges

        Ev=set()
        if len(Q)>0:
            R=ExtendByVerifiableEdges(G, V0, Q, H, Ev) #▷ Ev: verified extension edges
        if R is not None:   #there exist state(v) = qacc for some (u, v) ∈ Ev then
            G.yesWitness="".join(R).strip('ϵ')
            return True
        elif len(Ev)==0:                  #▷ No feasible edge extended
            return False
        Q=CollectRestrictedBoundaryEdges(G,H, Ev)    #▷ Eb: newly collected boundary edges
        log.debug(f"Collected Boundary Edges:{len(Q)}")

    return False

def printStat(H, sec):
    print("Total edge count:", H.size())
    print("Edges extended directly:", H.size() - H.cntExtendedByVerification)
    print("Edges extended by verification:", H.cntExtendedByVerification)
    print("Candidate edges verified:", H.cntCandiateForVerificaition, "(may be counted multiple times)")
    print("Disjoint edges computed:", H.cntRemovedDisjointEdge)
    print("Pruned walks:", H.cntPrunedWalk)
    print("Halting edges (Accept/Reject):", H.cntHaltingEdge)
    print("Extended maximal computation walks:", H.cntExtendedComputationWalk)
    print("Average computation walk length extended: %.2f" %
          (H.cntSumOfComputationWalkLength / H.cntExtendedComputationWalk))
    resultTime = datetime.timedelta(seconds=sec)
    print("Elapsed time:", resultTime)


def SimulateVerifierForAllCertificates(L, m, q0,Σ, δ,Q, certSymbols=""):
    F={'Accept','Reject'}
    G=NPDynamicComputationGraph(L, m, q0,Q,Σ, δ,F, certSymbols)

    s = L[0]                #▷ Problem Instance is not empty string
    v0 =G.V[0][0][q0][s].vertex(None)   #▷ v0: vertex at index 0, tier 0, state q0, symbol s
    
    H = dcg.DynamicComputationGraph() #▷ Computation Graph
    print("Tape string:",L)
    print("Tape input length:", len(L))
    print("Certificate length:",m)
    start = time.time()
    result=IsAcceptedOnFootmarks(G,H, {v0}) # ▷ v0:Initial vertex where state(v0) = q0
    end = time.time()
    if result and m > 0:
        print("Witness for accepted certificate:", G.yesWitness.split('#')[1])
    
    printStat(H, end-start)
    
    if result: return 'Yes'
    else: return 'No'






