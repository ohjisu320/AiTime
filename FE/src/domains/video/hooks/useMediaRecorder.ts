// src/domains/video/hooks/useMediaRecorder.ts
import { useState, useRef, useCallback } from 'react';

interface AttemptMeta {
  attempt_start_ts: number;
  attempt_end_ts: number;
}

export const useMediaRecorder = () => {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const [attempts, setAttempts] = useState<AttemptMeta[]>([]);
  const currentStartRef = useRef<number>(0);

  // 카메라/마이크 시작
  const startSession = useCallback(async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      setStream(mediaStream);
    } catch (err) {
      throw new Error('CAMERA_PERMISSION_DENIED');
    }
  }, []);

  // 녹화 시작
  const startRecording = useCallback(() => {
    if (!stream) return;
    chunksRef.current = [];
    currentStartRef.current = Date.now();
    
    const recorder = new MediaRecorder(stream);
    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };
    
    recorder.start();
    mediaRecorderRef.current = recorder;
    setIsRecording(true);
  }, [stream]);

  // 녹화 중지
  const stopRecording = useCallback((): Promise<Blob> => {
    return new Promise((resolve) => {
      if (!mediaRecorderRef.current) return;
      
      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'video/mp4' });
        const endTs = Date.now();
        setAttempts(prev => [...prev, { 
          attempt_start_ts: currentStartRef.current, 
          attempt_end_ts: endTs 
        }]);
        setIsRecording(false);
        resolve(blob);
      };
      
      mediaRecorderRef.current.stop();
    });
  }, []);

  return { stream, isRecording, attempts, startSession, startRecording, stopRecording };
};