"""
dynamicComputationGraph.py

Purpose:
- Implements the core data structures and routines for dynamic computation graphs used in NP verifier simulations.
- Models vertices, transition cases, edges, tiers, and cells to represent the unfolding of a nondeterministic Turing Machine.
- Provides functionality to add, remove, and traverse edges and vertices, including folding, merging, and combining edge types.
- Supports predecessor/successor retrieval and weak ceiling adjacency operations for computation walks.

Main Classes:
- TransitionCase: Represents a Turing Machine transition at a specific index, tier, state, and symbol.
- vertex: Represents a vertex in the dynamic computation graph corresponding to a transition case.
- EdgeListOf / EdgeSlice / CellArray / TierArray: Hierarchical data structures for storing edges and vertices efficiently.
- SymbolDict / StateDict: Provides automatic creation and access of vertices based on state and symbol.
- DynamicComputationGraph: Core class representing the dynamic computation graph with full edge and vertex management.

Key Functions:
- ISuccedent / IPrecedent: Retrieve successor or precedent vertices for a given vertex.
- addEdge / removeEdge / hasEdge: Manage graph connectivity.
- filterWithPathForward / filterWithPathBackward: Utility functions for path filtering during verification walks.
- GetForwardWeakCeilingAdjacentEdges / GetWeakCeilingAdjacentEdges: Identify weak ceiling-adjacent edges for folding and merging operations.
- existsPath / areAdjacent / IsIndexAdjacent: Graph traversal and adjacency checks.

Usage:
    This module is intended for research-level simulation of NP verifier Turing Machines,
    providing the underlying computation graph implementation used by higher-level simulation routines
    (e.g., simulateAllCertificatePoly.py).

Notes:
- Supports detailed graph statistics tracking for analysis of edge extension, computation walk lengths, and verification steps.
- Designed for research verification purposes; not optimized for general-purpose NP problem solving.
"""


import traceback
import collections
from .log_ext import *
log=get_logger(__name__)

class TransitionCase(set):
    delta=None
    def __init__(self, i, t, q, s):
        (self.index, self.tier, self.state, self.symbol) =(i, t, q, s)
        (q_, s_, d) = TransitionCase.delta(q, s)
        
        (self.dir, self.next_index) = (d, d + self.index)
        (self.next_state, self.output) = (q_, s_)
        if(self.tier==0): self.add(vertex(self,None))

    def vertex(self,P):
        if(self.tier==0):
            if(P is not None): log.error(f"Floor node cannot have precedent:{P}"); return None
            return list(self)[0]

        assert P.index==self.index, "Wrong index for vertex"
        assert P.tier==self.tier-1, "Wrong tier for vertex"

        items=list(filter(lambda x:x.state==P.state and x.symbol==P.symbol,self))
        if(len(items)>0): return items[0]
        else: v=vertex(self,P); self.add(v); return v
    def __eq__(self, other):
        return self.index==other.index and self.tier==other.tier and self.state==other.state and self.symbol==other.symbol

class vertex:
    def __init__(self,T,P):
        self.T=T
        self.pred=P
        if T.tier==0:
            self.key=(T.index,T.tier,T.state,T.symbol)
        else:
            self.key=(T.index,T.tier,T.state,T.symbol,P.state,P.symbol)
    def __eq__(self, other):
        return self.key==other.key

    def __hash__(self):
        return hash(self.key)
        
    def __str__(self):
        v=self
        if v.tier()==0:
            return f"({v.index()},{v.tier()},{v.state()},{v.symbol()})"
        else:
            return f"({v.index()},{v.tier()},{v.state()},{v.symbol()},{v.pred.state},{v.pred.symbol})"
        
    def __repr__(self):
        v=self
        if v.tier()==0 :
            return f"({v.index()},{v.tier()},{v.state()},{v.symbol()})"
        else:
            return f"({v.index()},{v.tier()},{v.state()},{v.symbol()},{v.pred.state},{v.pred.symbol})"
 
    def index(self): return self.T.index
    def tier(self): return self.T.tier
    def state(self): return self.T.state
    def symbol(self): return self.T.symbol
    def output(self): return self.T.output
    def transitionCase(self): return self.T
    def next_index(self): return self.T.next_index
    def next_state(self): return self.T.next_state
    def last_state(self): return self.pred.state
    def last_symbol(self): return self.pred.symbol

