export interface HealthResponse {
  status: string;
  environment: string;
}

export interface ReadinessCheck {
  status: string;
  detail?: string;
  connected?: boolean;
  webservice_ready?: boolean;
  user?: string;
  warnings?: string[];
  path?: string;
}

export interface ReadinessResponse {
  status: "ready" | "degraded";
  environment: string;
  checks: {
    maarch: ReadinessCheck;
    email: ReadinessCheck;
    audit: ReadinessCheck;
  };
}

export interface EmailStatusResponse {
  configured: boolean;
  host: string | null;
  mailbox: string;
  fetch_limit: number;
  default_destination: number | null;
  mark_as_read: boolean;
}

export interface EmailHealthResponse {
  status: string;
  mailbox?: string;
  unseen_count?: number;
}

export interface ClassificationSummary {
  category: string;
  confidence: number;
  method: string;
  destination_entity_id?: string | null;
  destination_serial_id?: number | null;
  doctype_id?: number | null;
  doctype_label?: string | null;
  ocr_source?: string | null;
  reasoning?: string | null;
}

export interface IngestedEmailResult {
  uid: string;
  message_id?: string | null;
  subject: string;
  res_id: number;
  attachments: Array<{ filename: string; attachment_id: number }>;
  classification?: ClassificationSummary | null;
  skipped: boolean;
  reason?: string | null;
}

export interface EmailPollResponse {
  fetched: number;
  ingested: number;
  skipped: number;
  failed: number;
  results: IngestedEmailResult[];
  errors: string[];
}

export interface MaarchHealthResponse {
  status: string;
  application_name?: string;
  auth_mode?: string;
  maarch_url?: string;
}

export interface MaarchConnectionResponse {
  connected: boolean;
  webservice_ready: boolean;
  current_user?: string;
  warnings?: string[];
  maarch_url?: string;
}

export interface MaarchEntity {
  id: string;
  serialId: number;
  shortLabel?: string;
  enabled?: boolean;
}

export interface MaarchReferenceResponse {
  indexing_models: Array<{ id: number; label: string }>;
  statuses: Record<string, string>;
  priorities: Record<string, string>;
  defaults: {
    model_id: number;
    status: string;
    attachment_type: string;
    priority: string | null;
  };
}

export interface AnalysisStatusResponse {
  ocr_enabled: boolean;
  ocr_tesseract_enabled: boolean;
  ai_enabled: boolean;
  ai_provider: string;
  classification_min_confidence: number;
  openai_configured: boolean;
}

export interface RoutingRule {
  category: string;
  entity_id: string;
  keywords: string[];
  doctype_keywords: string[];
  default_doctype_id: number | null;
}

export interface ClassifyTextRequest {
  subject?: string;
  body_text?: string;
  sender?: string | null;
}

export interface ClassifyTextResponse {
  ocr_source: string;
  extracted_text_preview: string;
  classification: ClassificationSummary;
}

export interface AuditEvent {
  id: number;
  created_at: string;
  event_type: string;
  email_uid?: string | null;
  message_id?: string | null;
  subject?: string | null;
  sender_email?: string | null;
  res_id?: number | null;
  destination_serial_id?: number | null;
  doctype_id?: number | null;
  category?: string | null;
  confidence?: number | null;
  error_message?: string | null;
  details: Record<string, unknown>;
}

export interface AuditEventsResponse {
  enabled: boolean;
  count: number;
  events: AuditEvent[];
}
