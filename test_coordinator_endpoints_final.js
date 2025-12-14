/**
 * Test all coordinator endpoints after update
 */

const https = require('https');

function makeRequest(method, path, data = null) {
    return new Promise((resolve) => {
        const postData = data ? JSON.stringify(data) : null;
        
        const options = {
            hostname: 'playergold.es',
            port: 443,
            path: path,
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': 'PlayerGold-Wallet/1.0.0'
            },
            rejectUnauthorized: false
        };
        
        if (postData) {
            options.headers['Content-Length'] = Buffer.byteLength(postData);
        }
        
        const req = https.request(options, (res) => {
            let responseData = '';
            res.on('data', (chunk) => responseData += chunk);
            res.on('end', () => {
                resolve({
                    status: res.statusCode,
                    data: responseData
                });
            });
        });
        
        req.on('error', (error) => {
            resolve({
                status: 'ERROR',
                data: error.message
            });
        });
        
        req.setTimeout(10000, () => {
            req.destroy();
            resolve({
                status: 'TIMEOUT',
                data: 'Request timeout'
            });
        });
        
        if (postData) {
            req.write(postData);
        }
        req.end();
    });
}

async function testAllEndpoints() {
    console.log('🧪 Testing PlayerGold Network Coordinator - Full Endpoints');
    console.log('🌐 Host: https://playergold.es');
    console.log('');
    
    // Test 1: Health endpoint
    console.log('1. Testing Health endpoint...');
    const health = await makeRequest('GET', '/api/v1/health');
    console.log(`   Status: ${health.status}`);
    if (health.status === 200) {
        console.log(`   ✅ Response: ${health.data.substring(0, 100)}...`);
    } else {
        console.log(`   ❌ Error: ${health.data}`);
    }
    console.log('');
    
    // Test 2: Registration endpoint
    console.log('2. Testing Registration endpoint...');
    const registrationData = {
        node_id: 'PGtest' + Date.now(),
        public_ip: '127.0.0.1',
        port: 18333,
        latitude: 40.4168,
        longitude: -3.7038,
        os_info: 'win32 x64',
        node_type: 'regular',
        public_key: 'test_key_' + Date.now(),
        signature: 'test_signature'
    };
    
    const register = await makeRequest('POST', '/api/v1/register', registrationData);
    console.log(`   Status: ${register.status}`);
    if (register.status === 200) {
        console.log(`   ✅ Response: ${register.data.substring(0, 150)}...`);
    } else {
        console.log(`   ❌ Error: ${register.data}`);
    }
    console.log('');
    
    // Test 3: Network Map endpoint
    console.log('3. Testing Network Map endpoint...');
    const mapData = {
        requester_latitude: 40.4168,
        requester_longitude: -3.7038
    };
    
    const networkMap = await makeRequest('POST', '/api/v1/network-map', mapData);
    console.log(`   Status: ${networkMap.status}`);
    if (networkMap.status === 200) {
        console.log(`   ✅ Response: ${networkMap.data.substring(0, 150)}...`);
    } else {
        console.log(`   ❌ Error: ${networkMap.data}`);
    }
    console.log('');
    
    // Test 4: KeepAlive endpoint
    console.log('4. Testing KeepAlive endpoint...');
    const keepaliveData = {
        node_id: registrationData.node_id,
        blockchain_height: 0,
        connected_peers: 0,
        cpu_usage: 25.5,
        memory_usage: 45.2,
        network_latency: 10.0,
        ai_model_loaded: false,
        mining_active: false,
        signature: 'test_signature'
    };
    
    const keepalive = await makeRequest('POST', '/api/v1/keepalive', keepaliveData);
    console.log(`   Status: ${keepalive.status}`);
    if (keepalive.status === 200) {
        console.log(`   ✅ Response: ${keepalive.data.substring(0, 150)}...`);
    } else {
        console.log(`   ❌ Error: ${keepalive.data}`);
    }
    console.log('');
    
    // Test 5: Stats endpoint
    console.log('5. Testing Stats endpoint...');
    const stats = await makeRequest('GET', '/api/v1/stats');
    console.log(`   Status: ${stats.status}`);
    if (stats.status === 200) {
        console.log(`   ✅ Response: ${stats.data.substring(0, 150)}...`);
    } else {
        console.log(`   ❌ Error: ${stats.data}`);
    }
    console.log('');
    
    // Summary
    console.log('📊 SUMMARY:');
    const results = [
        { name: 'Health', status: health.status },
        { name: 'Register', status: register.status },
        { name: 'Network Map', status: networkMap.status },
        { name: 'KeepAlive', status: keepalive.status },
        { name: 'Stats', status: stats.status }
    ];
    
    let working = 0;
    results.forEach(result => {
        const icon = result.status === 200 ? '✅' : '❌';
        console.log(`   ${icon} ${result.name}: ${result.status}`);
        if (result.status === 200) working++;
    });
    
    console.log('');
    if (working === 5) {
        console.log('🎉 ALL ENDPOINTS WORKING! Coordinator is fully operational.');
    } else if (working > 0) {
        console.log(`⚠️  ${working}/5 endpoints working. Some endpoints need attention.`);
    } else {
        console.log('❌ NO ENDPOINTS WORKING. Coordinator needs to be updated.');
    }
}

testAllEndpoints();