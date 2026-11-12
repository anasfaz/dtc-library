"""Capture ONE brand completely, every component as its own shot (desktop 1440x900 + iPhone 13).

  python3 scripts/capture.py <slug> <home_url> [pdp_url] [--collection URL] [--query WORD]
                             [--device desktop|mobile|both] [--only hero,header,...] [--checkout]

Writes site/img/<slug>/<component>-<device>.jpg and data/captures/<slug>.json (what was captured + the URLs used).
Components (keys from data/component_types.json):
  announcement-bar, header (separate clips), mega-menu (desktop: hover/click a nav item), mobile-nav (mobile: open burger),
  search (opened, empty), search-results (typed query: predictive results, else /search?q=), hero, product-card (clipped grid),
  category-tiles?, comparison / bundle-builder / quiz (by heading text), footer, collection (full PLP page),
  pdp, pdp-details, variant-selector, subscribe-save, delivery-check, sticky-atc (mobile), reviews, cart-drawer (after add to cart),
  free-gift (if visible in the drawer), cart-page (/cart), checkout (only with --checkout, never signs in / types / pays).
A component is only saved when it is actually detected and the shot is not blank. Nothing is invented."""
import asyncio, json, sys, os, io, re, argparse
from urllib.parse import urljoin, urlparse, quote
from playwright.async_api import async_playwright
from PIL import Image, ImageStat
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'
KILL='''()=>{const vw=innerWidth,vh=innerHeight;document.querySelectorAll('body *').forEach(e=>{const s=getComputedStyle(e);if(s.position!='fixed')return;const r=e.getBoundingClientRect();
const iw=Math.max(0,Math.min(r.right,vw)-Math.max(r.left,0)),ih=Math.max(0,Math.min(r.bottom,vh)-Math.max(r.top,0));
if(iw*ih<vw*vh*0.25)return;if(s.display=='none'||s.visibility=='hidden'||+s.opacity<0.05||s.pointerEvents=='none')return;
const nm=(e.className+' '+e.id+' '+(e.getAttribute('aria-label')||''));if(/menu|nav|drawer|cart|header|search/i.test(nm)&&!/popup|modal|newsletter|klaviyo|geo|cookie|consent|privy|subscribe/i.test(nm))return;if(e.closest('[data-keep]'))return;e.style.setProperty('display','none','important')});
document.querySelectorAll('[class*=klaviyo],[id*=klaviyo],[class*=popup i],[id*=popup i],[class*=newsletter-modal],iframe[src*=gokwik]').forEach(e=>{const r=e.getBoundingClientRect();const iw=Math.max(0,Math.min(r.right,vw)-Math.max(r.left,0)),ih=Math.max(0,Math.min(r.bottom,vh)-Math.max(r.top,0));if(iw*ih>vw*vh*0.25)e.style.setProperty('display','none','important')});
document.body.style.overflow='';document.documentElement.style.overflow='';}'''
# visible links count (used to detect that a menu / drawer / search panel really opened)
VIS='''()=>[...document.querySelectorAll('a,input,button')].filter(a=>{const r=a.getBoundingClientRect();if(r.width<4||r.height<4||r.bottom<0||r.top>innerHeight||r.right<0||r.left>innerWidth)return false;const s=getComputedStyle(a);return s.visibility!='hidden'&&s.opacity!='0'}).length'''
MARK='''()=>{let n=0;document.querySelectorAll('a,input,button,li,img').forEach(a=>{const r=a.getBoundingClientRect();const v=r.width>=4&&r.height>=4&&r.bottom>0&&r.top<innerHeight&&r.right>0&&r.left<innerWidth&&getComputedStyle(a).visibility!='hidden';if(v){a.dataset.capv=1;n++}else delete a.dataset.capv});return n}'''
NEWVIS='''()=>[...document.querySelectorAll('a,input,button,li,img')].filter(a=>{if(a.dataset.capv)return false;const r=a.getBoundingClientRect();if(r.width<4||r.height<4||r.bottom<0||r.top>innerHeight||r.right<0||r.left>innerWidth)return false;const s=getComputedStyle(a);return s.visibility!='hidden'&&s.opacity!='0'}).length'''
PRODVIS='''()=>new Set([...document.querySelectorAll('a[href*="/products/"]')].filter(a=>{const r=a.getBoundingClientRect();return r.width>30&&r.height>20&&r.bottom>0&&r.top<innerHeight&&getComputedStyle(a).visibility!='hidden'}).map(a=>a.getAttribute('href').split('?')[0])).size'''
RECT='''(sel)=>{const e=typeof sel=='string'?document.querySelector(sel):sel;if(!e)return null;const r=e.getBoundingClientRect();return {y:r.top+scrollY,h:r.height,top:r.top,w:r.width}}'''
FIND_GRID='''()=>{const as=[...document.querySelectorAll('a[href*="/products/"]')].filter(a=>a.querySelector('img')&&a.getBoundingClientRect().width>60);
for(const a of as){let e=a;for(let i=0;i<12&&e;i++){e=e.parentElement;if(!e)break;const n=new Set([...e.querySelectorAll('a[href*="/products/"]')].map(x=>x.getAttribute('href').split('?')[0])).size;
const r=e.getBoundingClientRect();if(n>=3&&r.height>200){return {y:r.top+scrollY,h:r.height}}}}return null}'''
FOOT='''()=>{const f=[...document.querySelectorAll('footer,[class*=footer i]')].filter(e=>e.getBoundingClientRect().height>100).pop();if(!f)return null;const r=f.getBoundingClientRect();return {y:r.top+scrollY,h:r.height}}'''
# announcement bar + header as separate rects
TOP='''()=>{const vw=innerWidth,vis=e=>{const r=e.getBoundingClientRect();const s=getComputedStyle(e);return r.width>0&&r.height>0&&r.top<260&&r.top>-5&&s.visibility!='hidden'&&s.display!='none'};
const home=location.origin+'/';
const logo=[...document.querySelectorAll('a')].filter(a=>vis(a)&&(a.href==home||a.getAttribute('href')=='/'||/logo/i.test(a.className+' '+(a.id||'')))&&a.querySelector('img,svg')).sort((a,b)=>a.getBoundingClientRect().top-b.getBoundingClientRect().top)[0];
const cart=[...document.querySelectorAll('a[href*="/cart"],button,[class*=cart i]')].filter(e=>vis(e)&&/cart|bag|basket/i.test((e.getAttribute('href')||'')+' '+(e.getAttribute('aria-label')||'')+' '+e.className+' '+(e.id||''))&&e.getBoundingClientRect().width<200)[0];
if(!logo)return {ann:null,head:null};
let h=logo;if(cart){h=logo.parentElement;while(h&&!h.contains(cart))h=h.parentElement}
if(!h)h=logo;
while(h.parentElement&&h.parentElement!==document.body&&h.getBoundingClientRect().height<36&&h.parentElement.getBoundingClientRect().height<=320)h=h.parentElement;
if(h.getBoundingClientRect().height<30){const L=logo.getBoundingClientRect(),C=cart?cart.getBoundingClientRect():L;const t=Math.max(0,Math.min(L.top,C.top)-14),b=Math.max(L.bottom,C.bottom)+14;
 const head={y:t+scrollY,h:b-t};return {ann:t>=18?{y:0,h:Math.min(t,140)}:null,head}}
// grow to full-width bar (but stay a single row: height < 200)
while(h.parentElement&&h.parentElement!==document.body){const r=h.getBoundingClientRect(),q=h.parentElement.getBoundingClientRect();if(r.width>=vw*.9||q.height<r.height-2||q.height>Math.max(r.height*1.6,r.height+70))break;h=h.parentElement}
const r=h.getBoundingClientRect();if(r.height<30||r.height>320)return {ann:null,head:null};const head={y:Math.max(0,r.top+scrollY-6),h:r.height+12};
let ann=null;const top=r.top+scrollY;
if(top>=18){const txt=[...document.querySelectorAll('body *')].filter(e=>{const q=e.getBoundingClientRect();return q.bottom<=top+2&&q.top>=-2&&q.height>0&&e.childElementCount==0&&(e.innerText||'').trim().length>3}).length;if(txt)ann={y:0,h:Math.min(top,140)}}
return {ann,head}}'''
# element containing text rx -> rect of a sensible container
TEXTBOX='''([rx,minh,maxh,scope])=>{const re=new RegExp(rx,'i');const root=scope?document.querySelector(scope)||document.body:document.body;
const leaf=[...root.querySelectorAll('h1,h2,h3,h4,h5,label,p,span,button,legend,div,input')].filter(e=>{const r=e.getBoundingClientRect();if(!r.width||!r.height)return false;
 const t=(e.tagName=='INPUT'?(e.placeholder||'')+' '+(e.name||''):[...e.childNodes].filter(n=>n.nodeType==3).map(n=>n.textContent).join(' '));return re.test(t)});
for(const l of leaf){let e=l;for(let i=0;i<7&&e;i++){const r=e.getBoundingClientRect();if(r.height>=minh&&r.width>innerWidth*.25)break;e=e.parentElement}
 if(!e)continue;const r=e.getBoundingClientRect();if(r.height>=minh&&r.height<=maxh)return {y:r.top+scrollY,h:r.height}}return null}'''
