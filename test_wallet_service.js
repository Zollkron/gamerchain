// Test WalletService faucet functionality directly
const path = require('path');

// Add wallet services to path
const walletServicesPath = path.join(__dirname, 'wallet', 'src', 'services');
const WalletService = require(path.join(walletServicesPath, 'WalletService.js'));

async function testWalletServiceFaucet() {
    console.log('🧪 Testing WalletService faucet request...');
    
    // First, let's see what wallets exist
    const wallets = WalletService.store.get('wallets', []);
    console.log(`📱 Found ${wallets.length} wallets`);
    
    if (wallets.length === 0) {
        console.log('❌ No wallets found. Creating a test wallet...');
        
        // Create a test wallet
        const testWallet = {
            id: 'test-wallet-' + Date.now(),
            name: 'Test Wallet',
            address: 'PG691e12117e193b991d530707967a0a6d0ce879',
            createdAt: new Date().toISOString()
        };
        
        WalletService.store.set('wallets', [testWallet]);
        console.log('✅ Test wallet created:', testWallet);
    }
    
    // Get the first wallet
    const updatedWallets = WalletService.store.get('wallets', []);
    const testWallet = updatedWallets[0];
    console.log(`🎯 Testing with wallet: ${testWallet.name} (${testWallet.address})`);
    
    // Test faucet request
    console.log(`🚰 Requesting faucet tokens for wallet ID: ${testWallet.id}`);
    
    try {
        const result = await WalletService.requestFaucetTokens(testWallet.id, 1000);
        console.log('📋 WalletService faucet result:', result);
        
        if (result.success) {
            console.log('✅ WalletService faucet request successful!');
            console.log(`💰 Transaction ID: ${result.transactionId}`);
            console.log(`💵 Amount: ${result.amount} PRGLD`);
            console.log(`📝 Message: ${result.message}`);
        } else {
            console.log('❌ WalletService faucet request failed!');
            console.log(`🚨 Error: ${result.error}`);
        }
        
    } catch (error) {
        console.log('💥 Unexpected error:', error.message);
        console.log('📄 Stack:', error.stack);
    }
}

testWalletServiceFaucet().then(() => {
    console.log('🏁 WalletService test completed');
    process.exit(0);
}).catch(error => {
    console.error('💥 WalletService test failed:', error);
    process.exit(1);
});