#!/usr/bin/env python3
"""
PlayerGold Testnet Faucet
Distribuye tokens PRGLD de prueba para desarrollo y testing

Uso:
    python scripts/testnet_faucet.py --address PG123... --amount 1000
    python scripts/testnet_faucet.py --wallet-file wallet.json --amount 500
"""

import asyncio
import sys
import argparse
import logging
import json
from pathlib import Path
from datetime import datetime
import hashlib

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestnetFaucet:
    """Testnet faucet for distributing test tokens"""
    
    def __init__(self):
        self.faucet_address = "PGfaucet" + "0" * 33
        self.max_amount_per_request = 1000  # 1K PRGLD max
        self.daily_limit_per_address = 5000  # 5K PRGLD per day
        self.request_history = self._load_request_history()
        
    def _load_request_history(self):
        """Load faucet request history"""
        history_file = Path('data/testnet/faucet_history.json')
        if history_file.exists():
            with open(history_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_request_history(self):
        """Save faucet request history"""
        history_file = Path('data/testnet/faucet_history.json')
        history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(history_file, 'w') as f:
            json.dump(self.request_history, f, indent=2)
    
    async def request_tokens(self, recipient_address: str, amount: int) -> dict:
        """
        Request tokens from faucet
        
        Args:
            recipient_address: Address to send tokens to
            amount: Amount of PRGLD to send
            
        Returns:
            dict: Result of faucet request
        """
        logger.info(f"Faucet request: {amount} PRGLD to {recipient_address}")
        
        # Validate amount
        if amount <= 0:
            return {
                'success': False,
                'error': 'Amount must be positive'
            }
        
        if amount > self.max_amount_per_request:
            return {
                'success': False,
                'error': f'Amount exceeds maximum of {self.max_amount_per_request} PRGLD'
            }
        
        # Check daily limit
        today = datetime.utcnow().date().isoformat()
        address_history = self.request_history.get(recipient_address, {})
        daily_total = address_history.get(today, 0)
        
        if daily_total + amount > self.daily_limit_per_address:
            remaining = self.daily_limit_per_address - daily_total
            return {
                'success': False,
                'error': f'Daily limit exceeded. Remaining today: {remaining} PRGLD'
            }
        
        # Create faucet transaction
        transaction = await self._create_faucet_transaction(recipient_address, amount)
        
        # Update history
        if recipient_address not in self.request_history:
            self.request_history[recipient_address] = {}
        self.request_history[recipient_address][today] = daily_total + amount
        self._save_request_history()
        
        logger.info(f"✓ Faucet sent {amount} PRGLD to {recipient_address}")
        logger.info(f"  Transaction ID: {transaction['tx_id']}")
        logger.info(f"  Daily usage: {daily_total + amount}/{self.daily_limit_per_address} PRGLD")
        
        return {
            'success': True,
            'transaction': transaction,
            'amount': amount,
            'recipient': recipient_address,
            'daily_remaining': self.daily_limit_per_address - (daily_total + amount)
        }
    
    async def _create_faucet_transaction(self, recipient_address: str, amount: int) -> dict:
        """Create a faucet transaction"""
        timestamp = datetime.utcnow().isoformat()
        
        transaction = {
            'type': 'faucet_transfer',
            'from_address': self.faucet_address,
            'to_address': recipient_address,
            'amount': amount,
            'timestamp': timestamp,
            'memo': f'Testnet faucet - {amount} PRGLD',
            'network_id': 'playergold-testnet-genesis',
            'fee': 0,  # No fees for faucet transactions
            'nonce': self._generate_nonce()
        }
        
        # Calculate transaction ID
        tx_string = json.dumps(transaction, sort_keys=True)
        transaction['tx_id'] = hashlib.sha256(tx_string.encode()).hexdigest()
        
        # Save transaction to pending pool
        await self._save_transaction(transaction)
        
        return transaction
    
    def _generate_nonce(self) -> int:
        """Generate transaction nonce"""
        # Simple nonce based on timestamp
        return int(datetime.utcnow().timestamp() * 1000000)
    
    async def _save_transaction(self, transaction: dict):
        """Save transaction to pending pool"""
        pending_dir = Path('data/testnet/pending_transactions')
        pending_dir.mkdir(parents=True, exist_ok=True)
        
        tx_file = pending_dir / f"{transaction['tx_id']}.json"
        with open(tx_file, 'w') as f:
            json.dump(transaction, f, indent=2)
        
        logger.debug(f"Saved pending transaction: {transaction['tx_id']}")
    
    async def get_faucet_status(self) -> dict:
        """Get faucet status and statistics"""
        today = datetime.utcnow().date().isoformat()
        
        # Calculate daily statistics
        daily_requests = 0
        daily_amount = 0
        
        for address, history in self.request_history.items():
            if today in history:
                daily_requests += 1
                daily_amount += history[today]
        
        # Calculate total statistics
        total_requests = len(self.request_history)
        total_amount = sum(
            sum(daily_amounts.values()) 
            for daily_amounts in self.request_history.values()
        )
        
        return {
            'faucet_address': self.faucet_address,
            'max_amount_per_request': self.max_amount_per_request,
            'daily_limit_per_address': self.daily_limit_per_address,
            'today': {
                'date': today,
                'requests': daily_requests,
                'amount_distributed': daily_amount
            },
            'total': {
                'unique_addresses': total_requests,
                'amount_distributed': total_amount
            }
        }
    
    async def check_address_limit(self, address: str) -> dict:
        """Check remaining daily limit for an address"""
        today = datetime.utcnow().date().isoformat()
        address_history = self.request_history.get(address, {})
        daily_used = address_history.get(today, 0)
        remaining = self.daily_limit_per_address - daily_used
        
        return {
            'address': address,
            'daily_limit': self.daily_limit_per_address,
            'used_today': daily_used,
            'remaining_today': remaining,
            'can_request': remaining > 0
        }


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='PlayerGold Testnet Faucet',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Request tokens for an address
  python scripts/testnet_faucet.py --address PG123abc... --amount 1000
  
  # Request tokens for wallet file
  python scripts/testnet_faucet.py --wallet-file wallets/testnet/my_wallet.json --amount 500
  
  # Check faucet status
  python scripts/testnet_faucet.py --status
  
  # Check address limit
  python scripts/testnet_faucet.py --check-limit PG123abc...
        """
    )
    
    parser.add_argument(
        '--address',
        type=str,
        help='Recipient address for tokens'
    )
    
    parser.add_argument(
        '--wallet-file',
        type=str,
        help='Path to wallet file (will extract address)'
    )
    
    parser.add_argument(
        '--amount',
        type=int,
        default=1000,
        help='Amount of PRGLD to request (default: 1000)'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show faucet status and statistics'
    )
    
    parser.add_argument(
        '--check-limit',
        type=str,
        help='Check daily limit for specific address'
    )
    
    args = parser.parse_args()
    
    try:
        faucet = TestnetFaucet()
        
        if args.status:
            # Show faucet status
            status = await faucet.get_faucet_status()
            
            print("\n" + "=" * 50)
            print("🚰 PLAYERGOLD TESTNET FAUCET STATUS")
            print("=" * 50)
            print(f"Faucet Address: {status['faucet_address']}")
            print(f"Max per request: {status['max_amount_per_request']:,} PRGLD")
            print(f"Daily limit per address: {status['daily_limit_per_address']:,} PRGLD")
            print("")
            print("Today's Activity:")
            print(f"  Requests: {status['today']['requests']}")
            print(f"  Amount distributed: {status['today']['amount_distributed']:,} PRGLD")
            print("")
            print("Total Statistics:")
            print(f"  Unique addresses served: {status['total']['unique_addresses']}")
            print(f"  Total distributed: {status['total']['amount_distributed']:,} PRGLD")
            print("=" * 50)
            
        elif args.check_limit:
            # Check address limit
            limit_info = await faucet.check_address_limit(args.check_limit)
            
            print(f"\n📊 Daily Limit for {args.check_limit}:")
            print(f"  Used today: {limit_info['used_today']:,} PRGLD")
            print(f"  Remaining: {limit_info['remaining_today']:,} PRGLD")
            print(f"  Daily limit: {limit_info['daily_limit']:,} PRGLD")
            print(f"  Can request: {'✓ Yes' if limit_info['can_request'] else '✗ No'}")
            
        else:
            # Request tokens
            recipient_address = None
            
            if args.wallet_file:
                # Extract address from wallet file
                wallet_path = Path(args.wallet_file)
                if not wallet_path.exists():
                    print(f"❌ Wallet file not found: {args.wallet_file}")
                    sys.exit(1)
                
                with open(wallet_path, 'r') as f:
                    wallet_data = json.load(f)
                    recipient_address = wallet_data.get('address')
                
                if not recipient_address:
                    print(f"❌ No address found in wallet file: {args.wallet_file}")
                    sys.exit(1)
                    
            elif args.address:
                recipient_address = args.address
            else:
                print("❌ Must specify either --address or --wallet-file")
                sys.exit(1)
            
            # Make faucet request
            result = await faucet.request_tokens(recipient_address, args.amount)
            
            if result['success']:
                print(f"\n✅ Faucet Request Successful!")
                print(f"   Amount: {result['amount']:,} PRGLD")
                print(f"   Recipient: {result['recipient']}")
                print(f"   Transaction ID: {result['transaction']['tx_id']}")
                print(f"   Remaining today: {result['daily_remaining']:,} PRGLD")
                print(f"\n💡 Transaction will be included in the next block")
            else:
                print(f"\n❌ Faucet Request Failed: {result['error']}")
                sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error in faucet operation: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())