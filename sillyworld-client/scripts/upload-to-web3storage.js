/**
 * Script to upload audio files to Web3.Storage
 */

const fs = require('fs');
const path = require('path');
const { Web3Storage, File } = require('web3.storage');
const dotenv = require('dotenv');
const mime = require('mime');

// Load environment variables
dotenv.config({ path: path.join(__dirname, '../.env.local') });

// Web3.Storage API token
const WEB3_STORAGE_TOKEN = process.env.WEB3_STORAGE_TOKEN;

// Source directory for audio files
const SOURCE_DIR = path.join(__dirname, '../public/audio');

// Create a Web3Storage client
function makeStorageClient() {
  return new Web3Storage({ token: WEB3_STORAGE_TOKEN });
}

// Function to upload a single file to Web3.Storage
async function uploadFile(filePath, fileName) {
  try {
    const fileContent = fs.readFileSync(filePath);
    
    // Use a hardcoded content type for MP3 files
    const contentType = 'audio/mpeg';
    
    // Create a File object
    const file = new File([fileContent], fileName, { type: contentType });
    
    // Create a client
    const client = makeStorageClient();
    
    // Upload the file
    const cid = await client.put([file], {
      name: fileName,
      maxRetries: 3,
      wrapWithDirectory: false
    });
    
    // Construct the IPFS URL
    const ipfsUrl = `https://${cid}.ipfs.w3s.link`;
    
    console.log(`Uploaded: ${fileName} to Web3.Storage with CID: ${cid}`);
    console.log(`IPFS URL: ${ipfsUrl}`);
    
    return { cid, ipfsUrl };
  } catch (error) {
    console.error(`Error uploading ${fileName}: ${error.message}`);
    return null;
  }
}

// Function to create a mapping file of audio names to IPFS URLs
function saveMapping(mapping) {
  const mappingPath = path.join(__dirname, '../public/ipfs-mapping.json');
  fs.writeFileSync(mappingPath, JSON.stringify(mapping, null, 2));
  console.log(`Mapping saved to: ${mappingPath}`);
  
  // Also save as an environment variable format for easy copy-paste
  const envPath = path.join(__dirname, '../ipfs-urls.env');
  const envContent = `NEXT_PUBLIC_AUDIO_BASE_URL=ipfs://\n` +
    Object.entries(mapping).map(([file, { cid }]) => 
      `NEXT_PUBLIC_IPFS_${file.replace(/\./g, '_').toUpperCase()}=${cid}`
    ).join('\n');
  
  fs.writeFileSync(envPath, envContent);
  console.log(`Environment variables saved to: ${envPath}`);
}

// Main function to upload all audio files
async function uploadAllFiles() {
  // Check if the source directory exists
  if (!fs.existsSync(SOURCE_DIR)) {
    console.error(`Source directory not found: ${SOURCE_DIR}`);
    return;
  }
  
  // Get all MP3 files in the source directory
  const files = fs.readdirSync(SOURCE_DIR).filter(file => file.endsWith('.mp3'));
  
  if (files.length === 0) {
    console.error('No MP3 files found in the source directory.');
    return;
  }
  
  console.log(`Found ${files.length} MP3 files to upload.`);
  
  let successCount = 0;
  let failCount = 0;
  const mapping = {};
  
  // Process each file
  for (const file of files) {
    const filePath = path.join(SOURCE_DIR, file);
    
    const result = await uploadFile(filePath, file);
    if (result) {
      mapping[file] = result;
      successCount++;
    } else {
      failCount++;
    }
  }
  
  console.log(`Upload complete: ${successCount} succeeded, ${failCount} failed.`);
  
  // Save the mapping
  if (successCount > 0) {
    saveMapping(mapping);
  }
  
  console.log(`Your audio files are now available on IPFS via Web3.Storage!`);
  console.log(`To use them in your app, set NEXT_PUBLIC_AUDIO_BASE_URL to "ipfs://" and update your code to use the CIDs.`);
}

// Check if Web3.Storage token is configured
if (!WEB3_STORAGE_TOKEN) {
  console.error('Web3.Storage token not found in environment variables.');
  console.error('Please set WEB3_STORAGE_TOKEN in your .env.local file.');
  console.error('You can get a free token at https://web3.storage/');
  process.exit(1);
}

// Run the main function
uploadAllFiles().catch(error => {
  console.error('Unhandled error:', error);
}); 