def index(e):
    return min(e[0].index(),e[1].index())
    
def dir(e):
    return e[1].index()-e[0].index()

class EdgeListOf:
    def __init__(self,vertex):
        self.at=vertex
        self.left_incoming=[]
        self.left_outgoing=[]
        self.right_incoming=[]
        self.right_outgoing=[]
    def __str__(self):
        s="Edge List vertexOf:"+str(self.at)
        s+="\nleft_incoming:"+str(len(self.left_incoming))
        s+="\nleft_outgoing:"+str(len(self.left_outgoing))
        s+="\nright_incoming:"+str(len(self.right_incoming))
        s+="\nright_outgoing:"+str(len(self.right_outgoing))
        return s
        
    def allList(sef):
        return self.left_incoming+self.left_outgoing+self.right_incoming+self.right_outgoing
    def count(self):
        n=len(self.left_incoming)+len(self.left_outgoing)+len(self.right_incoming)+len(self.right_outgoing)
        return n
    def countPrint(self):
        print("id, count of:",id(self), self.left_incoming,self.left_outgoing,self.right_incoming,self.right_outgoing)
        
class EdgeSlice:
    def __init__(self, index):
        self.index=index
        self.edges=dict()
        self.edgeCount=0
    def __getitem__(self, vertex):
        assert self.index in [vertex.index(),vertex.index()-1],f"getitem index error {self.index},{vertex}"
        if(self.edges.get(vertex.key) is None):
            self.edges[vertex.key]=EdgeListOf(vertex)
        return self.edges[vertex.key]
    def __setitem__(self, v, value):
        assert self.index in [vertex.index(),vertex.index()-1],f"setitem index error {self.index},{vertex}"
        self.edges[v.key]=value
        log.warning("Set Item is called!")
    def __str__(self):
        return "EdgeSlice of"+str(self.index)+":"+str(self.edges)
    def size(self):
        return self.edgeCount
    def printCount(self):
        print(id(self),list(self.edges.keys()))

    def getAllVertices(self):
        return set(map(lambda elist:elist.at, self.edges.values()))
        
    def getAllEdges(self):
        E=[]
        if len(self.edges)==0: return E
        for elist in self.edges.values():
            v=elist.at
            if(self.index==v.index()):
                E+=list(map(lambda u:(u,v), elist.right_incoming))
                E+=list(map(lambda w:(v,w), elist.right_outgoing))
        return E

    def hasIncomingEdge(self, v):
        if self.edges.get(v.key, None) is not None:
            l=len(self.edges[v.key].left_incoming)+len(self.edges[v.key].right_incoming)
            return l>0
        return False 
    def hasOutgoingEdge(self, v):
        if self.edges.get(v.key, None) is not None:
            l=len(self.edges[v.key].left_outgoing)+len(self.edges[v.key].right_outgoing)
            return l>0
        return False 
        
    def getFloorEdges(self):
        Eb=[]
        if len(self.edges)==0: return Eb
        for elist in self.edges.values():
            v=elist.at
            if(v.tier()==0):
                elist=elist.left_incoming+elist.right_incoming
                Eb+=list(map(lambda u:(u,v), elist))
        return Eb
     
class SymbolDict(dict):
    def __init__(self,index,tier, state):
        self.index=index
        self.tier=tier
        self.state=state
    def __getitem__(self, symbol):
        if self.get(symbol) is None:
            if symbol in SymbolDict.symbols:
                item=TransitionCase(self.index,self.tier,self.state,symbol)
                self.setdefault(symbol,item)
            else:
                log.error(f"Wrong symbol {symbol} not in {SymbolDict.symbols}")
                assert False, "No symbol:"+symbol
        return self.get(symbol)

