// src/features/auth/hooks/useFindAccount.ts
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Swal from "sweetalert2";
import type { FindIdResult, FindTabType } from "../types/findAccount";

export const useFindAccount = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<FindTabType>("FIND_ID");

  // 공통 상태: 휴대폰 번호 인증
  const [phoneNumber, setPhoneNumber] = useState("");
  const [authCode, setAuthCode] = useState("");
  const [isAuthSent, setIsAuthSent] = useState(false);
  const [isVerified, setIsVerified] = useState(false);

  // 아이디 찾기 결과 상태
  const [foundIdResult, setFoundIdResult] = useState<FindIdResult | null>(null);

  // 비밀번호 재설정 상태
  const [targetUserId, setTargetUserId] = useState<string>(""); // 식별된 유저 ID
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  // ------------------------------------------------
  // [Mock API] 인증번호 요청
  // ------------------------------------------------
  const requestAuth = () => {
    if (!phoneNumber)
      return Swal.fire("알림", "휴대폰 번호를 입력해주세요.", "warning");

    console.log("[API] POST /auth/phone/verification", { phoneNumber });
    setIsAuthSent(true);
    Swal.fire("발송 완료", "인증번호가 발송되었습니다. (123456)", "success");
  };

  // ------------------------------------------------
  // [Mock API] 인증번호 확인
  // ------------------------------------------------
  const verifyAuth = () => {
    if (!authCode)
      return Swal.fire("알림", "인증번호를 입력해주세요.", "warning");

    console.log("[API] POST /auth/phone/verify", {
      phoneNumber,
      verificationCode: authCode,
    });

    // 검증 성공 시뮬레이션
    setIsVerified(true);

    if (activeTab === "RESET_PW") {
      // 비밀번호 찾기인 경우: userId를 반환받았다고 가정 (PhoneVerifyForPasswordData)
      const mockUserId = "user-uuid-1234";
      setTargetUserId(mockUserId);
      Swal.fire("인증 성공", "비밀번호를 재설정해주세요.", "success");
    } else {
      Swal.fire("인증 성공", "아이디 조회 버튼을 눌러주세요.", "success");
    }
  };

  // ------------------------------------------------
  // [Mock API] 아이디 찾기 실행
  // ------------------------------------------------
  const handleFindId = () => {
    if (!isVerified)
      return Swal.fire("알림", "휴대폰 인증을 완료해주세요.", "warning");

    console.log("[API] GET /user/get-id", { phoneNumber });

    // 결과 수신 Mock
    setFoundIdResult({
      loginId: "aitime_parent",
      createdAt: "2025-01-15T10:00:00",
    });
  };

  // ------------------------------------------------
  // [Mock API] 비밀번호 재설정 실행
  // ------------------------------------------------
  const handleResetPassword = () => {
    if (!targetUserId) return;
    if (newPassword !== confirmPassword) {
      return Swal.fire("오류", "비밀번호가 일치하지 않습니다.", "error");
    }

    console.log("[API] PATCH /user/password", {
      userId: targetUserId,
      password: newPassword,
    });

    Swal.fire(
      "성공",
      "비밀번호가 변경되었습니다. 로그인해주세요.",
      "success",
    ).then(() => {
      navigate("/login");
    });
  };

  // 탭 변경 시 상태 초기화
  const handleTabChange = (tab: FindTabType) => {
    setActiveTab(tab);
    setPhoneNumber("");
    setAuthCode("");
    setIsAuthSent(false);
    setIsVerified(false);
    setFoundIdResult(null);
    setTargetUserId("");
    setNewPassword("");
    setConfirmPassword("");
  };

  return {
    activeTab,
    phoneNumber,
    authCode,
    isAuthSent,
    isVerified,
    foundIdResult,
    targetUserId,
    newPassword,
    confirmPassword,
    setPhoneNumber,
    setAuthCode,
    setNewPassword,
    setConfirmPassword,
    handleTabChange,
    requestAuth,
    verifyAuth,
    handleFindId,
    handleResetPassword,
    navigate,
  };
};
