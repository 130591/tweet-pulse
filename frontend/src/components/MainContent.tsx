import { Tabs, Card, Button, Pagination, Avatar, Typography, Space } from 'antd';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const { Text } = Typography;

interface MainContentProps {
  selectedTab: string;
  onTabChange: (tab: string) => void;
}

const chartData = [
  { date: '01 Oct', mentions: 800, reach: 400 },
  { date: '06 Oct', mentions: 900, reach: 500 },
  { date: '11 Oct', mentions: 1100, reach: 600 },
  { date: '16 Oct', mentions: 950, reach: 550 },
  { date: '21 Oct', mentions: 1200, reach: 700 },
  { date: '26 Oct', mentions: 1000, reach: 650 },
  { date: '31 Oct', mentions: 800, reach: 400 },
];

const sentimentData = [
  { period: '01 Oct - 04 Oct', positive: 1200, negative: 200 },
  { period: '05 Oct - 11 Oct', positive: 1300, negative: 180 },
  { period: '12 Oct - 18 Oct', positive: 1100, negative: 220 },
  { period: '19 Oct - 25 Oct', positive: 1450, negative: 250 },
  { period: '26 Oct - 31 Oct', positive: 1000, negative: 200 },
];

export function MainContent({ selectedTab, onTabChange }: MainContentProps) {
  const tabItems = [
    {
      key: 'mentions',
      label: 'Mentions & Reach',
    },
    {
      key: 'sentiment',
      label: 'Sentiment',
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* Tabs */}
      <Tabs
        activeKey={selectedTab}
        onChange={onTabChange}
        items={tabItems}
        style={{ marginBottom: '24px' }}
      />

      {/* Time Period */}
      <Space size={24} style={{ marginBottom: '24px' }}>
        {['Days', 'Weeks', 'Months'].map((period) => (
          <Button key={period} type="text" style={{ color: '#6b7280', padding: 0 }}>
            {period}
          </Button>
        ))}
      </Space>

      {/* Main Chart */}
      <Card style={{ marginBottom: '24px' }}>
        <Text style={{ fontSize: '14px', color: '#6b7280', display: 'block', marginBottom: '16px' }}>
          Click on the chart to filter by date
        </Text>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="date" 
              stroke="#9ca3af" 
              style={{ fontSize: '12px' }} 
            />
            <YAxis 
              stroke="#9ca3af" 
              style={{ fontSize: '12px' }} 
            />
            <Tooltip />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="mentions" 
              stroke="#3b82f6" 
              strokeWidth={2} 
              dot={false} 
            />
            <Line 
              type="monotone" 
              dataKey="reach" 
              stroke="#10b981" 
              strokeWidth={2} 
              dot={false} 
            />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      {/* Sentiment Chart */}
      <Card style={{ marginBottom: '24px' }}>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={sentimentData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="period" 
              stroke="#9ca3af" 
              style={{ fontSize: '12px' }} 
            />
            <YAxis 
              stroke="#9ca3af" 
              style={{ fontSize: '12px' }} 
            />
            <Tooltip />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="positive" 
              stroke="#10b981" 
              strokeWidth={2} 
              dot={false} 
            />
            <Line 
              type="monotone" 
              dataKey="negative" 
              stroke="#ef4444" 
              strokeWidth={2} 
              dot={false} 
            />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      {/* Mentions List */}
      <Card>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          marginBottom: '16px' 
        }}>
          <Text style={{ fontSize: '14px', color: '#6b7280' }}>By relevance</Text>
          <Text style={{ fontSize: '14px', color: '#6b7280' }}>Showing page 1 of 804</Text>
        </div>

        <div style={{ marginBottom: '24px' }}>
          <Card 
            hoverable
            style={{ 
              marginBottom: '16px',
              borderRadius: '8px'
            }}
          >
            <div style={{ display: 'flex', gap: '16px' }}>
              <Avatar 
                size={40} 
                style={{ 
                  backgroundColor: '#ef4444',
                  flexShrink: 0 
                }} 
              />
              <div style={{ flex: 1 }}>
                <Space direction="vertical" size={4} style={{ width: '100%' }}>
                  <div>
                    <Text strong style={{ marginRight: '8px' }}>@username</Text>
                    <Text style={{ fontSize: '14px', color: '#6b7280' }}>
                      x.com • 4.0B visits • Influence score: 10/10
                    </Text>
                  </div>
                  <Text style={{ fontSize: '14px', color: '#1f2937' }}>
                    Tweet content goes here...
                  </Text>
                  <Text style={{ fontSize: '12px', color: '#9ca3af' }}>
                    2025-10-19 01:46 PM
                  </Text>
                </Space>
              </div>
            </div>
          </Card>
        </div>

        {/* Pagination */}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <Pagination 
            current={1} 
            total={804 * 10} 
            pageSize={10}
            showSizeChanger={false}
          />
        </div>
      </Card>
    </div>
  );
}
