/**
 * Unit tests for VerdictBadge component.
 * Tests all 5 verdict states for correct icon, text, and CSS class presence.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { VerdictBadge } from "../components/VerdictBadge";

describe("VerdictBadge", () => {
  it("renders 'Confirmed Scam' with scam icon", () => {
    render(<VerdictBadge verdict="Confirmed Scam" />);
    expect(screen.getByText("Confirmed Scam")).toBeInTheDocument();
    expect(screen.getByText("🛑")).toBeInTheDocument();
  });

  it("renders 'Confirmed' with check icon", () => {
    render(<VerdictBadge verdict="Confirmed" />);
    expect(screen.getByText("Confirmed")).toBeInTheDocument();
    expect(screen.getByText("✅")).toBeInTheDocument();
  });

  it("renders 'Unconfirmed' with warning icon", () => {
    render(<VerdictBadge verdict="Unconfirmed" />);
    expect(screen.getByText("Unconfirmed")).toBeInTheDocument();
    expect(screen.getByText("⚠️")).toBeInTheDocument();
  });

  it("renders 'Disputed / False' with disputed icon", () => {
    render(<VerdictBadge verdict="Disputed / False" />);
    expect(screen.getByText("Disputed / False")).toBeInTheDocument();
    expect(screen.getByText("🚫")).toBeInTheDocument();
  });

  it("renders 'No Coverage Found' as default with unknown icon", () => {
    render(<VerdictBadge verdict="No Coverage Found" />);
    expect(screen.getByText("No Coverage Found")).toBeInTheDocument();
    expect(screen.getByText("❓")).toBeInTheDocument();
  });

  it("renders small size variant", () => {
    render(<VerdictBadge verdict="Confirmed" size="sm" />);
    const badge = screen.getByText("Confirmed").parentElement;
    expect(badge?.className).toContain("text-xs");
  });

  it("renders large size variant", () => {
    render(<VerdictBadge verdict="Confirmed" size="lg" />);
    const badge = screen.getByText("Confirmed").parentElement;
    expect(badge?.className).toContain("text-base");
  });
});
