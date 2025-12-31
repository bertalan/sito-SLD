export interface Service {
  id: string;
  title: string;
  description: string;
  tags: string[];
}

export interface Project {
  id: string;
  title: string;
  client: string;
  image: string;
  category: string;
}

export interface NavItem {
  label: string;
  href: string;
}

export enum LoadingState {
  IDLE = 'IDLE',
  LOADING = 'LOADING',
  SUCCESS = 'SUCCESS',
  ERROR = 'ERROR'
}

// Wagtail-like API response structure simulation
export interface PageResponse<T> {
  meta: {
    total_count: number;
  };
  items: T[];
}