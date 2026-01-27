// src/domains/video/components/VideoRecorder.tsx
import React, { useEffect, useRef } from 'react';

interface Props {
  stream: MediaStream | null;
  isRecording: boolean;
}

export const VideoRecorder: React.FC<Props> = ({ stream, isRecording }) => {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  return (
    <div className="relative w-full h-full flex items-center justify-center">
      <video
        ref={videoRef}
        autoPlay
        muted
        playsInline
        className="w-full h-full object-cover scale-x-[-1]" // 미러링 처리
      />
      
      {/* 녹화 중일 때 빨간 점 표시 */}
      {isRecording && (
        <div className="absolute top-10 right-10 flex items-center gap-2">
          <div className="w-3 h-3 bg-red-600 rounded-full animate-pulse" />
          <span className="text-red-600 font-bold text-sm">REC</span>
        </div>
      )}
    </div>
  );
};