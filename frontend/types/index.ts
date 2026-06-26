export interface TokenPairResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  is_admin: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface RegisterResponse {
  user: UserResponse;
  tokens: TokenPairResponse;
}

export interface ProviderStatus {
  provider: string;
  status: "healthy" | "degraded" | "down";
  latency_ms: number | null;
  avg_latency_ms: number | null;
  uptime_percentage: number | null;
  last_checked_at: string;
  error_message: string | null;
}

export interface RoutingCandidate {
  provider: string;
  model: string;
  cost_per_1k: number;
  avg_latency_ms: number;
  health: string;
  quality_score: number;
  score: number;
  score_breakdown: Record<string, number>;
}

export interface RoutingDecision {
  strategy: string;
  candidates: RoutingCandidate[];
  selected: string;
  reason: string;
}

export interface RequestRecord {
  id: string;
  user_id: string;
  provider: string;
  model: string;
  routing_strategy: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
  latency_ms: number | null;
  cache_hit: boolean;
  status: "success" | "error" | "timeout";
  error_message: string | null;
  routing_decision: RoutingDecision | null;
  created_at: string;
}

export interface AnalyticsOverview {
  total_requests: number;
  total_cost_usd: number;
  avg_latency_ms: number;
  cache_hit_rate: number;
  error_rate: number;
  period_days: number;
}

export interface APIKeyResponse {
  id: string;
  name: string;
  key_prefix: string;
  role: string;
  last_used_at: string | null;
  expires_at: string | null;
  revoked: boolean;
  is_active: boolean;
  created_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  role?: string;
}

export type RoutingStrategy = "auto" | "cheapest" | "fastest" | "quality";

// ---------------------------------------------------------------------------
// Chat — Phase 2
// ---------------------------------------------------------------------------

export type MessageRole = "system" | "user" | "assistant";

export interface ChatMessage {
  role: MessageRole;
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  routing_strategy: string;
  manual_provider?: string;
  model?: string;
  max_tokens?: number;
  temperature?: number;
  conversation_id?: string;
}

export interface ChatResponse {
  content: string;
  provider: string;
  model: string;
  finish_reason: string;
  routing_decision: RoutingDecision;
}

export type StreamChunkType = "delta" | "done" | "error";

export interface StreamChunk {
  type: StreamChunkType;
  content?: string;                    // type=delta
  provider?: string;                   // type=done
  model?: string;                      // type=done
  finish_reason?: string;              // type=done
  routing_decision?: RoutingDecision;  // type=done
  message?: string;                    // type=error
}

// A message in the local conversation UI (extends ChatMessage with metadata)
export interface ConversationMessage extends ChatMessage {
  id: string;
  timestamp: Date;
  isStreaming?: boolean;
  provider?: string;
  model?: string;
  error?: string;
  routing_decision?: RoutingDecision;
}

// ---------------------------------------------------------------------------
// Providers — Phase 2
// ---------------------------------------------------------------------------

export interface ModelInfo {
  id: string;
  context_window: number;
  quality_score: number;
}

export interface ProviderInfo {
  id: string;
  name: string;
  status: "healthy" | "down";
  models: ModelInfo[];
}

export interface ProvidersResponse {
  providers: ProviderInfo[];
}
