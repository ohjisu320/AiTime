import { useSignup } from "../hooks/useSignup";
import SignupHeader from "../components/signup/SignupHeader";
import SignupStepper from "../components/signup/SignupStepper";
import TermsStep from "../components/signup/TermsStep";
import UserInfoStep from "../components/signup/UserInfoStep";

export default function SignupPage() {
  const {
    step,
    agreements,
    isAllAgreed,
    formData,
    errors,
    handleAgreementChange,
    handleAllAgreeChange,
    handleInputChange,
    handleNextStep,
    handleBack,
    handleSubmit,
    checkDuplicateId,
    requestAuthCode,
    verifyAuthCode,
  } = useSignup();

  return (
    <div className="h-screen w-full flex flex-col items-center bg-[#E3E0F5] p-4 overflow-hidden">
      {/* 1. 헤더 */}
      <SignupHeader onBack={handleBack} />

      {/* 2. 단계 표시 (Stepper) */}
      <SignupStepper currentStep={step} />

      {/* 3. 카드 컨테이너 */}
      <div className="w-full max-w-[600px] bg-white rounded-[32px] shadow-[0_10px_30px_rgba(0,0,0,0.05)] mb-4 flex flex-col flex-1 min-h-0 overflow-hidden">
        <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
          {step === 1 && (
            <TermsStep
              agreements={agreements}
              isAllAgreed={isAllAgreed}
              onAgreementChange={handleAgreementChange}
              onAllAgreeChange={handleAllAgreeChange}
              onNext={handleNextStep}
            />
          )}

          {step === 2 && (
            <UserInfoStep
              formData={formData}
              errors={errors}
              onChange={handleInputChange}
              onSubmit={handleSubmit}
              onCheckDuplicate={checkDuplicateId}
              onRequestAuth={requestAuthCode}
              onVerifyAuth={verifyAuthCode}
            />
          )}
        </div>
      </div>
    </div>
  );
}
