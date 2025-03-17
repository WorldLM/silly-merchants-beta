/**
 * Script to compress audio files for Heroku deployment
 * 
 * This script takes the existing MP3 files and compresses them to a smaller size
 * while maintaining acceptable audio quality.
 */

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');

const execPromise = promisify(exec);

// Source and destination directories
const sourceDir = path.join(__dirname, '../public/audio');
const tempDir = path.join(__dirname, '../public/audio-compressed');

// Create temp directory if it doesn't exist
if (!fs.existsSync(tempDir)) {
  fs.mkdirSync(tempDir, { recursive: true });
}

// Function to check if ffmpeg is installed
async function checkFFmpeg() {
  try {
    await execPromise('ffmpeg -version');
    return true;
  } catch (error) {
    console.error('FFmpeg is not installed. Please install FFmpeg to compress audio files.');
    console.error('Installation instructions: https://ffmpeg.org/download.html');
    return false;
  }
}

// Function to compress a single audio file
async function compressAudioFile(inputFile, outputFile) {
  try {
    // Use a high compression level (lower quality but smaller file size)
    // -ab 32k sets the bitrate to 32 kbps (very low, adjust as needed)
    await execPromise(`ffmpeg -i "${inputFile}" -ab 32k -ar 22050 -ac 1 "${outputFile}"`);
    console.log(`Compressed: ${path.basename(inputFile)}`);
    return true;
  } catch (error) {
    console.error(`Error compressing ${inputFile}: ${error.message}`);
    return false;
  }
}

// Main function to compress all audio files
async function compressAllAudioFiles() {
  // Check if FFmpeg is installed
  const ffmpegInstalled = await checkFFmpeg();
  if (!ffmpegInstalled) {
    return;
  }

  // Get all MP3 files in the source directory
  const files = fs.readdirSync(sourceDir).filter(file => file.endsWith('.mp3'));
  
  if (files.length === 0) {
    console.error('No MP3 files found in the source directory.');
    return;
  }
  
  console.log(`Found ${files.length} MP3 files to compress.`);
  
  let successCount = 0;
  let failCount = 0;
  
  // Process each file
  for (const file of files) {
    const inputFile = path.join(sourceDir, file);
    const outputFile = path.join(tempDir, file);
    
    const success = await compressAudioFile(inputFile, outputFile);
    if (success) {
      successCount++;
    } else {
      failCount++;
    }
  }
  
  console.log(`Compression complete: ${successCount} succeeded, ${failCount} failed.`);
  
  // Replace original files with compressed ones
  if (successCount > 0) {
    console.log('Replacing original files with compressed versions...');
    
    for (const file of files) {
      const compressedFile = path.join(tempDir, file);
      const originalFile = path.join(sourceDir, file);
      
      if (fs.existsSync(compressedFile)) {
        // Get file sizes for comparison
        const originalSize = fs.statSync(originalFile).size;
        const compressedSize = fs.statSync(compressedFile).size;
        const savingsPercent = ((originalSize - compressedSize) / originalSize * 100).toFixed(2);
        
        // Replace the original file
        fs.copyFileSync(compressedFile, originalFile);
        console.log(`Replaced ${file} (${savingsPercent}% smaller)`);
      }
    }
    
    // Clean up temp directory
    console.log('Cleaning up temporary files...');
    for (const file of fs.readdirSync(tempDir)) {
      fs.unlinkSync(path.join(tempDir, file));
    }
    fs.rmdirSync(tempDir);
    
    console.log('All done! Audio files have been compressed and replaced.');
  }
}

// Run the main function
compressAllAudioFiles().catch(error => {
  console.error('Unhandled error:', error);
}); 