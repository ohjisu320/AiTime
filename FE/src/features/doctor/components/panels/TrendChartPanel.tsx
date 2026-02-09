
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

// 발표용 샘플 데이터
const SAMPLE_ADOS_DATA: AdosGraphs = {
  xAxis: ["1차", "2차", "3차", "4차", "5차"],
  graphs: {
    graph1: {
      series: {
        sa: [0.4, 0.8, 1.1, 1.5, 1.8],
        total: [0.6, 0.9, 1.3, 1.6, 1.9],
        peer: [0.5, 0.7, 1.0, 1.2, 1.5]
      }
    },
    graph2: {
      series: {
        rrb: [1.6, 1.4, 1.2, 1.0, 0.8],
        flexibility: [1.3, 1.1, 0.9, 1.0, 0.7],
        total: [1.5, 1.3, 1.1, 1.0, 0.9]
      }
    },
    graph3: {
      series: {
        verbal: [0.9, 1.0, 1.1, 1.0, 0.9],
        nonverbal: [0.6, 0.8, 1.0, 1.4, 1.7],
        total: [0.8, 0.9, 1.1, 1.3, 1.5]
      }
    },
    graph4: {
      series: {
        play: [1.2, 1.0, 1.3, 1.5, 1.8],
        joint: [0.7, 0.9, 0.8, 1.1, 1.0],
        total: [1.0, 1.1, 1.2, 1.4, 1.6]
      }
    }
  }
};

const GRAPH_CONFIGS = [
  { key: 'graph1', title: "사회적 정동 (Social Affect)" },
  { key: 'graph2', title: "제한/반복 행동 (RRB)" },
  { key: 'graph3', title: "의사소통 (Communication)" },
  { key: 'graph4', title: "상호작용 (Interaction)" },
] as const;

export default function TrendChartPanel({ adosGraphs }: Props) {
  const clampValue = (value: number) => Math.max(0, Math.min(2, value));

  const buildPaddedData = (source: AdosGraphs): AdosGraphs => {
    const seriesLengths = Object.values(source.graphs ?? {}).flatMap((graph) =>
      Object.values(graph.series).map((values) => values.length)
    );
    const currentLength = Math.max(source.xAxis.length, ...seriesLengths, 0);
    const targetLength = Math.max(5, currentLength);

    if (currentLength >= 5) return source;

    const prependCount = targetLength - currentLength;

    const padSeries = (values: number[]) => {
      const firstActual = values[0] ?? 1;
      const start = clampValue(firstActual - 0.2 * (prependCount + 1));
      const step = (firstActual - start) / (prependCount + 1);

      const dummies = Array.from({ length: prependCount }, (_, idx) =>
        clampValue(start + step * (idx + 1))
      );

      return [...dummies, ...values];
    };

    const paddedGraphs = GRAPH_CONFIGS.reduce<AdosGraphs['graphs']>((acc, { key }) => {
      const graph = source.graphs?.[key];
      if (!graph) return acc;

      const paddedSeries: Record<string, number[]> = {};
      Object.entries(graph.series).forEach(([label, values]) => {
        paddedSeries[label] = values.length >= targetLength ? values : padSeries(values);
      });

      acc[key] = { series: paddedSeries } as AdosGraphs['graphs'][keyof AdosGraphs['graphs']];
      return acc;
    }, {} as AdosGraphs['graphs']);

    const paddedXAxis = Array.from({ length: targetLength }, (_, idx) => `${idx + 1}차`);

    return {
      xAxis: paddedXAxis,
      graphs: paddedGraphs,
    };
  };

  const hasData = Boolean(adosGraphs?.xAxis?.length && adosGraphs?.graphs);
  const dataSource = hasData && adosGraphs
    ? buildPaddedData(adosGraphs)
    : SAMPLE_ADOS_DATA;

  return (
    <div className="flex flex-col gap-[3px] h-full overflow-y-auto custom-scrollbar bg-[#f0f0f0] p-[2px]">
      {GRAPH_CONFIGS.map((config) => {
        const graphData = dataSource.graphs?.[config.key];
        if (!graphData) return null;

        const chartData = {
          labels: dataSource.xAxis,
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
      })}
    </div>
  );
}