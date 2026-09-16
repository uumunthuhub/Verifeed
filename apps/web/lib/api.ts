import { VerificationResult, InstitutionalAlert, SubmissionCluster } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchStories(category?: string, skip = 0, limit = 50) {
  try {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (category) params.set("category", category);
    const res = await fetch(`${API_BASE}/api/v1/stories/?${params}`, {
      next: { revalidate: 30 },
    });
    if (!res.ok) return [];
    return res.json();
  } catch (err) {
    console.error("Error fetching stories:", err);
    return [];
  }
}

export async function searchStories(q: string, skip = 0, limit = 50) {
  try {
    const params = new URLSearchParams({ q, skip: String(skip), limit: String(limit) });
    const res = await fetch(`${API_BASE}/api/v1/stories/search?${params}`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    return res.json();
  } catch (err) {
    console.error("Error searching stories:", err);
    return [];
  }
}

export async function fetchStory(id: number) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/stories/${id}`, {
      next: { revalidate: 30 },
    });
    if (!res.ok) return null;
    return res.json();
  } catch (err) {
    console.error("Error fetching story:", err);
    return null;
  }
}

export async function fetchSources() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/sources/`, {
      next: { revalidate: 300 },
    });
    if (!res.ok) return [];
    return res.json();
  } catch (err) {
    console.error("Error fetching sources:", err);
    return [];
  }
}

export async function verifyClaim(
  query: string,
  imageData?: string | null,
  fileName?: string | null,
  priorScreening?: ScreeningResult | null,
): Promise<VerificationResult | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/verify/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        image_data: imageData,
        file_name: fileName,
        prior_screening: priorScreening ?? null,
      }),
    });
    if (!res.ok) return null;
    return res.json();
  } catch (err) {
    console.error("Error verifying claim:", err);
    return null;
  }
}

export async function submitScamReport(text: string, imageData?: string | null): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/verify/submit-scam`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, image_data: imageData }),
    });
    return res.ok;
  } catch (err) {
    console.error("Error submitting scam report:", err);
    return false;
  }
}

export async function verifyEmail(payload: {
  sender_address: string;
  display_name?: string;
  subject?: string;
  body_text: string;
  headers?: string;
}) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/verify/email`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) return null;
    return res.json();
  } catch (err) {
    console.error("Error verifying email:", err);
    return null;
  }
}

export async function fetchInstitutionalAlerts(): Promise<InstitutionalAlert[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/verify/alerts`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) return [];
    return res.json();
  } catch (err) {
    console.error("Error fetching alerts:", err);
    return [];
  }
}

export async function fetchRecentVerifications(): Promise<VerificationResult[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/verify/recent`, {
      next: { revalidate: 15 },
    });
    if (!res.ok) return [];
    return res.json();
  } catch (err) {
    console.error("Error fetching recent verifications:", err);
    return [];
  }
}

export async function fetchEmergingClusters(): Promise<SubmissionCluster[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/verify/clusters`, {
      next: { revalidate: 30 },
    });
    if (!res.ok) return [];
    return res.json();
  } catch (err) {
    console.error("Error fetching emerging clusters:", err);
    return [];
  }
}

export async function fetchVerificationById(id: string | number): Promise<VerificationResult | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/verify/${id}`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return res.json();
  } catch (err) {
    console.error("Error fetching verification:", err);
    return null;
  }
}


export interface ScreeningSignal {
  signal_type: string;
  description: string;
  matched_text: string | null;
  severity: "low" | "medium" | "high";
}

export interface ScreeningResult {
  risk_level: "Low" | "Medium" | "High";
  signals: ScreeningSignal[];
  pattern_matches: string[];
  needs_deep_verify: boolean;
  recommended_action: string;
  screened_urls: string[];
  detected_institutions: string[];
}

export async function screenContent(
  content: string,
  contentType: "message" | "url" | "email" | "notification" = "message",
): Promise<ScreeningResult | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/screen/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content, content_type: contentType }),
      cache: "no-store",
    });
    if (!res.ok) return null;
    return res.json();
  } catch (err) {
    console.error("Error screening content:", err);
    return null;
  }
}
