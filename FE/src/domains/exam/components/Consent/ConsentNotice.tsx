import React from 'react';
import { Info } from 'lucide-react';

const ConsentNotice: React.FC = () => (
  <div className="bg-amber-50 border-l-4 border-amber-400 p-5 rounded-r-xl flex gap-3 text-left">
    <Info className="w-6 h-6 text-amber-600 flex-shrink-0" />
    <div className="flex flex-col gap-1">
      <p className="text-amber-900 text-sm font-bold">중요 안내</p>
      <p className="text-amber-800 text-sm leading-relaxed">
        AiTime은 의료 보조 도구입니다. 검사 결과는 반드시 전문의와 상담하여 해석해야 하며, 자가 진단의 목적으로 사용되지 않습니다.
      </p>
    </div>
  </div>
);

export default ConsentNotice;