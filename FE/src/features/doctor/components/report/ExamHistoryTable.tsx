import { FileText } from "lucide-react";
import { Button } from "@/components/ui/button";

// Mock Data
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
  return (
    // [수정 1] h-full 제거: 부모 높이를 꽉 채우지 않고 내용물 크기만큼만 차지하게 함
    <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 flex flex-col">
      {/* 섹션 헤더 */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-purple-50 rounded-lg">
          <FileText className="w-6 h-6 text-[#5A55D6]" />
        </div>
        <h3 className="text-2xl font-bold text-gray-800">전체 검사 이력</h3>
      </div>

      {/* 테이블 영역 컨테이너 */}
      {/* [수정 2] flex-1 제거: 불필요한 늘어남 방지 */}
      <div className="flex flex-col border border-gray-200 rounded-xl overflow-hidden">
        {/* 1. 테이블 헤더 (고정) */}
        <div className="grid grid-cols-6 gap-6 py-4 bg-gray-50 text-sm font-bold text-gray-500 text-center uppercase tracking-wider border-b border-gray-200">
          <div>검사 일자</div>
          <div>동작모방</div>
          <div>발화모방</div>
          <div>비대면 호명반응</div>
          <div>대면 호명 반응</div>
          <div>상세보기</div>
        </div>

        {/* 2. 테이블 바디 (스크롤 적용 영역 - h-[400px] 고정) */}
        <div className="divide-y divide-gray-100 overflow-y-auto h-[400px] bg-white custom-scrollbar">
          {HISTORY_DATA.map((item) => (
            <div
              key={item.examId}
              className="grid grid-cols-6 gap-6 py-5 text-base text-center items-center hover:bg-gray-50 transition-colors"
            >
              <div className="font-bold text-gray-900">{item.date}</div>

              {/* 기본 회색 텍스트로 통일 */}
              <div className="text-gray-600">{item.scores.TASK1}/5</div>
              <div className="text-gray-600">{item.scores.TASK2}/5</div>
              <div className="text-gray-600">{item.scores.TASK3}/5</div>
              <div className="text-gray-600">{item.scores.TASK4}/5</div>

              <div className="flex justify-center">
                <Button
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
