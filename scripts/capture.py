"""Capture a brand: python scripts/capture.py <slug> <home_url> [pdp_url]
Writes site/img/<slug>/<component>-<device>.jpg and data/captures/<slug>.json"""
import asyncio, json, sys, os, io
from playwright.async_api import async_playwright
from PIL import Image
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'
KILL='''()=>{const vw=innerWidth,vh=innerHeight;document.querySelectorAll('body *').forEach(e=>{const s=getComputedStyle(e);if(s.position!='fixed')return;const r=e.getBoundingClientRect();
if(r.width*r.height<vw*vh*0.25)return;if(s.display=='none'||s.visibility=='hidden')return;e.style.setProperty('display','none','important')});
document.querySelectorAll('[class*=klaviyo],[id*=klaviyo],[class*=popup i],[id*=popup i],[class*=newsletter-modal],iframe[src*=gokwik]').forEach(e=>{const r=e.getBoundingClientRect();if(r.width*r.height>vw*vh*0.25)e.style.setProperty('display','none','important')});
document.body.style.overflow='';document.documentElement.style.overflow='';}'''
FIND_GRID='''()=>{const as=[...document.querySelectorAll('a[href*="/products/"]')].filter(a=>a.querySelector('img')&&a.getBoundingClientRect().width>60);
for(const a of as){let e=a;for(let i=0;i<12&&e;i++){e=e.parentElement;if(!e)break;const n=new Set([...e.querySelectorAll('a[href*="/products/"]')].map(x=>x.getAttribute('href').split('?')[0])).size;
const r=e.getBoundingClientRect();if(n>=3&&r.height>200){return {y:r.top+scrollY,h:r.height}}}}return null}'''
FOOT='''()=>{const f=document.querySelector('footer,[class*=footer i]');if(!f)return null;const r=f.getBoundingClientRect();return {y:r.top+scrollY,h:r.height}}'''
HEAD='''()=>{let b=0;document.querySelectorAll('header,[class*=announcement i],[class*=header i]').forEach(e=>{const r=e.getBoundingClientRect();if(r.top<250&&r.height<300&&r.height>20)b=Math.max(b,r.bottom)});return b}'''
async def dismiss(p):
    for t in ['Accept','Accept all','Accept All','Got it','OK','Close','No thanks','×','✕']:
        try:
            l=p.get_by_role('button',name=t,exact=True)
            if await l.count(): await l.first.click(timeout=800)
        except Exception: pass
    try: await p.keyboard.press('Escape')
    except Exception: pass
    try: await p.evaluate(KILL)
    except Exception: pass
def save(png,path,maxw):
    im=Image.open(io.BytesIO(png)).convert('RGB')
    if im.width>maxw: im=im.resize((maxw,int(im.height*maxw/im.width)))
    im.save(path,quality=80,optimize=True)
async def clip(p,path,y,h,maxw):
    w=p.viewport_size['width']; h=max(80,min(h,p.viewport_size['height']*1.6))
    await p.evaluate(f'scrollTo(0,{max(0,y-10)})'); await p.wait_for_timeout(1800); await dismiss(p)
    sy=await p.evaluate('scrollY')
    png=await p.screenshot(full_page=True,clip={'x':0,'y':y,'width':w,'height':h}); save(png,path,maxw)
async def run(pw,slug,home,pdp,dev,out):
    b=await pw.chromium.launch()
    if dev=='desktop': ctx=await b.new_context(viewport={'width':1440,'height':900},user_agent=UA,locale='en-IN'); mw=1440
    else: ctx=await b.new_context(**pw.devices['iPhone 13'],locale='en-IN'); mw=390*2
    p=await ctx.new_page(); d=f'site/img/{slug}'; os.makedirs(d,exist_ok=True)
    async def ok(c): out.setdefault(c,[]).append(dev); print(slug,dev,c,'ok',flush=True)
    try:
        await p.goto(home,wait_until='domcontentloaded',timeout=60000); await p.wait_for_timeout(7000); await dismiss(p); await p.wait_for_timeout(800); await dismiss(p)
        await p.evaluate('scrollTo(0,0)'); await p.wait_for_timeout(1000)
        save(await p.screenshot(),f'{d}/hero-{dev}.jpg',mw); await ok('hero')
        hb=await p.evaluate(HEAD)
        if hb>30: save(await p.screenshot(clip={'x':0,'y':0,'width':p.viewport_size['width'],'height':min(hb+8,300)}),f'{d}/header-{dev}.jpg',mw); await ok('header')
        H=await p.evaluate('document.body.scrollHeight')
        for y in range(0,min(H,20000),700): await p.evaluate(f'scrollTo(0,{y})'); await p.wait_for_timeout(250)
        g=await p.evaluate(FIND_GRID)
        if g: await clip(p,f'{d}/product-card-{dev}.jpg',g['y'],g['h'],mw); await ok('product-card')
        f=await p.evaluate(FOOT)
        if f and f['h']>100: await clip(p,f'{d}/footer-{dev}.jpg',f['y'],f['h'],mw); await ok('footer')
        if not pdp:
            pdp=await p.evaluate('''()=>{const a=[...document.querySelectorAll('a[href*="/products/"]')].find(a=>a.querySelector('img'));return a&&a.href}''')
        if pdp:
            await p.goto(pdp,wait_until='domcontentloaded',timeout=60000); await p.wait_for_timeout(6000); await dismiss(p); await p.evaluate('scrollTo(0,0)'); await p.wait_for_timeout(800)
            save(await p.screenshot(),f'{d}/pdp-{dev}.jpg',mw); await ok('pdp')
            vh=p.viewport_size['height']
            await p.evaluate(f'scrollTo(0,{vh})'); await p.wait_for_timeout(1500); await dismiss(p)
            save(await p.screenshot(),f'{d}/pdp-details-{dev}.jpg',mw); await ok('pdp-details')
            if dev=='mobile':
                await p.evaluate(f'scrollTo(0,{vh*2.2})'); await p.wait_for_timeout(1500); await dismiss(p)
                save(await p.screenshot(),f'{d}/sticky-atc-{dev}.jpg',mw); await ok('sticky-atc')
            # reviews
            r=await p.evaluate('''()=>{const e=[...document.querySelectorAll('section,div')].find(e=>/review/i.test(e.id+' '+e.className)&&e.getBoundingClientRect().height>200);if(!e)return null;const r=e.getBoundingClientRect();return {y:r.top+scrollY,h:r.height}}''')
            if r: await clip(p,f'{d}/reviews-{dev}.jpg',r['y'],r['h'],mw); await ok('reviews')
            out.setdefault('_pdp',pdp)
    except Exception as e: print(slug,dev,'ERR',str(e)[:200],flush=True)
    await b.close()
async def main():
    slug,home=sys.argv[1],sys.argv[2]; pdp=sys.argv[3] if len(sys.argv)>3 else None
    out={}
    async with async_playwright() as pw:
        await asyncio.gather(run(pw,slug,home,pdp,'desktop',out),run(pw,slug,home,pdp,'mobile',out))
    os.makedirs('data/captures',exist_ok=True); json.dump(out,open(f'data/captures/{slug}.json','w'),indent=1)
asyncio.run(main())
