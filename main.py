import hashlib
import time
import json

class Block:
    def __init__(self, index, previous_hash, timestamp, data, hash):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.data = data
        self.hash = hash

    def __str__(self):
        return json.dumps({
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "data": self.data,
            "hash": self.hash
        }, indent=4)

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        # Create the first block
        genesis_data = "Genesis Block"
        genesis_hash = self.calculate_hash(0, "0", genesis_data)
        genesis_block = Block(0, "0", time.time(), genesis_data, genesis_hash)
        self.chain.append(genesis_block)

    def calculate_hash(self, index, previous_hash, data):
        value = f"{index}{previous_hash}{data}{time.time()}".encode()
        return hashlib.sha256(value).hexdigest()

    def add_block(self, data):
        previous_block = self.chain[-1]
        new_index = previous_block.index + 1
        new_timestamp = time.time()
        new_hash = self.calculate_hash(new_index, previous_block.hash, data)
        new_block = Block(new_index, previous_block.hash, new_timestamp, data, new_hash)
        self.chain.append(new_block)
        return new_block

    def is_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]

            # Check if the hash of the current block is correct
            if current_block.hash != self.calculate_hash(current_block.index, current_block.previous_hash, current_block.data):
                return False

            # Check the previous hash
            if current_block.previous_hash != previous_block.hash:
                return False

        return True

    def __str__(self):
        return "\n".join(str(block) for block in self.chain)

# Example usage
if __name__ == "__main__":
    blockchain = Blockchain()
    print("Genesis Block:")
    print(blockchain.chain[0])

    # Add some blocks
    blockchain.add_block("First transaction")
    blockchain.add_block("Second transaction")

    print("\nBlockchain:")
    print(blockchain)

    print("\nIs blockchain valid?")
    print(blockchain.is_valid())