class StateDict(dict):
    def __init__(self,index,tier):
        self.index=index
        self.tier=tier
    def __getitem__(self, state):
        if self.get(state) is None:
            item=SymbolDict(self.index,self.tier,state)
            self.setdefault(state,item)
        return self.get(state)

class TierArray(list):
    states=[]
    symbols=""
    def __init__(self,i):
        self.cell_index=i
    def __getitem__(self, tier):
        i=len(self)
        while tier>=i:
            item=StateDict(self.cell_index,i)
            self.append(item)
            i+=1
        return super().__getitem__(tier)


class CellArray(list):
    TYPE_NONE=0
    TYPE_EDGESLICE=1
    TYPE_TIERARRAY=2
    TYPE_SET=3
    def __init__(self, kind=0):
        self.base=0
        self.kind=kind

    def newItem(self,index):
        match(self.kind):
            case CellArray.TYPE_EDGESLICE: item=EdgeSlice(index)
            case CellArray.TYPE_TIERARRAY: item=TierArray(index)
            case CellArray.TYPE_SET: item=set()
            case _: item=None;
        return item
    
    def __getitem__(self, index):
        if self.base<=index and index<len(self)+self.base:
            item=super().__getitem__(index-self.base)
            assert self.kind!=1 or item.index==index, f"index mismatch index={index}, item.index={item.index}"
            return item
        
        m=len(self)+self.base
        for i in range(m, index+1):
            item=self.newItem(i); super().append(item)
        for i in range(self.base-1,index-1,-1):
            item=self.newItem(i); super().insert(0,item);
            self.base-=1

    
        return item    
    def __setitem__(self, index, value):
        assert index<=self.base+len(self) and index>=self.base-1, "Wrong set item"
        if(self.kind!=0): print("set item called:",self.kind)
        if index==self.base-1:self.insert(0,value); self.base-=1;
        elif index==len(self)+self.base: self.append(value);
        else: super().__setitem__(index-self.base,value)

    def isDefined(self, index):
        return self.base<=index<len(self)+self.base

def initialize(states, symbols, delta):
    TransitionCase.delta=delta
    SymbolDict.symbols=symbols
    StateDict.states=states

