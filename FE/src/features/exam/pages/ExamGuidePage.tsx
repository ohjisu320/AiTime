import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/common/Button';
import ConsentHeader from '@/domains/exam/components/Consent/ConsentHeader';
import EnvironmentCard from '@/domains/exam/components/Guide/EnvironmentCard';

const ExamGuidePage = () => {
  const navigate = useNavigate();

  /* 체크리스트 항목 정의 - 아이콘 및 색상 추가 */
  const checklistItems = [
    { emoji: "📱", text: "태블릿 가로 고정", color: "bg-indigo-50 text-indigo-600" },
    { emoji: "👶", text: "아이 편안한 상태", color: "bg-pink-50 text-pink-600" },
    { emoji: "🔇", text: "주변 소음 제거", color: "bg-gray-100 text-gray-600" },
    { emoji: "🛜", text: "인터넷 연결 확인", color: "bg-blue-50 text-blue-600" },
    { emoji: "🔋", text: "배터리 충전 확인", color: "bg-green-50 text-green-600" }
  ];

  return (
    <div className="w-full min-h-screen flex flex-col overflow-y-auto">
      {/* 🚦 헤더 - ConsentHeader 자체가 이미 fixed */}
      <ConsentHeader
        currentStep={2}
        totalSteps={3}
        onBack={() => navigate('/parent/dashboard')}
        title="촬영 환경 준비"
        subtitle="정확한 검사를 위해 아래 환경을 준비해주세요"
      />

      <div className="flex-1 w-full flex flex-col items-center pt-24"> {/* h-20(80px) + 여유공간 = pt-24(96px) */}
        <main className="w-full max-w-5xl px-4 py-6 flex flex-col items-center gap-6">
          {/* 환경 안내 카드 섹션 - 높이 유동적으로 변경 */}
          <div className="flex gap-4 w-full flex-wrap lg:flex-nowrap justify-center">
            <EnvironmentCard
              emoji="💡"
              title="밝은 조명"
              bgColor="bg-yellow-100"
              description="자연광이나 밝은 실내 조명 아래에서 촬영해주세요. 아이의 얼굴이 선명하게 보여야 합니다."
            />
            <EnvironmentCard
              emoji="🔇"
              title="조용한 공간"
              bgColor="bg-blue-100"
              description="TV, 음악 등 배경 소음을 최소화하고 아이가 집중할 수 있는 조용한 환경을 만들어주세요."
            />
            <EnvironmentCard
              emoji="📏"
              title="적절한 거리"
              bgColor="bg-green-100"
              description="아이와 카메라 사이 약 1m 거리를 유지하고, 아이의 상체가 화면에 잘 보이도록 배치해주세요."
            />
          </div>

          {/* 체크리스트 섹션 - 미니 카드 스타일 */}
          <div className="w-full bg-white/50 rounded-xl flex flex-col gap-3">
            <h2 className="text-sm font-bold text-gray-800 flex items-center gap-2 px-2">
              📋 체크리스트
            </h2>
            <ul className="flex flex-wrap gap-3 justify-center">
              {checklistItems.map((item, index) => (
                <li key={index} className="flex flex-col items-center justify-center gap-2 p-3 bg-white rounded-xl shadow-sm border border-gray-100 w-full md:w-[calc(50%-0.6rem)] lg:w-[calc(33.33%-0.6rem)] grow transition-transform hover:scale-105">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-lg ${item.color}`}>
                    {item.emoji}
                  </div>
                  <span className="text-sm text-gray-700 font-bold text-center">{item.text}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* 준비 완료 버튼 */}
          <Button
            variant="default"
            className="w-full max-w-[600px] h-14 text-base font-bold rounded-xl transition-all bg-brand-purple hover:bg-brand-purple-dark text-white mt-4 mb-10 shadow-lg hover:shadow-xl transform active:scale-95"
            onClick={() => navigate('/exam/mission')}
          >
            준비 완료, 미션 선택하기
          </Button>
        </main>

        <footer className="w-full max-w-5xl px-4 pb-8 text-gray-500 text-xs text-center break-keep">
          AiTime은 12-23개월 영유아와 부모가, 가정 내에서 수행하는 표준화된 4가지 과제를, AI가 채점하여, 소아과 의사의 초기 면담/ 관찰 과정을 대체하는, 디지털 의료기기입니다.
        </footer>
      </div>
    </div>
  );
};

export default ExamGuidePage;