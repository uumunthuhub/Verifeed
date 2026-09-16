/**
 * Unit tests for EvidenceCard component.
 * Tests rendering of source type badges, outlet, title, optional snippet, and external link.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { EvidenceCard } from "../components/EvidenceCard";
import type { EvidenceSource } from "../components/EvidenceCard";

const makeSrc = (overrides?: Partial<EvidenceSource>): EvidenceSource => ({
  title: "Test Article Headline",
  outlet: "Reuters",
  url: "https://reuters.com/test",
  type: "News Article",
  ...overrides,
});

describe("EvidenceCard", () => {
  it("renders the title and outlet", () => {
    render(<EvidenceCard source={makeSrc()} />);
    expect(screen.getByText("Test Article Headline")).toBeInTheDocument();
    expect(screen.getByText("Reuters")).toBeInTheDocument();
  });

  it("renders a 'News Article' type badge", () => {
    render(<EvidenceCard source={makeSrc({ type: "News Article" })} />);
    expect(screen.getByText("News Article")).toBeInTheDocument();
  });

  it("renders an 'Official Institutional Alert' type badge", () => {
    render(
      <EvidenceCard
        source={makeSrc({
          type: "Official Institutional Alert",
          outlet: "Standard Bank",
        })}
      />,
    );
    expect(
      screen.getByText("Official Institutional Alert"),
    ).toBeInTheDocument();
  });

  it("renders a 'Fact Checker Rating' type badge", () => {
    render(<EvidenceCard source={makeSrc({ type: "Fact Checker Rating" })} />);
    expect(screen.getByText("Fact Checker Rating")).toBeInTheDocument();
  });

  it("renders an external link when url is provided", () => {
    render(
      <EvidenceCard source={makeSrc({ url: "https://reuters.com/story" })} />,
    );
    const link = screen.getByRole("link", { name: /Open primary source/i });
    expect(link).toHaveAttribute("href", "https://reuters.com/story");
    expect(link).toHaveAttribute("target", "_blank");
  });

  it("does not render an external link when url is omitted", () => {
    render(<EvidenceCard source={makeSrc({ url: undefined })} />);
    const links = screen.queryAllByRole("link");
    expect(links).toHaveLength(0);
  });

  it("renders a snippet when provided", () => {
    render(
      <EvidenceCard source={makeSrc({ snippet: "Key snippet text here" })} />,
    );
    expect(screen.getByText(/Key snippet text here/)).toBeInTheDocument();
  });

  it("does not render a snippet section when snippet is omitted", () => {
    render(<EvidenceCard source={makeSrc({ snippet: undefined })} />);
    expect(screen.queryByText(/snippet/i)).not.toBeInTheDocument();
  });

  it("renders fallback 'Evidence Source' badge for unknown type", () => {
    render(<EvidenceCard source={makeSrc({ type: undefined })} />);
    expect(screen.getByText("Evidence Source")).toBeInTheDocument();
  });
});
