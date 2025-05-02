import gmailService from './gmailService.js';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// Test function
async function testGmailService() {
  // Replace with your test user ID
  const userId = 20; // Use the actual user ID from your Supabase database
  
  try {
    console.log('Testing getAccessToken...');
    const accessToken = await gmailService.getAccessToken(userId);
    console.log('Access token retrieved successfully:', accessToken.substring(0, 10) + '...');
    
    console.log('\nTesting getInsuranceEmails...');
    const emails = await gmailService.getInsuranceEmails(userId);
    console.log(`Retrieved ${emails.length} emails`);
    
    if (emails.length > 0) {
      console.log('\nSample email:');
      console.log('- Subject:', emails[0].subject);
      console.log('- From:', emails[0].sender);
      console.log('- Snippet:', emails[0].snippet);
    }
    
    console.log('\nTest completed successfully!');
  } catch (error) {
    console.error('Test failed with error:', error);
  }
}

// Run the test
testGmailService(); 