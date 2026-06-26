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

// Summary view — prompt is truncated server-side to 200 chars
export interface RequestSummary {
  id: string;
  request_id: string | null;
  conversation_id: string | null;
  provider: string;
  model: string;
  routing_strategy: string;
  prompt: string | null;
  total_tokens: number;
  cost_usd: number;
  latency_ms: number | null;
  cache_hit: boolean;
  status: "success" | "error" | "timeout";
  created_at: string;
}

// Full detail record
export interface RequestRecord extends RequestSummary {
  routing_reason: string | null;
  response: string | null;
  prompt_tokens: number;
  completion_tokens: number;
  error_message: string | null;
  routing_decision: RoutingDecision | null;
}

export interface RequestListResponse {
  items: RequestSummary[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
}

export interface DashboardOverview {
  total_requests: number;
  total_conversations: number;
  avg_latency_ms: number;
  total_cost_usd: number;
  period_days: number;
}

// ---------------------------------------------------------------------------
// Analytics — Phase 5
// ---------------------------------------------------------------------------

export interface CostDataPoint {
  date: string;
  cost: number;
  openai: number;
  anthropic: number;
  gemini: number;
}

export interface CostOverTime {
  data: CostDataPoint[];
  period_days: number;
  total: number;
}

export interface LatencyDataPoint {
  date: string;
  avg_ms: number;
}

export interface LatencyAnalytics {
  data: LatencyDataPoint[];
  avg_ms: number;
  p50_ms: number | null;
  p95_ms: number | null;
  by_provider: Record<string, number>;
  period_days: number;
}

export interface ProviderStat {
  provider: string;
  requests: number;
  percentage: number;
  cost: number;
  avg_latency_ms: number | null;
  success_rate: number;
}

export interface ProviderDistribution {
  providers: ProviderStat[];
  period_days: number;
  total_requests: number;
}

export interface TokenAnalytics {
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  avg_per_request: number;
  period_days: number;
}

export interface ConversationAnalytics {
  total_conversations: number;
  avg_messages_per_conversation: number;
  period_days: number;
}

export interface RoutingInsights {
  strategy_distribution: Record<string, number>;
  most_used_strategy: string;
  most_selected_provider: string;
  period_days: number;
}

export interface ProviderStatusDetail {
  provider: string;
  status: "healthy" | "degraded" | "down";
  latency_ms: number | null;
  avg_latency_ms: number | null;
  uptime_percentage: number | null;
  last_checked_at: string;
  error_message: string | null;
}

export interface ProvidersStatusResponse {
  providers: ProviderStatusDetail[];
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

// ---------------------------------------------------------------------------
// Personal API keys — Phase 6
// ---------------------------------------------------------------------------

export interface UserAPIKey {
  id: string;
  name: string;
  key_prefix: string;
  last_used_at: string | null;
  is_active: boolean;
  created_at: string;
}

export interface UserAPIKeyCreateResponse extends UserAPIKey {
  key: string;
}

export interface CacheStats {
  hits: number;
  misses: number;
  hit_rate: number;
  total_requests_served: number;
  cached_entries: number;
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
  cache_hit: boolean;
  fallback_provider: string | null;
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
  cache_hit?: boolean;                 // type=done
  fallback_provider?: string | null;   // type=done
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
