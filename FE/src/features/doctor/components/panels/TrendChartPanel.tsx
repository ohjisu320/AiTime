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

const labels = ["24-03", "24-06", "24-09", "24-12", "25-03"];

const options = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      labels: { boxWidth: 8, font: { size: 8 } },
    },
  },
  scales: {
    x: { ticks: { font: { size: 8 } } },
    y: { beginAtZero: true, max: 100, ticks: { font: { size: 8 } } },
  },
};

const data = {
  labels,
  datasets: [
    {
      label: "성공률",
      data: [30, 45, 40, 60, 75],
      borderColor: "#ff0000",
      borderWidth: 1.5,
      pointRadius: 2,
    },
    {
      label: "음성",
      data: [20, 30, 35, 50, 65],
      borderColor: "#008000",
      borderWidth: 1.5,
      pointRadius: 2,
    },
    {
      label: "행동",
      data: [15, 25, 45, 40, 55],
      borderColor: "#0000ff",
      borderWidth: 1.5,
      pointRadius: 2,
    },
  ],
};

export default function TrendChartPanel() {
  const charts = [
    { id: 1, title: "01. 동작모방" },
    { id: 2, title: "02. 발화모방" },
    { id: 3, title: "03. 대면 호명반응" },
    { id: 4, title: "04. 비대면 호명반응" },
  ];

  return (
    // [수정 포인트 1] 전체 패널에 스크롤 적용 (overflow-y-auto)
    <div className="flex flex-col gap-[2px] h-full overflow-y-auto custom-scrollbar">
      {charts.map((chart) => (
        <WindowsContainer
          key={chart.id}
          // [수정 포인트 2] 각 차트의 높이를 고정(h-[240px])하고 줄어들지 않게(shrink-0) 설정
          // flex-1 제거 -> 억지로 늘어나거나 줄어들지 않음
          className="h-[240px] shrink-0 flex flex-col"
        >
          <div className="text-[10px] font-bold bg-[#e2e2e2] px-1 mb-1 border-b border-[#999] shrink-0">
            {chart.title}
          </div>
          <div className="flex-1 bg-white relative min-h-0">
            <Line options={options} data={data} />
          </div>
        </WindowsContainer>
      ))}
    </div>
  );
}