class DynamicComputationGraph:
    def __init__(self):
        self.V= CellArray(2)
        self.E= CellArray(1)
        self.__edgeCount=0
        #Variables for statistics        
        self.cntCandiateForVerificaition=0
        self.cntExtendedByVerification=0
        self.cntRemovedDisjointEdge=0
        self.cntPrunedWalk=0
        self.cntSumOfComputationWalkLength=0
        self.cntExtendedComputationWalk=0
        self.cntHaltingEdge=0
        
    def __getitem__(self, index):
        return self.E[index].right_incoming + self.E[index].right_outgoing

    def getCopyedGraph(self):
        G=DynamicComputationGraph()
        if self.size()==0:
            return G
        G.V=self.V
        m=self.minEdgeIndex(); M=self.maxEdgeIndex()
        for i in range(m,M+1):
            for elist in self.E[i].edges.values():
                u=elist.at
                for v in elist.right_incoming:
                    G.addEdge((v,u))
                for v in elist.right_outgoing:
                    G.addEdge((u,v))
        return G
    def printGraph(self):

        if self.size()==0:
            print('Empty Graph')
 
        m=self.minEdgeIndex(); M=self.maxEdgeIndex()
        for i in range(m,M+1):
            for elist in self.E[i].edges.values():
                u=elist.at
                for v in elist.right_incoming:
                    print((v,u))
                for v in elist.right_outgoing:
                    print((u,v)) 


    def print(self):
        Ev=set()
        Es=self.E[0].getFloorEdges()
        T=collections.deque(Es)
        Ea=[]
        while (len(T)>0):
            f=T.pop()
            if f in Ev: continue
            Ea.append(f)
            Ev.add(f)
            T.extend(self.getNextEdges(f))
        print(Ea)

    def size(self):
        return self.__edgeCount

    def edgesOf(self,u,index,dir):
        if u.index()==index and dir>0:
            return self.E[index][u].right_outgoing
        elif u.index()==index and dir<0:
            return self.E[index][u].right_incoming
        elif u.index()>index and dir>0:
            return self.E[index][u].left_incoming
        elif u.index()>index and dir<0:
            return self.E[index][u].left_outgoing        

    def minEdgeIndex(self):
        m=self.V.base
        while self.E[m].size()==0: m+=1
        return m
    def maxEdgeIndex(self):
        m=self.V.base+len(self.V)-1
        while self.E[m].size()==0: m-=1
        return m

    def incomingEdgeOf(self, v):
        i=v.index()
        L=self.E[i][v].right_incoming+self.E[i-1][v].left_incoming
        return list(map(lambda w:(w,v),L))

    def outgoingEdgeOf(self, v):
        i=v.index()
        L=self.E[i][v].right_outgoing+self.E[i-1][v].left_outgoing
        return list(map(lambda w:(v,w),L))

    def isExpendant(self, v):
        i=v.index()
        cnt_incoming=len(self.incomingEdgeOf(v))
        cnt_outgoing=len(self.outgoingEdgeOf(v))
        if(cnt_incoming==0 and cnt_outgoing>0): return True
        if(cnt_incoming>0 and cnt_outgoing==0): return True
        return False
        
    def isAdjacentTo(self, u, v):
        for u,w in self.outgoungEdgeOf(u):
            if v==w: return True
        return False

    def isFoldingNode(self, v):     # ▷ Folding edge is only possible to one direction
        i=v.index()
        if len(self.E[i-1][v].left_incoming)>0 and len(self.E[i-1][v].left_outgoing)>0:
            return True
        if len(self.E[i][v].right_incoming)>0 and len(self.E[i][v].right_outgoing)>0:
            return True
        return False
    def hasEdge(self,e):
        (u,v)=e
        index=min(u.index(),v.index())
        if(v in self.E[index][u].right_outgoing): return True 
        if(u in self.E[index][v].right_incoming): return True
        return False
    def hasIncomingEdge(self, v):
        if(len(self.E[v.index()][v].right_incoming)>0): return True
        if(len(self.E[v.index()-1][v].left_incoming)>0): return True
        return False

    def addVertex(self, v):
        self.V[v.index()][v.tier()][v.state()][v.symbol()].add(v)

    def addEdge(self, e):
        (u,v)=e

        index=min(u.index(),v.index())
        assert index==self.E[index].index, f"{index}!={self.E[index].index},{u},{v}"
        assert abs(u.index()-v.index()), f"index difference is not +1/-1,{u},{v}"

        if self.hasEdge(e): return
        self.addVertex(u); self.addVertex(v);
        if(u.index()<v.index()):
            self.E[u.index()][u].right_outgoing.append(v)
            self.E[u.index()][v].left_incoming.append(u)

        else:
            self.E[v.index()][u].left_outgoing.append(v)
            self.E[v.index()][v].right_incoming.append(u)

        self.E[index].edgeCount+=1

        self.__edgeCount+=1


    def isSplittingEdge(self,e):
        assert self.hasEdge(e), "No edge for splitting edge check"
        u,v=e
        if(u.index()<v.index()):
            return len(self.E[u.index()][u].right_outgoing)>1
        else:
            return len(self.E[v.index()][u].left_outgoing)>1

    def isCombinedFoldingEdge(self, e):
        u,v=e
        if self.isFoldingNode(u):
            for w in u.transitionCase():
                if u==w: continue
                for x,y in self.outgoingEdgeOf(w):
                    if y.transitionCase()==v.transitionCase(): return True

        return False

    def isCombinedMergingEdge(self,e):
        assert self.hasEdge(e), str(e)
        u,v=e        
        for f in self.incomingEdgeOf(v):
            if f[0]!=u and f[0].transitionCase()==u.transitionCase():
                return True
        return False


    def isCombiningEdge(self,e):   
        assert self.hasEdge(e), str(e)
        u,v=e
        for w in v.transitionCase():
            if v==w: continue
            for x in self.E[index(e)][w].left_incoming:
                if x.transitionCase()!=u.transitionCase(): return True
            for x in self.E[index(e)][w].right_incoming: 
                if x.transitionCase()!=u.transitionCase(): return True
            if self.isFoldingNode(w) and not self.isFoldingNode(v):
                return True
            elif not self.isFoldingNode(w) and self.isFoldingNode(v):
                return True
        return False

    def isPseudoCombiningEdge(self,e):
        u,v=e
        if self.isFoldingNode(v):
            return False
        for s in self.ISuccedent(v):
            if self.isFoldingNode(s): return True
        return False
    
    def isMergingEdge(self,e):
        assert self.hasEdge(e), str(e)

        u,v=e
        if(u.index()<v.index()):
            return len(self.E[u.index()][v].left_incoming)>1
        else:
            return len(self.E[v.index()][v].right_incoming)>1
        
    def getNextEdges(self,e):
        u,v=e
        return self.outgoingEdgeOf(v)
    
    def getPrevEdges(self,e):
        u,v=e
        return self.incomingEdgeOf(u)

    def getAllVerticesWith(self,i):
        V=self.E[i].getAllVertices() | self.E[i-1].getAllVertices()
        return set(filter(lambda v:v.index()==i, V))

    def removeEdge(self,e):
        u,v=e
        if not self.hasEdge(e): return
        if(u.index()<v.index()):
            self.E[u.index()][u].right_outgoing.remove(v)
            self.E[u.index()][v].left_incoming.remove(u)
            self.E[u.index()].edgeCount-=1
        else:
            self.E[v.index()][u].left_outgoing.remove(v)
            self.E[v.index()][v].right_incoming.remove(u)
            self.E[v.index()].edgeCount-=1
        self.__edgeCount-=1

    def IPrecedent(self, v):
        if v.tier()==0 : return set()
        (i,t,q,s)=(v.index(),v.tier()-1,v.last_state(),v.last_symbol())
        #print("Precedent:",i,t,q,s, self.V[i])
        return self.V[i][t][q][s]

    def ISuccedent(self, v):
        S=[]
        (i,t)=(v.index(),v.tier()+1)
        s=v.output()
        for q in self.V[i][t]:
            assert self.V[i][t][q][s] is not None, f"(i,t,q,s):({i},{t},{q},{s})"
            L=list(filter(lambda s:s.pred==v.T, self.V[i][t][q][s]))
            S.extend(L)
        return set(S)
        
    def CountIPrecedents(self, e):
        Es=self.E[min(e[0].index(),e[1].index())]
        cnt=0
        for p in self.IPrecedent(e[1]):       # vertex on Precedent of u
            cnt+=len(Es[p].right_outgoing)+len(Es[p].left_outgoing)
        return cnt
                   
    def GetIPrecedents(self, e):       # return PrecG(e)
        P = []
        #print("GetIPrecedents",e)
        (u, v) = e; i=min(u.index(),v.index())
        if v.tier()==0: return set()  #floor edge
        for v_ in self.IPrecedent(v):       # vertex on Precedent of u
            for (v_,u_) in self.outgoingEdgeOf(v_):
                if(u_ in self.IPrecedent(u)) or u==u_ or u_.tier()<u.tier()-1:
                    P.append((v_,u_))
        return set(P)
        
    def CountISuccedents(self, e):
        Es=self.E[min(e[0].index(),e[1].index())]
        cnt=0
        for s in self.ISuccedent(e[0]):       # vertex on Precedent of u
            cnt+=len(Es[s].left_incoming)+len(Es[s].right_incoming)
        return cnt

    def GetISuccedents(self, e):        #▷ Returns SuccG(e)
        S =[]
        (u, v) = e; i=min(u.index(),v.index())
        for u_ in self.ISuccedent(u):       # vertex on Precedent of u
            for (v_, w) in self.incomingEdgeOf(u_):
                if(v_ in self.ISuccedent(v)) or v==v_ or v_.tier()>v.tier()+1:
                    S.append((v_,u_))        
        return set(S)

    def existsPathAvodingStartIndex(self,e0,f):
        Q=collections.deque()
        i0=index(e0)
        Q.append(e0)
        Ev=set()
        while len(Q)>0:
            (u,v)=e=Q.pop()
            if e in Ev: continue
            Ev.add(e)
            if(e==f): return True
            if e!=e0 and index(e)==i0: continue
            Q.extend(set(self.outgoingEdgeOf(v)))
        return False
       

