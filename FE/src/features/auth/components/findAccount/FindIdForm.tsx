import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { FindIdResult } from "../../types/findAccount";

interface FindIdFormProps {
  phoneNumber: string;
  authCode: string;
  isAuthSent: boolean;
  isVerified: boolean;
  foundIdResult: FindIdResult | null;
  onPhoneChange: (val: string) => void;
  onAuthCodeChange: (val: string) => void;
  onRequestAuth: () => void;
  onVerifyAuth: () => void;
  onFindId: () => void;
  onGoLogin: () => void;
}

export default function FindIdForm({
  phoneNumber,
  authCode,
  isAuthSent,
  isVerified,
  foundIdResult,
  onPhoneChange,
  onAuthCodeChange,
  onRequestAuth,
  onVerifyAuth,
  onFindId,
  onGoLogin,
}: FindIdFormProps) {
  // 결과가 나온 경우 결과 화면 표시
  if (foundIdResult) {
    return (
      <div className="text-center py-8 animate-fade-in">
        <p className="text-gray-600 mb-2">회원님의 아이디는</p>
        <h3 className="text-2xl font-bold text-[#5A55D6] mb-1">
          {foundIdResult.loginId}
        </h3>
        <p className="text-xs text-gray-400 mb-8">
          가입일: {foundIdResult.createdAt.split("T")[0]}
        </p>
        <Button
          onClick={onGoLogin}
          className="w-full h-12 bg-[#5A55D6] hover:bg-[#4844b8] text-white font-bold rounded-xl"
        >
          로그인하러 가기
        </Button>
      </div>
    );
  }

  // 입력 폼
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="space-y-1">
        <Label className="text-sm font-bold text-gray-700">휴대전화번호</Label>
        <div className="flex gap-2">
          <Input
            value={phoneNumber}
            onChange={(e) => onPhoneChange(e.target.value)}
            placeholder="숫자만 입력"
            className="flex-1 h-12"
            disabled={isVerified}
          />
          <Button
            onClick={onRequestAuth}
            disabled={isVerified}
            className="h-12 w-24 bg-[#EBE9FF] text-[#5A55D6] hover:bg-[#dcd9fc] font-bold"
          >
            {isAuthSent ? "재전송" : "인증요청"}
          </Button>
        </div>
      </div>

      {isAuthSent && !isVerified && (
        <div className="space-y-1">
          <div className="flex gap-2">
            <Input
              value={authCode}
              onChange={(e) => onAuthCodeChange(e.target.value)}
              placeholder="인증번호 6자리"
              className="flex-1 h-12"
            />
            <Button
              onClick={onVerifyAuth}
              className="h-12 w-24 bg-[#5A55D6] text-white hover:bg-[#4844b8] font-bold"
            >
              확인
            </Button>
          </div>
        </div>
      )}

      <Button
        onClick={onFindId}
        disabled={!isVerified}
        className="w-full h-14 mt-4 bg-[#5A55D6] hover:bg-[#4844b8] text-white font-bold rounded-xl text-lg disabled:bg-gray-300"
      >
        아이디 찾기
      </Button>
    </div>
  );
}