SEC='''(rx)=>{const re=new RegExp(rx,'i');const c=[...document.querySelectorAll('main section, main > div, [class*=shopify-section]')].filter(e=>{const r=e.getBoundingClientRect();return r.height>150&&r.height<2500&&re.test((e.querySelector('h1,h2,h3,h4')||{}).innerText||'')});const e=c[0];if(!e)return null;const r=e.getBoundingClientRect();return {y:r.top+scrollY,h:r.height}}'''
TILES='''()=>{const as=[...document.querySelectorAll('a[href*="/collections/"]')].filter(a=>a.querySelector('img')&&a.getBoundingClientRect().width>80&&a.getBoundingClientRect().top+scrollY>200);
for(const a of as){let e=a;for(let i=0;i<8&&e;i++){e=e.parentElement;if(!e)break;const n=new Set([...e.querySelectorAll('a[href*="/collections/"]')].filter(x=>x.querySelector('img')).map(x=>x.getAttribute('href').split('?')[0])).size;const r=e.getBoundingClientRect();if(n>=3&&r.height>150&&r.height<1400)return {y:r.top+scrollY,h:r.height}}}return null}'''

def blank(im):
    st=ImageStat.Stat(im.convert('L')); return st.stddev[0]<6
SEEN={}
def save(png,path,maxw):
    im=Image.open(io.BytesIO(png)).convert('RGB')
    if blank(im): print('  skip blank',os.path.basename(path)); return False
    dev=path.rsplit('-',1)[-1]; small=im.convert('L').resize((48,48))
    for other,sm in SEEN.get(dev,{}).items():  # never save the same screen twice under two component names
        if sum(abs(a-b) for a,b in zip(small.tobytes(),sm.tobytes()))/2304<4: print('  skip',os.path.basename(path),'= duplicate of',other); return False
    SEEN.setdefault(dev,{})[os.path.basename(path)]=small
    if im.width>maxw: im=im.resize((maxw,int(im.height*maxw/im.width)))
    im.save(path,quality=80,optimize=True); return True

