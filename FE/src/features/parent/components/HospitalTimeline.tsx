import React from 'react';
import { Hospital as HospitalIcon, Plus, ChevronDown, ChevronUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface Hospital {
  hospitalId: string;
  name: string;
}

interface HospitalTimelineProps {
  hospitals: Hospital[];
  childName: string;
  onAddClick?: () => void;
}

const HospitalTimeline = ({ hospitals, childName, onAddClick }: HospitalTimelineProps) => {
  const [isExpanded, setIsExpanded] = React.useState(false);

  // 데이터가 정말로 있는지 확인하는 조건 (배열 길이가 0보다 커야 함)
  const hasHospitals = hospitals && hospitals.length > 0;

  return (
    <Card className="w-full h-full rounded-3xl shadow-xl border-gray-100 flex flex-col overflow-hidden bg-white transition-all duration-300">
      <CardHeader className="p-8 pb-4">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-indigo-50 rounded-lg">
            <HospitalIcon className="w-5 h-5 text-[#6366F1]" />
          </div>
          <CardTitle className="text-xl font-bold text-gray-800">연결된 병원</CardTitle>
        </div>
      </CardHeader>

      <CardContent className="flex-1 px-8 pb-8 flex flex-col">
        {hasHospitals ? (
          /* 1. 병원 목록이 있을 때: 타임라인 디자인 적용 */
          <div className={`relative flex-1 transition-all duration-500 ease-in-out ${isExpanded ? 'max-h-[1000px]' : 'max-h-[400px] overflow-hidden'}`}>
            <div className="space-y-8 mt-4 pb-4">
              {hospitals.map((h, i) => (
                <div key={h.hospitalId} className="relative flex gap-4">
                  {/* 타임라인 수직 선 */}
                  {i !== hospitals.length - 1 && (
                    <div className="absolute left-[7px] top-5 w-0.5 h-full bg-gray-100" />
                  )}
                  {/* 타임라인 점 */}
                  <div className="relative z-10 w-4 h-4 mt-1.5 rounded-full bg-[#6366F1] border-4 border-white shadow-sm" />
                  {/* 병원 정보 */}
                  <div className="flex flex-col gap-1">
                    <span className="text-xs text-gray-400 font-medium">{childName}의 담당 병원</span>
                    <span className="text-sm font-bold text-gray-700">{h.name}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Gradient Overlay when collapsed */}
            {!isExpanded && (
              <div className="absolute bottom-0 left-0 w-full h-32 bg-gradient-to-t from-white via-white/80 to-transparent pointer-events-none" />
            )}
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-6 bg-gray-50/50 rounded-2xl border-2 border-dashed border-gray-200 my-4">
            <div className="relative mb-6">
              <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center shadow-sm">
                <HospitalIcon className="w-8 h-8 text-gray-300" />
              </div>
              <div className="absolute -right-1 -bottom-1 bg-[#6366F1] text-white rounded-full p-1.5 shadow-md animate-bounce">
                <Plus className="w-4 h-4" />
              </div>
            </div>

            <p className="text-gray-900 font-bold mb-1">연결된 병원이 없어요</p>
            <p className="text-gray-400 text-[11px] leading-relaxed mb-6">
              {childName} 어린이의 검사 결과를 전송받을<br />병원의 초대 코드를 등록해 주세요.
            </p>

            <Button
              variant="outline"
              className="rounded-xl border-indigo-100 text-[#6366F1] font-bold hover:bg-indigo-600 hover:text-white transition-all text-xs px-6"
              onClick={onAddClick}
            >
              초대 코드 등록하기
            </Button>
          </div>
        )}

        {/* 전체 활동 보기 버튼은 항상 하단에 위치 */}
        {hasHospitals && (
          <Button
            variant="ghost"
            className="w-full h-14 mt-auto bg-gray-50 text-gray-500 rounded-2xl font-bold hover:bg-gray-100 transition-colors"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? (
              <>
                접기
                <ChevronUp className="w-4 h-4 ml-1" />
              </>
            ) : (
              <>
                전체 활동 보기
                <ChevronDown className="w-4 h-4 ml-1" />
              </>
            )}
          </Button>
        )}
      </CardContent>
    </Card>
  );
};

export default HospitalTimeline;