// Type definitions for TweetPulse

export interface Tweet {
  id: string;
  author: string;
  content: string;
  created_at: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  confidence: number;
  metrics: TweetMetrics;
  time?: string;
}

export interface TweetMetrics {
  likes: number;
  retweets: number;
  replies: number;
}

export interface OverviewData {
  total_tweets: number;
  total_change_percent: number;
  sentiment_distribution: {
    positive: SentimentData;
    neutral: SentimentData;
    negative: SentimentData;
  };
}

export interface SentimentData {
  count: number;
  percent: number;
  change: number;
}

export interface ChartDataPoint {
  hour: string;
  count: number;
}

export interface Keyword {
  keyword: string;
  count: number;
}

export interface DashboardState {
  overview: OverviewData | null;
  tweets: Tweet[];
  chartData: ChartDataPoint[];
  keywords: Keyword[];
  loading: boolean;
  error: string | null;
}
