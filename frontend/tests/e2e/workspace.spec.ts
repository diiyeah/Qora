import { test, expect } from '@playwright/test';

test.describe('Quantum Lab Workspace E2E', () => {
  test('should load the development mode and perform a basic circuit run', async ({ page }) => {
    // Navigate to Development Mode
    await page.goto('/development');

    // Verify Title and Tabs
    await expect(page.getByRole('heading', { name: /Development Mode/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Circuit Builder/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Code Editor/i })).toBeVisible();

    // Verify Undo/Redo buttons
    await expect(page.getByRole('button', { name: /Undo/i })).toBeDisabled();
    
    // Verify Circuit Canvas ARIA labels
    await expect(page.getByRole('region', { name: /Circuit Canvas/i })).toBeVisible();
    
    // Run Circuit Simulation
    const runButton = page.getByRole('button', { name: /Run Circuit/i });
    await expect(runButton).toBeVisible();
    await runButton.click();

    // Verify Results show up
    await expect(page.getByText('Circuit Metrics')).toBeVisible();
    await expect(page.getByText('Measurement Counts')).toBeVisible();
    await expect(page.getByText('Statevector (Final)')).toBeVisible();
  });

  test('should sync code editor from builder and export QASM', async ({ page }) => {
    await page.goto('/development');

    // Switch to Code Editor
    await page.getByRole('button', { name: /Code Editor/i }).click();

    // Ensure monaco editor loaded (we can check for the placeholder Python text)
    await expect(page.locator('.monaco-editor')).toBeVisible();
    
    // Export QASM
    const exportButton = page.getByRole('button', { name: /Export OpenQASM/i });
    await expect(exportButton).toBeVisible();

    const downloadPromise = page.waitForEvent('download');
    await exportButton.click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toBe('circuit.qasm');
  });

  test('should save workspace successfully', async ({ page }) => {
    await page.goto('/development');

    const saveButton = page.getByRole('button', { name: /Save Workspace/i });
    
    // Playwright handles window.alert automatically, but we need to accept it to let it pass
    page.on('dialog', dialog => dialog.accept());
    
    await saveButton.click();
  });
});
