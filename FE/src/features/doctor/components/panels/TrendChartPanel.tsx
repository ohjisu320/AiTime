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

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

interface Props {
  adosGraphs: AdosGraphs | null;
}

const GRAPH_CONFIGS = [
  { key: 'graph1', title: "사회적 정동 (Social Affect)" },
  { key: 'graph2', title: "제한/반복 행동 (RRB)" },
  { key: 'graph3', title: "의사소통 (Communication)" },
  { key: 'graph4', title: "상호작용 (Interaction)" },
] as const;

export default function TrendChartPanel({ adosGraphs }: Props) {
  const hasData = adosGraphs && adosGraphs.xAxis && adosGraphs.xAxis.length > 0;

  return (
    <div className="flex flex-col gap-[3px] h-full overflow-y-auto custom-scrollbar bg-[#f0f0f0] p-[2px]">
      {!hasData ? (
        <div className="flex items-center justify-center h-full text-gray-500 font-['Gulim'] text-[13px]">
          표시할 그래프 데이터가 없습니다.
        </div>
      ) : (
        GRAPH_CONFIGS.map((config) => {
          const graphData = adosGraphs?.graphs?.[config.key];
          if (!graphData) return null;

          const chartData = {
            labels: adosGraphs!.xAxis,
            datasets: Object.entries(graphData.series).map(([label, data], idx) => ({
              label: label.toUpperCase(),
              data: data as number[],
              borderColor: `hsl(${idx * 60 + 200}, 70%, 45%)`,
              backgroundColor: `hsl(${idx * 60 + 200}, 70%, 45%)`,
              tension: 0.1,
              pointRadius: 4, // 포인트 크기 증가
              pointHoverRadius: 6,
              borderWidth: 2,
            })),
          };

          return (
            <div key={config.key} className="h-[220px] bg-white border border-[#808080] p-1 flex flex-col shrink-0">
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
                        suggestedMax: 3,
                        ticks: {
                          stepSize: 1,
                          // [수정] 차트 폰트 12px로 증가
                          font: { family: "'Gulim', sans-serif", size: 12 }
                        },
                        grid: { color: '#f0f0f0' }
                      },
                      x: {
                        ticks: {
                          // [수정] 차트 폰트 12px로 증가
                          font: { family: "'Gulim', sans-serif", size: 12 }
                        },
                        grid: { display: false }
                      }
                    },
                    plugins: {
                      legend: {
                        position: 'right',
                        labels: {
                          boxWidth: 12,
                          font: { size: 12, family: "'Gulim', sans-serif" },
                          padding: 10
                        }
                      },
                      tooltip: {
                        titleFont: { family: "'Gulim', sans-serif", size: 12 },
                        bodyFont: { family: "'Gulim', sans-serif", size: 12 },
                        padding: 10,
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