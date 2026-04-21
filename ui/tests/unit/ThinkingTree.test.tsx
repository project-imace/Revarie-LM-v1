import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ThinkingTree from '../../components/ThinkingTree';

describe('ThinkingTree', () => {
  it('renders steps', () => {
    render(<ThinkingTree steps={['Step 1', 'Step 2']} />);
    expect(screen.getByText('Step 1')).toBeDefined();
    expect(screen.getByText('Step 2')).toBeDefined();
  });
});
