def tally_votes(chain):
    """
    Tallies the votes from the blockchain, grouping votes by party.

    Args:
        chain (list): The blockchain containing vote data.

    Returns:
        dict: A dictionary where keys are parties and values are vote counts.
    """
    vote_counts = {}
    for block in chain[1:]:  # Skip the genesis block
        # Access the party from the dictionary
        party = block.data['party']
        if party in vote_counts:
            vote_counts[party] += 1
        else:
            vote_counts[party] = 1
    return vote_counts
