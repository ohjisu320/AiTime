// src/domains/exam/components/layout/ExamBaseLayout.tsx
import React from 'react';
import VideoPreview from '../common/VideoPreview';

interface ExamBaseLayoutProps {
  sidebarContent: React.ReactNode;
  videoStream: MediaStream | null;
  isRecording: boolean;
  onBack: () => void;
  // ✅ 추가된 인터페이스 
  isAligned: boolean;
  volume: number;
  videoRef: React.RefObject<HTMLVideoElement>;
  children?: React.ReactNode;
}

const ExamBaseLayout: React.FC<ExamBaseLayoutProps> = ({ 
  sidebarContent, isRecording, onBack, isAligned, volume, videoRef, children, 
}) => {
  return (
    <div className="flex w-full h-screen bg-black overflow-hidden">
      <section className="relative flex-1 bg-gray-900">
        <VideoPreview 
          videoRef={videoRef}
          stream={null} 
          isAligned={isAligned}
          volume={volume}
          isRecording={isRecording}
          onBack={onBack} 
        />
      </section>
      <aside className="w-[504px] bg-white border-l border-gray-100 flex flex-col shadow-2xl z-20">
        {sidebarContent}
      </aside>
      {children}
    </div>
  );
};

export default ExamBaseLayout;