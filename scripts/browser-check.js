// Playwright CLI run-code script. Uses a real extraction (token charges apply).
async (page) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.reload();
  await page
    .locator("input[type=file]")
    .setInputFiles("examples/cuestionario-es.pdf");
  await page
    .getByRole("button", { name: "Extraer cuestionario →", exact: true })
    .click();
  await page
    .getByRole("heading", {
      name: "Cuestionario ficticio de hábitos y lógica",
      exact: true,
    })
    .waitFor({ timeout: 90000 });
  if (!(await page.locator("pre").isVisible()))
    throw new Error("The JSON result should be visible immediately, without a tab switch");
  const result = JSON.parse(await page.locator("pre").innerText());
  if (result.total_items !== 6 || result.items.length !== 6)
    throw new Error("Expected six items");
  if (result.items[3].respuesta_correcta !== null)
    throw new Error("An unmarked answer was invented");
  const downloadEvent = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Descargar JSON ↓", exact: true })
    .click();
  const download = await downloadEvent;
  await download.saveAs("output/browser-result.json");
  await page.screenshot({ path: "output/ui-result.png", fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  if (
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)
  )
    throw new Error("Mobile overflow");
  await page.screenshot({ path: "output/ui-mobile.png", fullPage: true });
  await page
    .locator("input[type=file]")
    .setInputFiles({
      name: "invalid.txt",
      mimeType: "text/plain",
      buffer: Buffer.from("not a questionnaire"),
    });
  await page
    .getByRole("button", { name: "Extraer cuestionario →", exact: true })
    .click();
  await page
    .getByRole("alert")
    .filter({ hasText: "Formato inválido" })
    .waitFor();
  return "PASS: real PDF upload, six items, JSON view/download, mobile layout and invalid-format error";
}
