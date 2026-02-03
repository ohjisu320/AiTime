import { useState, useRef, useCallback, useEffect } from 'react';

interface AttemptMeta {
  attempt_start_ts: number;
  attempt_end_ts: number;
}

export const useMediaRecorder = () => {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [isRecording, setIsRecording] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const currentStartRef = useRef<number>(0);

  // 스트림 참조를 유지하여 cleanup 시 사용
  const streamRef = useRef<MediaStream | null>(null);

  // [Attempts는 API 변경으로 사용되지 않을 수 있지만, 호환성을 위해 유지]
  const [attempts, setAttempts] = useState<AttemptMeta[]>([]);

  // Cleanup Function
  const stopStream = useCallback(() => {
    if (streamRef.current) {
      console.log('📷 [useMediaRecorder] Stopping camera tracks...');
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setStream(null);
  }, []);

  // 카메라/마이크 시작
  const startSession = useCallback(async () => {
    // 기존 스트림이 있다면 정리
    if (streamRef.current) {
      stopStream();
    }

    try {
      console.log('📷 [useMediaRecorder] Requesting camera permission...');
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720 }, // 해상도 화질 개선
        audio: true
      });
      console.log('✅ [useMediaRecorder] Camera permission granted, Stream ID:', mediaStream.id);

      setStream(mediaStream);
      streamRef.current = mediaStream;
      return mediaStream;
    } catch (err) {
      console.error('❌ [useMediaRecorder] Camera permission denied or error:', err);
      throw new Error('CAMERA_PERMISSION_DENIED');
    }
  }, [stopStream]);

  // 녹화 시작
  const startRecording = useCallback(() => {
    if (!stream) {
      console.warn('⚠️ [useMediaRecorder] Cannot start recording: No stream available');
      return;
    }

    console.log('🔴 [useMediaRecorder] Start Recording...');
    chunksRef.current = [];
    currentStartRef.current = Date.now();

    // MimeType 지원 체크 (Chrome/Safari 호환성)
    const options = MediaRecorder.isTypeSupported('video/mp4; codecs=h264')
      ? { mimeType: 'video/mp4; codecs=h264' }
      : MediaRecorder.isTypeSupported('video/webm; codecs=vp9')
        ? { mimeType: 'video/webm; codecs=vp9' }
        : undefined;

    const recorder = new MediaRecorder(stream, options);

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };

    recorder.start();
    mediaRecorderRef.current = recorder;
    setIsRecording(true);
  }, [stream]);

  // 녹화 중지
  const stopRecording = useCallback((): Promise<{ blob: Blob, attempt: AttemptMeta }> => {
    return new Promise((resolve) => {
      if (!mediaRecorderRef.current) {
        console.warn('⚠️ [useMediaRecorder] Cannot stop: No recorder instance');
        return;
      }

      console.log('⏹️ [useMediaRecorder] Stop Recording...');
      mediaRecorderRef.current.onstop = () => {
        const mimeType = mediaRecorderRef.current?.mimeType || 'video/mp4';
        const blob = new Blob(chunksRef.current, { type: mimeType });

        const endTs = Date.now();
        const newAttempt = {
          attempt_start_ts: currentStartRef.current,
          attempt_end_ts: endTs
        };

        console.log(`💾 [useMediaRecorder] Recording finished. Size: ${blob.size}, Type: ${mimeType}`);

        setAttempts(prev => [...prev, newAttempt]);
        setIsRecording(false);
        resolve({ blob, attempt: newAttempt });
      };

      mediaRecorderRef.current.stop();
    });
  }, []);

  // Unmount 시 자동 Cleanup
  useEffect(() => {
    return () => {
      stopStream();
    };
  }, [stopStream]);

  return { stream, isRecording, attempts, startSession, startRecording, stopRecording };
};