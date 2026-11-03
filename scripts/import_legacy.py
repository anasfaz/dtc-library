# one-off: copy earlier research screenshots into site/img/<slug>/<component>-<device>.jpg
import glob,os,re
from PIL import Image
MAP={'product-shop':'product-card','globe':'brand-story','category-tiles':'category-tiles','footer':'footer','nav-menu':'mega-menu','product-carousel':'product-card','shop-the-look':'shop-the-look','product-grid':'product-card','quiz-cta':'quiz','mega-menu':'mega-menu','reviews-carousel':'reviews','category-slider':'category-tiles','product-cards':'product-card','hero':'hero','pdp':'pdp','pdp-info':'pdp-details'}
def put(src,slug,comp,dev):
    d=f'site/img/{slug}'; os.makedirs(d,exist_ok=True)
    im=Image.open(src).convert('RGB'); mw=1440 if dev!='mobile' else 780
    if im.width>mw: im=im.resize((mw,int(im.height*mw/im.width)))
    if im.height>2600: im=im.crop((0,0,im.width,2600))
    im.save(f'{d}/{comp}-{dev}.jpg',quality=80,optimize=True)
for root in ['/workspace/awwwards-shopify','/workspace/pet-fish-stores']:
    for f in glob.glob(root+'/*/*.png'):
        slug=f.split('/')[-2]; m=re.match(r'(desktop|mobile)-(.+)\.png',os.path.basename(f))
        if m and m.group(2) in MAP: put(f,slug,MAP[m.group(2)],m.group(1))
for f in glob.glob('/workspace/goda/goda/*-hero.png'):
    pg,dev,_=os.path.basename(f).split('-'); put(f,'goda','hero' if pg=='home' else 'pdp',dev)
AG={'calmenta':'calmenta','cosmoslac':'cosmos-lac','giordanos':'giordanos','cazal':'cazal'}
for f in glob.glob('/workspace/goda/agencies/*/*.png'):
    m=re.match(r'(\w+)-(desktop|mobile)-(hero|section)\.png',os.path.basename(f))
    if m and m.group(1) in AG: put(f,AG[m.group(1)],'hero' if m.group(3)=='hero' else ('bundle-builder' if m.group(1)=='giordanos' else 'section'),m.group(2))
W={'01-brooklinen':('brooklinen','bundle-builder'),'02-eadem':('eadem','pdp'),'03-almada':('almada','product-card'),'04-buckmason':('buck-mason','cross-sell')}
for f in glob.glob('/workspace/weekly-inspiration/2026-10-26/images/*.jpg'):
    k='-'.join(os.path.basename(f).split('-')[:2])
    if k in W: put(f,W[k][0],W[k][1],'combined')
