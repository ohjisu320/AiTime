import { useRef, useState, useCallback } from 'react';
import { sendSdpOffer } from '../api/screeningApi';

// 💡 나중에 서버가 연결되면 false로 바꾸세요! 
const USE_MOCK = true; 

export const useWebRTCScreening = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const dcRef = useRef<RTCDataChannel | null>(null);

  const [isAligned, setIsAligned] = useState(false);
  const [volume, setVolume] = useState(0);
  const [connectionStatus, setConnectionStatus] = useState<'IDLE' | 'CONNECTING' | 'CONNECTED' | 'DISCONNECTED'>('IDLE');

  // --- [Mock Data 생성기] --- 
  const runMockSimulation = useCallback(() => {
    console.warn("⚠️ 현재 Mock 모드로 동작 중입니다.");
    setConnectionStatus('CONNECTED');

    // 1. 소음 수치 시뮬레이션 (0.1초마다 랜덤)
    const vInterval = setInterval(() => {
      setVolume(Math.floor(Math.random() * 45)); 
    }, 100);

    // 2. 얼굴 정렬 시뮬레이션 (3초 후 통과)
    const aTimeout = setTimeout(() => {
      setIsAligned(true);
      console.log("✅ [Mock] 스크리닝 통과!");
    }, 3000);

    return () => {
      clearInterval(vInterval);
      clearTimeout(aTimeout);
    };
  }, []);

  // --- [실제 WebRTC 연결 로직] --- 
  const startRealConnection = useCallback(async (localStream: MediaStream) => {
    const pc = new RTCPeerConnection({
      iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
    });
    pcRef.current = pc;

    const dc = pc.createDataChannel("result-channel");
    dcRef.current = dc;

    dc.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.volume !== undefined) setVolume(data.volume);
      if (data.face !== undefined && data.noise !== undefined) {
        setIsAligned(data.face && data.noise);
      }
    };

    localStream.getTracks().forEach(track => pc.addTrack(track, localStream));

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    const answer = await sendSdpOffer(pc.localDescription!.sdp, pc.localDescription!.type);
    await pc.setRemoteDescription(answer);
    setConnectionStatus('CONNECTED');
  }, []);

  // --- [메인 시작 함수] --- 
  const startCamera = useCallback(async () => {
    setConnectionStatus('CONNECTING');
    try {
      const localStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720 },
        audio: true
      });

      if (videoRef.current) videoRef.current.srcObject = localStream;

      if (USE_MOCK) {
        return runMockSimulation(); // Mock 모드일 때 
      } else {
        await startRealConnection(localStream); // 실연동 모드일 때 
      }
    } catch (e) {
      console.error("연결 오류:", e);
      setConnectionStatus('DISCONNECTED');
    }
  }, [runMockSimulation, startRealConnection]);

  // 자원 해제 로직 (생략 - 기존과 동일) 
  const stopCamera = useCallback(() => {
    if (pcRef.current) { pcRef.current.close(); pcRef.current = null; }
    if (videoRef.current?.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    setConnectionStatus('IDLE');
    setIsAligned(false);
    setVolume(0);
  }, []);

  return { videoRef, isAligned, volume, connectionStatus, startCamera, stopCamera };
};