import { useState, useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Calendar } from "lucide-react";

// ✅ 분리된 컴포넌트 및 데이터 Import
// (파일 경로가 정확한지 확인해주세요)
import {
  type TaskVideoItem,
  type VideoType,
  generateMockVideos,
} from "../components/video/doctor-video-data";
import DoctorTaskSidebar from "../components/video/DoctorTaskSidebar";
import DoctorTaskTabs from "../components/video/DoctorTaskTabs";
import DoctorVideoCard from "../components/video/DoctorVideoCard";

export default function DoctorTaskVideoPage() {
  const navigate = useNavigate();
  const location = useLocation();

  // 1. URL Query 파싱
  const searchParams = new URLSearchParams(location.search);
  const initialTask = (searchParams.get("task") as VideoType) || "TASK1";
  const initialDate = searchParams.get("date");

  // 2. State 관리
  const [activeTask, setActiveTask] = useState<VideoType>(initialTask);
  const [videoList, setVideoList] = useState<TaskVideoItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);

  // 3. Refs
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const videoRefs = useRef<(HTMLDivElement | null)[]>([]);

  // 4. Data Fetching (Mock)
  useEffect(() => {
    const data = generateMockVideos(activeTask);
    setVideoList(data);

    // 과제 변경 시 스크롤 최상단 초기화
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = 0;
    }
  }, [activeTask]);

  // 5. Initial Scroll (진입 시 특정 날짜로 이동)
  useEffect(() => {
    if (videoList.length > 0 && initialDate) {
      const targetIndex = videoList.findIndex(
        (v) => v.examDate === initialDate,
      );
      if (targetIndex !== -1 && videoRefs.current[targetIndex]) {
        setTimeout(() => {
          videoRefs.current[targetIndex]?.scrollIntoView({
            behavior: "smooth",
          });
        }, 100);
      }
    }
  }, [videoList, initialDate]);

  // 6. Scroll Observer (현재 보이는 영상 감지)
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const index = Number(entry.target.getAttribute("data-index"));
            setCurrentIndex(index);
          }
        });
      },
      { threshold: 0.6 },
    );

    videoRefs.current.forEach((el) => el && observer.observe(el));
    return () => observer.disconnect();
  }, [videoList]);

  // 7. Event Handlers
  const handleDateClick = (index: number) => {
    videoRefs.current[index]?.scrollIntoView({ behavior: "smooth" });
  };

  const currentData = videoList[currentIndex];

  return (
    <div className="flex h-screen bg-[#F5F6F8] overflow-hidden font-['Pretendard']">
      {/* Left Sidebar */}
      <DoctorTaskSidebar
        videoList={videoList}
        currentIndex={currentIndex}
        onDateClick={handleDateClick}
        onBack={() => navigate(-1)}
      />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative bg-gray-50">
        {/* Top Navigation */}
        <DoctorTaskTabs activeTask={activeTask} onTaskChange={setActiveTask} />

        {/* Floating Date Badge (Center) */}
        {currentData && (
          <div className="absolute top-6 left-6 z-10 bg-black/50 text-white px-4 py-2 rounded-full text-sm font-bold backdrop-blur-md flex items-center gap-2 pointer-events-none">
            <Calendar className="w-4 h-4" />
            {currentData.examDate}
          </div>
        )}

        {/* Video Scroll Container */}
        <div
          ref={scrollContainerRef}
          className="flex-1 overflow-y-auto snap-y snap-mandatory scroll-smooth no-scrollbar relative"
        >
          {videoList.map((item, index) => (
            <div
              key={item.videoId}
              ref={(el) => (videoRefs.current[index] = el)}
              data-index={index}
              className="w-full h-full flex items-center justify-center snap-start snap-always relative p-8"
            >
              <DoctorVideoCard item={item} isActive={index === currentIndex} />
            </div>
          ))}

          {/* Bottom Padding for scroll snap feel */}
          <div className="h-20 w-full snap-start" />
        </div>
      </main>
    </div>
  );
}
