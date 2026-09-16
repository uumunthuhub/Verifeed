/**
 * Unit tests for VerdictFirstResult component.
 * Tests rendering of the dual-verdict display (claim + authenticity),
 * risk level badge, confidence indicator, summary, guidance card,
 * extracted entities, and evidence list.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { VerdictFirstResult } from "../components/VerdictFirstResult";
import type { EvidenceSource } from "../components/EvidenceCard";

const baseProps = {
  riskLevel: "High" as const,
  confidenceScore: 0.9,
  summary: "Official scam alerts from Airtel Money confirm this is fraudulent.",
  sources: [] as EvidenceSource[],
  recommendedActions: [
    {
      action: "Do not send money or share personal information",
      priority: "critical" as const,
      reason: "High-risk message detected",
    },
  ],
};

describe("VerdictFirstResult", () => {
  it("renders the VERDICT section heading", () => {
    render(<VerdictFirstResult {...baseProps} />);
    expect(screen.getByText("VERDICT")).toBeInTheDocument();
  });

  it("renders the summary text", () => {
    render(<VerdictFirstResult {...baseProps} />);
    expect(
      screen.getByText(
        "Official scam alerts from Airtel Money confirm this is fraudulent.",
      ),
    ).toBeInTheDocument();
  });

  it("renders the WHY? section heading", () => {
    render(<VerdictFirstResult {...baseProps} />);
    expect(screen.getByText("WHY?")).toBeInTheDocument();
  });

  it("renders the claim verdict when provided", () => {
    render(
      <VerdictFirstResult {...baseProps} claimVerdict="False" />,
    );
    expect(screen.getByText("Claim Verdict")).toBeInTheDocument();
  });

  it("renders the message authenticity verdict when provided", () => {
    render(
      <VerdictFirstResult
        {...baseProps}
        messageAuthenticityVerdict="Suspicious"
      />,
    );
    expect(screen.getByText("Message Authenticity")).toBeInTheDocument();
  });

  it("does not render claim verdict section when omitted", () => {
    render(<VerdictFirstResult {...baseProps} />);
    expect(screen.queryByText("Claim Verdict")).not.toBeInTheDocument();
  });

  it("does not render message authenticity section when omitted", () => {
    render(<VerdictFirstResult {...baseProps} />);
    expect(screen.queryByText("Message Authenticity")).not.toBeInTheDocument();
  });

  it("renders the High risk level badge", () => {
    render(<VerdictFirstResult {...baseProps} riskLevel="High" />);
    // Risk level appears in both the verdict card and the guidance card
    const highBadges = screen.getAllByText("High");
    expect(highBadges.length).toBeGreaterThan(0);
  });

  it("renders the Low risk level badge", () => {
    render(<VerdictFirstResult {...baseProps} riskLevel="Low" />);
    const lowBadges = screen.getAllByText("Low");
    expect(lowBadges.length).toBeGreaterThan(0);
  });

  it("renders the recommended action text", () => {
    render(<VerdictFirstResult {...baseProps} />);
    expect(
      screen.getByText("Do not send money or share personal information"),
    ).toBeInTheDocument();
  });

  it("renders the EVIDENCE section when sources are provided", () => {
    const sources: EvidenceSource[] = [
      {
        title: "Airtel Money warns about fake promotions",
        outlet: "Airtel Money",
        url: "https://airtel.mw/alerts/fake-promotions",
        type: "Official Institutional Alert",
      },
    ];
    render(<VerdictFirstResult {...baseProps} sources={sources} />);
    expect(screen.getByText("EVIDENCE")).toBeInTheDocument();
    expect(screen.getByText("1 sources")).toBeInTheDocument();
  });

  it("does not render the EVIDENCE section when sources array is empty", () => {
    render(<VerdictFirstResult {...baseProps} sources={[]} />);
    expect(screen.queryByText("EVIDENCE")).not.toBeInTheDocument();
  });

  it("renders the extracted entities section when provided", () => {
    render(
      <VerdictFirstResult
        {...baseProps}
        extractedEntities={{
          sender: "AIRTELMW",
          institution_names: ["Airtel Money"],
          phone_numbers: ["+265999123456"],
          urls: ["http://bit.ly/fakeclaim"],
        }}
      />,
    );
    expect(screen.getByText("EXTRACTED INFORMATION")).toBeInTheDocument();
    expect(screen.getByText("AIRTELMW")).toBeInTheDocument();
    expect(screen.getByText("Airtel Money")).toBeInTheDocument();
    expect(screen.getByText("+265999123456")).toBeInTheDocument();
    expect(screen.getByText("1 detected")).toBeInTheDocument();
  });

  it("does not render extracted entities section when not provided", () => {
    render(<VerdictFirstResult {...baseProps} />);
    expect(
      screen.queryByText("EXTRACTED INFORMATION"),
    ).not.toBeInTheDocument();
  });

  it("renders multiple extracted institution names with overflow count", () => {
    render(
      <VerdictFirstResult
        {...baseProps}
        extractedEntities={{
          institution_names: ["Airtel Money", "Standard Bank", "RBM"],
        }}
      />,
    );
    // "Airtel Money" appears in both the summary and the entity chip
    const airtelElements = screen.getAllByText(/Airtel Money/);
    expect(airtelElements.length).toBeGreaterThan(0);
    // The overflow badge "+2" should be present
    expect(screen.getByText(/\+2/)).toBeInTheDocument();
  });
});
