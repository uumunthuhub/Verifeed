/**
 * Unit tests for VerdictBadge component.
 * Tests all 5 verdict states for correct icon, text, and CSS class presence.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { VerdictBadge } from "../components/VerdictBadge";

describe("VerdictBadge", () => {
  it("renders 'Confirmed Scam' mapped to High Risk Scam", () => {
    render(<VerdictBadge verdict="Confirmed Scam" />);
    expect(screen.getByText("High Risk Scam")).toBeInTheDocument();
    expect(screen.getByText("🚨")).toBeInTheDocument();
  });

  it("renders 'Confirmed' mapped to Verified Authentic", () => {
    render(<VerdictBadge verdict="Confirmed" />);
    expect(screen.getByText("Verified Authentic")).toBeInTheDocument();
    expect(screen.getByText("✅")).toBeInTheDocument();
  });

  it("renders 'Unconfirmed' mapped to Pending Verification", () => {
    render(<VerdictBadge verdict="Unconfirmed" />);
    expect(screen.getByText("Pending Verification")).toBeInTheDocument();
    expect(screen.getByText("🕐")).toBeInTheDocument();
  });

  it("renders 'Disputed / False' mapped to Verified False", () => {
    render(<VerdictBadge verdict="Disputed / False" />);
    expect(screen.getByText("Verified False")).toBeInTheDocument();
    expect(screen.getByText("🚫")).toBeInTheDocument();
  });

  it("renders 'No Coverage Found' mapped to Unverified", () => {
    render(<VerdictBadge verdict="No Coverage Found" />);
    expect(screen.getByText("Unverified")).toBeInTheDocument();
    expect(screen.getByText("❓")).toBeInTheDocument();
  });

  it("renders small size variant", () => {
    render(<VerdictBadge verdict="Confirmed" size="sm" />);
    const badge = screen.getByText("Verified Authentic").parentElement;
    expect(badge?.className).toContain("text-xs");
  });

  it("renders large size variant", () => {
    render(<VerdictBadge verdict="Confirmed" size="lg" />);
    const badge = screen.getByText("Verified Authentic").parentElement;
    expect(badge?.className).toContain("text-base");
  });
});

