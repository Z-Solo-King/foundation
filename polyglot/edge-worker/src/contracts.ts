export type HttpMethod = "GET" | "POST";

export type EdgeRoute =
  | "health"
  | "readiness"
  | "dashboard"
  | "chat"
  | "chat_stream"
  | "chatbot_diagnostic"
  | "storage_diagnostic"
  | "research_publish"
  | "research_run"
  | "research"
  | "not_found";

export interface RouteMatch {
  route: EdgeRoute;
  method: HttpMethod;
  pathname: string;
  requiresAuth: boolean;
}

export interface ChatResponseEnvelope {
  response_id: string;
  result_state: string;
  text: string;
  generation_status?: string;
  usage?: {
    input_tokens?: number;
    output_tokens?: number;
  };
}

export interface ChatProxyEnvelope {
  ok: boolean;
  response?: ChatResponseEnvelope;
}

export interface EdgeError {
  ok: false;
  error: string;
}

export const MAX_PUBLIC_JSON_BODY_BYTES = 1_048_576;
export const MAX_SSE_CHUNK_CHARS = 256;
