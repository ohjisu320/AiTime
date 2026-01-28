import { PieChart } from "lucide-react";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

const CURRENT_BALANCE_DATA = [
  { subject: "동작모방", A: 80, fullMark: 100 },
  { subject: "발화모방", A: 40, fullMark: 100 },
  { subject: "비대면 호명", A: 60, fullMark: 100 }, // 이름 줄임
  { subject: "대면 호명", A: 90, fullMark: 100 },
];

export default function BalanceChartSection() {
  return (
    <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 h-full flex flex-col">
      <div className="flex items-center gap-3 mb-8">
        <div className="p-2 bg-purple-50 rounded-lg">
          <PieChart className="w-6 h-6 text-[#5A55D6]" />
        </div>
        <h3 className="text-2xl font-bold text-gray-800">
          최근 검사 영역 비교
        </h3>
      </div>

      <div className="flex-1 w-full min-h-[450px] flex justify-center items-center">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart
            cx="50%"
            cy="50%"
            outerRadius="75%"
            data={CURRENT_BALANCE_DATA}
          >
            <PolarGrid stroke="#E5E7EB" />
            <PolarAngleAxis
              dataKey="subject"
              tick={{ fill: "#4B5563", fontSize: 16, fontWeight: "bold" }}
            />
            <PolarRadiusAxis
              angle={30}
              domain={[0, 100]}
              tick={false}
              axisLine={false}
            />
            <Radar
              name="점수"
              dataKey="A"
              stroke="#5A55D6"
              strokeWidth={3}
              fill="#5A55D6"
              fillOpacity={0.4}
            />
            <Tooltip
              contentStyle={{
                borderRadius: "12px",
                border: "none",
                boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
              }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      <div className="text-center text-base text-gray-500 bg-gray-50 py-4 rounded-xl mt-4">
        * <span className="font-bold text-[#5A55D6]">발화모방</span> 영역이 타영역
        대비 낮게 측정되었습니다.
      </div>
    </section>
  );
}
