// src/features/auth/hooks/useSignup.ts
import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import Swal from "sweetalert2";
import type {
  SignupFormData,
  TermsAgreement,
  UserJoinRequest,
} from "../types/signup";

import {
  checkDuplicateId as apiCheckDuplicateId,
  sendPhoneVerification,
  verifyPhoneCode,
  signupUser,
} from "../api/signup/signupApi";

export const useSignup = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // URL 파라미터로 단계 제어
  const initialStep = Number(searchParams.get("step")) === 2 ? 2 : 1;
  const [step, setStep] = useState<1 | 2>(initialStep as 1 | 2);

  // --- 상태 관리 ---
  // 약관 동의
  const [agreements, setAgreements] = useState<TermsAgreement>({
    term1: false,
    term2: false,
  });
  const isAllAgreed = Object.values(agreements).every(Boolean);

  // 폼 데이터
  const [formData, setFormData] = useState<SignupFormData>({
    loginId: "",
    password: "",
    confirmPassword: "",
    name: "",
    phoneNumber: "",
    authCode: "",
  });

  // 에러 메시지
  const [errors, setErrors] = useState<Partial<SignupFormData>>({});

  // [추가] 검증 상태 관리 (중복확인, 본인인증 완료 여부)
  const [isIdChecked, setIsIdChecked] = useState(false);
  const [isPhoneVerified, setIsPhoneVerified] = useState(false);

  // --- Step 제어 ---
  useEffect(() => {
    const currentStepParam = searchParams.get("step");
    // 2단계 진입 시 약관 미동의면 1단계로 강제 이동
    if (currentStepParam === "2" && !isAllAgreed) {
      Swal.fire({
        icon: "warning",
        text: "약관 동의가 필요합니다.",
        confirmButtonColor: "#9593D9",
      });
      setStep(1);
      setSearchParams({ step: "1" });
    } else {
      setStep((Number(currentStepParam) as 1 | 2) || 1);
    }
  }, [searchParams, isAllAgreed, setSearchParams]);

  // --- 핸들러 ---

  // 입력값 변경 핸들러
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    // 값이 변경되면 관련 검증 상태 초기화
    if (name === "loginId") setIsIdChecked(false);
    if (name === "phoneNumber") setIsPhoneVerified(false);

    // 에러 메시지 초기화
    if (errors[name as keyof SignupFormData]) {
      setErrors((prev) => ({ ...prev, [name]: "" }));
    }
  };

  // 약관 동의 핸들러
  const handleAgreementChange = (id: string, checked: boolean) => {
    setAgreements((prev) => ({ ...prev, [id]: checked }));
  };

  const handleAllAgreeChange = (checked: boolean) => {
    setAgreements({
      term1: checked,
      term2: checked,
    });
  };

  const handleNextStep = () => {
    if (isAllAgreed) {
      setStep(2);
      setSearchParams({ step: "2" });
    } else {
      Swal.fire("약관 동의 필요", "모든 필수 약관에 동의해주세요.", "warning");
    }
  };

  const handleBack = () => {
    if (step === 2) {
      setStep(1);
      setSearchParams({ step: "1" });
    } else {
      navigate(-1);
    }
  };

  // --- API 연동 로직 ---

  // 1. 아이디 중복 확인
  const checkDuplicateId = async () => {
    if (!formData.loginId) {
      Swal.fire("아이디 입력", "아이디를 입력해주세요.", "warning");
      return;
    }
    try {
      const isDuplicate = await apiCheckDuplicateId(formData.loginId);
      if (isDuplicate) {
        Swal.fire("사용 불가", "이미 사용 중인 아이디입니다.", "error");
        setIsIdChecked(false);
      } else {
        Swal.fire("사용 가능", "사용 가능한 아이디입니다.", "success");
        setIsIdChecked(true);
      }
    } catch (error) {
      console.error(error);
      Swal.fire("오류", "중복 확인 중 오류가 발생했습니다.", "error");
    }
  };

  // 2. 인증번호 요청
  const requestAuthCode = async () => {
    // 전화번호 형식 검사 (간단한 정규식)
    const phoneRegex = /^010[0-9]{8}$/;
    if (!phoneRegex.test(formData.phoneNumber)) {
      Swal.fire(
        "형식 오류",
        "'-' 없이 010으로 시작하는 11자리 숫자를 입력해주세요.",
        "warning",
      );
      return;
    }

    try {
      await sendPhoneVerification(formData.phoneNumber);
      Swal.fire("발송 완료", "인증번호가 발송되었습니다.", "success");
    } catch (error) {
      console.error(error);
      Swal.fire("발송 실패", "인증번호 발송에 실패했습니다.", "error");
    }
  };

  // 3. 인증번호 확인
  const verifyAuthCode = async () => {
    if (!formData.authCode) {
      Swal.fire("입력 필요", "인증번호를 입력해주세요.", "warning");
      return;
    }
    try {
      const isVerified = await verifyPhoneCode(
        formData.phoneNumber,
        formData.authCode,
      );
      if (isVerified) {
        Swal.fire("인증 성공", "휴대폰 인증이 완료되었습니다.", "success");
        setIsPhoneVerified(true);
      } else {
        Swal.fire("인증 실패", "인증번호가 일치하지 않습니다.", "error");
        setIsPhoneVerified(false);
      }
    } catch (error) {
      console.error(error);
      Swal.fire("오류", "인증 과정에서 오류가 발생했습니다.", "error");
    }
  };

  // 4. 회원가입 제출
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 유효성 검사
    if (!isAllAgreed)
      return Swal.fire("오류", "약관에 동의해주세요.", "warning");
    if (!isIdChecked)
      return Swal.fire("확인 필요", "아이디 중복 확인을 해주세요.", "warning");
    if (!isPhoneVerified)
      return Swal.fire("확인 필요", "휴대폰 인증을 완료해주세요.", "warning");

    if (formData.password !== formData.confirmPassword) {
      setErrors((prev) => ({
        ...prev,
        confirmPassword: "비밀번호가 일치하지 않습니다.",
      }));
      return;
    }

    // API 요청 데이터 구성
    const requestBody: UserJoinRequest = {
      loginId: formData.loginId,
      password: formData.password,
      name: formData.name,
      phoneNumber: formData.phoneNumber,
      privacyAgreed: true,
    };

    try {
      await signupUser(requestBody);

      await Swal.fire({
        icon: "success",
        title: "가입 완료!",
        text: "회원가입이 성공적으로 완료되었습니다.",
        confirmButtonColor: "#9593D9",
      });
      navigate("/login"); // 로그인 페이지로 이동
    } catch (error: any) {
      console.error(error);
      const errorMessage =
        error.response?.data?.message || "회원가입에 실패했습니다.";
      Swal.fire("가입 실패", errorMessage, "error");
    }
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
