import React from 'react';
import { flags } from '../config/flags';
import TopicsHub from '../pages/TopicsHub';
import TopicsDisabled from '../pages/TopicsDisabled';

interface TopicsRouteWrapperProps {
  children?: React.ReactNode;
}

export const TopicsRouteWrapper: React.FC<TopicsRouteWrapperProps> = ({ children }) => {
  if (!flags.labelsEnabled) {
    return <TopicsDisabled />;
  }

  return <TopicsHub />;
};

export default TopicsRouteWrapper;
