interface SignupStepperProps {
  currentStep: 1 | 2;
}

export default function SignupStepper({ currentStep }: SignupStepperProps) {
  return (
    <div className="w-full max-w-[400px] mb-6 flex flex-col items-center">
      <div className="relative flex items-center justify-between w-[200px] mb-2">
        {/* 보라색 연결선 */}
        <div className="absolute left-0 top-1/2 w-full h-[4px] bg-[#9593D9] -z-10 -translate-y-1/2"></div>

        {/* 1단계 원 */}
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold z-10 transition-colors ${
            currentStep >= 1
              ? "bg-[#9593D9] text-white shadow-md"
              : "bg-gray-200 text-gray-500"
          }`}
        >
          1
        </div>

        {/* 2단계 원 */}
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold z-10 transition-colors ${
            currentStep === 2
              ? "bg-[#9593D9] text-white shadow-md"
              : "bg-gray-200 text-gray-500"
          }`}
        >
          2
        </div>
      </div>

      {/* 텍스트 라벨 */}
      <div className="flex justify-between w-[240px]">
        <span
          className={`text-sm font-bold ${
            currentStep >= 1 ? "text-[#9593D9]" : "text-gray-400"
          }`}
        >
          약관 동의
        </span>
        <span
          className={`text-sm font-bold ${
            currentStep === 2 ? "text-[#9593D9]" : "text-gray-400"
          }`}
        >
          회원정보 입력
        </span>
      </div>
    </div>
  );
}
