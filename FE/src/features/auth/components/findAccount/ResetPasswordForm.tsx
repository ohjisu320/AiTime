import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface ResetPasswordFormProps {
  // 인증 관련 Props
  phoneNumber: string;
  authCode: string;
  isAuthSent: boolean;
  isVerified: boolean;
  onPhoneChange: (val: string) => void;
  onAuthCodeChange: (val: string) => void;
  onRequestAuth: () => void;
  onVerifyAuth: () => void;

  // 비밀번호 변경 관련 Props
  newPw: string;
  confirmPw: string;
  onNewPwChange: (val: string) => void;
  onConfirmPwChange: (val: string) => void;
  onResetPassword: () => void;
}

export default function ResetPasswordForm({
  phoneNumber,
  authCode,
  isAuthSent,
  isVerified,
  onPhoneChange,
  onAuthCodeChange,
  onRequestAuth,
  onVerifyAuth,
  newPw,
  confirmPw,
  onNewPwChange,
  onConfirmPwChange,
  onResetPassword,
}: ResetPasswordFormProps) {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* 1. 본인 인증 영역 */}
      {!isVerified && (
        <>
          <div className="space-y-1">
            <Label className="text-sm font-bold text-gray-700">
              휴대전화번호
            </Label>
            <div className="flex gap-2">
              <Input
                value={phoneNumber}
                onChange={(e) => onPhoneChange(e.target.value)}
                placeholder="가입된 번호 입력"
                className="flex-1 h-12"
              />
              <Button
                onClick={onRequestAuth}
                className="h-12 w-24 bg-[#EBE9FF] text-[#5A55D6] hover:bg-[#dcd9fc] font-bold"
              >
                {isAuthSent ? "재전송" : "인증요청"}
              </Button>
            </div>
          </div>

          {isAuthSent && (
            <div className="flex gap-2">
              <Input
                value={authCode}
                onChange={(e) => onAuthCodeChange(e.target.value)}
                placeholder="인증번호"
                className="flex-1 h-12"
              />
              <Button
                onClick={onVerifyAuth}
                className="h-12 w-24 bg-[#5A55D6] text-white hover:bg-[#4844b8] font-bold"
              >
                확인
              </Button>
            </div>
          )}
        </>
      )}

      {/* 2. 비밀번호 재설정 영역 (인증 후 표시) */}
      {isVerified && (
        <div className="space-y-4 pt-2">
          <div className="p-3 bg-green-50 text-green-600 text-sm rounded-lg text-center font-bold">
            본인 인증이 완료되었습니다.
          </div>
          <div className="space-y-1">
            <Label className="text-sm font-bold text-gray-700">
              새 비밀번호
            </Label>
            <Input
              type="password"
              value={newPw}
              onChange={(e) => onNewPwChange(e.target.value)}
              placeholder="새 비밀번호 입력"
              className="h-12"
            />
          </div>
          <div className="space-y-1">
            <Label className="text-sm font-bold text-gray-700">
              비밀번호 확인
            </Label>
            <Input
              type="password"
              value={confirmPw}
              onChange={(e) => onConfirmPwChange(e.target.value)}
              placeholder="새 비밀번호 재입력"
              className="h-12"
            />
          </div>

          <Button
            onClick={onResetPassword}
            className="w-full h-14 mt-4 bg-[#5A55D6] hover:bg-[#4844b8] text-white font-bold rounded-xl text-lg"
          >
            비밀번호 변경하기
          </Button>
        </div>
      )}
    </div>
  );
}
