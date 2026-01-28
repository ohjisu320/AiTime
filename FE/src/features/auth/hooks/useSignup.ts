// src/features/auth/hooks/useSignup.ts
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Swal from "sweetalert2";
// ✅ 충돌 방지를 위해 별도로 생성한 파일에서 타입 Import
import type { SignupFormData, TermsAgreement } from "../types/signup";

export const useSignup = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState<1 | 2>(1);

  // --- Step 1: 약관 동의 State ---
  const [agreements, setAgreements] = useState<TermsAgreement>({
    term1: false,
    term2: false,
    term3: false,
  });

  const isAllAgreed = Object.values(agreements).every(Boolean);

  const handleAgreementChange = (
    key: keyof TermsAgreement,
    checked: boolean,
  ) => {
    setAgreements((prev) => ({ ...prev, [key]: checked }));
  };

  const handleAllAgreeChange = (checked: boolean) => {
    setAgreements({
      term1: checked,
      term2: checked,
      term3: checked,
    });
  };

  // --- Step 2: 회원 정보 State ---
  const [formData, setFormData] = useState<SignupFormData>({
    loginId: "",
    password: "",
    confirmPassword: "",
    name: "",
    phoneNumber: "",
    authCode: "",
  });

  const [errors, setErrors] = useState<Partial<SignupFormData>>({});

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // 입력 시 에러 초기화
    if (errors[name as keyof SignupFormData]) {
      setErrors((prev) => ({ ...prev, [name]: "" }));
    }
  };

  // --- Navigation & Mock API Logic ---
  const handleNextStep = () => {
    if (!isAllAgreed) {
      Swal.fire({
        icon: "warning",
        text: "모든 필수 약관에 동의해주세요.",
        confirmButtonColor: "#9593D9",
      });
      return;
    }
    setStep(2);
  };

  const handleBack = () => {
    if (step === 2) setStep(1);
    else navigate("/login");
  };

  // [API Mock] 아이디 중복 확인
  const checkDuplicateId = async () => {
    console.log("중복 확인 요청:", formData.loginId);
    // 실제 API 호출 로직이 들어갈 자리
    Swal.fire("성공", "사용 가능한 아이디입니다.", "success");
  };

  // [API Mock] 인증번호 요청
  const requestAuthCode = async () => {
    console.log("인증번호 요청:", formData.phoneNumber);
    // 실제 API 호출 로직이 들어갈 자리
    Swal.fire("발송 완료", "인증번호가 발송되었습니다.", "success");
  };

  // [API Mock] 인증번호 확인
  const verifyAuthCode = async () => {
    console.log("인증번호 확인:", formData.authCode);
    // 실제 API 호출 로직이 들어갈 자리
    Swal.fire("인증 성공", "휴대폰 인증이 완료되었습니다.", "success");
  };

  // [API Mock] 회원가입 요청
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formData.password !== formData.confirmPassword) {
      setErrors((prev) => ({
        ...prev,
        confirmPassword: "비밀번호가 일치하지 않습니다.",
      }));
      return;
    }

    // API 요청 데이터 매핑 (UserJoinRequest 형식)
    const requestBody = {
      loginId: formData.loginId,
      password: formData.password,
      name: formData.name,
      phoneNumber: formData.phoneNumber,
      privacyAgreed: true, // 필수 약관 동의 확인됨
    };

    console.log("API Request Body:", requestBody);

    await Swal.fire({
      icon: "success",
      title: "회원가입 완료",
      text: "환영합니다! 이제 로그인이 가능합니다.",
      confirmButtonColor: "#9593D9",
    });

    navigate("/login");
  };

  return {
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
  };
};
