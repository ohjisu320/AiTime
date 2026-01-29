import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
// ✅ 분리된 타입 파일 import
import type { TermsAgreement } from "../../types/signup";

// 약관 데이터 (기존 파일에서 분리)
const TERMS_DATA = [
  {
    id: "term1",
    title: "[Part 1] 회원가입 시 필수 약관",
    content: `제1조 (목적)
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
2. AI 검사 결과는 의료진이 자폐 스펙트럼 등을 진단함에 있어 시간을 단축하고 정확도를 높이기 위한 보조적 참고 자료(진단 지원 도구)로만 제공됩니다.
3. 회사는 가정 내 검사 환경, 촬영 조건, 아동의 일시적 컨디션 등에 따라 결과가 달라질 수 있음에 대해 책임을 지지 않습니다.`,
  },
  {
    id: "term2",
    title: "[Part 2] 개인정보 수집 및 이용 동의 (필수)",
    content: `1. 수집·이용 목적

- 회원 관리 및 본인 확인
- 초대코드 기반 서비스 이용 자격(제휴 병원 환자 여부) 확인
- 12~23개월 아동 행동 분석 AI 검사 수행 및 리포트 제공
- 제휴 의료기관 연계 서비스 제공

2. 수집 항목

- 보호자 정보: 아이디, 비밀번호, 성명, 이메일, 휴대전화번호
- 아동 정보: 성명(또는 닉네임), 생년월일, 성별
- 병원 정보: 초대코드, 제휴 의료기관명
- ※ 아동 정보는 만 14세 미만 아동의 개인정보로서, 법정대리인의 동의를 전제로 수집됩니다.

3. 보유 및 이용 기간

- 회원 탈퇴 시 즉시 파기합니다.
- 단, 관계 법령에 따라 보존이 필요한 경우 해당 기간 동안 보관합니다.`,
  },
];

interface TermsStepProps {
  agreements: TermsAgreement;
  isAllAgreed: boolean;
  onAgreementChange: (key: keyof TermsAgreement, checked: boolean) => void;
  onAllAgreeChange: (checked: boolean) => void;
  onNext: () => void;
}

export default function TermsStep({
  agreements,
  isAllAgreed,
  onAgreementChange,
  onAllAgreeChange,
  onNext,
}: TermsStepProps) {
  return (
    <div className="animate-fade-in">
      <h2 className="text-xl font-bold text-gray-800 mb-6 border-b pb-2">
        서비스 이용약관 동의
      </h2>

      <div className="space-y-8 mb-8">
        {TERMS_DATA.map((term) => {
          const termKey = term.id as keyof TermsAgreement;
          return (
            <div key={term.id} className="flex flex-col gap-2">
              <div className="flex justify-between items-center px-1">
                <span className="text-sm font-bold text-gray-700">
                  {term.title}
                </span>
              </div>
              <div className="w-full h-32 bg-gray-50 rounded-xl border border-gray-100 p-4 overflow-y-auto custom-scrollbar">
                <pre className="whitespace-pre-wrap font-sans text-xs text-gray-600 leading-relaxed">
                  {term.content}
                </pre>
              </div>
              <div
                className="flex items-center space-x-2 p-2 cursor-pointer hover:bg-gray-50 rounded-lg transition-colors"
                onClick={() => onAgreementChange(termKey, !agreements[termKey])}
              >
                <Checkbox
                  id={term.id}
                  checked={agreements[termKey]}
                  onCheckedChange={(checked) =>
                    onAgreementChange(termKey, checked as boolean)
                  }
                  className="w-4 h-4 border-gray-300 data-[state=checked]:bg-[#9593D9] data-[state=checked]:border-[#9593D9]"
                />
                <Label
                  htmlFor={term.id}
                  className="text-sm text-gray-600 cursor-pointer select-none"
                >
                  {term.title}에 동의합니다.
                </Label>
              </div>
            </div>
          );
        })}
      </div>

      <div className="border-t border-gray-100 pt-6 mb-6">
        <div
          className="flex items-center space-x-3 p-4 bg-[#F5F4FF] rounded-xl cursor-pointer hover:bg-[#EBE9FF] transition-colors border border-[#9593D9]/20"
          onClick={() => onAllAgreeChange(!isAllAgreed)}
        >
          <Checkbox
            id="all-agree"
            checked={isAllAgreed}
            onCheckedChange={(checked) => onAllAgreeChange(checked as boolean)}
            className="w-5 h-5 border-2 border-[#9593D9] data-[state=checked]:bg-[#9593D9] data-[state=checked]:text-white"
          />
          <Label
            htmlFor="all-agree"
            className="text-base font-bold text-[#5A5880] cursor-pointer select-none"
          >
            위의 모든 필수 약관을 확인하였으며, 이에 모두 동의합니다.
          </Label>
        </div>
      </div>

      <Button
        onClick={onNext}
        className={cn(
          "w-full h-14 text-lg font-bold rounded-xl transition-all",
          isAllAgreed
            ? "bg-[#9593D9] hover:bg-[#8381c9] text-white shadow-md shadow-[#9593D9]/20"
            : "bg-gray-300 text-gray-500 cursor-not-allowed",
        )}
      >
        다음으로 넘어가기
      </Button>
    </div>
  );
}
