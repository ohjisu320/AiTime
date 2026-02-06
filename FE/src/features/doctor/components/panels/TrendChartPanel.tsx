// src/features/doctor/components/panels/TrendChartPanel.tsx
import { Line } from "react-chartjs-2";
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
import { SectionHeader } from "../layout/WindowsLayout";
import type { AdosGraphs } from "@/api/types/examReport.types";

// Chart.js 모듈 등록
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

interface Props {
  adosGraphs: AdosGraphs | null;
}

// 그래프 설정 (API 응답 키와 제목 매핑)
const GRAPH_CONFIGS = [
  { key: 'graph1', title: "사회적 정동 (Social Affect)" },
  { key: 'graph2', title: "제한/반복 행동 (RRB)" },
  { key: 'graph3', title: "의사소통 (Communication)" },
  { key: 'graph4', title: "상호작용 (Interaction)" },
] as const;

export default function TrendChartPanel({ adosGraphs }: Props) {
  // 데이터 유효성 검사 (데이터가 없거나 X축 날짜 정보가 없는 경우)
  const hasData = adosGraphs && adosGraphs.xAxis && adosGraphs.xAxis.length > 0;

  return (
    <div className="flex flex-col gap-[3px] h-full overflow-y-auto custom-scrollbar bg-[#f0f0f0] p-[2px]">
      {!hasData ? (
        <div className="flex items-center justify-center h-full text-gray-500 font-['Gulim'] text-[12px]">
          표시할 그래프 데이터가 없습니다.
        </div>
      ) : (
        GRAPH_CONFIGS.map((config) => {
          // 해당 그래프 데이터 추출 (API 응답 구조: graphs.graph1.series...)
          // adosGraphs가 null이 아님을 hasData로 확인했으나, graphs 내부 키 접근 시 안전하게 처리
          const graphData = adosGraphs?.graphs?.[config.key];

          if (!graphData) return null;

          const chartData = {
            labels: adosGraphs!.xAxis, // hasData 체크로 인해 null 아님 보장
            datasets: Object.entries(graphData.series).map(([label, data], idx) => ({
              label: label.toUpperCase(), // a2, b6 등을 대문자로 변환
              data: data,
              borderColor: `hsl(${idx * 60 + 200}, 70%, 45%)`, // 색상 자동 생성 (가시성 좋은 톤)
              backgroundColor: `hsl(${idx * 60 + 200}, 70%, 45%)`,
              tension: 0.1, // 직선에 가깝게
              pointRadius: 3,
              pointHoverRadius: 5,
              borderWidth: 2,
            })),
          };

          return (
            <div key={config.key} className="h-[200px] bg-white border border-[#808080] p-1 flex flex-col shrink-0">
              <SectionHeader title={config.title} />
              <div className="flex-1 min-h-0 w-full relative pt-2">
                <Line
                  data={chartData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                      y: {
                        beginAtZero: true,
                        suggestedMax: 3, // ADOS 점수는 보통 낮으므로 3까지 보여줌
                        ticks: {
                          stepSize: 1,
                          font: { family: "'Gulim', sans-serif", size: 10 }
                        },
                        grid: { color: '#f0f0f0' }
                      },
                      x: {
                        ticks: {
                          font: { family: "'Gulim', sans-serif", size: 10 }
                        },
                        grid: { display: false }
                      }
                    },
                    plugins: {
                      legend: {
                        position: 'right',
                        labels: {
                          boxWidth: 10,
                          font: { size: 10, family: "'Gulim', sans-serif" },
                          padding: 10
                        }
                      },
                      tooltip: {
                        titleFont: { family: "'Gulim', sans-serif" },
                        bodyFont: { family: "'Gulim', sans-serif" },
                        padding: 8,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)'
                      }
                    }
                  }}
                />
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}