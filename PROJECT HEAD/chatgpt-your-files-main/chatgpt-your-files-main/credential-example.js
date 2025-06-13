/**
 * credential-example.js
 * 
 * This example demonstrates how to securely retrieve Supabase credentials
 * that were previously stored in the system keychain using vault-setup.js
 */

import keytar from 'keytar';

// The service name used when storing credentials
const SERVICE = 'supabase';

/**
 * Retrieves a credential from the system keychain
 * @param {string} credentialName - Name of the credential ('anon', 'service_role', or 'jwt_secret')
 * @returns {Promise<string|null>} - The credential value or null if not found
 */
async function getCredential(credentialName) {
  try {
    const credential = await keytar.getPassword(SERVICE, credentialName);
    
    if (!credential) {
      console.warn(`Credential '${credentialName}' not found in keychain`);
      return null;
    }
    
    return credential;
  } catch (error) {
    console.error(`Error retrieving '${credentialName}' credential:`, error.message);
    return null;
  }
}

/**
 * Main function to demonstrate retrieving all Supabase credentials
 */
async function retrieveSupabaseCredentials() {
  try {
    console.log('Retrieving Supabase credentials from system keychain...');
    
    // Retrieve ANON key (public key)
    const anonKey = await getCredential('anon');
    
    // Retrieve SERVICE_ROLE key (admin key)
    const serviceRoleKey = await getCredential('service_role');
    
    // Retrieve JWT_SECRET
    const jwtSecret = await getCredential('jwt_secret');
    
    // Display status (without showing the actual credentials)
    console.log('\nCredential Status:');
    console.log(`- ANON key: ${anonKey ? '✅ Retrieved' : '❌ Not found'}`);
    console.log(`- SERVICE_ROLE key: ${serviceRoleKey ? '✅ Retrieved' : '❌ Not found'}`);
    console.log(`- JWT_SECRET: ${jwtSecret ? '✅ Retrieved' : '❌ Not found'}`);
    
    // Example of how you would use these credentials
    if (anonKey && serviceRoleKey && jwtSecret) {
      console.log('\n✅ All credentials retrieved successfully!');
      console.log('You can now use these credentials to initialize your Supabase client.');
      
      // This is just an example - DON'T log actual credentials in production
      console.log('\nExample usage (DO NOT LOG ACTUAL CREDENTIALS IN PRODUCTION):');
      console.log(`ANON key length: ${anonKey.length} characters`);
      console.log(`SERVICE_ROLE key length: ${serviceRoleKey.length} characters`);
      console.log(`JWT_SECRET length: ${jwtSecret.length} characters`);
    } else {
      console.log('\n❌ Some credentials are missing. Run vault-setup.js to store them.');
    }
    
    return { anonKey, serviceRoleKey, jwtSecret };
  } catch (error) {
    console.error('Error in retrieveSupabaseCredentials:', error.message);
    return { anonKey: null, serviceRoleKey: null, jwtSecret: null };
  }
}

// Execute the demonstration
retrieveSupabaseCredentials();

/**
 * USAGE IN NEXT.JS APPLICATION
 * 
 * In a Next.js application, you would typically:
 * 
 * 1. For server-side operations (API routes, Server Components, etc.):
 *    - Create a utility module similar to this file
 *    - Import it in your server-side code
 *    - Use it to retrieve credentials when needed
 * 
 * Example for a Next.js API route:
 * ```js
 * // In lib/supabase-admin.js
 * import { createClient } from '@supabase/supabase-js';
 * import keytar from 'keytar';
 * 
 * let supabaseAdmin = null;
 * 
 * export async function getSupabaseAdmin() {
 *   if (supabaseAdmin) return supabaseAdmin;
 *   
 *   const serviceRoleKey = await keytar.getPassword('supabase', 'service_role');
 *   const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
 *   
 *   if (!serviceRoleKey || !url) {
 *     throw new Error('Missing Supabase admin credentials');
 *   }
 *   
 *   supabaseAdmin = createClient(url, serviceRoleKey, {
 *     auth: { persistSession: false }
 *   });
 *   
 *   return supabaseAdmin;
 * }
 * ```
 * 
 * 2. For client-side operations:
 *    - Continue using environment variables with NEXT_PUBLIC_ prefix
 *    - The keytar approach is primarily for server-side credentials
 * 
 * IMPORTANT NOTES:
 * - Keytar requires native dependencies and works in Node.js environments
 * - In serverless environments (like Vercel), use environment variables instead
 * - This approach is most useful for local development and self-hosted deployments
 */

