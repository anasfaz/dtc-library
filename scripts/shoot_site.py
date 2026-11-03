import asyncio
from playwright.async_api import async_playwright
async def m():
  async with async_playwright() as pw:
    b=await pw.chromium.launch()
    for name,kw in [('desktop',dict(viewport={'width':1440,'height':900})),('mobile',pw.devices['iPhone 13'])]:
      p=await (await b.new_context(**kw)).new_page(); await p.goto('http://localhost:8765/'); await p.wait_for_timeout(3500)
      await p.screenshot(path=f'/workspace/dtc-library/screens/site-{name}.png')
      await p.fill('#q','sticky'); await p.wait_for_timeout(1500); await p.screenshot(path=f'/workspace/dtc-library/screens/site-search-{name}.png')
      await p.goto('http://localhost:8765/#/brand/superbottoms'); await p.wait_for_timeout(2500); await p.screenshot(path=f'/workspace/dtc-library/screens/site-brand-{name}.png')
    await b.close()
asyncio.run(m())
