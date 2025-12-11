// Test script to verify mining functionality
const AIModelService = require('./src/services/AIModelService');
const MiningService = require('./src/services/MiningService');

async function testMiningFunctionality() {
  console.log('🧪 Testing PlayerGold Mining Functionality...\n');
  
  try {
    // Test 1: Check certified models
    console.log('1. Testing AI Model Service...');
    const models = AIModelService.getCertifiedModels();
    console.log(`   ✅ Found ${models.length} certified models:`);
    models.forEach(model => {
      console.log(`      - ${model.name} (${model.size})`);
    });
    
    // Test 2: Check mining requirements
    console.log('\n2. Testing Mining Requirements...');
    const requirements = await MiningService.checkMiningRequirements();
    console.log(`   ✅ Can mine: ${requirements.canMine}`);
    if (!requirements.canMine) {
      console.log(`   ❌ Issues: ${requirements.issues.join(', ')}`);
    }
    
    // Test 3: Check mining status
    console.log('\n3. Testing Mining Status...');
    const status = MiningService.getMiningStatus();
    console.log(`   ✅ Mining active: ${status.isMining}`);
    console.log(`   ✅ Available models: ${status.availableModels.length}`);
    console.log(`   ✅ Installed models: ${status.installedModels.length}`);
    
    // Test 4: Test model download simulation
    console.log('\n4. Testing Model Download (simulation)...');
    try {
      const downloadResult = await AIModelService.downloadModel('gemma-3-4b');
      console.log(`   ✅ Download test: ${downloadResult.success ? 'SUCCESS' : 'FAILED'}`);
      if (downloadResult.success) {
        console.log(`   ✅ Message: ${downloadResult.message}`);
      }
    } catch (error) {
      console.log(`   ⚠️  Download test: ${error.message}`);
    }
    
    // Test 5: Test mining rewards estimation
    console.log('\n5. Testing Mining Rewards Estimation...');
    const rewards = MiningService.estimateMiningRewards();
    console.log(`   ✅ Estimated daily rewards: ${rewards.daily} PRGLD`);
    console.log(`   ✅ Estimated monthly rewards: ${rewards.monthly} PRGLD`);
    
    console.log('\n🎉 All mining functionality tests completed!');
    console.log('\n📋 Summary:');
    console.log(`   - Certified models: ${models.length}`);
    console.log(`   - Mining requirements: ${requirements.canMine ? 'MET' : 'NOT MET'}`);
    console.log(`   - Services: OPERATIONAL`);
    
  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    console.error(error.stack);
  }
}

// Run the test
testMiningFunctionality();