const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 2 });
  await p.goto('file://' + process.argv[2]);
  await p.evaluate(async () => { await document.fonts.ready; });
  await p.waitForTimeout(1500);
  for (const id of ['how', 'vs']) await (await p.$('#' + id)).screenshot({ path: `${id}.png` });
  await b.close();
})();
