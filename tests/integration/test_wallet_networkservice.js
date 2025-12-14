// Test NetworkService faucet functionality directly
const path = require('path');

// Add wallet services to path
const walletServicesPath = path.join(__dirname, 'wallet', 'src', 'services');
const NetworkService = require(path.join(walletServicesPath, 'NetworkService.js'));

async function testFaucetRequest() {
    console.log('🧪 Testing NetworkService faucet request...');
    console.log('📍 Current network:', NetworkService.getNetworkInfo());
    
    const testAddress = 'PG691e12117e193b991d530707967a0a6d0ce879';
    const amount = 1000;
    
    console.log(`🚰 Requesting ${amount} PRGLD for address: ${testAddress}`);
    
    try {
        const result = await NetworkService.requestFaucetTokens(testAddress, amount);
        console.log('📋 Faucet result:', result);
        
        if (result.success) {
            console.log('✅ Faucet request successful!');
            console.log(`💰 Transaction ID: ${result.transactionId}`);
            console.log(`💵 Amount: ${result.amount} PRGLD`);
            console.log(`📝 Message: ${result.message}`);
        } else {
            console.log('❌ Faucet request failed!');
            console.log(`🚨 Error: ${result.error}`);
            console.log(`📄 Details: ${result.details}`);
        }
        
    } catch (error) {
        console.log('💥 Unexpected error:', error.message);
    }
}

testFaucetRequest().then(() => {
    console.log('🏁 Test completed');
    process.exit(0);
}).catch(error => {
    console.error('💥 Test failed:', error);
    process.exit(1);
});