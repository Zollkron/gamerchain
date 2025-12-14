/**
 * Test wallet connection to coordinator after fix
 * This simulates what the wallet does when it starts up
 */

const NetworkValidator = require('./wallet/src/services/NetworkValidator');

async function testWalletConnection() {
    console.log('🧪 Testing Wallet Connection to Network Coordinator');
    console.log('🌐 This simulates what happens when the wallet starts up');
    console.log('');
    
    try {
        // Create network validator (same as wallet does)
        const validator = new NetworkValidator();
        
        console.log('🔒 Starting mandatory network validation...');
        
        // Perform the same validation the wallet does
        const result = await validator.validateNetworkOrFail();
        
        console.log('');
        console.log('📊 VALIDATION RESULT:');
        console.log(`   Success: ${result.success}`);
        console.log(`   Source: ${result.source || 'N/A'}`);
        console.log(`   Message: ${result.message}`);
        
        if (result.networkMap) {
            console.log(`   Active Nodes: ${result.networkMap.active_nodes}`);
            console.log(`   Genesis Nodes: ${result.networkMap.genesis_nodes}`);
            console.log(`   Development Mode: ${result.networkMap.development_mode || false}`);
            console.log(`   Pioneer Mode: ${result.isPioneer}`);
        }
        
        console.log('');
        
        if (result.success) {
            if (result.source === 'coordinator') {
                console.log('🎉 SUCCESS! Wallet can connect to coordinator and get real network map');
                console.log('✅ All coordinator endpoints are working correctly');
                console.log('✅ Wallet will operate in normal mode');
            } else if (result.source === 'cached') {
                console.log('✅ SUCCESS! Wallet using cached network map (coordinator was reached before)');
                console.log('ℹ️  This is normal behavior for subsequent wallet starts');
            } else {
                console.log('⚠️  SUCCESS with fallback - Wallet created development network map');
                console.log('🔧 This means coordinator endpoints are not fully functional yet');
                console.log('🔧 Wallet will work but in development/pioneer mode');
            }
            
            // Test if wallet can operate
            if (validator.canWalletOperate()) {
                console.log('✅ Wallet validation: CAN OPERATE');
            } else {
                console.log('❌ Wallet validation: CANNOT OPERATE');
            }
            
        } else {
            console.log('❌ FAILED! Wallet cannot connect to coordinator');
            console.log('🚫 Wallet will not be able to start');
            console.log('🔧 Coordinator needs to be fixed before wallet can work');
        }
        
        // Show validation status
        const status = validator.getValidationStatus();
        console.log('');
        console.log('📋 Detailed Status:');
        console.log(`   Validated: ${status.isValidated}`);
        console.log(`   Can Operate: ${status.canOperate}`);
        console.log(`   Has Network Map: ${status.hasNetworkMap}`);
        console.log(`   Map Age (hours): ${status.mapAge ? status.mapAge.toFixed(1) : 'N/A'}`);
        
    } catch (error) {
        console.error('❌ Test failed with error:', error.message);
        console.error('🔧 This indicates a problem with the coordinator or network connection');
    }
}

// Run the test
testWalletConnection();