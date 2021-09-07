import math
import numpy as np
from queue import PriorityQueue
import random
from treelib import Node, Tree
import time as sleep_time 

MAX_BLK_SIZE = 1000

# concatenates the pid with the block number generated by that peer 
def generate_b_id(p_id, b_id):
    str_p_id = str(p_id)
    str_b_id = str(b_id)
    digits1 = len(str_p_id)
    digits2 = len(str_b_id)
    zer1 = "0"*(6 - digits1)
    zer2 = "0"*(6 - digits2)
    strng = zer1+str_p_id+zer2+str_b_id
    return strng

# concatenates the pid with the transaction number generated by that peer 
def generate_t_id(p_id, t_id):
    str_p_id = str(p_id)
    str_t_id = str(t_id)
    digits1 = len(str_p_id)
    digits2 = len(str_t_id)
    zer1 = "0"*(6 - digits1)
    zer2 = "0"*(6 - digits2)
    strng = zer1+str_p_id+zer2+str_t_id
    return strng

# sampling from the exp dist with mean Tk to deicde POW time for peer k
def generate_POW_time(Tk):
    return np.random.exponential(Tk)

# for compressed visualisation
class CompressNode(object):
    def __init__(self):
        self.node = "*"

# contains all the data of the P2P network
class P2P(object):
    def __init__(self, num_peers, z, Tx, Tk):
        self.transaction_map = {} # t_id to transaction info mapping
        self.block_map = {} # b_id to block info mapping
        self.num_peers = num_peers # number of peers in the network
        self.peers = [] # p_id to peer info mapping
        self.genesis_block = None # created and set for all peers at the start of the simulation
        self.check1 = False
        self.check2 = False

        num_fast = math.floor(num_peers*z/100)
        count_fast = 0
        self.Tx = Tx
        self.Tk = Tk

        # adding slow and fast peers to the network
        for i in range(1, num_peers+1):
            if count_fast<num_fast:
                self.peers.append(self.Peer(i,'fast', self))
            else:
                self.peers.append(self.Peer(i,'slow', self))
            count_fast += 1

        # setting the connectivity graph for the network
        self.peer_graph = self.Graph(self)
        for peer in self.peers:
            self.peer_graph.add_vertex(peer.p_id, peer.fast_slow)
            
        self.adj_mat = self.peer_graph.generate_random_graph()

        # tree structures for simulation visualisation
        self.visual_trees = []
        for i in range(num_peers):
            self.visual_trees.append(Tree())
    
    # creates genesis block with id = 0*12, adds to the start of block chain trees of all peers
    def genesis(self):
        for i in range(self.num_peers):
            self.visual_trees[i].create_node("(b_id: 000000000000, time: 0)", "000000000000", data=CompressNode())
        self.genesis_block = self.Block([], "000000000000", -1, 0)
        self.block_map["000000000000"] = self.genesis_block
        # trigger block creation at all peers
        for peer in self.peers:
            event = self.Event("cblk", -1, 0)
            peer.add_event(1, event)

    # runs the simulation for the p2p network
    def run(self, sim_time, check1, check2):
        self.check1 = check1
        self.check2 = check2
        self.genesis()
        time = 0
        clk_time = 1
        for i in range(10*sim_time):
            for peer in self.peers:
                peer.handle_events(time)
            time += clk_time
            sleep_time.sleep(0.001)

    # contains transaction info
    class Transaction(object):
        def __init__(self, t_id, payer, receiver, amt):
            self.payer = payer
            self.receiver = receiver
            self.amt = amt
            self.t_id = t_id
            self.txn_string = "%s: pID: %d pays pID: %d %d coins"%(t_id, payer, receiver, amt)
            
        def __iter__(self):
            return iter(self.vertices_dict.values())
        
        def add_vertex(self, node, fast_slow):
            self.num_vertices = self.num_vertices + 1
            new_vertex = self.p2p.Vertex(node, fast_slow)
            self.vertices_dict[node] = new_vertex
            return new_vertex
                    
        def add_edge(self, vertex_from, vertex_to, weight):
            if vertex_from not in self.vertices_dict:
                self.add_vertex(vertex_from, 0)
                
            if vertex_to not in self.vertices_dict:
                self.add_vertex(vertex_to, 0)
            
            self.vertices_dict[vertex_from].add_neighbour(self.vertices_dict[vertex_to], weight)
            # self.ver
            self.receiver = receiver
            self.amt = amt
            self.t_id = t_id
            self.txn_string = "%s: %d pays %d %d coins" % (t_id, payer, receiver, amt)

    # contains block info
    class Block(object):
        def __init__(self, txns, b_id, prev_b_id, miner):
            self.prev_b_id = prev_b_id
            self.txns = txns
            self.b_id = b_id
            self.miner = miner

    # contains node metadata for all blocks in the blockchain tree for each peer
    # each peer would have overlapping blocks but their metadata would be different, hence the need for this separate class
    class BlockTree:
        def __init__(self, b_id, length, peer):
            self.peer = peer # the peer in whose blockchain tree this node appears
            # children nodes
            self.children = []
            self.b_id = b_id            
            self.length = length # length of the branch ending at this block node        
            self.accounts = [] # account balance for each peer at this block node as per the chain 
            # to which this block node belongs in the block chain tree   


    class Event(object):
        def __init__(self, typ, data, sender):
            self.type = typ # type of the event
            self.data = data  # event metadata - bid/ tid etc
            self.sender = sender # blk/txn sender

        # defined for allowing ordering of time, event tuples in the events queue for each peer
        def __gt__(self, other):
            return False

    # contains peer info
    class Peer(object):
        def __init__(self, p_id, fast_slow, p2p):
            self.p_id = p_id
            self.pending_txs = [] # txns received or created but not yet added in any block 
            self.events = PriorityQueue() # events queue
            self.next_t = 0 # mantains number of txns generated so far for this peer
            self.next_b = 0 # mantains number of blocks generated so far for this peer
            self.p2p = p2p # p2p network to which this peer belongs
            self.fast_slow = fast_slow # fast or slow
            self.block_tree_root = self.p2p.BlockTree("000000000000", 1, self) # root of the block chain tree at this peer

            # !! change?
            # setting default number of bitcoins with the peers to 0 in the beginning
            for peer_num in range(self.p2p.num_peers):
                self.block_tree_root.accounts.append(0)
            # !!
            self.longest = ["000000000000"] # list of bids of blocks at the end of longest chains of the block tree at this peer
            self.block_node_map = {} # block id to block node mapping for this peer (different for different peers
            # as the blcok chain tree for each node differs)
            self.block_node_map["000000000000"] = self.block_tree_root # setting the root node to contain the genesis block

            file = open("peer %d"%(self.p_id), "w")
            file.write(f"{'blockID' : <10}{'depth' : ^10}{'time_of_arrival': ^10}{'parent_blockID' : >15}\n")
            file.close()

            self.add_next_transaction(0)

        # inserts a block node to the block chain tree of this peer
        def tree_insert(self, b_id, time):
            prev_b_id = self.p2p.block_map[b_id].prev_b_id # bid of the block to which thid block has to be attached
            miner = self.p2p.block_map[b_id].miner # pid of the miner of this block

            # adding the block to the tree structure for visualization
            node_val = "(b_id: %s, time: %f)" % (b_id, time)
            self.p2p.visual_trees[self.p_id-1].create_node(node_val, b_id, parent=prev_b_id, data=CompressNode())

            is_longest = False # true if the addition of this block creates the longest chain
            parent_block_node = self.block_node_map[prev_b_id]
            block_tree_node = self.p2p.BlockTree(b_id, parent_block_node.length+1, self)

            # updating the balance accounts for the chain of the block tree to which this node was inserted
            block_tree_node.accounts = parent_block_node.accounts
            for txn in self.p2p.block_map[b_id].txns:
                payer = self.p2p.transaction_map[txn].payer
                receiver = self.p2p.transaction_map[txn].receiver
                amt = self.p2p.transaction_map[txn].amt
                block_tree_node.accounts[payer-1] = parent_block_node.accounts[payer-1] - amt
                block_tree_node.accounts[receiver-1] = parent_block_node.accounts[receiver-1] + amt

            # adding mining fee
            block_tree_node.accounts[miner-1] += 50

            self.block_node_map[b_id] = block_tree_node
            # add the block to the children of its previous block
            parent_block_node.children.append(block_tree_node)

            longest_length = self.block_node_map[self.longest[0]].length # length of the longest chain in the tree
            if longest_length < block_tree_node.length:
                self.longest = [b_id] # updated the longest chains list if new longest chain formed
                is_longest = True # set if the new block creates the longest chain
            # !! to be deleted ?
            if longest_length == block_tree_node.length:
                self.longest.append(b_id)
            # !!

            file = open("peer %d"%(self.p_id), "a")
            file.write(f"{b_id : <10}{block_tree_node.length : ^10}{time : ^10}{prev_b_id : >15}\n")
            file.close()

            return is_longest

        # generates the next transaction time by sampling the delay from the last txn from an exp dist
        def add_next_transaction(self, time):
            self.next_t += 1
            t_id = generate_t_id(self.p_id, self.next_t)
            next_time = time + np.random.exponential(self.p2p.Tx)
            self.events.put((next_time, self.p2p.Event("gtxn",t_id, self.p_id)))

        # adds an event to the events queue, used when one event for one peer generates another one for another peer
        def add_event(self, time, event):
            self.events.put((time, event))

        def generate_txn(self, t_id, time):
            if self.p2p.check1:
                print("pID: %d generated txn with TxnID: %s at time: %f" %
                      (self.p_id, t_id, time))
            # choose a random peer
            peer_num = 1 + np.random.randint(self.p2p.num_peers)
            if(peer_num == self.p_id): # if self chosen, update
                if(self.p_id == 1):
                    peer_num += 1
                else:
                    peer_num -= 1
            # !! change?
            amt = np.random.uniform(1, 100, 1)
            # !!
            txn = self.p2p.Transaction(t_id, self.p_id, peer_num, amt)
            self.p2p.transaction_map[txn.t_id] = txn

            if self.p2p.check1:
                print(txn.txn_string)
            # receive own txn
            self.receive_txn(t_id, time, self.p_id)

            # set next txn time for this peer
            self.add_next_transaction(time)

        def receive_txn(self, t_id, time, sender):
            if self.p2p.check1:
                print("pID: %d received txn with TxnID: %s at time: %f from pID: %d" %
                      (self.p_id, t_id, time, sender))
            if t_id not in self.pending_txs:
                self.pending_txs.append(t_id)
                for i in range(self.p2p.num_peers):
                    if self.p2p.adj_mat[self.p_id-1][i]>0 and i+1 != sender:
                        event = self.p2p.Event("rtxn", t_id, self.p_id)
                        if(self.p2p.peers[i].fast_slow==1 and self.fast_slow==1):
                            cij = 100
                        else:
                            cij = 5
                        txn_sz = 8
                        delay = time+(self.p2p.adj_mat[self.p_id-1][i]+(txn_sz/cij)+np.random.exponential(96/cij))
                        self.p2p.peers[i].add_event(delay, event)

        def receive_block(self, b_id, time, sender):
            if self.p2p.check2:
                print("pID: %d received block with BlkID: %s at time: %f from pID: %d" %
                      (self.p_id, b_id, time, sender))
            if self.verify_block(b_id, time): # if block is verified
                # remove block txns from pending list
                for txn in self.p2p.block_map[b_id].txns:
                    self.rem_txn(txn)
                # insert the  block node into the tree              
                is_longest = self.tree_insert(b_id, time)

                # forward the block to neighbours
                for i in range(self.p2p.num_peers):
                    if self.p2p.adj_mat[self.p_id-1][i]>0 and i+1 != sender:
                        event = self.p2p.Event("rblk", b_id, self.p_id)
                        if(self.p2p.peers[i].fast_slow==1 and self.fast_slow==1):
                            cij = 100
                        else:
                            cij = 5
                        blk_size = max(8*len(self.p2p.block_map[b_id].txns), 8)
                        delay = time+(self.p2p.adj_mat[self.p_id-1][i]+(blk_size/cij)+np.random.exponential(96/cij))
                        self.p2p.peers[i].add_event(delay, event)
                # start mining if longest chain formed
                if is_longest:
                    self.create_block(time)
            else:
                if self.p2p.check2:
                    print("INVALID BLOCK!!")
                pass

        def verify_block(self, b_id, time):
            if self.p2p.check2:
                print("pID: %d verifying BlkID: %s at time: %f" % (
                    self.p_id, b_id, time))
            block = self.p2p.block_map[b_id]

            # check if parent exists, return false otherwise
            try:
                parent_block_node = self.block_node_map[block.prev_b_id]
            except:
                if self.p2p.check2:
                    print("Previous block has not arrived!")
                return False

            for child in parent_block_node.children:
                if(child.b_id == b_id):
                    if self.p2p.check2:
                        print("Block received earlier!")
                    return False

            pay_sum = [] # stores total amount payed by each peer in all txns in this block 
            for i in range(self.p2p.num_peers):
                pay_sum.append(0)

            # check that payed sum does not exceed present balance at any point, return false otherwise 
            for t_id in block.txns:
                amt = self.p2p.transaction_map[t_id].amt
                payer_id = self.p2p.transaction_map[t_id].payer
                pay_sum[payer_id-1] += amt
                if parent_block_node.accounts[payer_id-1] < pay_sum[payer_id-1]:
                    if self.p2p.check2:
                        print("INVALID - pID: %d trying to pay more than its balance of %d" % (
                           payer_id, parent_block_node.accounts[payer_id-1]))
                    return False

            if self.p2p.check2:
                print("VERIFIED!!")

            return True # iff all checks passed

        # remove from pending txns if present
        def rem_txn(self, t_id):
            try:
                self.pending_txs.remove(t_id)
            except:
                pass

        # start mining a new block
        def create_block(self, time):
            # choose random subset of txns
            ttxns = []
            if len(self.pending_txs) < MAX_BLK_SIZE:
                ttxns = self.pending_txs
            else:
                ttxns = random.sample(self.pending_txs, MAX_BLK_SIZE)

            prev_b_id = self.longest[0]

            # filtering out invalid txns
            pay_sum = [] # stores total amount payed by each peer in all selected txns
            for i in range(self.p2p.num_peers):
                pay_sum.append(0)

            parent_block_node = self.block_node_map[prev_b_id]
            # check that payed sum does not exceed present balance at any point, remove txn otherwise 
            txns = []
            for t_id in ttxns:
                amt = self.p2p.transaction_map[t_id].amt
                payer_id = self.p2p.transaction_map[t_id].payer
                pay_sum[payer_id-1] += amt
                if parent_block_node.accounts[payer_id-1] >= pay_sum[payer_id-1]:
                    txns.append(t_id)


            self.next_b += 1 # increment number of blks generated by this peer

            b_id = generate_b_id(self.p_id, self.next_b) # generate a blk id
            current_block = self.p2p.Block(
                txns, b_id, prev_b_id, self.p_id)
            self.p2p.block_map[b_id] = current_block

            if self.p2p.check2:
                print("pID: %d started mining block with BlkID: %s at time: %f" % (self.p_id,
                    b_id, time))

            # generate POW time
            # !! change
            tk = generate_POW_time(Tk[self.p_id-1])
            # !!

            # add broadcast event at POW time delay to own events queue
            event = self.p2p.Event("bblk", b_id, self.p_id)
            self.events.put((time + tk, event))

        # processes broadcast event
        def broadcast_block(self, b_id, time):
            current_block = self.p2p.block_map[b_id]
            if self.longest[0] == current_block.prev_b_id:
                if self.p2p.check2:
                    print("pID: %d broadcasted BlkID: %s at time %f" % (
                        self.p_id, b_id, time))

                # receive own block
                self.receive_block(b_id, time, self.p_id)


        # event handler, shedules the event to be executed by popping it from the events queue,
        # and invoking the correct handler
        def handle_events(self, time):
            if self.events.empty():
                return
            event_time, event = self.events.get()
            while math.ceil(event_time) == math.ceil(time):
                if(event.type == "gtxn"):
                    self.generate_txn(event.data, event_time)
                if(event.type == "rtxn"):
                    self.receive_txn(event.data, event_time, event.sender)
                if(event.type == "rblk"):
                    self.receive_block(event.data, event_time, event.sender)
                if(event.type == "cblk"):
                    self.create_block(time)
                if(event.type == "bblk"):
                    self.broadcast_block(event.data, event_time)
                if self.events.empty():
                    return
                event_time, event = self.events.get()
            self.events.put((event_time, event))

    # for connecting peers
    #class to convert each peer into graph node with peer_id and its fast_slow
    class Vertex(object):
        def __init__(self, vertex, fast_slow):
            self.fast_slow = fast_slow
            self.id = vertex
            self.neighbours = {}
            
        def __str__(self) -> str:
            return str(self.id) + ' connected to: ' + str([x.id for x in self.neighbours])
        
        #add the adjacent peers of the peer corresponding to this vertex
        def add_neighbour(self, neighbour, weight):
            if neighbour not in self.neighbours.keys():
                self.neighbours[neighbour] = weight

        #get the adjacent peers of the peer corresponding to this vertex
        def get_connections(self):
            return self.neighbours.keys()
        
        def get_id(self):
            return self.id

        #get the weight of edge between given neughbour and the peer corresponding to this vertex
        def get_weight(self, neighbor):
            return self.neighbours[neighbor]
                              
        def __repr__(self) -> str:
            return str(self.neighbours)
        
    # graph of peers
    class Graph(object):
        def __init__(self, p2p):
            self.vertices_dict = {}
            self.num_vertices = 0
            self.adj_matrix = None
            self.p2p = p2p
            self.num_edges = 0
            self.in_graph = set()
            self.is_complete = False
            
        def __iter__(self):
            return iter(self.vertices_dict.values())
        
        #add vertex to the graph
        def add_vertex(self, node, fast_slow):
            self.num_vertices = self.num_vertices + 1
            new_vertex = self.p2p.Vertex(node, fast_slow)
            self.vertices_dict[node] = new_vertex
            return new_vertex
        
        #add edge to the graph          
        def add_edge(self, vertex_from, vertex_to, weight):
            if vertex_from not in self.vertices_dict:
                self.add_vertex(vertex_from, 0)
                
            if vertex_to not in self.vertices_dict:
                self.add_vertex(vertex_to, 0)
            
            self.vertices_dict[vertex_from].add_neighbour(self.vertices_dict[vertex_to], weight)
            self.num_edges += 1
        
        #get graph vertices  
        def get_vertices(self):
            return self.vertices_dict.keys() 
        
        # helper function for generate_random_graph
        def _generate_random_graph(self, n):
            if (self.is_complete):
                return
            if len(self.in_graph)==self.num_vertices:
                self.is_complete = True
                for i in range(self.num_vertices):
                    for j in range(self.num_vertices):
                        if(self.adj_matrix[i][j]==0 and i!=j):
                            flag = np.random.randint(0, 2)
                            if(flag==1):
                                p_xy = np.random.uniform(10, 500)
                                self.add_edge(i+1, j+1, p_xy)
                                self.adj_matrix[i][j] = p_xy
                                self.adj_matrix[i][j] = p_xy
                return

            num_c = np.random.randint(1, self.num_vertices)
            children = np.random.randint(1, self.num_vertices+1, size=num_c)
            for c in children:
                if n!=c:
                    p_xy = np.random.uniform(10, 500)
                    self.add_edge(n, c, p_xy)
                    self.adj_matrix[n-1][c-1] = p_xy
                    self.adj_matrix[c-1][n-1] = p_xy
                    self.in_graph.add(c)
            for c in children:
                if (n!=c):
                    self._generate_random_graph(c)

        # creates a connected graph of peers in which each peer is connected to a random number of peers
        def generate_random_graph(self):
            self.adj_matrix = np.zeros(shape=(self.num_vertices, self.num_vertices), dtype=np.int32)
            r = np.random.randint(1, self.num_vertices+1)
            self.in_graph.add(r)
            self._generate_random_graph(r)
            
            return self.adj_matrix


print("P2P simulation")

print("Enter simulation time in milli seconds: ", end="")
sim_time = int(input())

print("Enter number of peers: ", end="")
num_peers = int(input())

print("Enter percentage of fast peers: ", end="")
z = int(input())

print("Enter Tx(mean inter-transaction gap) in milli seconds: ", end="")
Tx = int(input())

Tk = []
for i in range(num_peers):
    print("Enter Tk(mean POW time) for peer k = %d in milli seconds :"%(i+1), end="")
    Tk.append(int(input()))

print("Track txn generation, loopless forwarding and latencies?: (Y/N)", end="")
check1 = input()

print("Track blk creation, broadcast, verification, fork resolution?: (Y/N)", end="")
check2 = input()

p2p = P2P(num_peers, z, Tx, Tk)
p2p.run(sim_time, check1=="Y", check2=="Y")


for i in range(p2p.num_peers):
    print("View the blockchain tree for peer %d? (Y/N)"%(i+1))
    response = input()
    if response=="Y":
        print("Compress? (Y/N)")
        cmprs = input()
        if cmprs=="Y":
            p2p.visual_trees[i].show(data_property="node")
        else:
            p2p.visual_trees[i].show()
