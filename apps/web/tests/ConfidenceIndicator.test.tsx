/**
 * Unit tests for ConfidenceIndicator component.
 * Tests score clamping, label thresholds, and percentage display.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { ConfidenceIndicator } from "../components/ConfidenceIndicator";

describe("ConfidenceIndicator", () => {
  it("shows 'Strong Evidence' label for score >= 0.85", () => {
    render(<ConfidenceIndicator score={0.95} />);
    expect(screen.getByText(/Strong Evidence/)).toBeInTheDocument();
    expect(screen.getByText(/95%/)).toBeInTheDocument();
  });

  it("shows 'Moderate Evidence' label for score between 0.60 and 0.84", () => {
    render(<ConfidenceIndicator score={0.7} />);
    expect(screen.getByText(/Moderate Evidence/)).toBeInTheDocument();
    expect(screen.getByText(/70%/)).toBeInTheDocument();
  });

  it("shows 'Limited Evidence' label for score below 0.60", () => {
    render(<ConfidenceIndicator score={0.3} />);
    expect(screen.getByText(/Limited Evidence/)).toBeInTheDocument();
    expect(screen.getByText(/30%/)).toBeInTheDocument();
  });

  it("clamps score above 1.0 to 100%", () => {
    render(<ConfidenceIndicator score={1.5} />);
    expect(screen.getByText(/100%/)).toBeInTheDocument();
  });

  it("clamps score below 0 to 0%", () => {
    render(<ConfidenceIndicator score={-0.5} />);
    expect(screen.getByText(/0%/)).toBeInTheDocument();
  });

  it("renders the progress bar element", () => {
    const { container } = render(<ConfidenceIndicator score={0.75} />);
    // The progress fill div has an inline style with width
    const bars = container.querySelectorAll("[style*='width']");
    expect(bars.length).toBeGreaterThan(0);
  });
});
