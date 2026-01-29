// src/domains/exam/components/layout/ExamBaseLayout.tsx 
import React from 'react';
import VideoPreview from '../common/VideoPreview';

interface ExamBaseLayoutProps {
  sidebarContent: React.ReactNode;
  videoStream: MediaStream | null;
  isRecording: boolean;
  onBack: () => void;
  isAligned: boolean;
  volume: number;
  videoRef: React.RefObject<HTMLVideoElement>;
  children?: React.ReactNode;
  // ✅ 시각적 가이드(점선, 게이지) 표시 여부 추가 
  showVisualGuide?: boolean;
}

const ExamBaseLayout: React.FC<ExamBaseLayoutProps> = ({
  sidebarContent, videoStream, isRecording, onBack, isAligned, volume, videoRef, children,
  showVisualGuide = true // 👈 기본값은 true로 설정 
}) => {
  return (
    <div className="flex w-full h-screen bg-black overflow-hidden">
      <section className="relative flex-1 bg-gray-900">
        <VideoPreview
          videoRef={videoRef}
          stream={videoStream}
          // ✅ showVisualGuide가 false이면 가이드 관련 값을 무효화하거나 
          // VideoPreview 내부에서 이를 처리하도록 넘겨줍니다. 
          isAligned={showVisualGuide ? isAligned : true} // false면 정렬된 것으로 간주 
          volume={showVisualGuide ? volume : 0}          // false면 볼륨 0으로 처리 
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