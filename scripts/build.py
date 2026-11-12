"""Build site/data.json from data/*.json + site/img/<slug>/<component>-<device>.jpg
Component keys come from data/component_types.json (label, short, group, order, tags, note).
Groups drive the site tabs: home, collection, product, search, menu, cart, checkout."""
import json,glob,os,re,datetime
from zoneinfo import ZoneInfo
from PIL import Image
IST=ZoneInfo('Asia/Kolkata')
B=json.load(open('data/brands.json')); T=json.load(open('data/component_types.json')); N=json.load(open('data/notes.json'))
GROUPS=[('home','Home'),('collection','Collection'),('product','Product'),('search','Search'),('menu','Menu'),('cart','Cart'),('checkout','Checkout')]
comps={}; dims={}; mt={}
for f in sorted(glob.glob('site/img/*/*.jpg')):
    slug=f.split('/')[-2]; m=re.match(r'(.+)-(desktop|mobile|combined)\.jpg$',os.path.basename(f))
    if not m or slug not in B: continue
    c,dev=m.groups(); comps.setdefault((slug,c),{})[dev]=f[len('site/'):]
    try:
        with Image.open(f) as im: dims.setdefault((slug,c),{})[dev]=[im.width,im.height]
    except Exception: pass
    mt[slug]=max(mt.get(slug,0),os.path.getmtime(f))
IND=[('Pets & Live Fish',r'pet|fish'),('Baby & Kids',r'baby|kids|diaper'),('Electronics',r'electronic|audio'),('Food & Beverage',r'food|coffee|snack|chocolate|beer|grocery|tea'),
     ('Beauty & Personal Care',r'beauty|skin|hair|groom|fragrance|perfum|sunscreen|personal care|incense'),('Health & Wellness',r'wellness|supplement|vitamin'),
     ('Accessories, Footwear & Travel',r'footwear|eyewear|jewel|luggage|leather|bag'),('Fashion & Apparel',r'fashion|wear|apparel|lingerie|denim|fabric|handloom|shirt'),
     ('Home & Living',r'home|bedding|mattress|furniture|kitchen|cleaning')]
def industry(c):
    for n,rx in IND:
        if re.search(rx,c or '',re.I): return n
    return 'Other'
items=[]
for (slug,c),imgs in comps.items():
    b=B[slug]; t=T.get(c,{"label":c,"tags":[],"note":""})
    note=N.get(slug,{}).get(c) or t['note']
    items.append({"id":f"{slug}--{c}","brand":slug,"brandName":b['name'],"component":c,"componentLabel":t['label'],
      "short":t.get('short',t['label']),"group":t.get('group','home'),"order":t.get('order',99),
      "region":b['region'],"country":b['country'],"agency":b.get('agency','Unknown'),"platform":b.get('platform',''),"category":b.get('category',''),"industry":industry(b.get('category','')),
      "added":b['added'],"url":b.get('url',''),"tags":sorted(set(t['tags']+b.get('tags',[])+[b.get('category','').lower()])),
      "note":note,"brandWhy":b.get('why',''),"images":imgs,"dims":dims.get((slug,c),{})})
items.sort(key=lambda x:(x['added'],x['region']=='India'),reverse=True)
brands=[dict(slug=k,**v,industry=industry(v.get('category','')),count=sum(1 for i in items if i['brand']==k),
             updated=datetime.datetime.fromtimestamp(mt.get(k,0),IST).strftime('%Y-%m-%d') if k in mt else v.get('added','')) for k,v in B.items()]
brands=[x for x in brands if x['count']]
AG=json.load(open("data/agencies.json")) if os.path.exists("data/agencies.json") else []
json.dump({"agencies":AG,"built":datetime.datetime.now(IST).strftime('%Y-%m-%d %H:%M IST'),"groups":GROUPS,"types":T,"brands":brands,"items":items},open('site/data.json','w'),ensure_ascii=False)
print(len(brands),'brands',len(items),'components',sum(len(i['images']) for i in items),'images')
