import * as React from "react";
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area
} from "recharts";
import { cn } from "@/lib/cn";

interface ChartDataPoint {
  time: string;
  value: number;
  [key: string]: string | number;
}

interface ChartProps {
  data: ChartDataPoint[];
  lines: {
    key: string;
    color: string;
    name?: string;
  }[];
  height?: number;
  showGrid?: boolean;
  showTooltip?: boolean;
  className?: string;
}

export function Chart({
  data,
  lines,
  height = 300,
  showGrid = true,
  showTooltip = true,
  className
}: ChartProps) {
  return (
    <div className={cn("w-full", className)}>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data} margin={{ top: 5, right: 10, left: 10, bottom: 0 }}>
          {showGrid && (
            <CartesianGrid strokeDasharray="3 3" stroke="#3c3c4a" />
          )}
          <XAxis 
            dataKey="time" 
            stroke="#9299aa"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <YAxis 
            stroke="#9299aa"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          {showTooltip && (
            <Tooltip
              contentStyle={{
                backgroundColor: "#171717",
                border: "1px solid #3c3c4a",
                borderRadius: "8px",
                color: "#ffffff"
              }}
            />
          )}
          {lines.map((line) => (
            <Area
              key={line.key}
              type="monotone"
              dataKey={line.key}
              stroke={line.color}
              fill={line.color}
              fillOpacity={0.1}
              strokeWidth={2}
              name={line.name || line.key}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

interface MiniChartProps {
  data: number[];
  color?: string;
  height?: number;
  className?: string;
}

export function MiniChart({
  data,
  color = "#60a5fa",
  height = 40,
  className
}: MiniChartProps) {
  const chartData = data.map((value, index) => ({
    time: index.toString(),
    value
  }));

  return (
    <div className={cn("w-full", className)}>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData}>
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
