/**
 * Test fresh coordinator connection (no cache)
 * This forces the wallet to connect to the coordinator directly
 */

const NetworkValidator = require('./wallet/src/services/NetworkValidator');
const fs = require('fs');
const path = require('path');

async function testFreshConnection() {
    console.log('🧪 Testing FRESH Coordinator Connection (No Cache)');
    console.log('🌐 This forces the wallet to connect directly to the coordinator');
    console.log('');
    
    try {
        // Create network validator
        const validator = new NetworkValidator();
        
        // Delete existing network map to force fresh connection
        const netMapPath = path.join(process.cwd(), 'data', 'net_map.json');
        if (fs.existsSync(netMapPath)) {
            fs.unlinkSync(netMapPath);
            console.log('🗑️ Deleted cached network map to force fresh connection');
        }
        
        console.log('🔒 Starting fresh network validation (no cache)...');
        
        // Force fresh validation
        const result = await validator.validateNetworkOrFail();
        
        console.log('');
        console.log('📊 FRESH VALIDATION RESULT:');
        console.log(`   Success: ${result.success}`);
        console.log(`   Source: ${result.source || 'N/A'}`);
        console.log(`   Message: ${result.message}`);
        
        if (result.networkMap) {
            console.log(`   Active Nodes: ${result.networkMap.active_nodes}`);
            console.log(`   Genesis Nodes: ${result.networkMap.genesis_nodes}`);
            console.log(`   Development Mode: ${result.networkMap.development_mode || false}`);
            console.log(`   Pioneer Mode: ${result.isPioneer}`);
            console.log(`   Coordinator URL: ${result.networkMap.coordinator_url}`);
        }
        
        console.log('');
        
        if (result.success) {
            if (result.source === 'coordinator') {
                console.log('🎉 PERFECT! Wallet connected directly to coordinator');
                console.log('✅ Coordinator endpoints are working correctly');
                console.log('✅ Wallet got fresh network map from server');
                console.log('✅ No need to run fix script - coordinator is operational');
            } else {
                console.log('⚠️  Wallet created development network map (coordinator not fully available)');
                console.log('🔧 This means coordinator endpoints are returning 503 or not working');
                console.log('🔧 Need to run fix script: sudo ./scripts/fix_coordinator_dependencies.sh');
                
                if (result.networkMap && result.networkMap.development_mode) {
                    console.log('🔧 Wallet is in development mode - coordinator needs fixing');
                }
            }
        } else {
            console.log('❌ FAILED! Wallet cannot connect and has no fallback');
            console.log('🚫 This would prevent wallet startup');
            console.log('🔧 Coordinator must be fixed immediately');
        }
        
        return result;
        
    } catch (error) {
        console.error('❌ Fresh connection test failed:', error.message);
        console.error('🔧 This indicates coordinator is not responding at all');
        return { success: false, error: error.message };
    }
}

// Run the test
testFreshConnection().then(result => {
    console.log('');
    console.log('🎯 CONCLUSION:');
    
    if (result.success && result.source === 'coordinator') {
        console.log('✅ Coordinator is working - no action needed');
    } else if (result.success && result.source !== 'coordinator') {
        console.log('🔧 Coordinator needs fixing - run: sudo ./scripts/fix_coordinator_dependencies.sh');
    } else {
        console.log('❌ Coordinator is completely broken - urgent fix needed');
    }
});