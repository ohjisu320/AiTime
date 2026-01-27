import React from 'react';

// 1. 인터페이스에 subText 추가 (물음표?를 붙여서 선택 사항으로 만듦)
interface FullScreenOverlayTextProps {
  text: string;
  subText?: string; 
}

export const FullScreenOverlayText: React.FC<FullScreenOverlayTextProps> = ({ text, subText }) => {
  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-300">
      {/* 메인 텍스트 (카운트다운 숫자) */}
      <h1 className="text-9xl font-black text-white drop-shadow-[0_10px_10px_rgba(0,0,0,0.5)] animate-bounce">
        {text}
      </h1>
      
      {/* 2. 서브 텍스트 렌더링 추가 */}
      {subText && (
        <p className="mt-4 text-3xl font-bold text-white/80 animate-pulse">
          {subText}
        </p>
      )}
    </div>
  );
};