import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

interface HistogramProps {
  data: Record<string, number>;
  title: string;
  fillColor?: string;
}

export function Histogram({ data, title, fillColor = "#8884d8" }: HistogramProps) {
  const chartData = Object.entries(data).map(([key, value]) => ({
    state: key,
    value: value
  }));

  return (
    <div className="w-full h-64 mb-6">
      <h3 className="text-sm text-gray-400 mb-2">{title}</h3>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
          <XAxis dataKey="state" stroke="#9CA3AF" tick={{fill: '#9CA3AF'}} />
          <YAxis stroke="#9CA3AF" tick={{fill: '#9CA3AF'}} />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '4px', color: '#fff' }}
            cursor={{fill: '#374151', opacity: 0.4}}
          />
          <Bar dataKey="value" fill={fillColor} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
