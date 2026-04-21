import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Terminal from '../../components/Terminal';

describe('Terminal', () => {
  it('renders boot sequence', async () => {
    render(<Terminal />);
    // Wait for animation
    await new Promise(r => setTimeout(r, 200));
    expect(screen.getByText(/ARTERY v1.0/)).toBeDefined();
  });
});
