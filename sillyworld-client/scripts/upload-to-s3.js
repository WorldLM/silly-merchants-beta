/**
 * Script to upload audio files to AWS S3
 */

const fs = require('fs');
const path = require('path');
const AWS = require('aws-sdk');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config({ path: path.join(__dirname, '../.env.local') });

// AWS Configuration
const s3 = new AWS.S3({
  accessKeyId: process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  region: process.env.AWS_REGION || 'us-east-1'
});

const BUCKET_NAME = process.env.S3_BUCKET_NAME || 'sillyworld-audio-files';
const SOURCE_DIR = path.join(__dirname, '../public/audio');

// Function to upload a single file to S3
async function uploadFile(filePath, fileName) {
  try {
    const fileContent = fs.readFileSync(filePath);
    
    const params = {
      Bucket: BUCKET_NAME,
      Key: `audio/${fileName}`, // Path in the bucket
      Body: fileContent,
      ContentType: 'audio/mpeg',
      ACL: 'public-read' // Make the file publicly accessible
    };
    
    const data = await s3.upload(params).promise();
    console.log(`Uploaded: ${fileName} to ${data.Location}`);
    return data.Location;
  } catch (error) {
    console.error(`Error uploading ${fileName}: ${error.message}`);
    return null;
  }
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
  
  // Process each file
  for (const file of files) {
    const filePath = path.join(SOURCE_DIR, file);
    
    const location = await uploadFile(filePath, file);
    if (location) {
      successCount++;
    } else {
      failCount++;
    }
  }
  
  console.log(`Upload complete: ${successCount} succeeded, ${failCount} failed.`);
  console.log(`Your audio files are now available at: https://${BUCKET_NAME}.s3.amazonaws.com/audio/`);
}

// Check if AWS credentials are configured
if (!process.env.AWS_ACCESS_KEY_ID || !process.env.AWS_SECRET_ACCESS_KEY) {
  console.error('AWS credentials not found in environment variables.');
  console.error('Please set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION in your .env.local file.');
  process.exit(1);
}

// Run the main function
uploadAllFiles().catch(error => {
  console.error('Unhandled error:', error);
}); 