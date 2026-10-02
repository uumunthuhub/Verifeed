import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { ReportAskAgent } from "../components/ReportAskAgent";

describe("ReportAskAgent", () => {
  const baseProps = {
    reportId: 42,
    query: "Standard Bank collateral free instant WhatsApp loan promo",
    riskLevel: "High" as const,
    verdict: "Confirmed Scam",
    summary: "Official alerts from Standard Bank confirm this is a fraudulent message.",
  };

  it("renders the header and title for the Report AI Assistant", () => {
    render(<ReportAskAgent {...baseProps} />);
    expect(screen.getByText("Ask VeriFeed AI Assistant")).toBeInTheDocument();
    expect(screen.getByText(/Report #42/)).toBeInTheDocument();
    expect(screen.getByText("High Risk")).toBeInTheDocument();
  });

  it("renders the initial welcome message with report context", () => {
    render(<ReportAskAgent {...baseProps} />);
    expect(screen.getByText(/VeriFeed AI Verification Assistant/)).toBeInTheDocument();
    expect(screen.getAllByText(/High Risk/).length).toBeGreaterThan(0);
  });


  it("renders suggested prompt chips", () => {
    render(<ReportAskAgent {...baseProps} />);
    expect(screen.getByText("Suggested Questions:")).toBeInTheDocument();
    expect(
      screen.getByText(/What specific red flags were found in this message\?/)
    ).toBeInTheDocument();
  });

  it("allows user to type into the input field", () => {
    render(<ReportAskAgent {...baseProps} />);
    const input = screen.getByPlaceholderText(
      /Ask anything about Report #42/
    ) as HTMLInputElement;
    fireEvent.change(input, { target: { value: "Who can I contact?" } });
    expect(input.value).toBe("Who can I contact?");
  });
});
