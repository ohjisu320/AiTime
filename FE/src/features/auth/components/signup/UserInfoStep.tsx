import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
// ✅ 분리된 타입 파일 import
import type { SignupFormData } from "../../types/signup";

interface UserInfoStepProps {
  formData: SignupFormData;
  errors: Partial<SignupFormData>;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onSubmit: (e: React.FormEvent) => void;
  onCheckDuplicate: () => void;
  onRequestAuth: () => void;
  onVerifyAuth: () => void;
}

export default function UserInfoStep({
  formData,
  errors,
  onChange,
  onSubmit,
  onCheckDuplicate,
  onRequestAuth,
  onVerifyAuth,
}: UserInfoStepProps) {
  return (
    <div className="animate-fade-in">
      <h2 className="text-xl font-bold text-[#1A1A1A] mb-6 border-b pb-2">
        회원정보 입력
      </h2>

      <form onSubmit={onSubmit} className="space-y-4">
        {/* 아이디 */}
        <div className="space-y-1">
          <Label className="text-sm font-bold text-[#333]">아이디</Label>
          <div className="flex gap-2">
            <Input
              name="loginId"
              value={formData.loginId}
              onChange={onChange}
              placeholder="아이디 입력"
              className="flex-1 h-11 bg-white border border-gray-200 rounded-lg text-sm px-3 focus:border-[#9593D9] focus:ring-1 focus:ring-[#9593D9]"
            />
            <Button
              type="button"
              onClick={onCheckDuplicate}
              className="h-11 w-[90px] bg-[#D6D3F0] hover:bg-[#c2bde6] text-[#5A5880] font-bold rounded-lg text-sm shadow-none"
            >
              중복확인
            </Button>
          </div>
          <p className="text-[11px] text-red-500 pl-1 h-3">{errors.loginId}</p>
        </div>

        {/* 비밀번호 */}
        <div className="space-y-1">
          <Label className="text-sm font-bold text-[#333]">비밀번호</Label>
          <Input
            type="password"
            name="password"
            value={formData.password}
            onChange={onChange}
            placeholder="비밀번호 입력"
            className="h-11 bg-white border border-gray-200 rounded-lg text-sm px-3 focus:border-[#9593D9] focus:ring-1 focus:ring-[#9593D9]"
          />
        </div>

        {/* 비밀번호 확인 */}
        <div className="space-y-1">
          <Label className="text-sm font-bold text-[#333]">비밀번호 확인</Label>
          <Input
            type="password"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={onChange}
            placeholder="비밀번호 재입력"
            className="h-11 bg-white border border-gray-200 rounded-lg text-sm px-3 focus:border-[#9593D9] focus:ring-1 focus:ring-[#9593D9]"
          />
          <p className="text-[11px] text-red-500 pl-1 h-3">
            {errors.confirmPassword}
          </p>
        </div>

        {/* 보호자 이름 */}
        <div className="space-y-1">
          <Label className="text-sm font-bold text-[#333]">보호자 이름</Label>
          <Input
            name="name"
            value={formData.name}
            onChange={onChange}
            placeholder="이름 입력"
            className="h-11 bg-white border border-gray-200 rounded-lg text-sm px-3 focus:border-[#9593D9] focus:ring-1 focus:ring-[#9593D9]"
          />
        </div>

        {/* 휴대전화번호 및 인증 */}
        <div className="space-y-1 pt-1">
          <Label className="text-sm font-bold text-[#333]">휴대전화번호</Label>
          <div className="flex gap-2">
            <Input
              type="tel"
              name="phoneNumber"
              value={formData.phoneNumber}
              onChange={onChange}
              placeholder="010-1234-5678"
              className="flex-1 h-11 bg-white border border-gray-200 rounded-lg text-sm px-3 focus:border-[#9593D9] focus:ring-1 focus:ring-[#9593D9]"
            />
            <Button
              type="button"
              onClick={onRequestAuth}
              className="h-11 w-[90px] bg-[#D6D3F0] hover:bg-[#c2bde6] text-[#5A5880] font-bold rounded-lg text-sm shadow-none"
            >
              인증요청
            </Button>
          </div>
          <div className="flex gap-2 mt-2">
            <Input
              type="text"
              name="authCode"
              value={formData.authCode}
              onChange={onChange}
              placeholder="인증번호"
              className="flex-1 h-11 bg-white border border-gray-200 rounded-lg text-sm px-3 focus:border-[#9593D9] focus:ring-1 focus:ring-[#9593D9]"
            />
            <Button
              type="button"
              onClick={onVerifyAuth}
              className="h-11 w-[90px] bg-[#D6D3F0] hover:bg-[#c2bde6] text-[#5A5880] font-bold rounded-lg text-sm shadow-none"
            >
              확인
            </Button>
          </div>
        </div>

        <Button
          type="submit"
          className="w-full h-14 bg-[#9593D9] hover:bg-[#8381c9] text-white text-lg font-bold rounded-xl shadow-md mt-6"
        >
          회원가입 완료
        </Button>
      </form>
    </div>
  );
}
