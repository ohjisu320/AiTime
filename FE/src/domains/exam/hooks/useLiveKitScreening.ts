import { useRef, useState, useCallback, useEffect } from 'react';
import { Room, RoomEvent, RemoteParticipant, setLogLevel, LogLevel } from 'livekit-client';
import { startScreeningSession, completeScreening, type ScreeningDataMessage } from '../api/screeningApi';

// 개발 환경에서 LiveKit 디버그 로그 활성화
if (import.meta.env.DEV) {
    setLogLevel(LogLevel.debug);
}

export type ScreeningStatus = 'idle' | 'connecting' | 'screening' | 'ready' | 'error';

export interface UseLiveKitScreeningReturn {
    videoRef: React.RefObject<HTMLVideoElement>;
    videoStream: MediaStream | null;
    isAligned: boolean;
    volume: number;
    guideMessage: string;
    status: ScreeningStatus;
    sessionId: string | null;
    startScreening: (childId: string) => Promise<void>;
    stopScreening: () => Promise<void>;
}

export const useLiveKitScreening = (): UseLiveKitScreeningReturn => {
    const videoRef = useRef<HTMLVideoElement>(null);
    const roomRef = useRef<Room | null>(null);
    const videoStreamRef = useRef<MediaStream | null>(null); // For cleanup

    const [videoStream, setVideoStream] = useState<MediaStream | null>(null);
    const [isAligned, setIsAligned] = useState(false);
    const [volume, setVolume] = useState(0);
    const [guideMessage, setGuideMessage] = useState('');
    const [status, setStatus] = useState<ScreeningStatus>('idle');
    const [sessionId, setSessionId] = useState<string | null>(null);

    // --- 스크리닝 시작 ---
    const startScreening = useCallback(async (childId: string) => {
        try {
            console.log('🎬 [LiveKit] 스크리닝 시작 요청 for Child:', childId);
            setStatus('connecting');
            setGuideMessage('AI 서버 연결 중...');

            // 1. API로 세션 시작 및 토큰 발급
            const sessionData = await startScreeningSession(childId);
            const { userToken, roomName, sessionId: newSessionId } = sessionData;

            console.log(`✅ [LiveKit] Session Created: ${roomName} (${newSessionId})`);
            setSessionId(newSessionId);

            // 2. Room 생성
            const room = new Room();
            roomRef.current = room;

            // 3. 이벤트 핸들러 설정
            room.on(RoomEvent.ParticipantConnected, (participant: RemoteParticipant) => {
                console.log(`👤 [LiveKit] 참가자 입장: ${participant.identity}`);
                if (participant.identity.startsWith('ai-agent-')) {
                    setStatus('screening');
                    setGuideMessage('AI와 연결되었습니다. 가이드를 따라주세요.');
                }
            });

            room.on(RoomEvent.DataReceived, (payload: Uint8Array) => {
                try {
                    const decoder = new TextDecoder();
                    const msg = JSON.parse(decoder.decode(payload)) as ScreeningDataMessage;
                    console.log('📨 [LiveKit] 데이터 수신:', msg);

                    if (msg.type === 'guide') {
                        setGuideMessage(msg.message);
                        if (msg.distance !== undefined) {
                            setVolume(Math.min(100, Math.max(0, msg.distance / 3)));
                        }
                    } else if (msg.type === 'screening_complete') {
                        setStatus('ready');
                        setIsAligned(true);
                        setGuideMessage('스크리닝 완료! 검사를 시작할 수 있습니다.');
                        // 완료 API 호출
                        if (newSessionId) {
                            completeScreening(newSessionId, 'success').catch((e: any) => console.error("완료 API 실패", e));
                        }
                    } else if (msg.type === 'error') {
                        console.error('❌ [LiveKit] AI 에러:', msg.message);
                        setGuideMessage(`오류: ${msg.message}`);
                    }
                } catch (err) {
                    console.error('Data parsing error', err);
                }
            });

            room.on(RoomEvent.Disconnected, () => {
                console.log('🔌 [LiveKit] 연결 종료');
                setStatus(prev => prev === 'ready' ? 'ready' : 'idle');
            });

            // 4. LiveKit 연결
            const wsUrl = import.meta.env.VITE_LIVEKIT_URL || 'ws://localhost:7880';
            console.log(`🔗 [LiveKit] Connecting to ${wsUrl} with token...`);

            await room.connect(wsUrl, userToken);
            console.log('✅ [LiveKit] Room Connected');

            // 5. 카메라/마이크 활성화
            await room.localParticipant.setCameraEnabled(true);
            await room.localParticipant.setMicrophoneEnabled(true);

            // 6. 비디오 엘리먼트 연결
            setTimeout(() => {
                const tracks = Array.from(room.localParticipant.videoTrackPublications.values());
                const videoTrack = tracks.find(t => t.kind === 'video'); // 비디오 트랙 찾기

                if (videoTrack && videoTrack.track) {
                    if (videoRef.current) {
                        videoTrack.track.attach(videoRef.current);
                    }
                    if (videoTrack.track.mediaStream) {
                        setVideoStream(videoTrack.track.mediaStream);
                        videoStreamRef.current = videoTrack.track.mediaStream;
                    }
                }
            }, 500);

        } catch (error: any) {
            console.error('❌ [LiveKit] Error:', error);
            setStatus('error');
            setGuideMessage('연결 실패: ' + (error?.message || String(error)));
        }
    }, []);

    // --- 스크리닝 종료 ---
    const stopScreening = useCallback(async () => {
        if (roomRef.current) {
            await roomRef.current.disconnect();
            roomRef.current = null;
        }

        // MediaStream cleanup via ref
        if (videoStreamRef.current) {
            videoStreamRef.current.getTracks().forEach(track => track.stop());
            videoStreamRef.current = null;
        }

        setStatus('idle');
        setVideoStream(null);
        setGuideMessage('');
    }, []);

    // --- Cleanup ---
    useEffect(() => {
        return () => {
            if (roomRef.current) {
                roomRef.current.disconnect();
            }
            if (videoStreamRef.current) {
                videoStreamRef.current.getTracks().forEach(track => track.stop());
            }
            // eslint-disable-next-line react-hooks/exhaustive-deps
        };
    }, []);

    return {
        videoRef,
        videoStream,
        isAligned,
        volume,
        guideMessage,
        status,
        sessionId,
        startScreening,
        stopScreening
    };
};
