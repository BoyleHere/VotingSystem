import hashlib
import json
import time

class Block:
    def __init__(self, data, previous_hash=''):
        self.timestamp = time.time()
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        return hashlib.sha256((str(self.timestamp) + str(self.data) + self.previous_hash).encode()).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        return Block("Genesis Block", "0")

    def add_block(self, data):
        previous_block = self.chain[-1]
        new_block = Block(data, previous_block.hash)
        self.chain.append(new_block)

def is_chain_valid(self):
    for i in range(1, len(self.chain)):
        current_block = self.chain[i]
        previous_block = self.chain[i - 1]

        # Check if current block's hash matches the calculated hash
        if current_block.hash != current_block.calculate_hash():
            print("Data tampering detected in block:", i)
            return False

        # Check if current block's previous hash matches the previous block's hash
        if current_block.previous_hash != previous_block.hash:
            print("Chain linkage tampered between blocks:", i, "and", i - 1)
            return False
    print("Blockchain integrity validated.")
    return True
