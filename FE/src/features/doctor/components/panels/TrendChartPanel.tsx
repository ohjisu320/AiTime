import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { WindowsContainer } from "../layout/WindowsLayout";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
);

// 컬러 팔레트: 파란색, 빨간색, 검정색, 주황색
const COLORS = ["#0066CC", "#CC0000", "#333333", "#FF6600"];

// ADOS 항목 이름 매핑
const ADOS_LABELS: Record<string, string> = {
  A3: "A3 음성·언어 억양",
  A8: "A8 제스처",
  B1: "B1 유별난 눈맞춤",
  B4: "B4 얼굴 표정",
  B6: "B6 공유된 즐거움",
  B7: "B7 이름 반응",
  B18: "B18 라포의 질",
};

// 더미 데이터 - API 연결 시 교체
const MOCK_TREND_DATA = {
  labels: ["2024.03", "2024.06", "2024.09", "2024.12", "2025.03"],

  pose_imitation: {
    B6: [1, 1, 0, 1, 0],
    A8: [2, 2, 1, 1, 0],
    B18: [1, 1, 1, 0, 0],
  },
  speech_imitation: {
    A3: [3, 2, 2, 1, 1],
    B18: [1, 1, 1, 0, 0],
  },
  name_facing: {
    B1: [3, 2, 2, 1, 1],
    B4: [2, 2, 1, 1, 0],
    B6: [1, 1, 0, 0, 0],
    B18: [1, 1, 1, 0, 0],
  },
  name_non_facing: {
    B7: [3, 2, 2, 1, 1],
    B18: [1, 1, 0, 0, 0],
  },
};

const METRIC_CONFIG = {
  pose_imitation: ["B6", "A8", "B18"],
  speech_imitation: ["A3", "B18"],
  name_facing: ["B1", "B4", "B6", "B18"],
  name_non_facing: ["B7", "B18"],
};

const CHART_TYPES = [
  { id: "pose_imitation", title: "01. 동작모방 (Pose Imitation)", maxY: 3 },
  { id: "speech_imitation", title: "02. 발화모방 (Speech Imitation)", maxY: 3 },
  { id: "name_facing", title: "03. 대면 호명반응 (Name Facing)", maxY: 3 },
  { id: "name_non_facing", title: "04. 비대면 호명반응 (Name Non-Facing)", maxY: 3 },
];

export default function TrendChartPanel() {
  const getChartData = (chartId: string) => {
    const metrics = METRIC_CONFIG[chartId as keyof typeof METRIC_CONFIG];
    const rawData = MOCK_TREND_DATA[chartId as keyof typeof MOCK_TREND_DATA];

    if (typeof rawData === 'object' && !Array.isArray(rawData)) {
      // 마커 스타일: 원, 사각형, 삼각형, 다이아몬드
      const POINT_STYLES = ['circle', 'rect', 'triangle', 'rectRot'];

      const datasets = metrics.map((metricKey, index) => ({
        label: ADOS_LABELS[metricKey] || metricKey,
        data: (rawData as Record<string, number[]>)[metricKey] || [],
        borderColor: COLORS[index % COLORS.length],
        backgroundColor: COLORS[index % COLORS.length],
        borderWidth: 2,
        pointRadius: 6,
        pointHoverRadius: 8,
        pointStyle: POINT_STYLES[index % POINT_STYLES.length],
        pointBackgroundColor: COLORS[index % COLORS.length],
        pointBorderColor: "#FFFFFF",
        pointBorderWidth: 2,
        tension: 0,
        fill: false,
      }));

      return {
        labels: MOCK_TREND_DATA.labels,
        datasets,
      };
    }
    return { labels: [], datasets: [] };
  };

  const getChartOptions = (maxY: number) => ({
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: "index" as const,
      intersect: false,
    },
    plugins: {
      legend: {
        display: true,
        position: "bottom" as const,
        labels: {
          boxWidth: 14,
          boxHeight: 2,
          font: { size: 10, family: "Gulim" },
          color: "#333",
          padding: 8,
          usePointStyle: false,
        },
      },
      tooltip: {
        backgroundColor: "rgba(255,255,255,0.95)",
        titleColor: "#333",
        bodyColor: "#333",
        borderColor: "#ccc",
        borderWidth: 1,
        padding: 10,
        titleFont: { size: 11, weight: "bold" as const },
        bodyFont: { size: 10 },
        displayColors: true,
        callbacks: {
          label: (context: any) => {
            return `${context.dataset.label}: ${context.parsed.y}점`;
          },
        },
      },
    },
    scales: {
      x: {
        ticks: { font: { size: 10 }, color: "#333" },
        grid: { color: "#e8e8e8", lineWidth: 1 },
        border: { color: "#999" },
      },
      y: {
        beginAtZero: true,
        max: maxY,
        ticks: {
          font: { size: 10 },
          color: "#333",
          stepSize: 1,
          callback: (value: number) => `${value}점`,
        },
        grid: { color: "#e8e8e8", lineWidth: 1 },
        border: { color: "#999" },
        title: {
          display: true,
          text: "ADOS 점수",
          font: { size: 10 },
          color: "#666",
        },
      },
    },
  });

  return (
    <div className="flex flex-col gap-[3px] h-full overflow-y-auto custom-scrollbar bg-[#f0f0f0] p-[2px]">
      {CHART_TYPES.map((chart) => (
        <WindowsContainer
          key={chart.id}
          className="h-[280px] shrink-0 flex flex-col"
        >
          <div className="text-[11px] font-bold bg-gradient-to-r from-[#d0d0d0] to-[#e8e8e8] px-2 py-1 border-b border-[#999] shrink-0 flex items-center">
            <span className="text-[#000080]">■</span>
            <span className="ml-1">{chart.title}</span>
          </div>
          <div className="flex-1 bg-white relative min-h-0 p-2">
            <Line options={getChartOptions(chart.maxY) as any} data={getChartData(chart.id)} />
          </div>
        </WindowsContainer>
      ))}
    </div>
  );
}
