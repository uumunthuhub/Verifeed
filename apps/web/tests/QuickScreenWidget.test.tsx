/**
 * Unit tests for QuickScreenWidget component.
 *
 * Tests: initial render, textarea placeholder, example message clicks,
 * Screen button state, Clear button, and API mock integration.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { QuickScreenWidget } from "../components/QuickScreenWidget";

// Mock the API module
vi.mock("@/lib/api", () => ({
  screenContent: vi.fn(),
}));

import { screenContent } from "../lib/api";
const mockScreenContent = vi.mocked(screenContent);

const LOW_RISK_RESULT = {
  risk_level: "Low" as const,
  signals: [],
  pattern_matches: [],
  needs_deep_verify: false,
  recommended_action: "No immediate concerns detected.",
  screened_urls: [],
  detected_institutions: [],
};

const HIGH_RISK_RESULT = {
  risk_level: "High" as const,
  signals: [
    {
      signal_type: "monetary_request",
      description: "Money transfer request detected",
      matched_text: "send money",
      severity: "high" as const,
    },
    {
      signal_type: "suspicious_url",
      description: "Suspicious URL detected",
      matched_text: "http://bit.ly/scam",
      severity: "high" as const,
    },
  ],
  pattern_matches: ["monetary_request", "suspicious_url"],
  needs_deep_verify: true,
  recommended_action: "Do not click any links or send money.",
  screened_urls: ["http://bit.ly/scam"],
  detected_institutions: ["Airtel Money"],
};

describe("QuickScreenWidget", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the Quick Screen heading", () => {
    render(<QuickScreenWidget />);
    expect(screen.getByText("Quick Screen")).toBeInTheDocument();
  });

  it("renders the Stage 1 subtitle", () => {
    render(<QuickScreenWidget />);
    expect(screen.getByText(/Instant Stage 1 scan/i)).toBeInTheDocument();
  });

  it("renders the textarea with placeholder", () => {
    render(<QuickScreenWidget />);
    expect(
      screen.getByPlaceholderText(/Paste a suspicious message/i),
    ).toBeInTheDocument();
  });

  it("Screen Content button is disabled when textarea is empty", () => {
    render(<QuickScreenWidget />);
    expect(
      screen.getByRole("button", { name: /Screen Content/i }),
    ).toBeDisabled();
  });

  it("Screen Content button is enabled after typing", () => {
    render(<QuickScreenWidget />);
    const textarea = screen.getByPlaceholderText(/Paste a suspicious message/i);
    fireEvent.change(textarea, {
      target: { value: "Congratulations! You have won MK500,000." },
    });
    expect(
      screen.getByRole("button", { name: /Screen Content/i }),
    ).not.toBeDisabled();
  });

  it("shows example messages initially (before any text is entered)", () => {
    render(<QuickScreenWidget />);
    expect(screen.getByText("Try an example:")).toBeInTheDocument();
  });

  it("hides example messages after text is entered", () => {
    render(<QuickScreenWidget />);
    const textarea = screen.getByPlaceholderText(/Paste a suspicious message/i);
    fireEvent.change(textarea, { target: { value: "Some content" } });
    expect(screen.queryByText("Try an example:")).not.toBeInTheDocument();
  });

  it("shows Clear button after text is entered", () => {
    render(<QuickScreenWidget />);
    const textarea = screen.getByPlaceholderText(/Paste a suspicious message/i);
    fireEvent.change(textarea, { target: { value: "Something here" } });
    expect(screen.getByRole("button", { name: /Clear/i })).toBeInTheDocument();
  });

  it("clicking Clear resets the textarea", () => {
    render(<QuickScreenWidget />);
    const textarea = screen.getByPlaceholderText(/Paste a suspicious message/i);
    fireEvent.change(textarea, { target: { value: "Text to clear" } });
    fireEvent.click(screen.getByRole("button", { name: /Clear/i }));
    expect((textarea as HTMLTextAreaElement).value).toBe("");
  });

  it("shows Low Risk badge after successful low-risk screening", async () => {
    mockScreenContent.mockResolvedValueOnce(LOW_RISK_RESULT);
    render(<QuickScreenWidget />);
    const textarea = screen.getByPlaceholderText(/Paste a suspicious message/i);
    fireEvent.change(textarea, {
      target: { value: "Your appointment is confirmed." },
    });
    fireEvent.click(screen.getByRole("button", { name: /Screen Content/i }));
    await waitFor(() =>
      expect(screen.getByText("Low Risk")).toBeInTheDocument(),
    );
  });

  it("shows High Risk badge after high-risk screening", async () => {
    mockScreenContent.mockResolvedValueOnce(HIGH_RISK_RESULT);
    render(<QuickScreenWidget />);
    const textarea = screen.getByPlaceholderText(/Paste a suspicious message/i);
    fireEvent.change(textarea, {
      target: { value: "URGENT: send money now! http://bit.ly/scam" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Screen Content/i }));
    await waitFor(() =>
      expect(screen.getByText("High Risk")).toBeInTheDocument(),
    );
  });

  it("shows signal chips after screening", async () => {
    mockScreenContent.mockResolvedValueOnce(HIGH_RISK_RESULT);
    render(<QuickScreenWidget />);
    const textarea = screen.getByPlaceholderText(/Paste a suspicious message/i);
    fireEvent.change(textarea, {
      target: { value: "send money to bit.ly/scam" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Screen Content/i }));
    await waitFor(() =>
      expect(screen.getByText(/monetary request/i)).toBeInTheDocument(),
    );
  });

  it("shows error message when API returns null", async () => {
    mockScreenContent.mockResolvedValueOnce(null);
    render(<QuickScreenWidget />);
    const textarea = screen.getByPlaceholderText(/Paste a suspicious message/i);
    fireEvent.change(textarea, { target: { value: "Some suspicious text" } });
    fireEvent.click(screen.getByRole("button", { name: /Screen Content/i }));
    await waitFor(() =>
      expect(
        screen.getByText(/Could not connect to screening service/i),
      ).toBeInTheDocument(),
    );
  });
});
