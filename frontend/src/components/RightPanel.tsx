import { useState } from 'react';
import { Layout, Typography, Button, Checkbox, Slider, Select, Input, Space } from 'antd';

const { Sider } = Layout;
const { Title, Text } = Typography;

export function RightPanel() {
  const [influenceRange, setInfluenceRange] = useState(10);
  const [sentimentFilters, setSentimentFilters] = useState({
    negative: false,
    neutral: false,
    positive: false,
  });
  const [excludeCountries, setExcludeCountries] = useState(false);
  const [excludeLanguages, setExcludeLanguages] = useState(false);

  return (
    <Sider 
      width={320} 
      theme="light"
      style={{ 
        background: 'white',
        borderLeft: '1px solid #e5e7eb',
        padding: '24px',
        overflow: 'auto'
      }}
    >
      <Space direction="vertical" size={24} style={{ width: '100%' }}>
        {/* Sources */}
        <div>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: '16px'
          }}>
            <Title level={5} style={{ margin: 0, fontSize: '14px', fontWeight: 600 }}>
              Sources
            </Title>
            <Button 
              type="link" 
              size="small" 
              style={{ padding: 0, height: 'auto' }}
            >
              Show all (29546)
            </Button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px',
              padding: '8px',
              border: '1px solid #d1d5db',
              borderRadius: '4px'
            }}>
              <Checkbox defaultChecked />
              <div>
                <Text strong style={{ fontSize: '12px' }}>X (Twitter)</Text>
                <Text style={{ fontSize: '12px', color: '#9ca3af', marginLeft: '4px' }}>(2803)</Text>
              </div>
            </div>
          </div>
        </div>

        {/* Sentiment */}
        <div>
          <Title level={5} style={{ margin: 0, marginBottom: '12px', fontSize: '14px', fontWeight: 600 }}>
            Sentiment
          </Title>
          <Space direction="vertical" size={8}>
            {[
              { label: 'Negative', key: 'negative', color: '#ef4444' },
              { label: 'Neutral', key: 'neutral', color: '#9ca3af' },
              { label: 'Positive', key: 'positive', color: '#10b981' },
            ].map((item) => (
              <div key={item.key} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Checkbox
                  checked={sentimentFilters[item.key as keyof typeof sentimentFilters]}
                  onChange={(e) =>
                    setSentimentFilters({
                      ...sentimentFilters,
                      [item.key]: e.target.checked,
                    })
                  }
                />
                <div 
                  style={{ 
                    width: '8px', 
                    height: '8px', 
                    borderRadius: '50%',
                    backgroundColor: item.color 
                  }} 
                />
                <Text style={{ fontSize: '14px' }}>{item.label}</Text>
              </div>
            ))}
          </Space>
        </div>

        {/* Influence Score */}
        <div>
          <Title level={5} style={{ margin: 0, marginBottom: '12px', fontSize: '14px', fontWeight: 600 }}>
            Influence score
          </Title>
          <Slider
            min={0}
            max={10}
            value={influenceRange}
            onChange={setInfluenceRange}
            marks={{
              0: '0',
              10: '10'
            }}
          />
          <Text style={{ fontSize: '12px', color: '#6b7280' }}>
            Current: {influenceRange}
          </Text>
        </div>

        {/* Geolocation */}
        <div>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: '8px'
          }}>
            <Title level={5} style={{ margin: 0, fontSize: '14px', fontWeight: 600 }}>
              Geolocation
            </Title>
            <Checkbox
              checked={excludeCountries}
              onChange={(e) => setExcludeCountries(e.target.checked)}
            >
              <Text style={{ fontSize: '12px', color: '#6b7280' }}>Exclude countries</Text>
            </Checkbox>
          </div>
          <Select
            placeholder="Choose countries"
            style={{ width: '100%' }}
            options={[
              { value: 'us', label: 'United States' },
              { value: 'br', label: 'Brazil' },
              { value: 'uk', label: 'United Kingdom' },
            ]}
          />
        </div>

        {/* Language */}
        <div>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: '8px'
          }}>
            <Title level={5} style={{ margin: 0, fontSize: '14px', fontWeight: 600 }}>
              Language
            </Title>
            <Checkbox
              checked={excludeLanguages}
              onChange={(e) => setExcludeLanguages(e.target.checked)}
            >
              <Text style={{ fontSize: '12px', color: '#6b7280' }}>Exclude languages</Text>
            </Checkbox>
          </div>
          <Input
            placeholder="Choose languages"
            style={{ width: '100%' }}
          />
        </div>
      </Space>
    </Sider>
  );
}
