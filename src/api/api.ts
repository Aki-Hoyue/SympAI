import { ConfigInterface } from '@type/chat';

export const getChatCompletionStream = async (
  endpoint: string,
  messages: string,
  id: string,
  config: ConfigInterface,
  apiKey?: string,
) => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'User-Agent': 'sympai'
  };
  if (apiKey) headers.Authorization = `Bearer ${apiKey}`;

  const response = await fetch("http://127.0.0.1:8000/api/chat", {
    method: 'POST',
    headers,
    body: JSON.stringify({
      message: messages,
      session_id: id,
    }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API request failed: ${text}`);
  }

  const stream = response.body;
  return stream;
};
