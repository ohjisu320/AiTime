// src/features/auth/hooks/useFindAccount.ts
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Swal from "sweetalert2";
import type { FindIdResult, FindTabType } from "../types/findAccount";

// [API Import]
import {
  sendPhoneVerification,
  verifyPhoneCode,
} from "../api/signup/signupApi"; // 기존 회원가입 API 재사용
import {
  findLoginId,
  verifyIdentity,
  resetPassword,
} from "../api/recovery/recoveryApi";

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
  // 1. 인증번호 요청 (공통)
  // ------------------------------------------------
  const requestAuth = async () => {
    // 유효성 검사
    if (!/^010[0-9]{8}$/.test(phoneNumber)) {
      return Swal.fire(
        "형식 오류",
        "'-' 없이 010으로 시작하는 11자리 숫자를 입력해주세요.",
        "warning",
      );
    }

    try {
      await sendPhoneVerification(phoneNumber);
      setIsAuthSent(true);
      Swal.fire("발송 완료", "인증번호가 발송되었습니다.", "success");
    } catch (error: any) {
      console.error(error);
      const msg =
        error.response?.status === 500
          ? "서버 설정 문제로 발송 실패"
          : "발송 실패";
      Swal.fire("오류", msg, "error");
    }
  };

  // ------------------------------------------------
  // 2. 인증번호 확인 (공통)
  // ------------------------------------------------
  const verifyAuth = async () => {
    if (!authCode)
      return Swal.fire("입력 필요", "인증번호를 입력해주세요.", "warning");

    try {
      const isOk = await verifyPhoneCode(phoneNumber, authCode);

      if (isOk) {
        setIsVerified(true);
        Swal.fire("인증 성공", "본인 인증이 완료되었습니다.", "success");

        // [비밀번호 찾기 모드]인 경우 -> userId를 받아와야 함
        if (activeTab === "RESET_PW") {
          try {
            const identityData = await verifyIdentity(phoneNumber);
            if (identityData.isVerified) {
              setTargetUserId(identityData.userId);
            } else {
              Swal.fire("오류", "가입된 정보를 찾을 수 없습니다.", "error");
              setIsVerified(false);
            }
          } catch (err) {
            console.error(err);
            Swal.fire(
              "오류",
              "사용자 정보를 조회하는 중 오류가 발생했습니다.",
              "error",
            );
            setIsVerified(false);
          }
        }
      } else {
        Swal.fire("인증 실패", "인증번호가 일치하지 않습니다.", "error");
      }
    } catch (error) {
      console.error(error);
      Swal.fire("오류", "인증 확인 중 문제가 발생했습니다.", "error");
    }
  };

  // ------------------------------------------------
  // 3. 아이디 찾기 실행
  // ------------------------------------------------
  const handleFindId = async () => {
    if (!isVerified)
      return Swal.fire(
        "인증 필요",
        "휴대폰 인증을 먼저 진행해주세요.",
        "warning",
      );

    try {
      const result = await findLoginId(phoneNumber);
      setFoundIdResult({
        loginId: result.loginId,
        createdAt: result.createdAt,
      });
    } catch (error) {
      console.error(error);
      Swal.fire("실패", "가입된 아이디 정보를 찾을 수 없습니다.", "error");
    }
  };

  // ------------------------------------------------
  // 4. 비밀번호 재설정 실행
  // ------------------------------------------------
  const handleResetPassword = async () => {
    if (!targetUserId)
      return Swal.fire(
        "오류",
        "사용자 정보를 찾을 수 없습니다. 다시 인증해주세요.",
        "error",
      );

    if (newPassword !== confirmPassword) {
      return Swal.fire("불일치", "비밀번호가 일치하지 않습니다.", "warning");
    }
    if (newPassword.length < 4) {
      return Swal.fire(
        "길이 부족",
        "비밀번호는 4자리 이상이어야 합니다.",
        "warning",
      );
    }

    try {
      await resetPassword(targetUserId, newPassword);
      await Swal.fire(
        "성공",
        "비밀번호가 변경되었습니다. 로그인해주세요.",
        "success",
      );
      navigate("/login");
    } catch (error) {
      console.error(error);
      Swal.fire("오류", "비밀번호 변경 중 오류가 발생했습니다.", "error");
    }
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
