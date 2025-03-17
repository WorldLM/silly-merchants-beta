import { useState, useRef, useEffect } from 'react';
import { resolveIpfsUrl } from '@/utils/ipfsResolver';

// Map of content types to audio files
const audioMap = {
  // Coaching questions
  'businessIdea': 'alex_1.mp3',
  'problemSolution': 'alex_2.mp3',
  'valueProposition': 'alex_3.mp3',
  'teamBackground': 'alex_4.mp3',
  'fundingUsage': 'alex_5.mp3',
  'teamCulture': 'alex_6.mp3',
  
  // Coaching follow-ups
  'businessIdea_followup': 'alex_followup_1.mp3',
  'problemSolution_followup': 'alex_followup_2.mp3',
  'valueProposition_followup': 'alex_followup_3.mp3',
  'teamBackground_followup': 'alex_followup_4.mp3',
  'fundingUsage_followup': 'alex_followup_5.mp3',
  'teamCulture_followup': 'alex_followup_6.mp3',
  
  // Judge questions (3 judges, 3 questions each)
  'judge_1_question_1': 'judge_1_1.mp3',
  'judge_1_question_2': 'judge_1_2.mp3',
  'judge_1_question_3': 'judge_1_3.mp3',
  'judge_2_question_1': 'judge_2_1.mp3',
  'judge_2_question_2': 'judge_2_2.mp3',
  'judge_2_question_3': 'judge_2_3.mp3',
  'judge_3_question_1': 'judge_3_1.mp3',
  'judge_3_question_2': 'judge_3_2.mp3',
  'judge_3_question_3': 'judge_3_3.mp3',
  
  // Pitch presentations
  'pitch_ai': 'pitch_1.mp3',
  'pitch_blockchain': 'pitch_2.mp3',
  'pitch_wearable': 'pitch_3.mp3',
  
  // System messages
  'accept': 'system_1.mp3',
  'negotiate': 'system_2.mp3',
  'reject': 'system_3.mp3',
  'intro': 'system_4.mp3',
  'conclusion': 'system_5.mp3',
};

export function useAudio() {
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [currentAudioKey, setCurrentAudioKey] = useState('');
  const audioRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  
  // Initialize audio element
  useEffect(() => {
    const audio = new Audio();
    audioRef.current = audio;
    
    audio.onended = () => {
      setIsPlaying(false);
    };
    
    return () => {
      // Cleanup
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);
  
  // Function to get the appropriate audio file for the content
  const getAudioFile = (text, voiceType, judgeIndex = 0, questionIndex = 0) => {
    // For coaching questions and follow-ups
    if (voiceType === 'alex' && currentAudioKey) {
      const fileName = audioMap[currentAudioKey];
      return resolveIpfsUrl(fileName);
    }
    
    if (voiceType === 'alex-followup' && currentAudioKey) {
      const fileName = `${currentAudioKey}_followup`;
      return resolveIpfsUrl(audioMap[fileName]);
    }
    
    // For judge questions
    if (voiceType === 'judge') {
      const fileName = `judge_${judgeIndex + 1}_question_${questionIndex + 1}.mp3`;
      return resolveIpfsUrl(fileName);
    }
    
    // For judge feedback
    if (voiceType === 'judge-feedback') {
      const fileName = `judge_${judgeIndex + 1}_feedback.mp3`;
      return resolveIpfsUrl(fileName);
    }
    
    // For Alex answers to judge questions
    if (voiceType === 'alex' && text.includes('customer acquisition')) {
      return resolveIpfsUrl('alex_answer_cac_ltv.mp3');
    } else if (voiceType === 'alex' && text.includes('first 100 customers')) {
      return resolveIpfsUrl('alex_answer_customers.mp3');
    } else if (voiceType === 'alex' && text.includes('different from existing')) {
      return resolveIpfsUrl('alex_answer_differentiation.mp3');
    } else if (voiceType === 'alex' && text.includes('go-to-market')) {
      return resolveIpfsUrl('alex_answer_go_to_market.mp3');
    } else if (voiceType === 'alex' && text.includes('scalable')) {
      return resolveIpfsUrl('alex_answer_scalability.mp3');
    } else if (voiceType === 'alex' && text.includes('risks')) {
      return resolveIpfsUrl('alex_answer_risks.mp3');
    } else if (voiceType === 'alex' && text.includes('team')) {
      return resolveIpfsUrl('alex_answer_team.mp3');
    } else if (voiceType === 'alex' && text.includes('revenue model')) {
      return resolveIpfsUrl('alex_answer_revenue.mp3');
    } else if (voiceType === 'alex' && text.includes('investment capital')) {
      return resolveIpfsUrl('alex_answer_funding.mp3');
    }
    
    // For pitch presentations
    if (voiceType === 'pitch') {
      if (text.includes('AI') || text.includes('artificial intelligence')) {
        return resolveIpfsUrl('pitch_ai.mp3');
      } else if (text.includes('blockchain')) {
        return resolveIpfsUrl('pitch_blockchain.mp3');
      } else {
        return resolveIpfsUrl('pitch_wearable.mp3');
      }
    }
    
    // For system messages
    if (voiceType === 'system') {
      if (text.includes('Congratulations')) {
        return resolveIpfsUrl('system_accept.mp3');
      } else if (text.includes('negotiate')) {
        return resolveIpfsUrl('system_negotiate.mp3');
      } else if (text.includes('reject')) {
        return resolveIpfsUrl('system_reject.mp3');
      } else if (text.includes('Welcome') || text.includes("Hi, I'm Alex")) {
        return resolveIpfsUrl('system_intro.mp3');
      } else {
        return resolveIpfsUrl('system_conclusion.mp3');
      }
    }
    
    // Default fallback
    return resolveIpfsUrl('alex_question_1.mp3');
  };
  
  // Function to play audio
  const playAudio = async (text, voiceType, judgeIndex = 0, questionIndex = 0, answerKey = '') => {
    try {
      setIsPlaying(true);
      
      // Get the appropriate audio file
      let audioFile;
      
      if (answerKey) {
        // Use the specific answer audio file
        audioFile = getAudioFile(text, voiceType, judgeIndex, questionIndex);
      } else {
        audioFile = getAudioFile(text, voiceType, judgeIndex, questionIndex);
      }
      
      // Play the audio
      if (audioRef.current) {
        audioRef.current.src = audioFile;
        audioRef.current.play();
      }
    } catch (err) {
      console.error("Error playing audio:", err);
      setIsPlaying(false);
      alert("There was an error playing the audio. Please try again.");
    }
  };
  
  // Function to start recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      
      mediaRecorder.ondataavailable = (e) => {
        chunksRef.current.push(e.data);
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        
        // Create form data for API request
        const formData = new FormData();
        formData.append('audio', audioBlob);
        
        try {
          const response = await fetch('/api/transcribe', {
            method: 'POST',
            body: formData,
          });
          
          if (!response.ok) {
            throw new Error('Failed to transcribe audio');
          }
          
          const data = await response.json();
          setTranscript(data.text);
        } catch (err) {
          console.error("Error transcribing audio:", err);
          alert("There was an error transcribing your audio. Please try again.");
        }
      };
      
      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Error starting recording:", err);
      alert("There was an error accessing your microphone. Please check your permissions and try again.");
    }
  };
  
  // Function to stop recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };
  
  return {
    isRecording,
    isPlaying,
    transcript,
    setTranscript,
    playAudio,
    startRecording,
    stopRecording,
    audioRef,
    setCurrentAudioKey
  };
} 