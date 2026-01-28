import { useNavigate, useParams } from "react-router-dom";
import { FileText } from "lucide-react";
import { Button } from "@/components/ui/button";

// ----------------------------------------------------------------------
// [Mock Data]
// API 명세상 ExamHistoryItem은 { examId, completedAt, status }만 포함하지만,
// 화면(Table)에는 각 과제별 점수를 표시해야 하므로 Mock 데이터를 확장하여 사용합니다.
// 실제 연동 시에는 별도 API로 점수를 조회하거나, 백엔드에 필드 추가 요청이 필요할 수 있습니다.
// ----------------------------------------------------------------------
const HISTORY_DATA = [
  {
    examId: "e6",
    date: "2026.01.19",
    scores: { TASK1: 4, TASK2: 2, TASK3: 3, TASK4: 5 },
  },
  {
    examId: "e5",
    date: "2025.12.15",
    scores: { TASK1: 3, TASK2: 2, TASK3: 3, TASK4: 4 },
  },
  {
    examId: "e4",
    date: "2025.11.30",
    scores: { TASK1: 3, TASK2: 2, TASK3: 2, TASK4: 3 },
  },
  {
    examId: "e3",
    date: "2025.11.15",
    scores: { TASK1: 2, TASK2: 1, TASK3: 2, TASK4: 3 },
  },
  {
    examId: "e2",
    date: "2025.10.30",
    scores: { TASK1: 2, TASK2: 2, TASK3: 2, TASK4: 2 },
  },
  {
    examId: "e1",
    date: "2025.10.15",
    scores: { TASK1: 1, TASK2: 1, TASK3: 1, TASK4: 2 },
  },
  {
    examId: "e0",
    date: "2025.09.30",
    scores: { TASK1: 2, TASK2: 2, TASK3: 2, TASK4: 2 },
  },
];

export default function ExamHistoryTable() {
  const navigate = useNavigate();

  // URL 파라미터에서 현재 환자 ID(hospitalChildrenId)를 가져옵니다.
  // 라우터 설정에 따라 변수명(id 또는 childId 등)을 맞춰주세요.
  const { id } = useParams<{ id: string }>();
  // const childId = id || "test-uuid"; // 테스트용 Fallback

  // [이동 핸들러] 상세 영상 페이지로 이동
  const handleGoToVideo = (date: string) => {
    // 날짜 포맷 표준화 (YYYY.MM.DD -> YYYY-MM-DD) API Query 포맷 준수
    const formattedDate = date.replace(/\./g, "-");

    // 쿼리 파라미터로 선택된 날짜와 기본 과제(TASK1)를 전달합니다.
    navigate(`/doctor/report/${id}/videos?task=TASK1&date=${formattedDate}`);
  };

  return (
    <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 flex flex-col flex-1 min-h-0">
      {/* 섹션 헤더 */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-purple-50 rounded-lg">
          <FileText className="w-6 h-6 text-[#5A55D6]" />
        </div>
        <h3 className="text-2xl font-bold text-gray-800">전체 검사 이력</h3>
      </div>

      {/* 테이블 영역 (헤더 고정 + 바디 스크롤) */}
      <div className="flex flex-col border border-gray-200 rounded-xl overflow-hidden h-full">
        {/* 1. 테이블 헤더 (Sticky) */}
        <div className="grid grid-cols-6 gap-6 py-4 bg-gray-50 text-sm font-bold text-gray-500 text-center uppercase tracking-wider border-b border-gray-200 sticky top-0 z-10">
          <div>검사 일자</div>
          <div>동작모방</div>
          <div>발화모방</div>
          <div>비대면 호명반응</div>
          <div>대면 호명 반응</div>
          <div>상세보기</div>
        </div>

        {/* 2. 테이블 바디 (Scrollable) */}
        {/* h-[400px]: 높이 고정 (화면 설계에 따라 조절 가능) */}
        <div className="divide-y divide-gray-100 overflow-y-auto bg-white custom-scrollbar h-[400px]">
          {HISTORY_DATA.map((item) => (
            <div
              key={item.examId}
              className="grid grid-cols-6 gap-6 py-5 text-base text-center items-center hover:bg-gray-50 transition-colors"
            >
              <div className="font-bold text-gray-900">{item.date}</div>

              {/* 점수 데이터 (회색 텍스트 통일) */}
              <div className="text-gray-600">{item.scores.TASK1}/5</div>
              <div className="text-gray-600">{item.scores.TASK2}/5</div>
              <div className="text-gray-600">{item.scores.TASK3}/5</div>
              <div className="text-gray-600">{item.scores.TASK4}/5</div>

              <div className="flex justify-center">
                <Button
                  onClick={() => handleGoToVideo(item.date)} // 페이지 이동 함수 호출
                  variant="outline"
                  size="sm"
                  className="h-9 px-5 text-xs font-bold text-gray-500 border-gray-300 hover:text-[#5A55D6] hover:border-[#5A55D6] hover:bg-purple-50 rounded-lg"
                >
                  결과 보기
                </Button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
