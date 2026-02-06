import React from 'react'; // JSX 인식을 위해 추가
import { ChevronLeft } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useNavigate } from 'react-router-dom';

interface ConsentHeaderProps {
  currentStep: number;
  totalSteps: number;
  onBack?: () => void;
  title?: string;
  subtitle?: string;
}

const ConsentHeader: React.FC<ConsentHeaderProps> = ({ currentStep, totalSteps, onBack, title, subtitle }) => {
  const navigate = useNavigate();

  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      navigate(-1);
    }
  };

  return (
    <header className="fixed top-0 left-0 w-full h-20 bg-white shadow-sm flex items-center justify-center z-50">
      <div className="w-full max-w-[1555px] px-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={handleBack}
            className="p-2 rounded-xl hover:bg-gray-100 transition-colors"
          >
            <ChevronLeft className="w-6 h-6 text-gray-600" />
          </button>
          <img src="/parentLogo.svg" alt="AiTime Logo" className="h-8 w-auto cursor-pointer" onClick={() => navigate('/parent/dashboard')} />
          {title && (
            <div className="ml-4">
              <h1 className="text-lg font-bold text-gray-800">{title}</h1>
              {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
            </div>
          )}
        </div>
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
      </div>
    </header>
  );
}
export default ConsentHeader;