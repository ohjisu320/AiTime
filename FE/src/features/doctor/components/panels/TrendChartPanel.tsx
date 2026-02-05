import { useMemo } from "react";
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
import type { AdosGraphs } from "@/api/types/examReport.types";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
);

// Props 인터페이스
interface Props {
  adosGraphs?: AdosGraphs | null;
}

// 컬러 팔레트: 파란색, 빨간색, 검정색, 주황색
const COLORS = ["#0066CC", "#CC0000", "#333333", "#FF6600"];

// ADOS 항목 이름 매핑 (소문자 키 지원)
const ADOS_LABELS: Record<string, string> = {
  a3: "A3 음성·언어 억양",
  a8: "A8 제스처",
  b1: "B1 유별난 눈맞춤",
  b4: "B4 얼굴 표정",
  b6: "B6 공유된 즐거움",
  b7: "B7 이름 반응",
  b18: "B18 라포의 질",
  // 대문자 키도 지원 (기존 호환)
  A3: "A3 음성·언어 억양",
  A8: "A8 제스처",
  B1: "B1 유별난 눈맞춤",
  B4: "B4 얼굴 표정",
  B6: "B6 공유된 즐거움",
  B7: "B7 이름 반응",
  B18: "B18 라포의 질",
};

// 그래프 ID와 API graph 키 매핑
const GRAPH_KEY_MAP: Record<string, keyof AdosGraphs["graphs"]> = {
  pose_imitation: "graph1",
  speech_imitation: "graph2",
  name_facing: "graph3",
  name_non_facing: "graph4",
};

// Mock 데이터 (API 연결 전 폴백용)
const MOCK_TREND_DATA = {
  labels: ["2024.03", "2024.06", "2024.09", "2024.12", "2025.03"],
  pose_imitation: {
    b6: [1, 1, 0, 1, 0],
    a8: [2, 2, 1, 1, 0],
    b18: [1, 1, 1, 0, 0],
  },
  speech_imitation: {
    a3: [3, 2, 2, 1, 1],
    b18: [1, 1, 1, 0, 0],
  },
  name_facing: {
    b1: [3, 2, 2, 1, 1],
    b4: [2, 2, 1, 1, 0],
    b6: [1, 1, 0, 0, 0],
    b18: [1, 1, 1, 0, 0],
  },
  name_non_facing: {
    b7: [3, 2, 2, 1, 1],
    b18: [1, 1, 0, 0, 0],
  },
};

const CHART_TYPES = [
  { id: "pose_imitation", title: "01. 동작모방 (Pose Imitation)", maxY: 3 },
  { id: "speech_imitation", title: "02. 발화모방 (Speech Imitation)", maxY: 3 },
  { id: "name_facing", title: "03. 대면 호명반응 (Name Facing)", maxY: 3 },
  { id: "name_non_facing", title: "04. 비대면 호명반응 (Name Non-Facing)", maxY: 3 },
];

export default function TrendChartPanel({ adosGraphs }: Props) {
  // API 데이터 또는 Mock 데이터 사용 판단
  const useApiData = useMemo(() => {
    return adosGraphs && adosGraphs.xAxis && adosGraphs.xAxis.length > 0;
  }, [adosGraphs]);

  // 날짜 라벨 포맷팅 (YYYY-MM-DD → YYYY.MM)
  const formatDateLabel = (dateStr: string): string => {
    if (!dateStr) return "";
    const parts = dateStr.split("-");
    if (parts.length >= 2) {
      return `${parts[0]}.${parts[1]}`;
    }
    return dateStr;
  };

  const getChartData = (chartId: string) => {
    const POINT_STYLES = ['circle', 'rect', 'triangle', 'rectRot'];

    if (useApiData && adosGraphs) {
      // API 데이터 사용
      const graphKey = GRAPH_KEY_MAP[chartId];
      const graphData = adosGraphs.graphs[graphKey];

      if (!graphData || !graphData.series) {
        return { labels: [], datasets: [] };
      }

      const labels = adosGraphs.xAxis.map(formatDateLabel);
      const seriesKeys = Object.keys(graphData.series);

      const datasets = seriesKeys.map((metricKey, index) => ({
        label: ADOS_LABELS[metricKey] || metricKey.toUpperCase(),
        data: graphData.series[metricKey] || [],
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

      return { labels, datasets };
    } else {
      // Mock 데이터 사용 (폴백)
      const rawData = MOCK_TREND_DATA[chartId as keyof typeof MOCK_TREND_DATA];

      if (typeof rawData === 'object' && !Array.isArray(rawData)) {
        const seriesKeys = Object.keys(rawData);

        const datasets = seriesKeys.map((metricKey, index) => ({
          label: ADOS_LABELS[metricKey] || metricKey.toUpperCase(),
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
    }
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
      {/* API 데이터 사용 여부 표시 (개발용) */}
      {!useApiData && (
        <div className="text-[10px] text-orange-600 bg-orange-50 px-2 py-1 border border-orange-200">
          ⚠️ Mock 데이터 사용 중 (API 연결 대기)
        </div>
      )}

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
