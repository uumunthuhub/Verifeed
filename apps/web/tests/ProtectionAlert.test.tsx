/**
 * Unit tests for ProtectionAlert component.
 *
 * Tests: rendering for High/Medium risk, signal chips,
 * dismiss behavior, verify CTA link, and absence for Low risk.
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { ProtectionAlert } from "../components/ProtectionAlert";
import type { ScreeningResult } from "../lib/api";

const HIGH_RISK_RESULT: ScreeningResult = {
  risk_level: "High",
  signals: [
    {
      signal_type: "monetary_request",
      description: "Money transfer request detected",
      matched_text: "send money",
      severity: "high",
    },
    {
      signal_type: "suspicious_url",
      description: "Suspicious URL",
      matched_text: "http://bit.ly/fake",
      severity: "high",
    },
  ],
  pattern_matches: ["monetary_request", "suspicious_url"],
  needs_deep_verify: true,
  recommended_action:
    "Do not click any links or send money. Contact the institution directly.",
  screened_urls: ["http://bit.ly/fake"],
  detected_institutions: ["Airtel Money"],
};

const MEDIUM_RISK_RESULT: ScreeningResult = {
  risk_level: "Medium",
  signals: [
    {
      signal_type: "urgency_language",
      description: "Urgency language detected",
      matched_text: "act now",
      severity: "medium",
    },
  ],
  pattern_matches: ["urgency_language"],
  needs_deep_verify: true,
  recommended_action: "Proceed with caution. Verify before acting.",
  screened_urls: [],
  detected_institutions: [],
};

describe("ProtectionAlert", () => {
  it("renders HIGH RISK label for high risk result", () => {
    render(
      <ProtectionAlert
        result={HIGH_RISK_RESULT}
        content="Send money to bit.ly/fake"
        onDismiss={vi.fn()}
      />,
    );
    expect(screen.getByText("HIGH RISK")).toBeInTheDocument();
  });

  it("renders SUSPICIOUS label for medium risk result", () => {
    render(
      <ProtectionAlert
        result={MEDIUM_RISK_RESULT}
        content="Act now!"
        onDismiss={vi.fn()}
      />,
    );
    expect(screen.getByText("SUSPICIOUS")).toBeInTheDocument();
  });

  it("renders the signal count", () => {
    render(
      <ProtectionAlert
        result={HIGH_RISK_RESULT}
        content="test"
        onDismiss={vi.fn()}
      />,
    );
    expect(screen.getByText(/2 signals detected/i)).toBeInTheDocument();
  });

  it("renders the recommended action text", () => {
    render(
      <ProtectionAlert
        result={HIGH_RISK_RESULT}
        content="test"
        onDismiss={vi.fn()}
      />,
    );
    expect(
      screen.getByText(/Do not click any links or send money/i),
    ).toBeInTheDocument();
  });

  it("renders the detected institutions", () => {
    render(
      <ProtectionAlert
        result={HIGH_RISK_RESULT}
        content="test"
        onDismiss={vi.fn()}
      />,
    );
    expect(screen.getByText(/Airtel Money/)).toBeInTheDocument();
  });

  it("renders the Stage 1 disclaimer note", () => {
    render(
      <ProtectionAlert
        result={HIGH_RISK_RESULT}
        content="test"
        onDismiss={vi.fn()}
      />,
    );
    expect(screen.getByText(/Stage 1 signal scan only/i)).toBeInTheDocument();
  });

  it("calls onDismiss when dismiss button is clicked", () => {
    const onDismiss = vi.fn();
    render(
      <ProtectionAlert
        result={HIGH_RISK_RESULT}
        content="test"
        onDismiss={onDismiss}
      />,
    );
    fireEvent.click(screen.getByLabelText("Dismiss alert"));
    expect(onDismiss).toHaveBeenCalledOnce();
  });

  it("hides the alert after dismissal", () => {
    const { container } = render(
      <ProtectionAlert
        result={HIGH_RISK_RESULT}
        content="test"
        onDismiss={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByLabelText("Dismiss alert"));
    expect(container.firstChild).toBeNull();
  });

  it("renders the Verify with VeriFeed button", () => {
    render(
      <ProtectionAlert
        result={HIGH_RISK_RESULT}
        content="suspicious text"
        onDismiss={vi.fn()}
      />,
    );
    expect(
      screen.getByRole("button", { name: /Verify with VeriFeed/i }),
    ).toBeInTheDocument();
  });

  it("renders URL count badge when screened URLs are present", () => {
    render(
      <ProtectionAlert
        result={HIGH_RISK_RESULT}
        content="test"
        onDismiss={vi.fn()}
      />,
    );
    expect(screen.getByText(/1 URL flagged/i)).toBeInTheDocument();
  });

  it("does not render URL badge when no URLs were screened", () => {
    render(
      <ProtectionAlert
        result={MEDIUM_RISK_RESULT}
        content="test"
        onDismiss={vi.fn()}
      />,
    );
    expect(screen.queryByText(/URL flagged/i)).not.toBeInTheDocument();
  });
});
