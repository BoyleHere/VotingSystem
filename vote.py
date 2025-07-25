import hashlib
from cryptography.fernet import Fernet

# Generate a key for encryption and decryption
key = Fernet.generate_key()
cipher_suite = Fernet(key)

def submit_vote(vote_data):
    """
    Encrypts and hashes the vote data, including the party information.

    Args:
        vote_data (str): The party name for which the vote is being cast.

    Returns:
        dict: A dictionary containing the encrypted vote and the vote hash.
    """
    # Generate SHA-256 hash of the vote data
    vote_hash = hashlib.sha256(vote_data.encode()).hexdigest()

    # Encrypt the vote data using AES
    encrypted_vote = cipher_suite.encrypt(vote_data.encode())

    # Return a dictionary
    return {'encrypted_vote': encrypted_vote, 'vote_hash': vote_hash, 'party': vote_data}  # Add party to the dictionary
