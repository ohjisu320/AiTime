import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/common/Button';
import ConsentHeader from '../components/ConsentHeader';
import EnvironmentCard from '../components/EnvironmentCard';
import ChecklistItem from '../components/ChecklistItem';

const ExamGuidePage = () => {
  const navigate = useNavigate();

  // 체크리스트 상태 관리
  const [checks, setChecks] = useState({
    landscape: false,
    natural: false,
    noise: false,
    internet: false,
    battery: false,
  });

  const allChecked = Object.values(checks).every(Boolean);

  const handleToggle = (key: keyof typeof checks) => {
    setChecks(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="flex flex-col items-center w-full">
      {/* 🚦 Step 1 완료(체크표시), Step 2 활성화 상태의 헤더 */}
      <ConsentHeader
        currentStep={2}
        totalSteps={3}
        onBack={() => navigate('/exam/consent')}
      />

      <main className="w-full max-w-[1187px] mt-10 mb-20 px-4 flex flex-col items-center">
        {/* 헤더 섹션 */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-800 mb-3">촬영 환경 준비</h1>
          <p className="text-xl text-gray-600">정확한 검사를 위해 아래 환경을 준비해주세요</p>
        </div>

        {/* 환경 안내 카드 섹션 */}
        <div className="flex gap-8 mb-12">
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

        {/* 체크리스트 섹션 */}
        <div className="w-full max-w-[1024px] bg-white rounded-2xl shadow-lg p-10 flex flex-col gap-6 mb-10">
          <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
            📋 체크리스트
          </h2>
          <div className="flex flex-col gap-3">
            <ChecklistItem
              label="태블릿을 가로 모드로 고정했나요?"
              isChecked={checks.landscape}
              onToggle={() => handleToggle('landscape')}
            />
            <ChecklistItem
              label="아이가 편안하고 자연스러운 상태인가요?"
              isChecked={checks.natural}
              onToggle={() => handleToggle('natural')}
            />
            <ChecklistItem
              label="주변의 소음이 심하지 않은 상태인가요?"
              isChecked={checks.noise}
              onToggle={() => handleToggle('noise')}
            />
            <ChecklistItem
              label="인터넷 연결이 안정적인가요?"
              isChecked={checks.internet}
              onToggle={() => handleToggle('internet')}
            />
            <ChecklistItem
              label="충분한 배터리 또는 충전기를 준비했나요?"
              isChecked={checks.battery}
              onToggle={() => handleToggle('battery')}
            />
          </div>
        </div>

        {/* 준비 완료 버튼 */}
        <Button
          disabled={!allChecked}
          variant={allChecked ? "default" : "secondary"}
          className="w-full max-w-[1024px] h-16 text-lg font-bold rounded-2xl transition-all"
          onClick={() => navigate('/exam/mission')}
        >
          준비 완료, 미션 선택하기
        </Button>
      </main>

      <footer className="mt-auto mb-8 text-gray-500 text-sm">
        AiTime은 12~23개월 무발화 영유아의 자폐 스펙트럼(ASD) 조기 진단을 보조합니다
      </footer>
    </div>
  );
};

export default ExamGuidePage;