import { useState, useMemo } from "react";
import { Activity } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

// Mock Data
const TASK_TYPES = {
  TASK1: "동작모방",
  TASK2: "발화모방",
  TASK3: "비대면 호명반응",
  TASK4: "대면 호명 반응",
};

const TREND_DATA_SOURCE = [
  { date: "10.15", scores: { TASK1: 45, TASK2: 30, TASK3: 55, TASK4: 60 } },
  { date: "10.30", scores: { TASK1: 52, TASK2: 35, TASK3: 58, TASK4: 62 } },
  { date: "11.15", scores: { TASK1: 48, TASK2: 40, TASK3: 60, TASK4: 65 } },
  { date: "11.30", scores: { TASK1: 60, TASK2: 42, TASK3: 65, TASK4: 70 } },
  { date: "12.15", scores: { TASK1: 65, TASK2: 50, TASK3: 70, TASK4: 75 } },
  { date: "01.19", scores: { TASK1: 72, TASK2: 55, TASK3: 78, TASK4: 85 } },
];

export default function TrendChartSection() {
  const [activeTask, setActiveTask] =
    useState<keyof typeof TASK_TYPES>("TASK1");

  const filteredData = useMemo(() => {
    return TREND_DATA_SOURCE.map((item) => ({
      date: item.date,
      score: item.scores[activeTask],
    }));
  }, [activeTask]);

  return (
    <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 h-full flex flex-col">
      <div className="flex items-center gap-3 mb-8">
        <div className="p-2 bg-purple-50 rounded-lg">
          <Activity className="w-6 h-6 text-[#5A55D6]" />
        </div>
        <h3 className="text-2xl font-bold text-gray-800">
          누적 발달 추이{" "}
          <span className="text-[#5A55D6] ml-1">
            ({TASK_TYPES[activeTask]})
          </span>
        </h3>
      </div>

      {/* 탭 버튼 */}
      <div className="flex gap-3 mb-8 border-b border-gray-100 overflow-x-auto pb-1">
        {Object.entries(TASK_TYPES).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setActiveTask(key as keyof typeof TASK_TYPES)}
            className={`px-5 py-3 font-bold text-base whitespace-nowrap transition-all relative top-[1px] ${
              activeTask === key
                ? "text-[#5A55D6] border-b-2 border-[#5A55D6]"
                : "text-gray-400 hover:text-gray-600"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* 그래프 영역 (높이 확대) */}
      <div className="flex-1 w-full min-h-[450px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={filteredData}
            margin={{ top: 20, right: 30, left: 0, bottom: 0 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              vertical={false}
              stroke="#F3F4F6"
            />
            <XAxis
              dataKey="date"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#9CA3AF", fontSize: 14 }}
              dy={15}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              domain={[0, 100]}
              tick={{ fill: "#9CA3AF", fontSize: 14 }}
            />
            <Tooltip
              contentStyle={{
                borderRadius: "12px",
                border: "none",
                boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
              }}
              cursor={{
                stroke: "#5A55D6",
                strokeWidth: 1,
                strokeDasharray: "5 5",
              }}
            />
            <Line
              type="monotone"
              dataKey="score"
              stroke="#5A55D6"
              strokeWidth={4}
              dot={{ r: 6, fill: "#5A55D6", stroke: "#fff", strokeWidth: 3 }}
              activeDot={{ r: 8 }}
              animationDuration={1500}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
