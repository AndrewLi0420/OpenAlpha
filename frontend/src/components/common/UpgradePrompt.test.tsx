import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import UpgradePrompt from './UpgradePrompt';

describe('UpgradePrompt', () => {
  it('renders upgrade prompt with correct message', () => {
    render(
      <BrowserRouter>
        <UpgradePrompt stockLimit={5} />
      </BrowserRouter>
    );

    expect(screen.getByText(/Free Tier Limit Reached/i)).toBeInTheDocument();
    expect(screen.getByText(/You've reached your free tier limit \(5 stocks\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Upgrade to Premium/i)).toBeInTheDocument();
  });

  it('renders upgrade button with correct link', () => {
    render(
      <BrowserRouter>
        <UpgradePrompt stockLimit={5} />
      </BrowserRouter>
    );

    const upgradeButton = screen.getByText(/Upgrade to Premium/i);
    expect(upgradeButton).toBeInTheDocument();
    expect(upgradeButton.closest('a')).toHaveAttribute('href', '/upgrade');
  });

  it('renders dismiss button when onDismiss is provided', () => {
    const onDismiss = vi.fn();
    render(
      <BrowserRouter>
        <UpgradePrompt stockLimit={5} onDismiss={onDismiss} />
      </BrowserRouter>
    );

    const dismissButton = screen.getByText(/Dismiss/i);
    expect(dismissButton).toBeInTheDocument();
  });

  it('does not render dismiss button when onDismiss is not provided', () => {
    render(
      <BrowserRouter>
        <UpgradePrompt stockLimit={5} />
      </BrowserRouter>
    );

    expect(screen.queryByText(/Dismiss/i)).not.toBeInTheDocument();
  });

  it('displays correct stock limit in message', () => {
    render(
      <BrowserRouter>
        <UpgradePrompt stockLimit={3} />
      </BrowserRouter>
    );

    expect(screen.getByText(/3 stocks/i)).toBeInTheDocument();
  });
});

