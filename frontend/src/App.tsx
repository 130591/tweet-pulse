import { useState } from 'react';
import { Layout } from 'antd';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { MainContent } from './components/MainContent';
import { RightPanel } from './components/RightPanel';
import './App.css';

const { Content } = Layout;

function App() {
  const [selectedTimeRange, setSelectedTimeRange] = useState('last-30-days');
  const [selectedTab, setSelectedTab] = useState('mentions');

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sidebar />
      <Layout>
        <Header 
          selectedTimeRange={selectedTimeRange} 
          onTimeRangeChange={setSelectedTimeRange} 
        />
        <Layout>
          <Content style={{ background: '#f5f5f5' }}>
            <MainContent 
              selectedTab={selectedTab} 
              onTabChange={setSelectedTab} 
            />
          </Content>
          <RightPanel />
        </Layout>
      </Layout>
    </Layout>
  );
}

export default App;
