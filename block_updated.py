import math
import numpy as np
from queue import PriorityQueue
import random

BLK_SIZE = 5


def generate_b_id(p_id, b_id):
    digits = len(str(p_id))
    p_num = p_id * (10**digits)

    return p_num + b_id


def generate_t_id(p_id, t_id):
    digits = len(str(p_id))
    p_num = p_id * (10**digits)

    return p_num + t_id


def generate_POW_time(Tk):
    return math.floor(np.random.exponential(Tk))


def generate_txn_times(Tk, num_txns):
    txn_times = []
    txn_time = 0
    for i in range(num_txns):
        txn_time += math.floor(np.random.exponential(Tk))
        txn_times.append(txn_time)
    return txn_times


def random_delays(minm, maxm, n):
    return minm + np.random.randint((maxm - minm), size=(n, n))


class P2P(object):
    def __init__(self, num_peers):
        self.transaction_map = {}
        self.block_map = {}
        self.account = {}
        self.num_peers = num_peers
        self.peers = []
        minm = 1
        maxm = 5
        self.delays = random_delays(minm, maxm, self.num_peers)
        for i in range(1, num_peers+1):
            self.peers.append(self.Peer(i, self))

    def genesis(self):
        pass

    def run(self, time):
        for i in range(1, time+1):
            print("running %d" % (i))
            for peer in self.peers:
                peer.handle_events(i)

    class Transaction(object):
        def __init__(self, t_id, payer, receiver, amt):
            self.payer = 0
            self.receiver = 0
            self.amt = 0
            self.t_id = t_id

    class Block(object):
        def __init__(self, txns, b_id, prev_b_id):
            self.prev_b_id = prev_b_id
            self.txns = txns
            self.b_id = b_id

    class Event(object):
        def __init__(self, typ, data):
            self.type = typ
            self.data = data

        def __gt__(self, other):
            return False

    class Peer(object):
        def __init__(self, p_id, p2p):
            self.p_id = p_id
            self.pending_txs = []
            self.events = PriorityQueue()
            self.next_t = 0
            self.next_b = 0
            self.p2p = p2p
            self.current_block = self.p2p.Block(None, None, None)
            self.block_chain = []
            self.coins = 100
            self.txn_times = generate_txn_times(10, 5)
            for txn_num in range(1, len(self.txn_times)+1):
                t_id = generate_t_id(self.p_id, txn_num)
                self.events.put(
                    (self.txn_times[txn_num-1], self.p2p.Event("gtxn", t_id)))

        def add_event(self, time, event):
            self.events.put((time, event))

        def generate_txn(self, t_id, time):
            peer_num = 1 + np.random.randint(self.p2p.num_peers+1)
            if(peer_num == self.p_id):
                if(self.p_id == 1):
                    peer_num += 1
                else:
                    peer_num -= 1
            amt = 1
            txn = self.p2p.Transaction(t_id, self.p_id, peer_num, amt)
            self.p2p.transaction_map[txn.t_id] = txn
            print("pid %d generated a transaction with TxnID: %d at time: %d" %
                  (self.p_id, t_id, time))
            for peer in self.p2p.peers:
                if(peer.p_id != self.p_id):
                    event = self.p2p.Event("rtxn", txn.t_id)
                    peer.add_event(
                        time+self.p2p.delays[self.p_id-1][peer.p_id-1], event)

        def receive_txn(self, t_id, time):
            if self.p2p.peers[self.p2p.transaction_map[t_id].payer].coins >= self.p2p.transaction_map[t_id].amt:
                self.pending_txs.append(t_id)
                print("pid %d received transaction with TxnID: %d at time: %d" % (
                    self.p_id, t_id, time))
            else:
                print("INVALID: pid %d received transaction with TxnID: %d at time: %d" % (
                    self.p_id, t_id, time))

        def receive_block(self, b_id):
            if verify_block(b_id):
                self.block_chain.append(b_id)
                if b_id != self.current_block.b_id:
                    for txn in self.block_chain[-1]:
                        self.rem_txn(txn)

        def verify_block(self, b_id):
            block = self.p2p.block_map[b_id]
            if (block.prev_b_id != self.block_chain[-1]):
                return False

            pay_sum = []
            for i in range(self.p2p.num_peers):
                pay_sum.append(0)

            present_amt = []
            for i in range(self.p2p.num_peers):
                present_amt.append(1000)
            for blk_id in self.block_chain:
                blk = self.p2p.block_map[blk_id]
                for t_id in blk.txns:
                    amt = self.p2p.transaction_map[t_id].amt
                    payer_id = self.p2p.transaction_map[t_id].payer
                    receiver_id = self.p2p.transaction_map[t_id].receiver
                    present_amt[payer_id-1] -= amt
                    present_amt[receiver_id-1] += amt

            for t_id in block.txns:
                amt = self.p2p.transaction_map[t_id].amt
                payer_id = self.p2p.transaction_map[t_id].payer
                pay_sum[payer_id-1] += amt
                if present_amt[payer_id-1] < pay_sum[payer_id-1]:
                    return False
            return True

        def rem_txn(self, t_id):
            try:
                self.pending_txs.remove(t_id)
            except:
                pass

        def create_block(self):
            txns = []
            if len(self.pending_txs) < BLK_SIZE:
                txns = self.pending_txs
            else:
                txns = random.sample(self.pending_txs, BLK_SIZE)
                # remove from pending transactions when broadcast

            self.next_b += 1
            b_id = generate_b_id(self.p_id, self.next_b)
            self.current_block = self.p2p.Block(
                txns, b_id, self.block_chain[-1])
            self.p2p.block_map[b_id] = self.current_block
            Tk = 5
            tk = generate_POW_time(Tk)
            event = self.p2p.Event("bblk", b_id)
            self.events.put(time + tk, event)

        def broadcast_block(self):
            if(self.block_chain[-1] == self.current_block.b_id):
                for txn in self.current_block.txns:
                    try:
                        self.pending_txs.remove(txn)
                    except:
                        pass
                self.receive_block(self.current_block.b_id)
                for peer in self.p2p.peers:
                    if(peer.p_id != self.p_id):
                        event = self.p2p.Event("rblk", self.current_block.b_id)
                        peer.add_event(
                            time+self.p2p.delays[self.p_id-1][peer.p_id-1], event)
                else:
                    self.current_block = self.p2p.Block(None, None, None)

        def handle_events(self, time):
            if self.events.empty():
                return
            event_time, event = self.events.get()
            while event_time == time:
                if(event.type == "gtxn"):
                    self.generate_txn(event.data, time)
                if(event.type == "rtxn"):
                    self.receive_txn(event.data, time)
                if(event.type == "rblk"):
                    self.receive_block(event.data)
                if(event.type == "bblk"):
                    self.broadcast_block()
                if self.events.empty():
                    return
                event_time, event = self.events.get()
            self.events.put((event_time, event))


p2p = P2P(5)
p2p.run(100)
