"""Screens of the local preview -> screens/redesign-*.png  (python3 scripts/shoot_redesign.py [base_url])"""
import asyncio,sys
from playwright.async_api import async_playwright
B=sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8765/'
O='/workspace/dtc-library/screens/'
async def m():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); errs=[]
    p=await (await b.new_context(viewport={'width':1440,'height':900})).new_page()
    p.on('pageerror',lambda e:errs.append(str(e))); p.on('console',lambda c:c.type=='error' and errs.append(c.text))
    async def go(h,f,wait=2500,full=False):
      await p.goto(B+h); await p.wait_for_timeout(wait); await p.screenshot(path=O+f,full_page=full)
    await go('#/','redesign-home.png',3500)
    await go('#/product','redesign-product.png')
    await go('#/menu','redesign-menu.png')
    await go('#/brand/shumee','redesign-brand.png',3500)
    await p.goto(B+'#/product'); await p.wait_for_timeout(2000); await p.click('.grid .thumb >> nth=0'); await p.wait_for_timeout(2500)
    await p.screenshot(path=O+'redesign-lightbox.png'); print('lb url',p.url)
    await p.keyboard.press('Escape'); await p.wait_for_timeout(800); print('after esc',p.url, await p.is_hidden('#lb'))
    await go('#/brands','redesign-brands.png'); await go('#/agencies','redesign-agencies.png')
    await p.goto(B+'#/menu'); await p.fill('#q','sticky'); await p.wait_for_timeout(1500); print('search url',p.url, await p.inner_text('.fr .n'))
    await p.screenshot(path=O+'redesign-search.png')
    m=await (await b.new_context(**pw.devices['iPhone 13'])).new_page(); m.on('pageerror',lambda e:errs.append(str(e)))
    await m.goto(B+'#/product'); await m.wait_for_timeout(3000); await m.screenshot(path=O+'redesign-mobile.png')
    await m.click('.grid .thumb >> nth=1'); await m.wait_for_timeout(2000); await m.screenshot(path=O+'redesign-mobile-lightbox.png')
    print('errors',errs); await b.close()
asyncio.run(m())
