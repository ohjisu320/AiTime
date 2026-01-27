// src/components/common/FullScreenOverlayText.tsx 

interface Props {
  text: string;
}

export const FullScreenOverlayText = ({ text }: Props) => (
  <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-0">
    <h1 className="text-gray-400 text-7xl md:text-9xl font-normal font-['Noto_Sans_KR'] opacity-30 text-center leading-tight whitespace-pre-wrap">
      {text}
    </h1>
  </div>
);