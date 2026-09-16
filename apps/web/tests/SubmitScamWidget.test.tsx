/**
 * Unit tests for SubmitScamWidget component.
 * Tests rendering of the report form, textarea, file attachment button,
 * submit button state, success/error message display.
 * Network calls are mocked — submitScamReport is not invoked in unit tests.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { SubmitScamWidget } from "../components/SubmitScamWidget";

// Mock the API module so no real network calls are made
vi.mock("@/lib/api", () => ({
  submitScamReport: vi.fn().mockResolvedValue(true),
}));

describe("SubmitScamWidget", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the report heading", () => {
    render(<SubmitScamWidget />);
    expect(
      screen.getByRole("heading", { name: /Report a New Scam/i }),
    ).toBeInTheDocument();
  });

  it("renders the description text", () => {
    render(<SubmitScamWidget />);
    expect(
      screen.getByText(/Received a suspicious SMS, email, or post/i),
    ).toBeInTheDocument();
  });

  it("renders the textarea with placeholder", () => {
    render(<SubmitScamWidget />);
    expect(
      screen.getByPlaceholderText(/Paste the exact text of the message/i),
    ).toBeInTheDocument();
  });

  it("renders the Attach Screenshot button", () => {
    render(<SubmitScamWidget />);
    expect(
      screen.getByRole("button", { name: /Attach Screenshot/i }),
    ).toBeInTheDocument();
  });

  it("renders the Submit Report button", () => {
    render(<SubmitScamWidget />);
    expect(
      screen.getByRole("button", { name: /Submit Report/i }),
    ).toBeInTheDocument();
  });

  it("Submit Report button is disabled when textarea is empty and no file attached", () => {
    render(<SubmitScamWidget />);
    const submitBtn = screen.getByRole("button", { name: /Submit Report/i });
    expect(submitBtn).toBeDisabled();
  });

  it("Submit Report button is enabled after typing in the textarea", () => {
    render(<SubmitScamWidget />);
    const textarea = screen.getByPlaceholderText(
      /Paste the exact text of the message/i,
    );
    fireEvent.change(textarea, {
      target: { value: "You won a free iPhone! Call 0999123456 to claim." },
    });
    const submitBtn = screen.getByRole("button", { name: /Submit Report/i });
    expect(submitBtn).not.toBeDisabled();
  });

  it("clears textarea content when the user deletes all text", () => {
    render(<SubmitScamWidget />);
    const textarea = screen.getByPlaceholderText(
      /Paste the exact text of the message/i,
    );
    fireEvent.change(textarea, { target: { value: "Some scam text" } });
    fireEvent.change(textarea, { target: { value: "" } });
    expect((textarea as HTMLTextAreaElement).value).toBe("");
  });

  it("does not render success message initially", () => {
    render(<SubmitScamWidget />);
    expect(
      screen.queryByText(/Your report has been submitted/i),
    ).not.toBeInTheDocument();
  });

  it("does not render error message initially", () => {
    render(<SubmitScamWidget />);
    expect(
      screen.queryByText(/Failed to submit report/i),
    ).not.toBeInTheDocument();
  });
});
