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

  // 현재 미션 ID에 맞는 영상 경로 가져오기
  const videoSrc = MISSION_VIDEOS[missionId] || MISSION_VIDEOS["1"];

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
      {/* 1. 비디오 영역: 반드시 'muted'가 있어야 자동 재생됩니다. */}
      <div className="w-full h-full absolute inset-0 bg-gray-900 pointer-events-none">
        <video
          ref={videoRef}
          key={videoSrc}
          className="w-full h-full object-contain"
          autoPlay 
          loop 
          muted // 👈 브라우저 자동 재생을 위해 필수!
          playsInline 
        >
          <source src={videoSrc} type="video/mp4" />
        </video>
      </div>

      {/* 2. 중앙 텍스트: videoSrc(경로) 대신 디자인 문구를 넣어줍니다. */}
      <div className="z-10 pointer-events-none">
        <FullScreenOverlayText text={`미션 0${missionId}\n사전 안내영상`} />
      </div>

      {/* 3. 일시정지 UI */}
      {isPaused && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/20 z-20">
          <div className="w-20 h-20 bg-white/30 rounded-full flex items-center justify-center backdrop-blur-sm">
            <Play className="text-white w-10 h-10 fill-white ml-1" />
          </div>
        </div>
      )}

      {/* 4. 뒤로가기 버튼 */}
      <div onClick={(e) => e.stopPropagation()} className="z-30">
        <GlassBackButton onClick={() => navigate('/exam/mission')} />
      </div>

      {/* 5. Skip 버튼 */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          navigate(`/exam/screening/${missionId}`);
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