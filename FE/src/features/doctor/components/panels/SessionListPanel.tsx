import { SectionHeader } from "../layout/WindowsLayout";
import type { ExamVideoListItem } from "@/api/types/examReport.types";

interface Props {
  examVideoList: ExamVideoListItem[];
  onSelectVideo: (examId: string, videoId: string) => void;
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
            open={exam.examId === currentVideoExamId || examVideoList[0].examId === exam.examId}
          >
            <summary className="font-bold text-[14px] select-none text-black group-hover:text-blue-900 list-none mb-1">
              <span className="inline-block w-4 mr-1 text-center group-open:rotate-90 transition-transform">▶</span>
              ▣ {exam.examDate} <span className="text-[12px] font-normal text-[#666]">({exam.examStatus})</span>
            </summary>

            <div className="pl-6 mt-1 flex flex-col gap-2 text-[13px] border-l-2 border-gray-300 ml-2 py-1">
              {exam.videos.length > 0 ? (
                // Video Sorting: Pose -> Speech -> Facing -> Non-Facing
                exam.videos
                  .sort((a, b) => {
                    const order: Record<string, number> = {
                      "POSE_IMITATION": 1,
                      "SPEECH_IMITATION": 2,
                      "NAME_FACING": 3,
                      "NAME_NON_FACING": 4
                    };
                    return (order[a.videoType] || 99) - (order[b.videoType] || 99);
                  })
                  .map((video) => {
                    let typeLabel: string = video.videoType;
                    if (video.videoType === "POSE_IMITATION") typeLabel = "동작 모방";
                    else if (video.videoType === "SPEECH_IMITATION") typeLabel = "발화 모방";
                    else if (video.videoType === "NAME_FACING") typeLabel = "대면 호명반응";
                    else if (video.videoType === "NAME_NON_FACING") typeLabel = "비대면 호명반응";

                    return (
                      <button
                        key={video.videoId}
                        onClick={() => onSelectVideo(exam.examId, video.videoId)}
                        className="text-left text-blue-800 hover:font-bold hover:text-red-600 hover:bg-blue-50 px-2 py-0.5 rounded cursor-pointer truncate"
                      >
                        ▷ {typeLabel}
                      </button>
                    );
                  })
              ) : (
                <span className="text-gray-400 pl-2">영상 없음</span>
              )}
            </div>
          </details>
        ))}

        {examVideoList.length === 0 && (
          <div className="text-center text-gray-500 mt-10 text-[14px]">
            검사 이력이 없습니다.
          </div>
        )}
      </div>
    </div>
  );
}