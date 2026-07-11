import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { HITLModal } from './HITLModal';

describe('HITLModal', () => {
  it('renders nothing when isOpen is false', () => {
    render(<HITLModal isOpen={false} blockedReason="Wait" onApprove={() => {}} onCancel={() => {}} />);
    expect(screen.queryByTestId('hitl-modal')).not.toBeInTheDocument();
  });

  it('shows blocked reason', () => {
    render(<HITLModal isOpen={true} blockedReason="Approval needed" onApprove={() => {}} onCancel={() => {}} />);
    expect(screen.getByTestId('blocked-reason')).toHaveTextContent("Approval needed");
  });

  it('can add environment variables and approve', () => {
    const onApprove = vi.fn();
    render(<HITLModal isOpen={true} blockedReason="Env needed" requiresEnvVars={true} onApprove={onApprove} onCancel={() => {}} />);
    
    fireEvent.change(screen.getByTestId('env-key-input'), { target: { value: 'API_KEY' } });
    fireEvent.change(screen.getByTestId('env-val-input'), { target: { value: 'secret' } });
    fireEvent.click(screen.getByTestId('env-add-btn'));
    
    expect(screen.getByTestId('env-list')).toHaveTextContent('API_KEY');
    
    fireEvent.click(screen.getByTestId('hitl-approve-btn'));
    expect(onApprove).toHaveBeenCalledWith({ 'API_KEY': 'secret' });
  });
});
