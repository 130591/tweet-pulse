import { Layout, Menu, Badge, Button, Typography } from 'antd';
import { PlusOutlined, MessageOutlined, LineChartOutlined } from '@ant-design/icons';
import type { MenuProps } from 'antd';

const { Sider } = Layout;
const { Title, Text } = Typography;

export function Sidebar() {
  const projects = [
    { id: 1, name: '#Flamengo', mentions: 1, unread: true }
  ];

  const menuItems: MenuProps['items'] = [
    {
      key: 'mentions',
      icon: <MessageOutlined />,
      label: 'Mentions',
    },
    {
      key: 'analysis',
      icon: <LineChartOutlined />,
      label: 'Analysis',
    },
  ];

  return (
    <Sider 
      width={288} 
      style={{ 
        background: '#0f172a',
        borderRight: '1px solid #334155'
      }}
    >
      {/* Logo */}
      <div style={{ 
        padding: '24px', 
        borderBottom: '1px solid #334155',
        display: 'flex',
        alignItems: 'center',
        gap: '8px'
      }}>
        <div style={{
          width: 32,
          height: 32,
          background: '#3b82f6',
          borderRadius: '4px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontWeight: 'bold',
          fontSize: '14px'
        }}>
          TP
        </div>
        <Title level={4} style={{ margin: 0, color: 'white' }}>TweetPulse</Title>
      </div>

      {/* Projects Section */}
      <div style={{ padding: '16px' }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: '16px'
        }}>
          <Text style={{ 
            fontSize: '12px', 
            fontWeight: 600, 
            textTransform: 'uppercase', 
            color: '#94a3b8' 
          }}>
            Projects
          </Text>
          <Button 
            type="text" 
            icon={<PlusOutlined />} 
            size="small"
            style={{ color: '#94a3b8' }}
          />
        </div>

        <div style={{ marginBottom: '16px' }}>
          {projects.map((project) => (
            <div
              key={project.id}
              style={{
                padding: '12px',
                borderRadius: '4px',
                background: '#1e293b',
                cursor: 'pointer',
                marginBottom: '8px',
                transition: 'background 0.2s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = '#334155'}
              onMouseLeave={(e) => e.currentTarget.style.background = '#1e293b'}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text style={{ fontSize: '14px', fontWeight: 500, color: 'white' }}>
                  {project.name}
                </Text>
                {project.unread && (
                  <Badge count={project.mentions} style={{ background: '#dc2626' }} />
                )}
              </div>
              <Text style={{ fontSize: '12px', color: '#94a3b8', display: 'block', marginTop: '4px' }}>
                1 New mention
              </Text>
            </div>
          ))}
        </div>

        {/* Navigation Menu */}
        <Menu
          mode="inline"
          items={menuItems}
          style={{ 
            background: 'transparent', 
            border: 'none',
            color: '#cbd5e1'
          }}
          theme="dark"
        />
      </div>
    </Sider>
  );
}
