/**
 * Audio preloader utility for the Idea Pitching POC
 */

// List of essential audio files to preload
const essentialAudioFiles = [
  '/audio/system_intro.mp3',
  '/audio/alex_question_1.mp3',
  '/audio/alex_followup_1.mp3',
  '/audio/pitch_ai.mp3',
  '/audio/pitch_blockchain.mp3',
  '/audio/pitch_wearable.mp3',
  '/audio/judge_1_question_1.mp3',
  '/audio/judge_2_question_1.mp3',
  '/audio/judge_3_question_1.mp3',
  '/audio/alex_answer_customers.mp3',
  '/audio/judge_1_feedback.mp3',
  '/audio/system_accept.mp3'
];

// Preload audio files
export function preloadAudioFiles(callback?: () => void): void {
  let loadedCount = 0;
  const totalFiles = essentialAudioFiles.length;
  
  console.log(`Preloading ${totalFiles} audio files...`);
  
  essentialAudioFiles.forEach(file => {
    const audio = new Audio();
    
    audio.oncanplaythrough = () => {
      loadedCount++;
      console.log(`Preloaded ${loadedCount}/${totalFiles}: ${file}`);
      
      if (loadedCount === totalFiles && callback) {
        console.log('All essential audio files preloaded');
        callback();
      }
    };
    
    audio.onerror = () => {
      console.warn(`Failed to preload audio file: ${file}`);
      loadedCount++;
      
      if (loadedCount === totalFiles && callback) {
        console.log('Audio preloading complete with some errors');
        callback();
      }
    };
    
    // Start loading the audio file
    audio.src = file;
    audio.load();
  });
} 