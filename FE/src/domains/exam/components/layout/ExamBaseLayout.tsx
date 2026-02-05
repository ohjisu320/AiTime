// src/domains/exam/components/layout/ExamBaseLayout.tsx 
import React from 'react';
import VideoPreview from '../common/VideoPreview';

interface ExamBaseLayoutProps {
  videoStream: MediaStream | null;
  isRecording: boolean;
  onBack: () => void;
  isAligned: boolean;
  volume: number;
  videoRef: React.RefObject<HTMLVideoElement>;
  children?: React.ReactNode;
  showVisualGuide?: boolean;
}

const ExamBaseLayout: React.FC<ExamBaseLayoutProps> = ({
  videoStream, isRecording, onBack, isAligned, volume, videoRef, children,
  showVisualGuide = true
}) => {
  return (
    <div className="relative w-full h-screen bg-black overflow-hidden">
      <section className="w-full h-full bg-gray-900">
        <VideoPreview
          videoRef={videoRef}
          stream={videoStream}
          isAligned={showVisualGuide ? isAligned : true}
          volume={showVisualGuide ? volume : 0}
          isRecording={isRecording}
          onBack={onBack}
        />
      </section>
      {/* Overlay Children */}
      {children}
    </div>
  );
};

export default ExamBaseLayout;