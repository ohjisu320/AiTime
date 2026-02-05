import { ArrowLeft } from "lucide-react";
import parentLogo from '@/assets/parentLogo.svg';

interface SignupHeaderProps {
  onBack: () => void;
}

export default function SignupHeader({ onBack }: SignupHeaderProps) {
  return (
    <div className="w-full max-w-[600px] flex items-center justify-between mb-4 mt-2 px-2">
      <div className="flex items-center gap-3">
        <img
          src={parentLogo}
          alt="AiTime Logo"
          className="w-10 h-10"
        />
        <span className="text-3xl font-bold text-[#1A1A1A] tracking-tight font-['DM_Sans']">
          AiTime
        </span>
      </div>

      <button
        onClick={onBack}
        className="flex items-center gap-2 text-gray-500 hover:text-[#9593D9] transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span className="text-base font-medium text-[#555555]">뒤로 가기</span>
      </button>
    </div>
  );
}

