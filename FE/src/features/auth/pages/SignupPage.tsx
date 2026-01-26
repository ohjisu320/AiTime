import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Swal from "sweetalert2";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";

// 약관 내용
const termsContent = `
아이타임(Ai-Time) 서비스 이용약관

[Part 1] 회원가입 시 필수 약관

제1조 (목적)
본 약관은 아이타임(Ai-Time)(이하 “회사”)이 제공하는 12~23개월 영유아 대상 행동 정량 분석 및 자폐 스펙트럼(ASD) 진단 보조 AI 서비스(이하 “서비스”)의 이용과 관련하여 회사와 회원 간의 권리·의무 및 책임사항을 규정함을 목적으로 합니다.

제2조 (용어의 정의)
1. 회원이란 본 약관에 동의하고 회사와 이용계약을 체결한 부모 또는 법정대리인을 말합니다.
2. 아동이란 본 서비스의 검사 및 분석 대상이 되는 영유아(주 대상: 12~23개월)를 말합니다.
3. 초대코드란 제휴 의료기관이 발급한 고유 인증 코드로, AI 검사 수행 및 리포트 확인을 위한 필수 수단을 말합니다.
4. AI 검사란 보호자와 아동의 가정 내 상호작용 영상을 촬영·업로드하여, AI 기술을 통해 행동 패턴을 정량적으로 분석하는 과정을 말합니다.
5. 리포트란 AI 검사를 통해 산출된 행동 분석 데이터 및 발달 지표 결과 보고서를 말합니다.

제3조 (이용계약의 성립)
1. 이용계약은 회원이 본 약관에 동의하고 회원가입을 신청한 후 회사가 이를 승낙함으로써 성립합니다.
2. 본 서비스는 검사 대상 아동의 법정대리인만 이용할 수 있습니다.
3. 회사는 별도의 증빙서류를 요구하지 않으나, 허위 사실이 확인될 경우 서비스 이용을 제한하거나 계약을 해지할 수 있습니다.

제4조 (서비스의 제공 및 이용 제한)
1. 회사는 회원에게 다음 각 호의 서비스를 제공합니다.
   - 보호자 및 아동 프로필 관리
   - AI 기반 행동 정량 분석 및 진단 보조 리포트 제공
   - 검사 이력 조회
2. 회원은 회원가입만으로 일부 기능만 이용할 수 있으며, AI 검사 및 리포트 제공은 유효한 초대코드를 입력한 경우에만 가능합니다.
3. 초대코드가 없거나 유효기간이 만료된 경우, AI 검사 기능은 제한됩니다.

제5조 (회원의 의무)
1. 회원은 아동의 영상을 촬영함에 있어 아동복지법 등 관계 법령에 위배되는 행위를 해서는 안 됩니다.
2. 초대코드는 회원 본인만 사용해야 하며, 양도·대여·공유할 수 없습니다.
3. 회원은 본 서비스에서 제공되는 AI 분석 결과가 의료행위 또는 의학적 진단을 대체하지 않으며, 최종적인 자폐 스펙트럼 진단 및 치료 판단은 의료진의 전문적 판단에 따라 이루어져야 함을 인지하고 동의합니다.

제6조 (의료행위 아님에 대한 고지 및 책임의 한계)
1. 본 서비스는 의료법상 의료행위에 해당하지 않으며, 의사의 진단, 처방, 치료를 대체하지 않습니다.
2. AI 검사 결과는 의료진이 자폐 스펙트럼 등을 진단함에 있어 시간을 단축하고 정확도를 높이기 위한 **보조적 참고 자료(진단 지원 도구)**로만 제공됩니다.
3. 회사는 가정 내 검사 환경, 촬영 조건, 아동의 일시적 컨디션 등에 따라 결과가 달라질 수 있음에 대해 책임을 지지 않습니다.

[Part 2] 개인정보 수집 및 이용 동의 (회원가입 시)

1. 수집·이용 목적
- 회원 관리 및 본인 확인
- 초대코드 기반 서비스 이용 자격(제휴 병원 환자 여부) 확인
- 12~23개월 아동 행동 분석 AI 검사 수행 및 리포트 제공
- 제휴 의료기관 연계 서비스 제공

2. 수집 항목
- 보호자 정보: 아이디, 비밀번호, 성명, 이메일, 휴대전화번호
- 아동 정보: 성명(또는 닉네임), 생년월일, 성별
- 병원 정보: 초대코드, 제휴 의료기관명
※ 아동 정보는 만 14세 미만 아동의 개인정보로서, 법정대리인의 동의를 전제로 수집됩니다.

3. 보유 및 이용 기간
- 회원 탈퇴 시 즉시 파기합니다.
- 단, 관계 법령에 따라 보존이 필요한 경우 해당 기간 동안 보관합니다.

[Part 3] 검사 시작 전 (영상 녹화 전) 필수 동의
(※ 본 동의는 검사 시작 버튼 클릭 후, 카메라 활성화 이전에 진행됩니다.)

1. 영상·음성 정보 수집 및 이용 동의 (필수)
회사는 정밀한 행동 분석을 위해 다음과 같은 민감정보 및 생체정보를 수집·이용합니다.
- 수집 항목: 보호자 및 아동의 얼굴 영상, 음성, 행동 정보(호명 반응, 눈맞춤 등), 시선 및 표정 변화 등 상호작용 데이터
- 이용 목적: AI 알고리즘을 통한 행동 정량 분석, 자폐 스펙트럼 진단 보조 데이터 산출 및 리포트 생성
- 보유 기간: 수집된 영상 및 음성 데이터는 리포트 생성 이후에도 5년간 보관되며, 해당 기간 경과 후 지체 없이 파기됩니다.

2. AI 모델 학습 및 고도화 목적 사용에 대한 고지
- 수집된 영상 및 음성 데이터는 AI 모델 학습, 성능 개선, 고도화, 재학습 목적에 사용되지 않습니다.
- 회사는 해당 데이터를 오직 개별 회원의 검사 결과 산출 및 사후 분쟁 대응, 서비스 품질 검증(오류 확인 등) 목적에 한하여 보관합니다.

3. 개인정보의 제3자 제공 동의 (필수 – 병원 제공)
- 제공받는 자: 초대코드를 발급한 제휴 의료기관
- 제공 목적: 아동 발달 상담 및 자폐 스펙트럼 정밀 진단 참고 자료 활용
- 제공 항목: AI 분석 결과 리포트 (영상 분석 정량 데이터)
- 제공 제외 항목: 원본 영상 및 음성 데이터 (병원의 별도 요청이 없는 한 리포트만 전송됨)
- 보유 및 이용 기간: 해당 의료기관의 관련 법령상 의무기록 보존 기간에 따름

4. AI 분석의 한계 및 면책 동의
본 서비스의 AI 분석 결과는 촬영 환경, 아동의 상태, 보호자의 상호작용 방식 등에 따라 차이가 발생할 수 있으며, 의학적 확진이나 치료 판단의 근거로 단독 사용될 수 없습니다. 회원은 위 사항을 충분히 인지하고 이에 동의합니다.
`;

