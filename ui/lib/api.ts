const HF_SPACE_URL = process.env.NEXT_PUBLIC_HF_SPACE_URL || 'https://revarie-lm-v1-engine.hf.space';

export interface ChatRequest {
  participant_id: string;
  message: string;
  persona?: 'samara' | 'artery';
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  persona: string;
  session_id: string;
  usage?: { total_tokens: number };
}

export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${HF_SPACE_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    throw new Error(`Chat API error: ${res.status}`);
  }

  return res.json();
}

export async function checkHealth(): Promise<{ status: string; version: string }> {
  const res = await fetch(`${HF_SPACE_URL}/health`);
  return res.json();
}
