export interface PrincipleItem {
  id: string;
  title: string;
  description: string;
  tags?: string[];
  source?: string;
}

export interface ActionItem {
  id: string;
  title: string;
  description: string;
  scope?: string;
  tags?: string[];
  source?: string;
}

export interface StoryItem {
  id: string;
  title: string;
  summary: string;
  impact?: string;
  link?: string;
}

export interface ContentResponse<T> {
  items: T[];
  count: number;
  source: 'demo' | 'file';
}
