"""
Example demonstrating PlayerGold blockchain core functionality.
Shows integration of blocks, transactions, rewards, and fee management.
"""

import time
from decimal import Decimal
from cryptography.hazmat.primitives.asymmetric import ed25519

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.blockchain import (
    Block, Transaction, TransactionType, create_genesis_block,
    RewardCalculator, StakeManager, StakeType,
    FeeCalculator, TokenBurnManager, NetworkMetrics,
    AIValidatorInfo, ConsensusProof
)


def main():
    """Demonstrate blockchain core functionality."""
    print("=== PlayerGold Blockchain Core Demo ===\n")
    
    # 1. Create genesis block
    print("1. Creating genesis block...")
    genesis_block = create_genesis_block()
    print(f"Genesis block created with hash: {genesis_block.hash[:16]}...")
    print(f"Genesis block index: {genesis_block.index}")
    print()
    
    # 2. Set up fee and reward systems
    print("2. Setting up fee and reward systems...")
    fee_calculator = FeeCalculator()
    reward_calculator = RewardCalculator()
    burn_manager = TokenBurnManager(initial_supply=Decimal('1000000000'))  # 1B tokens
    stake_manager = StakeManager()
    print("Systems initialized successfully")
    print()
    
    # 3. Create some AI validators
    print("3. Setting up AI validators...")
    ai_validators = [
        AIValidatorInfo(
            node_id="ai_node_1",
            model_hash="gemma_3_4b_hash_123",
            validation_signature="sig_1",
            response_time_ms=45,
            reputation_score=0.98
        ),
        AIValidatorInfo(
            node_id="ai_node_2", 
            model_hash="mistral_3b_hash_456",
            validation_signature="sig_2",
            response_time_ms=52,
            reputation_score=0.95
        ),
        AIValidatorInfo(
            node_id="ai_node_3",
            model_hash="qwen_3_4b_hash_789",
            validation_signature="sig_3",
            response_time_ms=38,
            reputation_score=0.97
        )
    ]
    print(f"Created {len(ai_validators)} AI validators")
    print()
    
    # 4. Add some stakers
    print("4. Adding stakers...")
    stake_manager.add_stake("staker_1", Decimal('10000'), StakeType.POOL)
    stake_manager.add_stake("staker_2", Decimal('5000'), StakeType.DELEGATED, "ai_node_1")
    stake_manager.add_stake("staker_3", Decimal('15000'), StakeType.POOL)
    
    total_staked = stake_manager.get_total_staked()
    print(f"Total staked: {total_staked} PRGLD")
    print()
    
    # 5. Create some transactions
    print("5. Creating transactions...")
    
    # Generate keys for signing
    private_key = ed25519.Ed25519PrivateKey.generate()
    
    # Create network metrics for fee calculation
    network_metrics = NetworkMetrics(
        transactions_per_second=35.0,  # Medium congestion
        pending_transactions=50,
        average_block_time=2.1,
        network_capacity=100,
        timestamp=time.time()
    )
    
    transactions = []
    
    # Transfer transaction
    transfer_fee = fee_calculator.calculate_fee(TransactionType.TRANSFER, network_metrics)
    transfer_tx = Transaction(
        from_address="user_1",
        to_address="user_2",
        amount=Decimal('100.0'),
        fee=transfer_fee,
        timestamp=time.time(),
        transaction_type=TransactionType.TRANSFER,
        nonce=1
    )
    transfer_tx.sign_transaction(private_key)
    transactions.append(transfer_tx)
    
    # Stake transaction
    stake_fee = fee_calculator.calculate_fee(TransactionType.STAKE, network_metrics)
    stake_tx = Transaction(
        from_address="user_3",
        to_address="stake_pool",
        amount=Decimal('1000.0'),
        fee=stake_fee,
        timestamp=time.time(),
        transaction_type=TransactionType.STAKE,
        nonce=1
    )
    stake_tx.sign_transaction(private_key)
    transactions.append(stake_tx)
    
    # Voluntary burn transaction
    burn_tx = Transaction(
        from_address="user_4",
        to_address=burn_manager.burn_address,
        amount=Decimal('500.0'),
        fee=Decimal('0.0'),  # No fee for burns
        timestamp=time.time(),
        transaction_type=TransactionType.BURN,
        nonce=1
    )
    burn_tx.sign_transaction(private_key)
    transactions.append(burn_tx)
    
    print(f"Created {len(transactions)} transactions")
    print(f"Transfer fee: {transfer_fee} PRGLD")
    print(f"Stake fee: {stake_fee} PRGLD")
    print()
    
    # 6. Create consensus proof
    print("6. Creating consensus proof...")
    consensus_proof = ConsensusProof(
        challenge_id="challenge_block_1",
        challenge_data={"type": "mathematical", "difficulty": 7},
        solutions=[
            {"node_id": "ai_node_1", "solution": "0x1a2b3c", "signature": "ai_sig_1"},
            {"node_id": "ai_node_2", "solution": "0x1a2b3c", "signature": "ai_sig_2"},
            {"node_id": "ai_node_3", "solution": "0x1a2b3c", "signature": "ai_sig_3"}
        ],
        cross_validations=[
            {"validator": "ai_node_1", "validated": ["ai_node_2", "ai_node_3"], "result": "valid"},
            {"validator": "ai_node_2", "validated": ["ai_node_1", "ai_node_3"], "result": "valid"},
            {"validator": "ai_node_3", "validated": ["ai_node_1", "ai_node_2"], "result": "valid"}
        ],
        consensus_timestamp=time.time()
    )
    print("Consensus proof created with cross-validation")
    print()
    
    # 7. Create new block
    print("7. Creating new block...")
    new_block = Block(
        index=1,
        previous_hash=genesis_block.hash,
        timestamp=time.time(),
        transactions=transactions,
        merkle_root="",  # Will be calculated automatically
        ai_validators=ai_validators,
        consensus_proof=consensus_proof
    )
    
    print(f"Block created with hash: {new_block.hash[:16]}...")
    print(f"Block contains {len(new_block.transactions)} transactions")
    print(f"Merkle root: {new_block.merkle_root[:16]}...")
    print(f"Validated by {len(new_block.ai_validators)} AI nodes")
    print()
    
    # 8. Calculate and distribute rewards
    print("8. Calculating rewards...")
    
    total_fees = new_block.get_total_fees()
    total_rewards = new_block.get_total_rewards()  # Base reward + fees
    
    print(f"Total fees collected: {total_fees} PRGLD")
    print(f"Total rewards to distribute: {total_rewards} PRGLD")
    
    # Prepare validator data for reward calculation
    validator_data = [
        {
            'node_id': validator.node_id,
            'model_hash': validator.model_hash,
            'participation_score': validator.reputation_score,
            'validation_count': 1
        }
        for validator in ai_validators
    ]
    
    # Get staker data
    staker_data = stake_manager.get_all_stakes()
    
    # Calculate reward distribution
    reward_distribution = reward_calculator.calculate_block_rewards(
        block_index=new_block.index,
        total_reward=total_rewards,
        ai_validators=validator_data,
        stakers=staker_data
    )
    
    print(f"AI validators receive: {reward_distribution.ai_portion} PRGLD (90%)")
    print(f"Stakers receive: {reward_distribution.staker_portion} PRGLD (10%)")
    
    # Show individual AI rewards
    print("\nAI Validator Rewards:")
    for ai_reward in reward_distribution.ai_validator_rewards:
        print(f"  {ai_reward.node_id}: {ai_reward.reward_amount} PRGLD")
    
    # Show individual staker rewards
    print("\nStaker Rewards:")
    for staker_reward in reward_distribution.staker_rewards:
        print(f"  {staker_reward.staker_address}: {staker_reward.reward_amount} PRGLD")
    print()
    
    # 9. Process fee burning
    print("9. Processing fee burning...")
    
    # Process fee distribution (20% liquidity, 80% burn)
    liquidity_tx, burn_tx = burn_manager.process_fee_distribution(
        total_fee=total_fees,
        block_index=new_block.index,
        transaction_hash="fee_collection_hash"
    )
    
    print(f"Liquidity pool receives: {liquidity_tx.amount} PRGLD (20%)")
    print(f"Burned: {burn_tx.amount} PRGLD (80%)")
    
    # Process voluntary burn
    voluntary_burn_tx = burn_manager.process_voluntary_burn(
        burner_address="user_4",
        amount=Decimal('500.0'),
        block_index=new_block.index
    )
    
    print(f"Voluntary burn: {voluntary_burn_tx.amount} PRGLD")
    
    # Show updated supply info
    supply_info = burn_manager.get_supply_info()
    print(f"\nUpdated Token Supply:")
    print(f"  Total supply: {supply_info.total_supply} PRGLD")
    print(f"  Circulating supply: {supply_info.circulating_supply} PRGLD")
    print(f"  Total burned: {supply_info.total_burned} PRGLD")
    print()
    
    # 10. Validate the block
    print("10. Validating block...")
    
    is_valid = new_block.is_valid(genesis_block)
    print(f"Block validation result: {'✓ VALID' if is_valid else '✗ INVALID'}")
    
    if is_valid:
        print("Block successfully validated with:")
        print(f"  - {len(new_block.transactions)} valid transactions")
        print(f"  - {len(new_block.ai_validators)} AI validator signatures")
        print(f"  - Valid consensus proof with cross-validation")
        print(f"  - Proper chain linkage to previous block")
    
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()