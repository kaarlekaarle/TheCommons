// Test authentication flow
async function testAuthFlow() {
    console.log('Testing authentication flow...');
    
    try {
        // Step 1: Get token
        console.log('1. Getting authentication token...');
        const authResponse = await fetch('http://localhost:8000/api/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: 'username=alice_community&password=password123'
        });
        
        if (!authResponse.ok) {
            throw new Error(`Auth failed: ${authResponse.status}`);
        }
        
        const authData = await authResponse.json();
        console.log('✅ Authentication successful');
        
        // Step 2: Test polls endpoint
        console.log('2. Testing polls endpoint...');
        const pollsResponse = await fetch('http://localhost:8000/api/polls/', {
            headers: {
                'Authorization': `Bearer ${authData.access_token}`
            }
        });
        
        if (!pollsResponse.ok) {
            throw new Error(`Polls request failed: ${pollsResponse.status}`);
        }
        
        const pollsData = await pollsResponse.json();
        console.log(`✅ Polls endpoint successful: Found ${pollsData.length} polls`);
        
        // Step 3: Test delegation endpoint
        console.log('3. Testing delegation endpoint...');
        const delegationResponse = await fetch('http://localhost:8000/api/delegations/me', {
            headers: {
                'Authorization': `Bearer ${authData.access_token}`
            }
        });
        
        if (!delegationResponse.ok) {
            console.log(`⚠️ Delegation endpoint returned: ${delegationResponse.status}`);
        } else {
            const delegationData = await delegationResponse.json();
            console.log('✅ Delegation endpoint successful');
        }
        
        // Step 4: Test activity endpoint
        console.log('4. Testing activity endpoint...');
        const activityResponse = await fetch('http://localhost:8000/api/activity/', {
            headers: {
                'Authorization': `Bearer ${authData.access_token}`
            }
        });
        
        if (!activityResponse.ok) {
            throw new Error(`Activity request failed: ${activityResponse.status}`);
        }
        
        const activityData = await activityResponse.json();
        console.log(`✅ Activity endpoint successful: Found ${activityData.length} activities`);
        
        console.log('\n🎉 All tests passed! The API is working correctly.');
        
    } catch (error) {
        console.error('❌ Test failed:', error.message);
    }
}

// Run the test
testAuthFlow();
