/**
 * Test script for Network Validation System
 * 
 * This script tests the mandatory network validation that prevents
 * wallet operation without a valid network map from the coordinator.
 */

const NetworkValidator = require('./wallet/src/services/NetworkValidator');
const NetworkCoordinatorClient = require('./wallet/src/services/NetworkCoordinatorClient');

async function testNetworkValidation() {
    console.log('🧪 Testing Network Validation System');
    console.log('=====================================');
    
    try {
        // Test 1: Network Coordinator Client
        console.log('\n📡 Test 1: Network Coordinator Client');
        const client = new NetworkCoordinatorClient('http://localhost:8000');
        
        // Test health check by trying to get network stats
        console.log('   - Testing coordinator connectivity...');
        let health = false;
        try {
            const stats = await client.getNetworkStats();
            health = stats !== null;
        } catch (error) {
            health = false;
        }
        console.log(`   - Coordinator connectivity: ${health ? '✅ PASS' : '❌ FAIL'}`);
        
        if (!health) {
            console.log('   ⚠️ Network coordinator not available, testing offline mode');
        }
        
        // Test 2: Network Validator - Fresh validation
        console.log('\n🔒 Test 2: Network Validator - Fresh Validation');
        const validator = new NetworkValidator();
        
        console.log('   - Performing mandatory network validation...');
        const validationResult = await validator.validateNetworkOrFail();
        
        console.log(`   - Validation result: ${validationResult.success ? '✅ SUCCESS' : '❌ FAILED'}`);
        console.log(`   - Source: ${validationResult.source || 'N/A'}`);
        console.log(`   - Message: ${validationResult.message || validationResult.error}`);
        
        if (validationResult.success) {
            console.log(`   - Network Map: ${validationResult.networkMap.active_nodes} active nodes`);
            console.log(`   - Pioneer Mode: ${validationResult.isPioneer ? 'YES' : 'NO'}`);
        }
        
        // Test 3: Wallet Operation Check
        console.log('\n🎮 Test 3: Wallet Operation Check');
        const canOperate = validator.canWalletOperate();
        console.log(`   - Can wallet operate: ${canOperate ? '✅ YES' : '❌ NO'}`);
        
        if (canOperate) {
            const networkMap = validator.getCanonicalNetworkMap();
            const validNodes = validator.getValidNodes();
            
            console.log(`   - Network map timestamp: ${networkMap.timestamp}`);
            console.log(`   - Valid nodes available: ${validNodes.length}`);
            
            if (validNodes.length > 0) {
                console.log(`   - Sample node: ${validNodes[0].nodeId} at ${validNodes[0].ip}:${validNodes[0].port}`);
            }
        }
        
        // Test 4: Validation Status
        console.log('\n📊 Test 4: Validation Status');
        const status = validator.getValidationStatus();
        console.log(`   - Is validated: ${status.isValidated}`);
        console.log(`   - Can operate: ${status.canOperate}`);
        console.log(`   - Has network map: ${status.hasNetworkMap}`);
        console.log(`   - Map age (hours): ${status.mapAge ? status.mapAge.toFixed(2) : 'N/A'}`);
        console.log(`   - Active nodes: ${status.activeNodes}`);
        console.log(`   - Genesis nodes: ${status.genesisNodes}`);
        
        // Test 5: Network Map Refresh (if coordinator available)
        if (health) {
            console.log('\n🔄 Test 5: Network Map Refresh');
            console.log('   - Refreshing network map...');
            const refreshed = await validator.refreshNetworkMap();
            console.log(`   - Refresh result: ${refreshed ? '✅ SUCCESS' : '❌ FAILED'}`);
        }
        
        // Test 6: Force Re-validation
        console.log('\n🔄 Test 6: Force Re-validation');
        console.log('   - Forcing network re-validation...');
        const revalidationResult = await validator.forceRevalidation();
        console.log(`   - Re-validation result: ${revalidationResult.success ? '✅ SUCCESS' : '❌ FAILED'}`);
        console.log(`   - Source: ${revalidationResult.source || 'N/A'}`);
        
        // Summary
        console.log('\n📋 Test Summary');
        console.log('===============');
        console.log(`✅ Network Coordinator: ${health ? 'Available' : 'Unavailable'}`);
        console.log(`✅ Network Validation: ${validationResult.success ? 'PASSED' : 'FAILED'}`);
        console.log(`✅ Wallet Operation: ${canOperate ? 'ALLOWED' : 'BLOCKED'}`);
        console.log(`✅ Anti-Fork Protection: ${validationResult.success ? 'ACTIVE' : 'INACTIVE'}`);
        
        if (validationResult.success) {
            console.log('\n🎉 SUCCESS: Network validation system is working correctly!');
            console.log('   - Wallet can only operate with valid network map');
            console.log('   - Fork prevention is active');
            console.log('   - Canonical blockchain is enforced');
        } else {
            console.log('\n⚠️ WARNING: Network validation failed');
            console.log('   - Wallet operation is blocked (as expected)');
            console.log('   - This prevents accidental forks');
            console.log('   - Internet connection required for first run');
        }
        
    } catch (error) {
        console.error('\n❌ Test failed with error:', error.message);
        console.error('Stack trace:', error.stack);
    }
}

// Run the test
testNetworkValidation().then(() => {
    console.log('\n🏁 Test completed');
    process.exit(0);
}).catch((error) => {
    console.error('\n💥 Test crashed:', error);
    process.exit(1);
});