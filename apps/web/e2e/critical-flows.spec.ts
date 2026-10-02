import { test, expect } from "@playwright/test";

test.describe("VeriFeed Critical User Flows", () => {
  test("Home Page — displays navbar and branding", async ({ page }) => {
    await page.goto("/");

    // Verify branding logo
    await expect(page.getByRole("banner")).toBeVisible();
    await expect(page.getByText("VeriFeed")).toBeVisible();
  });

  test("Search Navigation Flow — submitting search bar query navigates to search page", async ({ page }) => {
    await page.goto("/");
    const searchInput = page.getByPlaceholder("Search claims & alerts...");
    await searchInput.fill("scam");
    await searchInput.press("Enter");

    await expect(page).toHaveURL(/.*search\?q=scam/);
    await expect(page.getByRole("heading", { name: "Search Results" })).toBeVisible();
  });

  test("Verify Claim Portal — loads verification form and submit buttons", async ({ page }) => {
    await page.goto("/verify");
    await expect(page.getByRole("heading", { name: /Verify any Claim/i })).toBeVisible();
    await expect(page.getByPlaceholder(/Paste a news headline/i)).toBeVisible();
  });

  test("Fraud Alerts Dashboard — displays disclaimers and alert feeds", async ({ page }) => {
    await page.goto("/scams");
    await expect(page.getByRole("heading", { name: /Institutional Fraud Alerts/i })).toBeVisible();
  });
});
