import React, { useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Play } from 'lucide-react';
import { MISSION_VIDEOS } from '../constants/videoData';
import { GlassBackButton } from '@/components/common/GlassBackButton';
import { FullScreenOverlayText } from '@/components/common/FullScreenOverlayText';

const ExamGuideVideoPage: React.FC = () => {
  const navigate = useNavigate();
  const { missionId = "1" } = useParams<{ missionId: string }>();

  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPaused, setIsPaused] = useState(false);

  const videoSrc = missionId ? MISSION_VIDEOS[missionId] : null;

  if (!videoSrc) {
    return <div className="w-full h-screen bg-black flex items-center justify-center p-20 text-white font-['Noto_Sans_KR']">잘못된 접근입니다. (Video not found for {missionId})</div>;
  }

  // ✅ 다음 단계로 이동하는 공통 함수 
  const moveToNextStep = () => {
    navigate(`/exam/screening/${missionId}`);
  };

  // ✅ 재생/일시정지 토글
  const togglePlay = () => {
    if (!videoRef.current) return;
    if (videoRef.current.paused) {
      videoRef.current.play();
      setIsPaused(false);
    } else {
      videoRef.current.pause();
      setIsPaused(true);
    }
  };

  return (
    <div
      className="w-full h-screen relative bg-black overflow-hidden flex items-center justify-center cursor-pointer"
      onClick={togglePlay}
    >
      {/* 1. 배경 비디오 영역  */}
      <div className="w-full h-full absolute inset-0 bg-gray-900 pointer-events-none">
        <video
          ref={videoRef}
          key={videoSrc}
          className="w-full h-full object-contain"
          autoPlay
          muted
          playsInline
          onEnded={moveToNextStep} // 👈 영상 재생이 끝나면 자동으로 실행 
        // loop 속성은 제거했습니다. 
        >
          <source src={videoSrc} type="video/mp4" />
        </video>
      </div>

      {/* 2. 중앙 텍스트 오버레이  */}
      <div className="z-10 pointer-events-none">
        <FullScreenOverlayText text={`사전\n안내영상`} />
      </div>

      {/* 3. 일시정지 상태 피드백  */}
      {isPaused && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/20 z-20">
          <div className="w-20 h-20 bg-white/30 rounded-full flex items-center justify-center backdrop-blur-sm">
            <Play className="text-white w-10 h-10 fill-white ml-1" />
          </div>
        </div>
      )}

      {/* 4. 상단 뒤로가기 버튼  */}
      <div onClick={(e) => e.stopPropagation()} className="z-30">
        <GlassBackButton onClick={() => navigate('/exam/mission')} />
      </div>

      {/* 5. 하단 Skip 버튼  */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          moveToNextStep(); // 👈 수동으로 넘어가기 
        }}
        className="absolute right-10 bottom-10 w-32 h-11 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full shadow-2xl flex items-center justify-center gap-2 transition-all active:scale-95 z-30"
      >
        <span className="text-sm font-normal font-['Noto_Sans_KR'] leading-5">skip</span>
        <div className="w-2 h-2 border-t-2 border-r-2 border-white rotate-45 transform translate-y-[1px]" />
      </button>
    </div>
  );
};

export default ExamGuideVideoPage;