def IsIndexAdjacent(G,f,Ei,Ef,V0):
    (u, v) = f                      

    idx=Ei.index
    # ▷ Condition 1: Adjacency to an edge in Ei
    if u.index() in (idx, idx+1) and Ei[u] is not None and len(Ei[u].left_incoming)+len(Ei[u].right_incoming)>0:
        return True
    if v.index() in (idx, idx+1) and Ei[v] is not None and len(Ei[v].left_outgoing)+len(Ei[v].right_outgoing)>0:
        return True
   
    if idx==index(f)-dir(f) and (G.isFoldingNode(u) or u in V0):
        return True
    
    if idx==index(f)+dir(f) and (G.isFoldingNode(v) or f in Ef):
        return True
    return False

def GetWeakCeilingAdjacentEdges(G, e0, Ef):
    C =set()                 # ▷ Collected weakly-ceiling adjacent edges
    (u0,v0)=e0
    Vv = set()               # ▷ Visited vertices set
    Q = collections.deque({u0})
   
    if e0 in Ef:
        Q.append(v0)
        
    while len(Q)>0:
        u=Q.popleft()
        if u in Vv: continue
        Vv.add(u)
        if G.isFoldingNode(u) or u==v0:
            P=G.IPrecedent(u)
            for v in P: 
                Q.append(v)
        else:
            C.update(G.incomingEdgeOf(u))  #Add all incoming edges of u to C
    return C

