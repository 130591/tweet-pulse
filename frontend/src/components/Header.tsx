import React from 'react';
import { Layout, Input, Button, Space, Avatar, Badge, Typography } from 'antd';
import { SearchOutlined, QuestionCircleOutlined, BellOutlined, CloseOutlined } from '@ant-design/icons';

const { Header: AntHeader } = Layout;
const { Text } = Typography;

interface HeaderProps {
  selectedTimeRange: string;
  onTimeRangeChange: (range: string) => void;
}

const Header: React.FC<HeaderProps> = () => {
  return (
    <AntHeader
      style={{
        backgroundColor: '#fff',
        borderBottom: '1px solid #e5e7eb',
        padding: '16px 24px',
        height: 'auto',
        lineHeight: 'normal'
      }}
    >
      <div style={{ marginBottom: '16px' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px'
        }}>
          {/* Search Bar */}
          <div style={{ flex: 1, maxWidth: '768px' }}>
            <Input
              prefix={<SearchOutlined style={{ color: '#9ca3af' }} />}
              placeholder="Search through mentions, authors & domains..."
              style={{
                backgroundColor: '#f9fafb',
                borderColor: '#d1d5db',
                borderRadius: '8px'
              }}
              size="large"
            />
          </div>

          {/* Right Actions */}
          <Space size={16}>
            <Button
              type="primary"
              style={{
                backgroundColor: '#facc15',
                borderColor: '#facc15',
                color: '#000',
                fontWeight: 600,
                borderRadius: '9999px',
                paddingLeft: '16px',
                paddingRight: '16px',
                height: '32px',
                fontSize: '14px'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#eab308';
                e.currentTarget.style.borderColor = '#eab308';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#facc15';
                e.currentTarget.style.borderColor = '#facc15';
              }}
            >
              UPGRADE
            </Button>

            <Button
              type="text"
              icon={<QuestionCircleOutlined style={{ fontSize: '20px', color: '#6b7280' }} />}
              style={{
                padding: '8px',
                height: 'auto',
                width: 'auto'
              }}
            />

            <Badge dot status="success" offset={[-6, 6]}>
              <Button
                type="text"
                icon={<BellOutlined style={{ fontSize: '20px', color: '#6b7280' }} />}
                style={{
                  padding: '8px',
                  height: 'auto',
                  width: 'auto'
                }}
              />
            </Badge>

            <Avatar
              style={{
                backgroundColor: '#2563eb',
                fontSize: '14px',
                fontWeight: 600
              }}
              size={32}
            >
              E
            </Avatar>
          </Space>
        </div>
      </div>

      {/* Filters */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px'
      }}>
        <Space size={8} style={{ alignItems: 'center' }}>
          <Text style={{ fontSize: '14px', color: '#6b7280' }}>By relevance</Text>
          <Button
            type="text"
            size="small"
            icon={<CloseOutlined />}
            style={{
              padding: '2px 6px',
              height: 'auto',
              fontSize: '12px',
              color: '#9ca3af'
            }}
          />
        </Space>

        <Button
          type="link"
          size="small"
          style={{
            color: '#2563eb',
            padding: '0',
            height: 'auto'
          }}
        >
          Clear filters
        </Button>

        <Button
          type="link"
          size="small"
          style={{
            color: '#2563eb',
            padding: '0',
            height: 'auto'
          }}
        >
          Save filters
        </Button>

        <div style={{ marginLeft: 'auto' }}>
          <Text style={{ fontSize: '14px', color: '#6b7280' }}>Last 30 days</Text>
        </div>
      </div>
    </AntHeader>
  );
};

export { Header };
