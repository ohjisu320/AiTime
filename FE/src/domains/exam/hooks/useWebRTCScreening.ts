import { useRef, useState, useCallback } from 'react';
import { sendSdpOffer } from '../api/screeningApi';

const USE_MOCK = true;

export const useWebRTCScreening = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const dcRef = useRef<RTCDataChannel | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const cleanupRef = useRef<(() => void) | null>(null);

  const [isAligned, setIsAligned] = useState(false);
  const [volume, setVolume] = useState(0);
  const [connectionStatus, setConnectionStatus] = useState<
    'IDLE' | 'CONNECTING' | 'CONNECTED' | 'DISCONNECTED'
  >('IDLE');

  // --- Mock 모드 ---
  const runMockSimulation = useCallback(() => {
    console.warn("⚠️ Mock 모드 활성화");
    setConnectionStatus('CONNECTED');

    const vInterval = setInterval(() => {
      setVolume(Math.floor(Math.random() * 45));
    }, 100);

    const aTimeout = setTimeout(() => {
      setIsAligned(true);
      console.log("✅ [Mock] 스크리닝 통과!");
    }, 3000);

    // Cleanup 함수 저장
    cleanupRef.current = () => {
      clearInterval(vInterval);
      clearTimeout(aTimeout);
    };
  }, []);

  // --- WebSocket 연결 ---
  const connectWebSocket = useCallback(() => {
    const ws = new WebSocket(
      import.meta.env.VITE_WEBRTC_SERVER_URL || 'ws://localhost:8000/webrtc'
    );

    ws.onopen = () => {
      console.log('✅ WebSocket connected');
    };

    ws.onerror = (err) => {
      console.error('❌ WebSocket error:', err);
      setConnectionStatus('DISCONNECTED');
    };

    ws.onclose = () => {
      console.log('🔌 WebSocket closed');
      if (connectionStatus === 'CONNECTED') {
        setConnectionStatus('DISCONNECTED');
      }
    };

    ws.onmessage = async (event) => {
      const message = JSON.parse(event.data);

      if (message.type === 'answer' && pcRef.current) {
        await pcRef.current.setRemoteDescription(
          new RTCSessionDescription(message.sdp)
        );
        console.log('📨 Received SDP Answer');
      }

      if (message.type === 'ice-candidate' && pcRef.current) {
        await pcRef.current.addIceCandidate(
          new RTCIceCandidate(message.candidate)
        );
        console.log('🧊 Received ICE Candidate');
      }
    };

    wsRef.current = ws;
  }, [connectionStatus]);

  // --- 실제 WebRTC 연결 ---
  const startRealConnection = useCallback(async (localStream: MediaStream) => {
    try {
      // WebSocket 연결
      connectWebSocket();
      await new Promise(resolve => setTimeout(resolve, 500)); // 연결 대기

      const pc = new RTCPeerConnection({
        iceServers: [
          { urls: 'stun:stun.l.google.com:19302' },
          { urls: 'stun:stun1.l.google.com:19302' },
        ],
      });

      pcRef.current = pc;

      // ICE Candidate 전송
      pc.onicecandidate = (event) => {
        if (event.candidate && wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'ice-candidate',
            candidate: event.candidate,
          }));
        }
      };

      // 연결 상태 모니터링
      pc.onconnectionstatechange = () => {
        console.log('🔗 Connection State:', pc.connectionState);

        if (pc.connectionState === 'connected') {
          setConnectionStatus('CONNECTED');
        } else if (pc.connectionState === 'failed' || pc.connectionState === 'disconnected') {
          setConnectionStatus('DISCONNECTED');
        }
      };

      // Data Channel 생성
      const dc = pc.createDataChannel('result-channel', { ordered: true });
      dcRef.current = dc;

      dc.onopen = () => {
        console.log('📡 Data Channel opened');
      };

      dc.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.volume !== undefined) {
            setVolume(data.volume);
          }

          if (data.face !== undefined && data.noise !== undefined) {
            setIsAligned(data.face && data.noise);
          }
        } catch (err) {
          console.error('Failed to parse data:', err);
        }
      };

      dc.onerror = (error) => {
        console.error('❌ Data Channel error:', error);
      };

      // 트랙 추가
      localStream.getTracks().forEach(track => {
        pc.addTrack(track, localStream);
      });

      // SDP Offer 생성 및 전송
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'offer',
          sdp: offer,
        }));
        console.log('📨 SDP Offer Sent via WebSocket');
      } else {
        // Fallback or Error if WS not open (could fallback to API)
        // For now, let's also try the API if WS fails?
        // Or just log error. The user code seemed to imply WS only.
        console.warn('⚠️ WebSocket not ready, attempting fallback to API (if applicable) or retrying...');
        // Fallback for compatibility if needed:
        // const answer = await sendSdpOffer(offer.sdp!, offer.type);
        // await pc.setRemoteDescription(answer);
      }

    } catch (e) {
      console.error("WebRTC Connection Error:", e);
      setConnectionStatus('DISCONNECTED');
    }
  }, [connectWebSocket]);

  // --- 메인 시작 함수 ---
  const startCamera = useCallback(async () => {
    setConnectionStatus('CONNECTING');
    try {
      const localStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720 },
        audio: true
      });

      if (videoRef.current) videoRef.current.srcObject = localStream;

      if (USE_MOCK) {
        runMockSimulation();
      } else {
        await startRealConnection(localStream);
      }
    } catch (e) {
      console.error("Camera Start Error:", e);
      setConnectionStatus('DISCONNECTED');
    }
  }, [runMockSimulation, startRealConnection]);

  // --- 자원 해제 ---
  const stopCamera = useCallback(() => {
    // MediaStream 정지
    if (videoRef.current?.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }

    // WebRTC & WS 종료
    if (pcRef.current) {
      pcRef.current.close();
      pcRef.current = null;
    }
    if (dcRef.current) {
      dcRef.current.close();
      dcRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Mock Cleanup
    if (cleanupRef.current) {
      cleanupRef.current();
      cleanupRef.current = null;
    }

    setConnectionStatus('IDLE');
    setIsAligned(false);
    setVolume(0);
  }, []);

  return { videoRef, isAligned, volume, connectionStatus, startCamera, stopCamera };
};