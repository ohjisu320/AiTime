import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useFindAccount } from "../hooks/useFindAccount";
import FindAccountTabs from "../components/findAccount/FindAccountTabs";
import FindIdForm from "../components/findAccount/FindIdForm";
import ResetPasswordForm from "../components/findAccount/ResetPasswordForm";

export default function FindAccountPage() {
  const {
    activeTab,
    handleTabChange,
    navigate,
    phoneNumber,
    setPhoneNumber,
    authCode,
    setAuthCode,
    isAuthSent,
    isVerified,
    requestAuth,
    verifyAuth,
    // 아이디 찾기 관련
    foundIdResult,
    handleFindId,
    // 비번 재설정 관련
    newPassword,
    setNewPassword,
    confirmPassword,
    setConfirmPassword,
    handleResetPassword,
  } = useFindAccount();

  return (
    <div className="min-h-screen w-full flex flex-col items-center bg-[#E3E0F5] p-4">
      {/* Header */}
      <div className="w-full max-w-[500px] flex items-center justify-between mt-4 mb-8">
        <h1 className="text-2xl font-bold text-[#1A1A1A]">계정 찾기</h1>
        <Button
          variant="ghost"
          onClick={() => navigate("/login")}
          className="text-gray-500 gap-2"
        >
          <ArrowLeft className="w-4 h-4" /> 로그인으로
        </Button>
      </div>

      {/* Card Container */}
      <div className="w-full max-w-[500px] bg-white rounded-[32px] shadow-lg p-8">
        {/* Tabs */}
        <FindAccountTabs activeTab={activeTab} onTabChange={handleTabChange} />

        {/* Content */}
        {activeTab === "FIND_ID" ? (
          <FindIdForm
            phoneNumber={phoneNumber}
            authCode={authCode}
            isAuthSent={isAuthSent}
            isVerified={isVerified}
            foundIdResult={foundIdResult}
            onPhoneChange={setPhoneNumber}
            onAuthCodeChange={setAuthCode}
            onRequestAuth={requestAuth}
            onVerifyAuth={verifyAuth}
            onFindId={handleFindId}
            onGoLogin={() => navigate("/login")}
          />
        ) : (
          <ResetPasswordForm
            phoneNumber={phoneNumber}
            authCode={authCode}
            isAuthSent={isAuthSent}
            isVerified={isVerified}
            onPhoneChange={setPhoneNumber}
            onAuthCodeChange={setAuthCode}
            onRequestAuth={requestAuth}
            onVerifyAuth={verifyAuth}
            newPw={newPassword}
            confirmPw={confirmPassword}
            onNewPwChange={setNewPassword}
            onConfirmPwChange={setConfirmPassword}
            onResetPassword={handleResetPassword}
          />
        )}
      </div>
    </div>
  );
}
