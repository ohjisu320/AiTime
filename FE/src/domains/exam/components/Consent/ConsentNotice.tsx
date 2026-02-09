import React from 'react';
import { Info } from 'lucide-react';

const ConsentNotice: React.FC = () => (
  <div className="bg-amber-50 border-l-4 border-amber-400 p-5 rounded-r-xl flex gap-3 text-left">
    <Info className="w-6 h-6 text-amber-600 flex-shrink-0" />
    <div className="flex flex-col gap-1">
      <p className="text-amber-900 text-sm font-bold">중요 안내</p>
      <p className="text-amber-800 text-sm leading-relaxed">
        AiTime은 12-23개월 영유아와 부모가, 가정 내에서 수행하는 표준화된 4가지 과제를, AI가 채점하여, 소아과 의사의 초기 면담/ 관찰 과정을 대체하는, 디지털 의료기기입니다.
      </p>
    </div>
  </div>
);

export default ConsentNotice;