import keytar from 'keytar';
import readline from 'readline';

const SERVICE = 'supabase';
let ANON, serviceRole, jwtSecret;

// Create readline interface
const rl = readline.createInterface({ 
  input: process.stdin, 
  output: process.stdout 
});

/**
 * Prompts user for input with validation
 * @param {string} question - The prompt text
 * @param {string} description - Description of what to enter
 * @returns {Promise<string>} - Validated user input
 */
async function promptWithValidation(question, description) {
  console.log(`\n${description}`);
  
  while (true) {
    const answer = await new Promise(resolve => 
      rl.question(`${question}: `, ans => resolve(ans))
    );
    
    // Clean input - take only the first line if multiple lines were pasted
    const cleanedAnswer = answer.trim().split('\n')[0].trim();
    
    if (!cleanedAnswer) {
      console.log('⚠️  Error: Input cannot be empty. Please try again.');
      continue;
    }
    
    return cleanedAnswer;
  }
}

(async () => {
  try {
    console.log('===== Supabase Secure Credentials Setup =====');
    console.log('This script will securely store your Supabase credentials in your system keychain.');
    console.log('You will need three pieces of information from your Supabase project:');
    console.log('1. ANON key (public API key)');
    console.log('2. SERVICE_ROLE key (private admin key)');
    console.log('3. JWT_SECRET');
    console.log('You can find these in your Supabase dashboard under Project Settings > API');
    
    // Get and store ANON key
    ANON = await promptWithValidation(
      '▶ Enter your Supabase ANON key',
      'The ANON key starts with "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."'
    );
    await keytar.setPassword(SERVICE, 'anon', ANON);
    console.log('🔒 Supabase ANON key stored successfully.');
    
    // Get and store SERVICE_ROLE key
    serviceRole = await promptWithValidation(
      '▶ Enter your Supabase SERVICE_ROLE key',
      'The SERVICE_ROLE key is a private key used for administrative tasks'
    );
    await keytar.setPassword(SERVICE, 'service_role', serviceRole);
    console.log('🔒 SERVICE_ROLE key stored successfully.');
    
    // Get and store JWT_SECRET
    jwtSecret = await promptWithValidation(
      '▶ Enter your Supabase JWT_SECRET',
      'The JWT_SECRET is used for token verification'
    );
    await keytar.setPassword(SERVICE, 'jwt_secret', jwtSecret);
    console.log('🔒 JWT_SECRET stored successfully.');
    
    console.log('\n✅ All credentials stored securely in your system keychain!');
    console.log('You can now access them in your code using keytar.getPassword()');
    
    rl.close();
  } catch (error) {
    console.error('\n❌ Error storing credentials:', error.message);
    console.log('Please try again with valid credentials.');
    rl.close();
    process.exit(1);
  }
})();
