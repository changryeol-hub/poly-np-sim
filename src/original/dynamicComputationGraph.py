"""
dynamicComputationGraph.py

Purpose:
- Implements the Dynamic Computation Graph (DCG) as introduced in the P=NP simulation framework.
- Provides data structures and algorithms to represent Turing Machine computation walks
  as vertices and edges in a graph, allowing efficient construction, traversal, and verification.
- Supports both floor edges (tier 0) and higher-tier edges, and maintains folding, merging,
  and splitting properties of computation nodes.

Main Classes and Structures:
- TransitionCase(set):
    Represents a Turing Machine transition at a specific index, tier, state, and input symbol.
    Stores the next state, output symbol, and direction for constructing computation vertices.
- vertex:
    Encapsulates a unique vertex in the DCG corresponding to a TM configuration, with
    references to its preceding transition.
- EdgeListOf:
    Stores all incoming/outgoing edges (left/right) for a given vertex at a specific index.
- EdgeSlice:
    Represents a slice of edges at a particular index in the computation graph, and provides
    access to all edges, floor edges, and associated vertices.
- TierArray:
    Organizes TransitionCases by tier, state, and symbol, dynamically allocating tiers as needed.
- CellArray:
    Dynamically expands to store TierArrays, EdgeSlices, or sets of edges, supporting negative
    and positive indexing.
- DynamicComputationGraph:
    Core class representing the computation graph.
    Maintains vertices (V) and edges (E) via CellArrays.
    Provides methods for adding/removing edges, retrieving incoming/outgoing edges,
    precedence/succedent computations, folding/merging/splitting checks, and neighbor adjacency.

Main Functions:
- IsIndexAdjacent(G, f, Ei, Ef, V0):
    Checks whether an edge f is adjacent to the current index in the sweep for feasible graph computation.
- GetWeakCeilingAdjacentEdges(G, e0):
    Returns the set of edges that are ceiling-adjacent to a given edge e0.
- areAdjacent(e, f):
    Checks whether two edges share a common vertex.
- existsPathAvodingStartIndex(G, e0, f):
    Determines whether there exists a path from edge e0 to edge f in graph G.

Usage:
- Forms the foundational data structures for representing and simulating NP-verifier computations.
- Supports the computation of feasible graphs, extension of computation walks, and verification
  of acceptance paths in polynomial-time simulation.
- Interacts with other modules (feasibleGraph.py, simulateAllCertificatePoly.py, verificationWalk.py)
  for constructing and verifying computation walks.

Notes:
- Edges and vertices are dynamically allocated and indexed to allow arbitrary tape indices and tiers.
- Floor edges correspond to tier 0 and represent transitions directly over the input tape.
- The graph supports efficient query of precedents, succedents, and adjacency for feasible graph computations.
- Implements statistics tracking for experimental purposes (e.g., candidate verification count, extended edges).

Dependencies:
- collections
- traceback
"""


import traceback
import collections

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
            if(P is not None): print("tier0:",P); return None
            return list(self)[0]

        assert P.index==self.index, "Wrong index for vertex"
        assert P.tier==self.tier-1, "Wrong tier for vertex"

        items=list(filter(lambda x:x.state==P.state and x.symbol==P.symbol,self))
        if(len(items)>0): return items[0]
        else: v=vertex(self,P); self.add(v); return v

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


# utily functions for edges
def index(e):
    return min(e[0].index(),e[1].index())
    
def dir(e):
    return e[1].index()-e[0].index()
    
def areAdjacent(e,f):
    u,v=e;x,y=f
    return v==x or y==u


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
        #print("cont edgelist of ",self.at)
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
        self.edges[v.key]=value
        print("Set Item is called=============================")
    def __str__(self):
        return "EdgeSlice of"+str(self.index)+":"+str(self.edges)
    def size(self):
        return self.edgeCount
    def printCount(self):
        print(id(self),list(self.edges.keys()))
        #for elist in self.edges.values():elist.printCount()

    def getAllVertices(self):
        return set(map(lambda elist:elist.at, self.edges.values()))
        
    def getAllEdges(self):
        E=[]
        if len(self.edges)==0: return E
        for elist in self.edges.values():
            v=elist.at
            #print(self.index,v.index(),v)
            if(self.index==v.index()):
                E+=list(map(lambda u:(u,v), elist.right_incoming))
                E+=list(map(lambda w:(v,w), elist.right_outgoing))
        return E

        
    def getFloorEdges(self):
        Eb=[]
        if len(self.edges)==0: return Eb
        for elist in self.edges.values():
            v=elist.at
            if(v.tier()==0):
                elist=elist.left_incoming+elist.right_incoming
                Eb+=list(map(lambda u:(u,v), elist))
        return Eb


class TierArray(list):
    states=[]
    symbols=""
    def __init__(self,i):
        self.cell_index=i
    def __getitem__(self, tier):
        #print("__getitem",self.cell_index, tier, len(self))
        i=len(self)
        while i<=tier:
            item={}
            for q in TierArray.states:
                item[q]={}
                for s in TierArray.symbols:
                    item[q][s]=TransitionCase(self.cell_index,i,q,s)
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
            assert self.kind!=CellArray.TYPE_EDGESLICE or item.index==index, f"index mismatch index={index}, item.index={item.index}"
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
    TierArray.symbols=symbols
    TierArray.states=states


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
        #print("incoming:",L)
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

    def isFoldingNode(self, v): #▷ Folding edge is only possible to one direction
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
        self.addVertex(u); self.addVertex(v);
        index=min(u.index(),v.index())
        assert index==self.E[index].index, f"{index}!={self.E[index].index},{u},{v}"

        if self.hasEdge(e): return
        if(u.index()<v.index()):
            self.E[u.index()][u].right_outgoing.append(v)
            self.E[u.index()][v].left_incoming.append(u)

        else:
            self.E[v.index()][u].left_outgoing.append(v)
            self.E[v.index()][v].right_incoming.append(u)

        self.E[index].edgeCount+=1

        self.__edgeCount+=1

    def isSplittingEdge(self,e):
        if not self.hasEdge(e):
            print("No edge for splitting edge check")
            return False
        u,v=e
        if(u.index()<v.index()):
            #print("FindFirstMerging e:",e,self.E[u.index()][v].left_incoming)
            return len(self.E[u.index()][v].right_outgoing)>1
        else:
            
            #print("FindFirstMerging e:",e,self.E[u.index()][v].right_incoming)
            return len(self.E[v.index()][v].left_outgoing)>1
        

    
    def isMergingEdge(self,e):
        if not self.hasEdge(e):
            print("No edge for merging edge check")
            return False
        u,v=e
        if(u.index()<v.index()):
            #print("FindFirstMerging e:",e,self.E[u.index()][v].left_incoming)
            return len(self.E[u.index()][v].left_incoming)>1
        else:
            
            #print("FindFirstMerging e:",e,self.E[u.index()][v].right_incoming)
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



       


        