class Cap:
    def __init__(s,pw,a,dev,out):
        s.pw,s.a,s.dev,s.out=pw,a,dev,out; s.d=f'site/img/{a.slug}'; os.makedirs(s.d,exist_ok=True)
        s.only=set(a.only.split(',')) if a.only else None
    def want(s,c): return s.only is None or c in s.only
    async def ok(s,c,png=None,clip=None,full=False):
        if png is None: png=await s.p.screenshot(clip=clip,full_page=full) if clip else await s.p.screenshot()
        if save(png,f'{s.d}/{c}-{s.dev}.jpg',s.mw): s.out.setdefault(c,[]).append(s.dev); print(s.a.slug,s.dev,c,'ok',flush=True); return True
        return False
    async def dismiss(s):
        p=s.p
        for t in ['Accept','Accept all','Accept All','Got it','OK','Close','No thanks','×','✕']:
            try:
                l=p.get_by_role('button',name=t,exact=True)
                if await l.count() and await l.first.is_visible(): await l.first.click(timeout=800)
            except Exception: pass
        try: await p.keyboard.press('Escape')
        except Exception: pass
        try: await p.evaluate(KILL)
        except Exception: pass
    async def go(s,url,wait=6000):
        await s.p.goto(url,wait_until='domcontentloaded',timeout=60000); await s.p.wait_for_timeout(wait); await s.dismiss(); await s.p.wait_for_timeout(600); await s.dismiss()
        await s.p.evaluate('scrollTo(0,0)'); await s.p.wait_for_timeout(700)
    async def clip(s,c,r,maxh=1.6,pad=10):
        if not r or r['h']<40: return False
        try:
            w=s.p.viewport_size['width']; y=max(0,r['y']-pad)
            await s.p.evaluate(f'scrollTo(0,{max(0,y-10)})'); await s.p.wait_for_timeout(1500); await s.dismiss()
            H=await s.p.evaluate('Math.max(document.documentElement.scrollHeight,document.body.scrollHeight)')
            h=min(max(60,min(r['h']+2*pad,s.p.viewport_size['height']*maxh)),H-y)
            if h<40: print(s.a.slug,s.dev,c,'outside page, skipped'); return False
            return await s.ok(c,await s.p.screenshot(full_page=True,clip={'x':0,'y':y,'width':w,'height':h}))
        except Exception as e: print(s.a.slug,s.dev,c,'ERR',str(e).split('\n')[0][:120]); return False
    async def vis(s): return await s.p.evaluate(VIS)
    async def step(s,name,fn):
        try: await fn()
        except Exception as e: print(s.a.slug,s.dev,name,'ERR',str(e).split('\n')[0][:140],flush=True)

    # ---------- home ----------
    async def home(s):
        p=s.p; await s.go(s.a.home,7000)
        if s.want('hero'): await s.ok('hero')
        t=await p.evaluate(TOP)
        if t['ann'] and s.want('announcement-bar') and t['ann']['h']>=18:
            await s.ok('announcement-bar',clip={'x':0,'y':t['ann']['y'],'width':p.viewport_size['width'],'height':t['ann']['h']})
        if t['head'] and s.want('header'):
            await s.ok('header',clip={'x':0,'y':t['head']['y'],'width':p.viewport_size['width'],'height':min(t['head']['h'],320)})
    async def megamenu(s):
        p=s.p; await p.evaluate(MARK)
        cands=p.locator('header nav a:visible, header nav button:visible, header nav summary:visible, header [class*=menu] > li > a:visible, header details > summary:visible, nav[class*=header i] a:visible')
        n=min(await cands.count(),12)
        for i in range(n):
            el=cands.nth(i)
            try:
                bb=await el.bounding_box()
                if not bb or bb['y']>260 or bb['width']<20: continue
                await el.hover(timeout=2000); await p.wait_for_timeout(900)
                if await p.evaluate(NEWVIS)<5:
                    tag=await el.evaluate('e=>e.tagName')
                    if tag in ('BUTTON','SUMMARY') or await el.get_attribute('aria-expanded') is not None:
                        await el.click(timeout=2000); await p.wait_for_timeout(900)
                if await p.evaluate(NEWVIS)>=5:
                    await p.mouse.move(bb['x']+bb['width']/2,bb['y']+bb['height']/2+40); await p.wait_for_timeout(500)
                    if await p.evaluate(NEWVIS)>=5: return await s.ok('mega-menu')
                await p.mouse.move(5,600); await p.keyboard.press('Escape'); await p.wait_for_timeout(400)
            except Exception: continue
        print(s.a.slug,s.dev,'mega-menu not found')
    async def mobilenav(s):
        p=s.p; await p.evaluate(MARK)
        sel=('header-drawer summary, .menu-drawer__toggle, button[aria-label*="menu" i], a[aria-label*="menu" i], summary[aria-label*="menu" i], [aria-controls*="menu" i], '
             '[aria-controls*="drawer" i], [class*=hamburger i], [class*=burger i], [class*=menu-toggle i], [class*=nav-toggle i], [class*=mobile-menu i] button, button[class*=menu i]')
        c=p.locator(sel)
        for i in range(min(await c.count(),10)):
            el=c.nth(i)
            try:
                if not await el.is_visible(): continue
                bb=await el.bounding_box()
                if not bb or bb['y']>200: continue
                await el.click(timeout=2500); await p.wait_for_timeout(1800)
                if await p.evaluate(NEWVIS)>=4: return await s.ok('mobile-nav')
            except Exception: continue
        print(s.a.slug,s.dev,'mobile-nav not found')
    async def search(s):
        p=s.p
        sel=('summary[aria-label*="search" i], button[aria-label*="search" i], a[aria-label*="search" i], details-modal.header__search summary, '
             '[class*=search i] button, a[href*="/search"], [class*=search-toggle i], [class*=search-icon i], input[type=search], input[name=q]')
        c=p.locator(sel); opened=False
        for i in range(min(await c.count(),10)):
            el=c.nth(i)
            try:
                if not await el.is_visible(): continue
                bb=await el.bounding_box()
                if not bb or bb['y']>260: continue
                tag=await el.evaluate('e=>e.tagName')
                href=await el.get_attribute('href')
                if tag=='A' and href and '/search' in href and not await el.get_attribute('aria-controls'):
                    await s.go(urljoin(s.a.home,href),4000)
                else: await el.click(timeout=2500); await p.wait_for_timeout(1500)
                inp=p.locator('input[type=search]:visible, input[name=q]:visible, input[name=search]:visible, input[placeholder*="search" i]:visible').first
                if await inp.count():
                    opened=True
                    try: await inp.click(timeout=1500); await p.wait_for_timeout(1200)
                    except Exception: pass
                    if s.want('search'): await s.ok('search')
                    q=s.query; before=await p.evaluate(PRODVIS)
                    await inp.fill(''); await inp.type(q,delay=90); await p.wait_for_timeout(3500)
                    if await p.evaluate(PRODVIS)>=max(2,before+1) and s.want('search-results'):
                        await s.ok('search-results'); return
                    break
            except Exception: continue
        if s.want('search-results'):
            u=urljoin(s.a.home,'/search?q='+quote(s.query)+'&type=product')
            await s.go(u,5000)
            n=await p.evaluate('''()=>new Set([...document.querySelectorAll('main a[href*="/products/"], a[href*="/products/"]')].map(a=>a.getAttribute('href').split('?')[0])).size''')
            if n>=2: await s.ok('search-results',clip={'x':0,'y':0,'width':p.viewport_size['width'],'height':int(p.viewport_size['height']*1.4)},full=True)
        if not opened: print(s.a.slug,s.dev,'search panel not found')
    async def homebody(s):
        p=s.p; await s.go(s.a.home,6000)
        H=await p.evaluate('document.body.scrollHeight')
        for y in range(0,min(H,20000),700): await p.evaluate(f'scrollTo(0,{y})'); await p.wait_for_timeout(220)
        if s.want('product-card'):
            g=await p.evaluate(FIND_GRID)
            if g: s.got_card=await s.clip('product-card',g)
        if s.want('category-tiles'):
            g=await p.evaluate(TILES)
            if g: await s.clip('category-tiles',g)
        for comp,rx in [('comparison',r'\bvs\.?\b|versus|compare|comparison'),('bundle-builder',r'build your (own )?(box|bundle|kit)|bundles?\b|combos?\b'),('quiz',r'take (the|our) quiz|find your (match|routine|perfect)|routine (builder|quiz)')]:
            if s.want(comp):
                try: await s.clip(comp,await p.evaluate(SEC,rx))
                except Exception as e: print('sec',comp,e)
        if s.want('footer'):
            f=await p.evaluate(FOOT)
            if f and f['h']>100: await s.clip('footer',f)
        if not s.a.pdp:
            s.a.pdp=await p.evaluate('''()=>{const a=[...document.querySelectorAll('a[href*="/products/"]')].find(a=>a.querySelector('img'));return a&&a.href}''')
        if not s.a.collection:
            s.a.collection=await p.evaluate('''()=>{const a=[...document.querySelectorAll('header a[href*="/collections/"], nav a[href*="/collections/"], a[href*="/collections/"]')].map(a=>a.href).filter(h=>!/\\/products\\//.test(h));return a[0]||null}''') or urljoin(s.a.home,'/collections/all')
        if not s.query_set:
            t=await p.evaluate('''()=>{const a=[...document.querySelectorAll('a[href*="/products/"]')].map(a=>a.innerText.trim()).find(t=>t&&t.length>3);return a||''}''')
            w=[x for x in re.findall(r'[A-Za-z]{4,}',t) if x.lower() not in ('sale','with','pack','from','free','your','this','that','regular','price','save')]
            if w: s.query=w[0].lower()
    async def collection(s):
        p=s.p; await s.go(s.a.collection,6000)
        n=await p.evaluate('''()=>new Set([...document.querySelectorAll('a[href*="/products/"]')].map(a=>a.getAttribute('href').split('?')[0])).size''')
        if n<3: print(s.a.slug,s.dev,'collection has <3 products:',s.a.collection); return
        s.out['_collection']=s.a.collection
        if s.want('collection'): await s.ok('collection',clip={'x':0,'y':0,'width':p.viewport_size['width'],'height':int(p.viewport_size['height']*1.5)},full=True)
        if s.want('product-card') and not s.got_card:
            for y in range(0,3000,700): await p.evaluate(f'scrollTo(0,{y})'); await p.wait_for_timeout(200)
            g=await p.evaluate(FIND_GRID)
            if g: s.got_card=await s.clip('product-card',g)

    # ---------- product ----------
    async def product(s):
        p=s.p; await s.go(s.a.pdp,6000); s.out.setdefault('_pdp',s.a.pdp); vh=p.viewport_size['height']
        if s.want('pdp'): await s.ok('pdp')
        if s.want('variant-selector'):
            v=await p.evaluate('''()=>{const e=document.querySelector('variant-radios,variant-selects,variant-picker,[class*=variant-picker],[class*=product-form__input],fieldset[class*=variant],[class*=swatch]');if(!e)return null;const r=e.getBoundingClientRect();return {y:r.top+scrollY-20,h:Math.max(r.height+60,160)}}''')
            if v: await s.clip('variant-selector',v,pad=0)
        if s.want('subscribe-save'):
            await s.clip('subscribe-save',await p.evaluate(TEXTBOX,[r'subscribe\s*(&|and|\+)\s*save|subscribe & save|deliver(ed)? every|subscription',80,700,None]))
        if s.want('delivery-check'):
            await s.clip('delivery-check',await p.evaluate(TEXTBOX,[r'pin\s?code|postcode|zip ?code|check delivery|delivery date|estimated delivery|deliver(y|ed) by',50,500,None]))
        if s.want('pdp-details'):
            await p.evaluate(f'scrollTo(0,{vh})'); await p.wait_for_timeout(1500); await s.dismiss(); await s.ok('pdp-details')
        if s.dev=='mobile' and s.want('sticky-atc'):
            await p.evaluate(f'scrollTo(0,{vh*2.2})'); await p.wait_for_timeout(1500); await s.dismiss()
            st=await p.evaluate('''()=>[...document.querySelectorAll('body *')].some(e=>{const s=getComputedStyle(e);if(s.position!='fixed'&&s.position!='sticky')return false;const r=e.getBoundingClientRect();return r.bottom>innerHeight-140&&r.height<200&&r.width>innerWidth*.6&&/add|buy|cart|bag/i.test(e.innerText||'')})''')
            if st: await s.ok('sticky-atc')
            else: print(s.a.slug,s.dev,'no sticky add-to-cart bar')
        if s.want('reviews'):
            r=await p.evaluate('''()=>{const e=[...document.querySelectorAll('section,div')].find(e=>/review/i.test(e.id+' '+e.className)&&e.getBoundingClientRect().height>200);if(!e)return null;const r=e.getBoundingClientRect();return {y:r.top+scrollY,h:r.height}}''')
            if r: await s.clip('reviews',r)
        if s.want('cross-sell'):
            await s.clip('cross-sell',await p.evaluate(SEC,r'pair (it )?with|goes (great|well) with|complete the look|you may also like|frequently bought|recommended'))
        if not any(s.want(c) for c in ('cart-drawer','free-gift','cart-page','checkout')): return
        # add to cart -> drawer
        await p.evaluate('scrollTo(0,0)'); await s.dismiss()
        try:  # pick the first available size/variant if the button needs one
            await p.evaluate('''()=>{const f=document.querySelector('form[action*="/cart/add"]')||document;const b=f.querySelector('button[name=add],button[type=submit]');
             if(b&&!b.disabled&&!/select|choose/i.test(b.innerText))return;
             const o=[...document.querySelectorAll('fieldset input[type=radio]:not(:disabled), [class*=size i] button:not([disabled]), [class*=variant i] button:not([disabled]), [class*=option i] button:not([disabled])')].find(e=>!/sold|unavailable/i.test(e.className+' '+(e.getAttribute('aria-label')||'')));
             if(o){(o.tagName=='INPUT'&&o.labels&&o.labels[0]?o.labels[0]:o).click()}}'''); await p.wait_for_timeout(800)
        except Exception: pass
        btn=p.locator('form[action*="/cart/add"] button[type=submit]:visible, button[name=add]:visible, button:has-text("Add to cart"):visible, button:has-text("Add to bag"):visible, button:has-text("Add to Cart"):visible').first
        await btn.click(timeout=6000); await p.wait_for_timeout(3500); s.added=True
        if s.want('cart-drawer'):
            d=await p.evaluate('''()=>[...document.querySelectorAll('cart-drawer,[class*=cart-drawer i],[id*=cart-drawer i],[class*=mini-cart i],[class*=side-cart i],[class*=drawer i][class*=cart i],[id*=CartDrawer]')].some(e=>{const r=e.getBoundingClientRect();const s=getComputedStyle(e);return r.width>200&&r.height>300&&s.visibility!='hidden'&&r.right>innerWidth*.5&&r.left<innerWidth})''')
            if d: await s.ok('cart-drawer')
            else: print(s.a.slug,s.dev,'no cart drawer opened (maybe redirected to /cart)')
        if s.want('free-gift'):
            r=await p.evaluate(TEXTBOX,[r'free gift|choose your (free )?gift|gift with purchase|unlock(ed)? (a )?free',60,600,None])
            if r and r['h']<700:
                await s.ok('free-gift',clip={'x':0,'y':max(0,r['y']-10-await p.evaluate('scrollY')),'width':p.viewport_size['width'],'height':min(r['h']+20,vh)})
    async def cart(s):
        p=s.p
        if not s.added: return
        await s.go(urljoin(s.a.home,'/cart'),4500)
        n=await p.evaluate('''()=>/subtotal|total|check ?out/i.test(document.body.innerText)&&document.querySelectorAll('main a[href*="/products/"], form[action*="/cart"] a[href*="/products/"], [class*=cart-item i]').length>0''')
        if n and s.want('cart-page'): await s.ok('cart-page',clip={'x':0,'y':0,'width':p.viewport_size['width'],'height':int(p.viewport_size['height']*1.3)},full=True)
        if s.a.checkout and s.want('checkout') and n:
            b=p.locator('button[name=checkout]:visible, a[href*="/checkout"]:visible, button:has-text("Check out"):visible, button:has-text("Checkout"):visible').first
            await b.click(timeout=5000); await p.wait_for_timeout(8000)
            u=p.url; pw=await p.locator('input[type=password]:visible').count()
            if re.search(r'/checkouts?/',u) and not pw and await p.locator('input:visible').count():
                await s.ok('checkout'); s.out['_checkout']=u.split('?')[0]
            else: print(s.a.slug,s.dev,'checkout not reachable without sign-in, skipped:',u[:80])

    async def run(s):
        b=await s.pw.chromium.launch()
        if s.dev=='desktop': ctx=await b.new_context(viewport={'width':1440,'height':900},user_agent=UA,locale='en-IN'); s.mw=1440
        else: ctx=await b.new_context(**s.pw.devices['iPhone 13'],locale='en-IN'); s.mw=390*2
        s.p=await ctx.new_page(); s.added=False; s.got_card=False
        s.query=s.a.query or 'new'; s.query_set=bool(s.a.query)
        await s.step('home',s.home)
        if s.dev=='desktop' and s.want('mega-menu'): await s.step('mega-menu',s.megamenu)
        if s.dev=='mobile' and s.want('mobile-nav'): await s.step('mobile-nav',s.mobilenav)
        await s.step('homebody',s.homebody)
        if s.want('search') or s.want('search-results'):
            await s.step('search-reset',lambda: s.go(s.a.home,5000)); await s.step('search',s.search)
        if s.a.collection: await s.step('collection',s.collection)
        if s.a.pdp: await s.step('product',s.product)
        await s.step('cart',s.cart)
        await b.close()

