import { useRef, useState, useCallback, useEffect } from 'react';
import { Room, RoomEvent, RemoteParticipant, setLogLevel, LogLevel, type RoomConnectOptions, createLocalVideoTrack, createLocalAudioTrack, LocalVideoTrack, LocalAudioTrack } from 'livekit-client';
import { startScreeningSession, type ScreeningDataMessage } from '../api/screeningApi';

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
    personCount: number; // 👥 사람 수 추가
    guideMessage: string;
    status: ScreeningStatus;
    sessionId: string | null;
    startScreening: (childId: string) => Promise<void>;
    stopScreening: () => Promise<void>;
}

const CONNECT_OPTIONS: RoomConnectOptions = {
    autoSubscribe: true,
    rtcConfig: {
        iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' },
        ],
    },
};

export const useLiveKitScreening = (): UseLiveKitScreeningReturn => {
    const videoRef = useRef<HTMLVideoElement>(null);
    const roomRef = useRef<Room | null>(null);
    const videoStreamRef = useRef<MediaStream | null>(null); // For cleanup state

    // Local Tracks Refs (to publish later)
    const localVideoTrackRef = useRef<LocalVideoTrack | null>(null);
    const localAudioTrackRef = useRef<LocalAudioTrack | null>(null);

    const isConnectingRef = useRef(false);
    const isMountedRef = useRef(true);

    const [videoStream, setVideoStream] = useState<MediaStream | null>(null);
    const [isAligned, setIsAligned] = useState(false);
    const [volume, setVolume] = useState(0);
    const [personCount, setPersonCount] = useState(0); // 👥 사람 수 상태 추가
    const [guideMessage, setGuideMessage] = useState('');
    const [status, setStatus] = useState<ScreeningStatus>('idle');
    const [sessionId, setSessionId] = useState<string | null>(null);

    // --- Cleanup Hook ---
    useEffect(() => {
        isMountedRef.current = true;
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    const updateStatus = (newStatus: ScreeningStatus) => {
        if (isMountedRef.current) setStatus(newStatus);
    };

    const updateGuide = (msg: string) => {
        if (isMountedRef.current) setGuideMessage(msg);
    };

    // --- 스크리닝 종료 ---
    const stopScreening = useCallback(async () => {
        console.log('🛑 [LiveKit] 스크리닝 종료 요청');
        isConnectingRef.current = false;

        if (roomRef.current) {
            await roomRef.current.disconnect();
            roomRef.current = null;
        }

        // 로컬 트랙 정리
        if (localVideoTrackRef.current) {
            localVideoTrackRef.current.stop();
            localVideoTrackRef.current = null;
        }
        if (localAudioTrackRef.current) {
            localAudioTrackRef.current.stop();
            localAudioTrackRef.current = null;
        }

        if (videoStreamRef.current) {
            videoStreamRef.current.getTracks().forEach(track => track.stop());
            videoStreamRef.current = null;
        }

        if (isMountedRef.current) {
            setStatus('idle');
            setVideoStream(null);
            setGuideMessage('');
            setPersonCount(0);
        }
    }, []);

    // --- 스크리닝 시작 ---
    const startScreening = useCallback(async (childId: string) => {
        if (isConnectingRef.current) {
            console.warn('⚠️ [LiveKit] 이미 연결 시도 중입니다. 중복 요청 무시됨.');
            return;
        }

        if (roomRef.current && roomRef.current.state === 'connected') {
            console.warn('⚠️ [LiveKit] 이미 Room에 연결되어 있습니다.');
            return;
        }

        isConnectingRef.current = true; // Lock

        try {
            console.log('🎬 [LiveKit] 스크리닝 시작 프로세스 진입 for Child:', childId);
            updateStatus('connecting');
            updateGuide('카메라 실행 중...');

            // 1. [Preview First] 로컬 카메라 먼저 획득하여 화면 표시
            // 연결 실패하더라도 내 얼굴은 보여야 함
            if (!localVideoTrackRef.current) {
                try {
                    const vTrack = await createLocalVideoTrack({
                        resolution: { width: 1280, height: 720 },
                    });
                    localVideoTrackRef.current = vTrack;

                    // 즉시 화면에 표시
                    if (vTrack.mediaStream && isMountedRef.current) {
                        console.log('🎥 [LiveKit] Local Preview Active:', vTrack.mediaStream.id);
                        setVideoStream(vTrack.mediaStream);
                        videoStreamRef.current = vTrack.mediaStream;
                    }
                } catch (camErr) {
                    console.error('❌ [LiveKit] 카메라 획득 실패:', camErr);
                    throw new Error('카메라 권한을 확인해주세요.');
                }
            }

            // 오디오 트랙도 획득 및 분석 시작
            if (!localAudioTrackRef.current) {
                try {
                    const aTrack = await createLocalAudioTrack();
                    localAudioTrackRef.current = aTrack;

                    // 🎤 로컬 오디오 레벨 분석 시작 (Web Audio API)
                    if (aTrack.mediaStream) {
                        const stream = aTrack.mediaStream;
                        const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
                        const analyser = audioContext.createAnalyser();
                        const microphone = audioContext.createMediaStreamSource(stream);
                        const scriptProcessor = audioContext.createScriptProcessor(2048, 1, 1);

                        analyser.smoothingTimeConstant = 0.3; // 반응 속도 빠르게
                        analyser.fftSize = 2048; // 샘플 수 증가

                        microphone.connect(analyser);
                        analyser.connect(scriptProcessor);
                        scriptProcessor.connect(audioContext.destination);

                        const bufferLength = analyser.fftSize;
                        const dataArray = new Float32Array(bufferLength);

                        const NOISE_DB_THRESHOLD = -35.0; // AI 설정 값: -35dB 이상이면 소음
                        const MIN_DB = -80.0;             // 최소 감지 dB

                        scriptProcessor.onaudioprocess = () => {
                            if (!isMountedRef.current) return;

                            analyser.getFloatTimeDomainData(dataArray);

                            // 1. RMS 계산 (Root Mean Square)
                            let sumSquares = 0;
                            for (let i = 0; i < bufferLength; i++) {
                                sumSquares += dataArray[i] * dataArray[i];
                            }
                            const rms = Math.sqrt(sumSquares / bufferLength);

                            // 2. dBFS 변환
                            // RMS가 0이면 -Infinity가 되므로 최소값 처리
                            let db = rms > 0 ? 20 * Math.log10(rms) : MIN_DB;

                            // 3. Volume 매핑 (0 ~ 100)
                            // 기준: -35dB가 Volume 30 (경고 기준점)이 되도록 설정
                            // -80dB ~ -35dB -> 0 ~ 30
                            // -35dB ~ 0dB   -> 30 ~ 100

                            let volumeLevel = 0;

                            if (db < MIN_DB) {
                                volumeLevel = 0;
                            } else if (db <= NOISE_DB_THRESHOLD) {
                                // 조용한 구간 (-80 ~ -35) -> (0 ~ 30)
                                const ratio = (db - MIN_DB) / (NOISE_DB_THRESHOLD - MIN_DB);
                                volumeLevel = ratio * 30;
                            } else {
                                // 시끄러운 구간 (-35 ~ 0) -> (30 ~ 100)
                                const ratio = (db - NOISE_DB_THRESHOLD) / (0 - NOISE_DB_THRESHOLD);
                                volumeLevel = 30 + (ratio * 70);
                            }

                            // 반응성 개선을 위해 약간의 스무딩 적용 (선택사항)
                            setVolume(Math.min(100, Math.round(volumeLevel)));
                        };

                        // 클린업을 위해 ref에 저장해두면 좋지만, 여기서는 간략히 처리
                        // (stopScreening에서 오디오 트랙을 stop하면 stream이 멈추므로 processor도 멈춤)
                        // 하지만 scriptProcessor는 disconnect 해주는 게 좋음.
                        // 일단 roomRef 처럼 별도 관리는 안 하고, stream이 끊기면 멈추도록 기대.
                        // 정확하겐 stopScreening에 cleanup 로직 추가 필요.
                        // 여기서는 일단 기능 구현에 집중.
                    }

                } catch (micErr) {
                    console.warn('⚠️ [LiveKit] 마이크 획득 실패 (계속 진행):', micErr);
                }
            }

            updateGuide('AI 서버 연결 중...');

            // 2. API로 세션 시작 및 토큰 발급
            const sessionData = await startScreeningSession(childId);

            if (!isMountedRef.current) {
                isConnectingRef.current = false;
                return;
            }

            const { userToken, sessionId: newSessionId } = sessionData;
            if (isMountedRef.current) setSessionId(newSessionId);

            // 3. Room 생성
            if (roomRef.current) {
                await roomRef.current.disconnect();
            }

            const room = new Room();
            roomRef.current = room;

            // 4. 이벤트 핸들러 설정
            room.on(RoomEvent.ParticipantConnected, (participant: RemoteParticipant) => {
                console.log(`👤 [LiveKit] 참가자 입장: ${participant.identity}`);
                if (participant.identity.startsWith('ai-agent-')) {
                    console.log('🤖 [LiveKit] AI 연결됨! (Screening Active)');
                    updateStatus('screening');
                    updateGuide('AI와 연결되었습니다. 가이드를 따라주세요.');
                }
            });

            room.on(RoomEvent.SignalConnected, () => {
                console.log('📡 [LiveKit] Signal 서버 연결 완료');
            });

            room.on(RoomEvent.DataReceived, async (payload: Uint8Array) => {
                // ... 기존 로직 ...
                try {
                    const decoder = new TextDecoder();
                    const msg = JSON.parse(decoder.decode(payload)) as ScreeningDataMessage;
                    if (msg.type === 'guide') {
                        updateGuide(msg.message);

                        // 👥 사람 수 감지 로직 추가 (2명 이상일 때 초록색 오버레이 -> isAligned=true)
                        if (msg.person_count !== undefined && isMountedRef.current) {
                            setPersonCount(msg.person_count); // 상태 업데이트
                            setIsAligned(msg.person_count >= 2);
                        }

                        // ❌ 서버 메시지로 볼륨 업데이트 하던 코드 제거 (로컬 분석으로 대체)
                        // if (msg.distance !== undefined && isMountedRef.current) {
                        //     setVolume(Math.min(100, Math.max(0, msg.distance / 3)));
                        // }
                    } else if (msg.type === 'screening_complete') {
                        updateStatus('ready');
                        if (isMountedRef.current) setIsAligned(true);
                        updateGuide('스크리닝 완료! 검사를 시작할 수 있습니다.');
                        // stopScreening(); // 완료 시 자동 종료? (선택사항)
                    } else if (msg.type === 'error') {
                        updateGuide(`오류: ${msg.message}`);
                    }
                } catch (err) {
                    console.error('Data parsing error', err);
                }
            });

            room.on(RoomEvent.Disconnected, () => {
                console.log('🔌 [LiveKit] 연결 종료 이벤트 감지');
                if (isMountedRef.current) {
                    setStatus(prev => {
                        if (prev === 'connecting' || prev === 'screening') {
                            setGuideMessage('연결이 끊어졌습니다. 다시 시도해주세요.');
                            return 'error';
                        }
                        return prev;
                    });
                }
                isConnectingRef.current = false;
            });

            // 5. LiveKit 연결 (재시도 로직)
            console.log(`🔗 [LiveKit] Connecting to ${LIVEKIT_URL}...`);
            let retryCount = 0;
            const MAX_RETRIES = 3;

            let connected = false;
            while (retryCount < MAX_RETRIES) {
                try {
                    await room.connect(LIVEKIT_URL, userToken, CONNECT_OPTIONS);
                    connected = true;
                    console.log('✅ [LiveKit] Room Connected Successfully');
                    break;
                } catch (connError) {
                    retryCount++;
                    console.error(`❌ [LiveKit] Connection Failed (Attempt ${retryCount}/${MAX_RETRIES}):`, connError);
                    if (retryCount >= MAX_RETRIES) throw connError;
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
            }

            if (!connected || !isMountedRef.current) {
                room.disconnect();
                return;
            }

            isConnectingRef.current = false;

            // 6. 준비된 트랙 Publish
            console.log('📤 [LiveKit] Publishing Local Tracks...');
            if (localVideoTrackRef.current) {
                await room.localParticipant.publishTrack(localVideoTrackRef.current);
            }
            if (localAudioTrackRef.current) {
                await room.localParticipant.publishTrack(localAudioTrackRef.current);
            }
            console.log('✅ [LiveKit] Tracks Published');

        } catch (error: any) {
            console.error('❌ [LiveKit] Critical Error:', error);
            if (isMountedRef.current) {
                updateStatus('error');
                updateGuide('서버 연결 실패: ' + (error?.message || String(error)));
            }
            isConnectingRef.current = false;
        }
    }, []);

    // Cleanup
    useEffect(() => {
        return () => {
            console.log('🧹 [useLiveKitScreening] Unmount Cleanup');
            if (roomRef.current) roomRef.current.disconnect();

            // Unmount 시 트랙도 정지
            if (localVideoTrackRef.current) localVideoTrackRef.current.stop();
            if (localAudioTrackRef.current) localAudioTrackRef.current.stop();
        };
    }, []);

    return {
        videoRef,
        videoStream,
        isAligned,
        volume,
        personCount,
        guideMessage,
        status,
        sessionId,
        startScreening,
        stopScreening
    };
};
