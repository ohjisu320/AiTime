import { useRef, useState, useCallback, useEffect } from 'react';
import { Room, RoomEvent, RemoteParticipant, setLogLevel, LogLevel } from 'livekit-client';
import { startScreeningSession, completeScreening, type ScreeningDataMessage } from '../api/screeningApi';

// 개발 환경에서 LiveKit 디버그 로그 활성화
if (import.meta.env.DEV) {
    setLogLevel(LogLevel.debug);
}

const LIVEKIT_URL = import.meta.env.VITE_LIVEKIT_URL || 'ws://localhost:7880';

export type ScreeningStatus = 'idle' | 'connecting' | 'screening' | 'ready' | 'error';

export interface UseLiveKitScreeningReturn {
    videoRef: React.RefObject<HTMLVideoElement>;
    videoStream: MediaStream | null;
    isAligned: boolean;
    volume: number;
    guideMessage: string;
    status: ScreeningStatus;
    sessionId: string | null; // Added sessionId
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

    // --- 실제 LiveKit 연결 ---
    const connectToLiveKit = useCallback(async (childId: string) => {
        try {
            // 1. 백엔드에서 토큰 받기
            console.log('📤 [LiveKit] 세션 시작 요청...');
            const sessionData = await startScreeningSession(childId);
            const { userToken, roomName, sessionId: newSessionId } = sessionData;

            setSessionId(newSessionId);

            console.log(`✅ [LiveKit] 세션 생성: ${roomName} (ID: ${newSessionId})`);

            // 2. LiveKit Room 생성
            const room = new Room();
            roomRef.current = room;

            // 3. AI 참가자 입장 감지
            room.on(RoomEvent.ParticipantConnected, (participant: RemoteParticipant) => {
                console.log(`👤 [LiveKit] 참가자 입장: ${participant.identity}`);

                if (participant.identity.startsWith('ai-agent-')) {
                    console.log('🤖 [LiveKit] AI 연결됨!');
                    setStatus('screening');
                    setGuideMessage('AI와 연결되었습니다. 스크리닝을 시작합니다.');
                }
            });

            // 4. 참가자 퇴장 감지
            room.on(RoomEvent.ParticipantDisconnected, (participant: RemoteParticipant) => {
                console.log(`👋 [LiveKit] 참가자 퇴장: ${participant.identity}`);
            });

            // 5. AI로부터 메시지 수신 (Data Channel)
            room.on(RoomEvent.DataReceived, async (payload: Uint8Array) => {
                try {
                    const decoder = new TextDecoder();
                    const jsonString = decoder.decode(payload);
                    const message = JSON.parse(jsonString) as ScreeningDataMessage;

                    console.log('📨 [LiveKit] 데이터 수신:', message);

                    if (message.type === 'guide') {
                        setGuideMessage(message.message);
                        if (message.distance !== undefined) {
                            // 거리 정보를 볼륨처럼 사용 (0-100 스케일)
                            setVolume(Math.min(100, Math.max(0, message.distance / 3)));
                        }
                    } else if (message.type === 'screening_complete') {
                        setIsAligned(true);
                        setStatus('ready');
                        setGuideMessage('스크리닝 완료! 검사를 시작할 수 있습니다.');
                        console.log('✅ [LiveKit] 스크리닝 완료!');

                        // API로 완료 요청 전송
                        if (newSessionId) {
                            try {
                                await completeScreening(newSessionId, 'success');
                            } catch (apiErr) {
                                console.error('❌ [LiveKit] 완료 API 호출 실패:', apiErr);
                            }
                        }
                    } else if (message.type === 'error') {
                        const errorMsg = message.message;
                        console.error('❌ [LiveKit] AI 에러:', errorMsg);
                        setGuideMessage(`오류: ${errorMsg}`);
                    }
                } catch (err) {
                    console.error('❌ [LiveKit] 데이터 파싱 실패:', err);
                }
            });

            // 6. 연결 상태 모니터링
            room.on(RoomEvent.Disconnected, () => {
                console.log('🔌 [LiveKit] 연결 종료');
                setStatus('idle');
            });

            room.on(RoomEvent.Reconnecting, () => {
                console.log('🔄 [LiveKit] 재연결 중...');
                setGuideMessage('연결 재시도 중...');
            });

            room.on(RoomEvent.Reconnected, () => {
                console.log('✅ [LiveKit] 재연결 완료');
                setGuideMessage('연결이 복구되었습니다.');
            });

            // 7. LiveKit 연결
            console.log(`🔗 [LiveKit] 연결 시도: ${LIVEKIT_URL}`);
            console.log(`🔗 [LiveKit] 방 이름: ${roomName}`);
            await room.connect(LIVEKIT_URL, userToken);

            // ✅ 방 연결 성공 확인 로그
            console.log('═══════════════════════════════════════════');
            console.log('✅ [LiveKit] 룸 연결 성공!');
            console.log(`   📍 Room Name: ${room.name}`);
            console.log(`   📍 Room State: ${room.state}`);
            console.log(`   📍 Local Participant: ${room.localParticipant.identity}`);
            console.log(`   📍 Remote Participants: ${room.remoteParticipants.size}명`);
            console.log('═══════════════════════════════════════════');

            // 8. 카메라 활성화
            await room.localParticipant.setCameraEnabled(true);
            await room.localParticipant.setMicrophoneEnabled(true);
            console.log('📹 [LiveKit] 카메라/마이크 활성화 완료');

            // 9. 비디오 미리보기 연결
            setTimeout(() => {
                const tracks = Array.from(room.localParticipant.videoTrackPublications.values());
                if (tracks.length > 0 && videoRef.current && tracks[0].track) {
                    tracks[0].track.attach(videoRef.current);
                    console.log('🎥 [LiveKit] 비디오 미리보기 연결 완료');
                }
            }, 500);

        } catch (error) {
            console.error('❌ [LiveKit] 연결 실패:', error);
            setStatus('error');
            setGuideMessage('연결에 실패했습니다. 다시 시도해주세요.');
            throw error;
        }
    }, []);

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

            // 실제 LiveKit 연결
            setGuideMessage('AI 서버 연결 중...');
            await connectToLiveKit(childId);

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
    }, [connectToLiveKit]);

    // --- 스크리닝 종료 ---
    const stopScreening = useCallback(async () => {
        console.log('🛑 [LiveKit] 스크리닝 종료');

        // 2. LiveKit Room 연결 해제
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
        sessionId, // Added sessionId
        startScreening,
        stopScreening
    };
};
