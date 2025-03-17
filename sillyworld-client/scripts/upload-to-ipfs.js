/**
 * Script to upload audio files to IPFS using NFT.Storage
 */

const fs = require('fs');
const path = require('path');
const { NFTStorage } = require('nft.storage');
const dotenv = require('dotenv');
const mime = require('mime');

// Load environment variables
dotenv.config({ path: path.join(__dirname, '../.env.local') });

// NFT.Storage API key
const NFT_STORAGE_API_KEY = process.env.NFT_STORAGE_API_KEY;

// Source directory for audio files
const SOURCE_DIR = path.join(__dirname, '../public/audio');

// Function to upload a single file to IPFS
async function uploadFile(filePath, fileName) {
  try {
    const fileContent = fs.readFileSync(filePath);
    const contentType = mime.getType(filePath) || 'audio/mpeg';
    
    // Create NFTStorage client
    const client = new NFTStorage({ token: NFT_STORAGE_API_KEY });
    
    // Upload to IPFS
    const cid = await client.storeBlob(new Blob([fileContent], { type: contentType }));
    
    // Construct the IPFS URL
    const ipfsUrl = `https://${cid}.ipfs.nftstorage.link`;
    
    console.log(`Uploaded: ${fileName} to IPFS with CID: ${cid}`);
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
  
  console.log(`Your audio files are now available on IPFS!`);
  console.log(`To use them in your app, set NEXT_PUBLIC_AUDIO_BASE_URL to "ipfs://" and update your code to use the CIDs.`);
}

// Check if NFT.Storage API key is configured
if (!NFT_STORAGE_API_KEY) {
  console.error('NFT.Storage API key not found in environment variables.');
  console.error('Please set NFT_STORAGE_API_KEY in your .env.local file.');
  console.error('You can get a free API key at https://nft.storage/');
  process.exit(1);
}

// Run the main function
uploadAllFiles().catch(error => {
  console.error('Unhandled error:', error);
}); 