/**
 * Utility functions for audio handling in the Idea Pitching POC
 */

// Calculate the appropriate duration for text to be displayed
export function calculateTextDuration(text: string): number {
  // Average reading speed is about 200-250 words per minute
  // We'll use 200 words per minute (3.33 words per second)
  const words = text.split(/\s+/).length;
  const baseDuration = words / 3.33;
  
  // Add a minimum duration and some buffer time
  return Math.max(3, Math.ceil(baseDuration * 1.2));
}

// Adjust typewriter speed based on audio duration and text length
export function calculateTypewriterSpeed(text: string, audioDuration: number): number {
  const characters = text.length;
  
  // We want the typewriter to finish slightly before the audio
  const typewriterDuration = audioDuration * 0.9;
  
  // Calculate milliseconds per character
  return Math.max(10, Math.floor(typewriterDuration * 1000 / characters));
}

// Get audio duration (this would need to be pre-calculated or estimated)
export function getAudioDuration(audioFile: string): number {
  // In a real implementation, you would get the actual audio duration
  // For this POC, we'll use estimated durations based on the audio file name
  
  if (audioFile.includes('pitch')) {
    return 30; // Pitch presentations are longer
  } else if (audioFile.includes('answer')) {
    return 15; // Answers are medium length
  } else if (audioFile.includes('question')) {
    return 5; // Questions are short
  } else if (audioFile.includes('feedback')) {
    return 20; // Feedback is medium-long
  } else {
    return 10; // Default duration
  }
} 