async def main():
    ap=argparse.ArgumentParser(); ap.add_argument('slug'); ap.add_argument('home'); ap.add_argument('pdp',nargs='?')
    ap.add_argument('--collection'); ap.add_argument('--query'); ap.add_argument('--device',default='both'); ap.add_argument('--only')
    ap.add_argument('--checkout',action='store_true',help='also try to open the first checkout step (no sign-in, nothing typed, never pays)')
    a=ap.parse_args(); out={}
    devs=['desktop','mobile'] if a.device=='both' else [a.device]
    async with async_playwright() as pw:
        # separate arg copies so desktop/mobile discoveries don't race
        import copy
        await asyncio.gather(*[Cap(pw,copy.copy(a),d,out).run() for d in devs])
    os.makedirs('data/captures',exist_ok=True); path=f'data/captures/{a.slug}.json'
    prev=json.load(open(path)) if os.path.exists(path) else {}
    for k,v in out.items():
        if k.startswith('_'): prev[k]=v
        else: prev[k]=sorted(set(prev.get(k,[]))|set(v))
    json.dump(prev,open(path,'w'),indent=1)
    print('captured:',', '.join(f"{k}({'+'.join(sorted(v))})" for k,v in sorted(out.items()) if not k.startswith('_')))
if __name__=='__main__': asyncio.run(main())
