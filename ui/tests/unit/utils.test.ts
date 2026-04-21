import { describe, it, expect } from 'vitest';
import { PERSONA_CONFIG } from '../../lib/persona-config';

describe('Persona Config', () => {
  it('has samara configuration', () => {
    expect(PERSONA_CONFIG.samara.name).toBe('Samara');
    expect(PERSONA_CONFIG.samara.font).toBe('font-samara');
  });

  it('has artery configuration', () => {
    expect(PERSONA_CONFIG.artery.name).toBe('Artery 1.0');
    expect(PERSONA_CONFIG.artery.font).toBe('font-artery');
  });
});
