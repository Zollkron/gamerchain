#!/usr/bin/env python3
"""
Test script for PlayerGold Multi-Node System

Tests the complete multi-node blockchain implementation:
- Node startup and initialization
- P2P network connectivity
- Genesis block creation
- Consensus mechanism
- Block production
- API endpoints
"""

import asyncio
import time
import requests
import json
import logging
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MultiNodeSystemTester:
    """
    Comprehensive tester for the multi-node system
    """
    
    def __init__(self):
        self.nodes = [
            {
                'node_id': 'testnet_pioneer_1',
                'p2p_port': 18080,
                'api_port': 19080,
                'api_url': 'http://127.0.0.1:19080'
            },
            {
                'node_id': 'testnet_pioneer_2', 
                'p2p_port': 18081,
                'api_port': 19081,
                'api_url': 'http://127.0.0.1:19081'
            }
        ]
        
        self.test_results = {}
    
    async def run_all_tests(self):
        """Run all system tests"""
        logger.info("=" * 60)
        logger.info("🧪 STARTING PLAYERGOLD MULTI-NODE SYSTEM TESTS")
        logger.info("=" * 60)
        
        # Test 1: Node Health Checks
        await self.test_node_health()
        
        # Test 2: Network Status
        await self.test_network_status()
        
        # Test 3: Genesis Block Creation
        await self.test_genesis_creation()
        
        # Test 4: Block Production
        await self.test_block_production()
        
        # Test 5: Consensus Mechanism
        await self.test_consensus()
        
        # Test 6: API Functionality
        await self.test_api_endpoints()
        
        # Print results
        self.print_test_results()
    
    async def test_node_health(self):
        """Test node health endpoints"""
        logger.info("🏥 Testing node health endpoints...")
        
        for node in self.nodes:
            try:
                response = requests.get(f"{node['api_url']}/api/v1/health", timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ {node['node_id']} health check passed")
                    logger.info(f"   Status: {data.get('status')}")
                    logger.info(f"   Network: {data.get('network')}")
                    logger.info(f"   Blockchain height: {data.get('blockchain_height')}")
                    logger.info(f"   Peer count: {data.get('peer_count')}")
                    logger.info(f"   Genesis created: {data.get('genesis_created')}")
                    
                    self.test_results[f"{node['node_id']}_health"] = True
                else:
                    logger.error(f"❌ {node['node_id']} health check failed: HTTP {response.status_code}")
                    self.test_results[f"{node['node_id']}_health"] = False
                    
            except Exception as e:
                logger.error(f"❌ {node['node_id']} health check failed: {e}")
                self.test_results[f"{node['node_id']}_health"] = False
        
        await asyncio.sleep(2)
    
    async def test_network_status(self):
        """Test network status endpoints"""
        logger.info("🌐 Testing network status endpoints...")
        
        for node in self.nodes:
            try:
                response = requests.get(f"{node['api_url']}/api/v1/network/status", timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ {node['node_id']} network status retrieved")
                    logger.info(f"   Blockchain height: {data.get('blockchain', {}).get('height')}")
                    logger.info(f"   Peer count: {data.get('p2p', {}).get('peer_count')}")
                    logger.info(f"   Consensus status: {data.get('consensus', {}).get('is_mining')}")
                    
                    self.test_results[f"{node['node_id']}_network_status"] = True
                else:
                    logger.error(f"❌ {node['node_id']} network status failed: HTTP {response.status_code}")
                    self.test_results[f"{node['node_id']}_network_status"] = False
                    
            except Exception as e:
                logger.error(f"❌ {node['node_id']} network status failed: {e}")
                self.test_results[f"{node['node_id']}_network_status"] = False
        
        await asyncio.sleep(2)
    
    async def test_genesis_creation(self):
        """Test genesis block creation"""
        logger.info("🏗️  Testing genesis block creation...")
        
        # Wait for genesis block creation (up to 60 seconds)
        genesis_created = False
        max_wait = 60
        wait_time = 0
        
        while not genesis_created and wait_time < max_wait:
            try:
                response = requests.get(f"{self.nodes[0]['api_url']}/api/v1/health", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('genesis_created'):
                        genesis_created = True
                        logger.info("✅ Genesis block created successfully!")
                        self.test_results['genesis_creation'] = True
                        break
                
                logger.info(f"⏳ Waiting for genesis block creation... ({wait_time}s/{max_wait}s)")
                await asyncio.sleep(5)
                wait_time += 5
                
            except Exception as e:
                logger.error(f"Error checking genesis status: {e}")
                await asyncio.sleep(5)
                wait_time += 5
        
        if not genesis_created:
            logger.error("❌ Genesis block creation timed out")
            self.test_results['genesis_creation'] = False
    
    async def test_block_production(self):
        """Test block production (10-second intervals)"""
        logger.info("⏰ Testing block production...")
        
        try:
            # Get initial blockchain height
            response = requests.get(f"{self.nodes[0]['api_url']}/api/v1/network/status", timeout=5)
            if response.status_code == 200:
                initial_height = response.json().get('blockchain', {}).get('height', 0)
                logger.info(f"Initial blockchain height: {initial_height}")
                
                # Wait 15 seconds for at least one new block
                logger.info("⏳ Waiting 15 seconds for block production...")
                await asyncio.sleep(15)
                
                # Check new height
                response = requests.get(f"{self.nodes[0]['api_url']}/api/v1/network/status", timeout=5)
                if response.status_code == 200:
                    new_height = response.json().get('blockchain', {}).get('height', 0)
                    logger.info(f"New blockchain height: {new_height}")
                    
                    if new_height > initial_height:
                        logger.info(f"✅ Block production working! {new_height - initial_height} new blocks")
                        self.test_results['block_production'] = True
                    else:
                        logger.error("❌ No new blocks produced")
                        self.test_results['block_production'] = False
                else:
                    logger.error("❌ Failed to get blockchain status")
                    self.test_results['block_production'] = False
            else:
                logger.error("❌ Failed to get initial blockchain status")
                self.test_results['block_production'] = False
                
        except Exception as e:
            logger.error(f"❌ Block production test failed: {e}")
            self.test_results['block_production'] = False
    
    async def test_consensus(self):
        """Test consensus mechanism"""
        logger.info("🤝 Testing consensus mechanism...")
        
        try:
            # Check consensus status on both nodes
            consensus_working = True
            
            for node in self.nodes:
                response = requests.get(f"{node['api_url']}/api/v1/network/status", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    consensus_data = data.get('consensus', {})
                    
                    logger.info(f"📊 {node['node_id']} consensus status:")
                    logger.info(f"   Active validators: {consensus_data.get('active_validators')}")
                    logger.info(f"   Consensus threshold: {consensus_data.get('consensus_threshold')}")
                    logger.info(f"   Current block reward: {consensus_data.get('current_block_reward')}")
                    
                    if consensus_data.get('active_validators', 0) < 2:
                        consensus_working = False
                        logger.error(f"❌ {node['node_id']} has insufficient active validators")
                else:
                    consensus_working = False
                    logger.error(f"❌ Failed to get consensus status from {node['node_id']}")
            
            self.test_results['consensus'] = consensus_working
            
            if consensus_working:
                logger.info("✅ Consensus mechanism working correctly")
            else:
                logger.error("❌ Consensus mechanism has issues")
                
        except Exception as e:
            logger.error(f"❌ Consensus test failed: {e}")
            self.test_results['consensus'] = False
    
    async def test_api_endpoints(self):
        """Test various API endpoints"""
        logger.info("🔗 Testing API endpoints...")
        
        endpoints = [
            '/api/v1/health',
            '/api/v1/network/status',
            '/api/v1/blockchain/stats'
        ]
        
        for node in self.nodes:
            for endpoint in endpoints:
                try:
                    response = requests.get(f"{node['api_url']}{endpoint}", timeout=5)
                    
                    if response.status_code == 200:
                        logger.info(f"✅ {node['node_id']}{endpoint} - OK")
                        self.test_results[f"{node['node_id']}{endpoint}"] = True
                    else:
                        logger.error(f"❌ {node['node_id']}{endpoint} - HTTP {response.status_code}")
                        self.test_results[f"{node['node_id']}{endpoint}"] = False
                        
                except Exception as e:
                    logger.error(f"❌ {node['node_id']}{endpoint} - {e}")
                    self.test_results[f"{node['node_id']}{endpoint}"] = False
    
    def print_test_results(self):
        """Print comprehensive test results"""
        logger.info("=" * 60)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status} - {test_name}")
            
            if result:
                passed += 1
            else:
                failed += 1
        
        logger.info("=" * 60)
        logger.info(f"📈 TOTAL TESTS: {passed + failed}")
        logger.info(f"✅ PASSED: {passed}")
        logger.info(f"❌ FAILED: {failed}")
        logger.info(f"📊 SUCCESS RATE: {(passed / (passed + failed) * 100):.1f}%")
        logger.info("=" * 60)
        
        if failed == 0:
            logger.info("🎉 ALL TESTS PASSED! Multi-node system is working correctly!")
        else:
            logger.warning(f"⚠️  {failed} tests failed. System needs attention.")


async def main():
    """Main test runner"""
    tester = MultiNodeSystemTester()
    
    logger.info("🚀 Starting multi-node system tests...")
    logger.info("⚠️  Make sure the testnet is running before starting tests!")
    logger.info("   Run: python scripts/launch_testnet.py --nodes 2")
    logger.info("")
    
    # Wait a bit for user to start testnet
    logger.info("⏳ Waiting 10 seconds for testnet to be ready...")
    await asyncio.sleep(10)
    
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())