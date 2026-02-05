import { SectionHeader } from "../layout/WindowsLayout";
import type { ExamVideoListItem } from "@/api/types/examReport.types";

interface Props {
  examVideoList: ExamVideoListItem[];
  onSelectVideo: (videoId: string) => void;
  // 현재 재생중인 비디오의 examId를 알면 하이라이팅 가능 (선택 사항)
  currentVideoExamId?: string;
}

export default function SessionListPanel({ examVideoList, onSelectVideo, currentVideoExamId }: Props) {
  return (
    <div className="p-2 h-full bg-white border border-[#808080] font-['Gulim'] overflow-y-auto">
      <SectionHeader title="세션별 영상 목록" />
      <div className="flex flex-col gap-4 mt-2 px-1">
        {examVideoList.map((exam) => (
          <details
            key={exam.examId}
            className="cursor-pointer group"
            // 최신 검사이거나 현재 비디오가 속한 검사면 펼쳐두기
            open={exam.examId === currentVideoExamId || examVideoList[0].examId === exam.examId}
          >
            <summary className="font-bold text-[12px] select-none text-black group-hover:text-blue-900">
              ▣ {exam.examDate} <span className="text-[10px] font-normal">({exam.examStatus})</span>
            </summary>
            <div className="pl-4 mt-2 flex flex-col gap-1.5 text-[11px] text-blue-800 underline">
              {exam.videos.length > 0 ? (
                exam.videos.map((video) => (
                  <span
                    key={video.videoId}
                    onClick={() => onSelectVideo(video.videoId)}
                    className="cursor-pointer hover:font-bold hover:text-red-600"
                  >
                    ▷ {video.videoType}
                  </span>
                ))
              ) : (
                <span className="text-gray-400 no-underline">영상 없음</span>
              )}
            </div>
          </details>
        ))}
        {examVideoList.length === 0 && (
          <div className="text-center text-gray-500 mt-10">검사 이력이 없습니다.</div>
        )}
      </div>
    </div>
  );
}