// src/domains/exam/components/common/VideoPreview.tsx
import React, { useEffect } from 'react';
import { ChevronLeft, Mic } from 'lucide-react';
import { cn } from '@/lib/utils';

interface VideoPreviewProps {
  videoRef: React.RefObject<HTMLVideoElement>;
  stream: MediaStream | null;
  isAligned: boolean;
  volume: number; // 0 ~ 100 사이의 수치
  isRecording: boolean;
  onBack: () => void;
}

const VideoPreview: React.FC<VideoPreviewProps> = ({
  videoRef, stream, isAligned, volume, isRecording, onBack
}) => {

  useEffect(() => {
    if (videoRef.current && stream) {
      console.log('📺 [VideoPreview] Stream assigned to video element:', stream.id);
      videoRef.current.srcObject = stream;
    } else {
      console.log('📺 [VideoPreview] No stream or ref available');
    }
  }, [stream, videoRef]);

  // 🎤 실시간 이퀄라이저 컴포넌트
  const SoundVisualizer = () => {
    // 막대기 12개 생성
    const bars = Array.from({ length: 12 });

    return (
      <div className="absolute left-10 bottom-10 flex flex-col gap-3 p-6 bg-black/60 backdrop-blur-xl rounded-[32px] border border-white/10 shadow-2xl z-[70]">
        <div className="flex items-end gap-1.5 h-16 px-2">
          {bars.map((_, i) => {
            // 소음 수치에 랜덤성을 부여하여 더 역동적으로 표현
            const randomFactor = 0.4 + Math.random() * 0.6;
            const barHeight = Math.max(15, Math.min(100, volume * randomFactor));

            return (
              <div
                key={i}
                className={cn(
                  "w-2.5 rounded-full transition-all duration-150 ease-out",
                  volume > 30 ? "bg-rose-500" : "bg-emerald-400"
                )}
                style={{ height: `${barHeight}%` }}
              />
            );
          })}
        </div>

        <div className="flex items-center gap-2 px-1">
          <Mic size={18} className={volume > 30 ? "text-rose-500" : "text-emerald-400"} />
          <span className={cn(
            "text-lg font-bold transition-colors",
            volume > 30 ? "text-rose-500" : "text-emerald-400"
          )}>
            {volume > 30 ? "소음 주의" : "좋음"}
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="relative w-full h-full bg-black overflow-hidden flex items-center justify-center">
      <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover scale-x-[-1]" />

      {/* 1. 얼굴 가이드 (보내주신 점선 원 구조) */}
      {!isRecording && (
        <div className="absolute inset-0 pointer-events-none flex">
          {/* 중앙 분리선 */}
          <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-white/50 border-r border-dashed border-white/50 -translate-x-1/2 z-10" />

          {/* 왼쪽: 보호자 영역 */}
          <div className="flex-1 relative border-r border-white/20 flex flex-col items-center justify-center">
            <div className={cn(
              "absolute top-10 left-10 right-10 bottom-20 rounded-3xl border-4 border-dashed transition-all duration-500 flex items-center justify-center",
              isAligned ? "border-emerald-400 bg-emerald-400/5" : "border-white/30"
            )}>
              <span className="text-white text-xl font-bold text-center leading-relaxed drop-shadow-md bg-black/20 px-6 py-3 rounded-2xl backdrop-blur-sm">
                보호자 영역<br />
                <span className="text-sm opacity-80 font-normal">왼쪽 반 화면에 맞춰주세요</span>
              </span>
            </div>
          </div>

          {/* 오른쪽: 자녀 영역 */}
          <div className="flex-1 relative flex flex-col items-center justify-center">
            <div className={cn(
              "absolute top-10 left-10 right-10 bottom-20 rounded-3xl border-4 border-dashed transition-all duration-500 flex items-center justify-center",
              isAligned ? "border-emerald-400 bg-emerald-400/5" : "border-white/30"
            )}>
              <span className="text-white text-xl font-bold text-center leading-relaxed drop-shadow-md bg-black/20 px-6 py-3 rounded-2xl backdrop-blur-sm">
                아이 영역<br />
                <span className="text-sm opacity-80 font-normal">오른쪽 반 화면에 맞춰주세요</span>
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 2. 실시간 소음 이퀄라이저 */}
      {!isRecording && <SoundVisualizer />}

      {/* 뒤로가기 버튼 */}
      <button onClick={onBack} className="absolute left-6 top-6 w-12 h-12 bg-white/10 rounded-full flex items-center justify-center text-white backdrop-blur-md hover:bg-white/20 transition-all">
        <ChevronLeft size={24} />
      </button>
    </div>
  );
};

export default VideoPreview;