export default function SignupPage() {
  const navigate = useNavigate();

  // 현재 단계: 1(약관동의) -> 2(정보입력)
  const [step, setStep] = useState<1 | 2>(1);
  const [agreed, setAgreed] = useState(false);

  // 입력값 상태
  const [formData, setFormData] = useState({
    id: "",
    password: "",
    confirmPassword: "",
    name: "",
    phone: "",
    authCode: "",
  });

  // 에러 메시지 상태
  const [errors, setErrors] = useState({
    id: "",
    password: "",
    confirmPassword: "",
    name: "",
    phone: "",
    authCode: "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleNextStep = () => {
    if (!agreed) {
      Swal.fire({
        icon: "warning",
        text: "약관에 동의해주세요.",
        confirmButtonColor: "#9593D9",
      });
      return;
    }
    setStep(2);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formData.password !== formData.confirmPassword) {
      setErrors((prev) => ({
        ...prev,
        confirmPassword: "비밀번호가 일치하지 않습니다.",
      }));
      return;
    }

    await Swal.fire({
      icon: "success",
      title: "회원가입 완료",
      text: "환영합니다! 이제 로그인이 가능합니다.",
      confirmButtonColor: "#9593D9",
    });

    navigate("/login");
  };

  // UI 컴포넌트: 헤더
  const Header = () => (
    <div className="w-full max-w-[600px] flex items-center justify-between mb-4 mt-2 px-2">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-[#9593D9] rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-md">
          Ai
        </div>
        <span className="text-3xl font-bold text-[#1A1A1A] tracking-tight font-['DM_Sans']">
          AiTime
        </span>
      </div>

      <button
        onClick={() => {
          if (step === 2) setStep(1);
          else navigate("/login");
        }}
        className="flex items-center gap-2 text-gray-500 hover:text-[#9593D9] transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span className="text-base font-medium text-[#555555]">뒤로 가기</span>
      </button>
    </div>
  );

  // UI 컴포넌트: 단계 표시기 (Stepper) - 연결선 강화
  const Stepper = () => (
    <div className="w-full max-w-[400px] mb-6 flex flex-col items-center">
      <div className="relative flex items-center justify-between w-[200px] mb-2">
        {/* 보라색 연결선 (항상 보라색) */}
        <div className="absolute left-0 top-1/2 w-full h-[4px] bg-[#9593D9] -z-10 -translate-y-1/2"></div>

        {/* 1단계 원 */}
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold z-10 transition-colors ${
            step >= 1
              ? "bg-[#9593D9] text-white shadow-md"
              : "bg-gray-200 text-gray-500"
          }`}
        >
          1
        </div>

        {/* 2단계 원 */}
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold z-10 transition-colors ${
            step === 2
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
          className={`text-sm font-bold ${step >= 1 ? "text-[#9593D9]" : "text-gray-400"}`}
        >
          약관 동의
        </span>
        <span
          className={`text-sm font-bold ${step === 2 ? "text-[#9593D9]" : "text-gray-400"}`}
        >
          회원정보 입력
        </span>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen w-full flex flex-col items-center bg-[#E3E0F5] p-4 overflow-y-auto">
      <Header />
      <Stepper />

      {/* 카드 컨테이너: 너비 줄임(max-w-[600px]), 패딩 줄임 */}
      <div className="w-full max-w-[600px] bg-white rounded-[32px] shadow-[0_10px_30px_rgba(0,0,0,0.05)] p-8 mb-8">
        {/* Step 1: 약관 동의 */}
        {step === 1 && (
          <div className="animate-fade-in">
            <h2 className="text-xl font-bold text-gray-800 mb-4">
              서비스 이용약관
            </h2>

            <div className="w-full h-[400px] bg-gray-50 rounded-xl border border-gray-100 p-5 mb-6 overflow-y-auto custom-scrollbar">
              <pre className="whitespace-pre-wrap font-sans text-sm text-gray-600 leading-relaxed">
                {termsContent}
              </pre>
            </div>

            <div
              className="flex items-center space-x-3 mb-6 p-3 bg-gray-50 rounded-xl cursor-pointer hover:bg-gray-100 transition-colors border border-transparent hover:border-gray-200"
              onClick={() => setAgreed(!agreed)}
            >
              <Checkbox
                id="terms"
                checked={agreed}
                onCheckedChange={(checked) => setAgreed(checked as boolean)}
                className="w-5 h-5 border-2 data-[state=checked]:bg-[#9593D9] data-[state=checked]:border-[#9593D9]"
              />
              <Label
                htmlFor="terms"
                className="text-base text-gray-700 font-bold cursor-pointer select-none"
              >
                위 약관을 확인하였으며, 이에 동의합니다.
              </Label>
            </div>

            <Button
              onClick={handleNextStep}
              className={cn(
                "w-full h-14 text-lg font-bold rounded-xl transition-all",
                agreed
                  ? "bg-[#9593D9] hover:bg-[#8381c9] text-white shadow-md shadow-[#9593D9]/20"
                  : "bg-gray-300 text-gray-500 cursor-not-allowed",
              )}
            >
              다음으로 넘어가기
            </Button>
          </div>
        )}

        {/* Step 2: 회원정보 입력 (컴팩트 버전) */}
        {step === 2 && (
          <div className="animate-fade-in">
            <h2 className="text-xl font-bold text-[#1A1A1A] mb-6 border-b pb-2">
              회원정보 입력
            </h2>

            {/* space-y를 줄여서 간격을 좁힘 */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* 아이디 */}
              <div className="space-y-1">
                <Label className="text-sm font-bold text-[#333]">아이디</Label>
                <div className="flex gap-2">
                  <Input
                    name="id"
                    value={formData.id}
                    onChange={handleChange}
                    placeholder="아이디 입력"
                    className="flex-1 h-11 bg-white border border-gray-200 rounded-lg text-sm px-3 focus:border-[#9593D9] focus:ring-1 focus:ring-[#9593D9]"
                  />
                  <Button
                    type="button"
                    className="h-11 w-[90px] bg-[#D6D3F0] hover:bg-[#c2bde6] text-[#5A5880] font-bold rounded-lg text-sm shadow-none"
                  >
                    중복확인
                  </Button>
                </div>
                <p className="text-[11px] text-red-500 pl-1 h-3">{errors.id}</p>
              </div>

              {/* 비밀번호 & 확인 (가로 배치 고려 or 세로 간격 좁힘) */}
              <div className="space-y-1">
                <Label className="text-sm font-bold text-[#333]">
                  비밀번호
                </Label>
                <Input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="비밀번호 입력"
                  className="h-11 bg-white border border-gray-200 rounded-lg text-sm px-3 focus:border-[#9593D9] focus:ring-1 focus:ring-[#9593D9]"
                />
              </div>

              <div className="space-y-1">
                <Label className="text-sm font-bold text-[#333]">
                  비밀번호 확인
                </Label>
                <Input
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  placeholder="비밀번호 재입력"
                  className="h-11 bg-white border border-gray-200 rounded-lg text-sm px-3 focus:border-[#9593D9] focus:ring-1 focus:ring-[#9593D9]"
                />
                <p className="text-[11px] text-red-500 pl-1 h-3">
                  {errors.confirmPassword}
                </p>
              </div>

              {/* 보호자 이름 */}
              <div className="space-y-1">
                <Label className="text-sm font-bold text-[#333]">
                  보호자 이름
                </Label>
                <Input
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="이름 입력"
                  className="h-11 bg-white border border-gray-200 rounded-lg text-sm px-3 focus:border-[#9593D9] focus:ring-1 focus:ring-[#9593D9]"
                />
              </div>

              {/* 휴대전화번호 & 인증 */}
              <div className="space-y-1 pt-1">
                <div className="flex justify-between items-end mb-1">
                  <Label className="text-sm font-bold text-[#333]">
                    휴대전화번호
                  </Label>
                </div>

                {/* 1. 번호 입력 + 인증 요청 */}
                <div className="flex gap-2">
                  <Input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    placeholder="010-1234-5678"
                    className="flex-1 h-11 bg-white border border-gray-200 rounded-lg text-sm px-3 focus:border-[#9593D9] focus:ring-1 focus:ring-[#9593D9]"
                  />
                  <Button
                    type="button"
                    className="h-11 w-[90px] bg-[#D6D3F0] hover:bg-[#c2bde6] text-[#5A5880] font-bold rounded-lg text-sm shadow-none"
                  >
                    인증요청
                  </Button>
                </div>

                {/* 2. 인증번호 입력 + 확인 */}
                <div className="flex gap-2 mt-2">
                  <Input
                    type="text"
                    name="authCode"
                    value={formData.authCode}
                    onChange={handleChange}
                    placeholder="인증번호"
                    className="flex-1 h-11 bg-white border border-gray-200 rounded-lg text-sm px-3 focus:border-[#9593D9] focus:ring-1 focus:ring-[#9593D9]"
                  />
                  <Button
                    type="button"
                    className="h-11 w-[90px] bg-[#D6D3F0] hover:bg-[#c2bde6] text-[#5A5880] font-bold rounded-lg text-sm shadow-none"
                  >
                    확인
                  </Button>
                </div>
              </div>

              {/* 회원가입 완료 버튼 */}
              <Button
                type="submit"
                className="w-full h-14 bg-[#9593D9] hover:bg-[#8381c9] text-white text-lg font-bold rounded-xl shadow-md mt-6"
              >
                회원가입 완료
              </Button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}