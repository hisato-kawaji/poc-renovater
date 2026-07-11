import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ErrorModal } from './ErrorModal';

describe('ErrorModal', () => {
  it('renders nothing when isOpen is false', () => {
    render(<ErrorModal isOpen={false} errorMessage="Err" onRetry={() => {}} onCancel={() => {}} />);
    expect(screen.queryByTestId('error-modal')).not.toBeInTheDocument();
  });

  it('renders correct error message', () => {
    render(<ErrorModal isOpen={true} errorMessage="Syntax Error in line 5" onRetry={() => {}} onCancel={() => {}} />);
    expect(screen.getByTestId('error-message')).toHaveTextContent("Syntax Error in line 5");
  });

  it('calls onRetry when retry button is clicked', () => {
    const onRetry = vi.fn();
    render(<ErrorModal isOpen={true} errorMessage="Err" onRetry={onRetry} onCancel={() => {}} />);
    fireEvent.click(screen.getByTestId('retry-btn'));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
