import React from 'react'; // JSX 인식을 위해 추가
import { ChevronLeft } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ConsentHeaderProps {
  currentStep: number;
  totalSteps: number;
  onBack?: () => void;
}

const ConsentHeader: React.FC<ConsentHeaderProps> = ({ currentStep, totalSteps, onBack }) => (
  <header className="fixed top-0 left-0 w-full h-20 bg-white shadow-sm flex items-center justify-center z-50">
    <div className="w-full max-w-[1555px] px-6 flex items-center justify-between">
      <button 
        type="button" 
        onClick={onBack} 
        className="p-2 rounded-xl hover:bg-gray-100 transition-colors"
      >
        <ChevronLeft className="w-6 h-6 text-gray-600" />
      </button>
      <div className="flex items-center gap-2">
        {Array.from({ length: totalSteps }, (_, i) => i + 1).map((step) => (
          <div key={step} className="flex items-center gap-2">
            <div className={cn(
              "w-8 h-8 rounded-full flex justify-center items-center font-bold transition-colors",
              step === currentStep ? "bg-[#6366F1] text-white" : "bg-gray-200 text-gray-500"
            )}>
              {step}
            </div>
            {step < totalSteps && <div className="w-12 h-1 bg-gray-200" />}
          </div>
        ))}
      </div>
      <div className="w-10" />
    </div>
  </header>
);

export default ConsentHeader;