// Shared type definitions for VeriFeed API responses

export interface Source {
  id: number;
  name: string;
  website_url: string;
  rss_url?: string;
}

export interface Article {
  id: number;
  headline: string;
  url: string;
  published_at: string | null;
  source: Source;
}

export interface Story {
  id: number;
  title: string;
  category: string | null;
  summary: string | null;
  created_at: string;
  article_count: number;
}

export interface StoryDetail extends Story {
  articles: Article[];
}

export interface EvidenceSource {
  title: string;
  outlet: string;
  url: string;
  type: string;
}

export interface VerificationResult {
  id: number;
  query: string;
  // Legacy single verdict
  verdict: "Confirmed Scam" | "Confirmed" | "Unconfirmed" | "Disputed / False" | "No Coverage Found";
  // New dual verdict system
  claim_verdict?: "True" | "False" | "Partly True" | "Misleading" | "Insufficient Evidence";
  message_authenticity_verdict?: "Verified Official" | "Likely Legitimate" | "Unverified" | "Suspicious" | "Likely Fraudulent" | "Confirmed Fraudulent";
  confidence_score: number;
  risk_level?: "High" | "Medium" | "Low";
  summary: string;
  sources: EvidenceSource[];
  // Extracted entities
  extracted_sender?: string;
  extracted_numbers?: string[];
  extracted_urls?: string[];
  extracted_institutions?: string[];
  // Channel verification details
  verification_details?: {
    sender_verified?: boolean;
    channel_verified?: boolean;
    matched_institution?: string;
    matched_channels?: string[];
    institutions_checked?: string[];
  };
  // User guidance
  recommended_actions?: Array<{
    action: string;
    priority: "critical" | "high" | "medium" | "low";
    reason?: string;
  }>;
  // D2: Evidence pipeline methodology
  methodology?: string;
  created_at: string;
}

export interface InstitutionalAlert {
  id: number;
  title: string;
  alert_text: string;
  source_url: string;
  published_date: string;
  institution: {
    id: number;
    name: string;
    sector: string;
    website_url: string;
  };
}

export interface SubmissionCluster {
  id: number;
  representative_text: string;
  submission_count: number;
  status: "unconfirmed" | "confirmed_scam" | "confirmed_legitimate";
  first_seen: string;
  last_seen: string;
}
