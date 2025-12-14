const axios = require('axios');

async function testWalletFaucet() {
    console.log('Testing wallet faucet request...');
    
    const address = 'PG691e12117e193b991d530707967a0a6d0ce879';
    const amount = 1000;
    const apiUrl = 'http://127.0.0.1:18080';
    
    try {
        console.log(`Making request to: ${apiUrl}/api/v1/faucet`);
        console.log(`Data: ${JSON.stringify({ address, amount }, null, 2)}`);
        
        const response = await axios.post(`${apiUrl}/api/v1/faucet`, {
            address: address,
            amount: amount
        }, {
            timeout: 10000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        console.log(`✅ Success! Status: ${response.status}`);
        console.log(`Response data:`, response.data);
        
        return {
            success: true,
            transactionId: response.data.transactionId,
            amount: amount,
            address: address,
            message: `Requested ${amount} PRGLD from testnet faucet`
        };
        
    } catch (error) {
        console.log(`❌ Error: ${error.message}`);
        console.log(`Error code: ${error.code}`);
        console.log(`Response status: ${error.response?.status}`);
        console.log(`Response data: ${JSON.stringify(error.response?.data, null, 2)}`);
        
        return {
            success: false,
            error: error.message
        };
    }
}

testWalletFaucet().then(result => {
    console.log('Final result:', result);
    process.exit(0);
}).catch(error => {
    console.error('Unhandled error:', error);
    process.exit(1);
});