// src/domains/exam/components/Screening/InstructionList.tsx
import React from 'react';
import { Eye, Zap } from 'lucide-react';

interface InstructionItem {
  id: number;
  text: string;
  boldText: string;
  suffix?: string;
}

const InstructionList: React.FC<{ title: string; items: InstructionItem[] }> = ({ title, items }) => (
  <div className="flex flex-col gap-5">
    <h3 className="text-gray-700 text-lg font-bold">{title}</h3>
    <div className="space-y-4">
      {items.map((item) => (
        <div key={item.id} className="flex items-start gap-4">
          <div className="w-7 h-7 mt-0.5 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 shrink-0">
            {item.id === 1 ? <Eye size={16} /> : <Zap size={16} />}
          </div>
          <p className="text-gray-600 text-base leading-snug">
            {item.text} <span className="font-bold text-gray-800 underline decoration-indigo-200 decoration-2 underline-offset-4">{item.boldText}</span> {item.suffix}
          </p>
        </div>
      ))}
    </div>
  </div>
);

export default InstructionList;