def GetForwardWeakCeilingAdjacentEdges(G, e0):
    C =set()                
    (u0,v0)=e0

    assert v0.next_index()!=u0.index, "No forward Ceiling edge for Folding imcoming folding Edge"
    #print("Ceiling Adjacent edge of:",e0)
    Ev =set()               #▷ Visited vertex set
    Q = collections.deque()
    #print("ForwardCeiling:",i, e0)
    if v0.state() in ['Accept','Reject']:
        return C
    Q.append(v0)
    while len(Q)>0:

        u=Q.popleft()
        if u in Ev: continue
        Ev.add(u) 
        
        if G.isFoldingNode(u) or u==v0:
            P=G.IPrecedent(u)
            if len(P)==0: C.add(None)
            for v in P: 
                Q.append(v)
        else:
            C.update(G.incomingEdgeOf(u))

    return C

def areAdjacent(e,f):
    u,v=e;x,y=f
    return v==x or y==u

def filterWithPathBackward(G,ef,Es):
    Q=collections.deque()
    Ec=set()
    Q.append(ef)
    if Es is None or len(Es)==0: return Ec
   
    i0=min(ef[1].index(),ef[1].next_index())
    Ev=set()

    while len(Q)>0:
        e=Q.pop()
        if e is None:
            Ec.add(e)
        else:
            (u,v)=e
            if e in Ev: continue
            Ev.add(e)
            if(e in Es): Ec.add(e)
            if index(e)==i0: continue
            Q.extend(G.getPrevEdges(e))
    return Ec
    

def filterWithPathForward(G,es,Ef):
    Q=collections.deque()
    Q.append(es)
    i0=index(es)
    Ev=set()
    Ec=set()
    while len(Q)>0:
        (u,v)=e=Q.pop()
        if e in Ev: continue
        Ev.add(e)
        if(e in Ef): Ec.add(e)
        if e!=es and index(e)==i0: continue
        Q.extend(G.getNextEdges(e))
    return Ec
    


        
