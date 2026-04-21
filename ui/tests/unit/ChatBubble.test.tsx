import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ChatBubble from '../../components/ChatBubble';

describe('ChatBubble', () => {
  it('renders user message correctly', () => {
    render(<ChatBubble role="user" content="Hello" />);
    expect(screen.getByText('Hello')).toBeDefined();
  });

  it('applies samara styling', () => {
    const { container } = render(<ChatBubble role="assistant" content="Hi" persona="samara" />);
    expect(container.querySelector('.chat-bubble-samara')).toBeDefined();
  });

  it('applies artery terminal styling', () => {
    const { container } = render(<ChatBubble role="assistant" content="OK" persona="artery" />);
    expect(container.querySelector('.font-artery')).toBeDefined();
  });
});
