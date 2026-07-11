import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { JobTracker } from './JobTracker';

describe('JobTracker', () => {
  it('renders without crashing', () => {
    render(<JobTracker currentStepId="UPLOADED" status="IN_PROGRESS" />);
    expect(screen.getByTestId('job-tracker')).toBeInTheDocument();
  });

  it('shows IN_PROGRESS for current step', () => {
    render(<JobTracker currentStepId="CODE_EMBEDDING_INGESTION" status="IN_PROGRESS" />);
    expect(screen.getByText('(In Progress...)')).toBeInTheDocument();
  });

  it('shows Failed status', () => {
    render(<JobTracker currentStepId="CHARTER_EVALUATION" status="FAILED" />);
    expect(screen.getByText('(Failed)')).toBeInTheDocument();
  });

  it('shows Blocked status', () => {
    render(<JobTracker currentStepId="IMPLEMENTATION_START" status="BLOCKED" />);
    expect(screen.getByText('(Blocked - Action Required)')).toBeInTheDocument();
  });
});
