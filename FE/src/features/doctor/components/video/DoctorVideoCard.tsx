import {
  Activity,
  Calendar,
  CheckCircle,
  Clock,
  Eye,
  VideoOff,
} from "lucide-react";
import type { TaskVideoItem } from "./doctorVideoData"; // [수정] TASK_TABS, VideoType 제거

interface DoctorVideoCardProps {
  item: TaskVideoItem;
  // activeTask: VideoType; // [삭제] 사용하지 않음
  isActive: boolean;
}

// [수정] activeTask 제거
export default function DoctorVideoCard({
  item,
  isActive,
}: DoctorVideoCardProps) {
  return (
    <div className="w-full max-w-[1200px] h-full bg-white rounded-[40px] shadow-2xl overflow-hidden flex flex-col border border-gray-200">
      {/* 1. Video Player Area */}
      <div className="flex-1 bg-black relative flex items-center justify-center group">
        {/* Date Overlay */}
        <div className="absolute top-8 left-8 z-10 bg-black/60 text-white px-6 py-3 rounded-full text-base font-bold backdrop-blur-md flex items-center gap-3 shadow-lg">
          <Calendar className="w-5 h-5 text-[#9FA9FF]" />
          {item.examDate}
        </div>

        {/* Player */}
        {item.status === "UPLOADED" && item.videoUrl ? (
          <video
            src={item.videoUrl}
            className="w-full h-full object-contain"
            controls
            autoPlay={isActive}
            muted={!isActive}
          />
        ) : (
          <div className="flex flex-col items-center justify-center text-gray-500 gap-6">
            <div className="w-24 h-24 rounded-full bg-gray-800 flex items-center justify-center">
              <VideoOff className="w-10 h-10 text-gray-500" />
            </div>
            <p className="text-2xl font-bold text-gray-400">
              {item.status === "ANALYZING"
                ? "현재 AI 분석 중입니다."
                : "재생할 수 없는 영상입니다."}
            </p>
          </div>
        )}
      </div>

      {/* 2. Bottom Info Bar */}
      <div className="h-[120px] bg-white border-t border-gray-100 flex items-center justify-between px-10 flex-shrink-0">
        <div className="flex items-center gap-12">
          <MetricItem
            icon={<Clock className="w-5 h-5 text-[#5A55D6]" />}
            label="Response Time"
            value={item.analysisResult?.responseTime}
          />
          <div className="w-px h-12 bg-gray-200" />
          <MetricItem
            icon={<Eye className="w-5 h-5 text-[#5A55D6]" />}
            label="Eye Contact"
            value={item.analysisResult?.eyeContact}
          />
          <div className="w-px h-12 bg-gray-200" />
          <MetricItem
            icon={<CheckCircle className="w-5 h-5 text-[#5A55D6]" />}
            label="Success Rate"
            value={item.analysisResult?.successRate}
          />
        </div>

        <div className="flex items-center gap-4 bg-[#F8F9FC] px-8 py-4 rounded-2xl border border-gray-100">
          <Activity className="w-6 h-6 text-[#5A55D6]" />
          <span className="text-lg font-bold text-gray-600">종합 점수</span>
          <span className="text-3xl font-black text-[#5A55D6] translate-y-[-2px]">
            {item.analysisResult?.score || "-"}
          </span>
        </div>
      </div>
    </div>
  );
}

// Sub Component
function MetricItem({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value?: string;
}) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs text-gray-400 font-bold uppercase tracking-wide">
        {label}
      </span>
      <div className="flex items-center gap-3">
        {icon}
        <span className="text-2xl font-bold text-gray-900">{value || "-"}</span>
      </div>
    </div>
  );
}
