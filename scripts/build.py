"""Build site/data.json from data/*.json + site/img/<slug>/<component>-<device>.jpg"""
import json,glob,os,re,datetime
B=json.load(open('data/brands.json')); T=json.load(open('data/component_types.json')); N=json.load(open('data/notes.json'))
comps={}
for f in sorted(glob.glob('site/img/*/*.jpg')):
    slug=f.split('/')[-2]; m=re.match(r'(.+)-(desktop|mobile|combined)\.jpg$',os.path.basename(f))
    if not m or slug not in B: continue
    c,dev=m.groups(); comps.setdefault((slug,c),{})[dev]=f[len('site/'):]
items=[]
for (slug,c),imgs in comps.items():
    b=B[slug]; t=T.get(c,{"label":c,"tags":[],"note":""})
    note=N.get(slug,{}).get(c) or t['note']
    items.append({"id":f"{slug}--{c}","brand":slug,"brandName":b['name'],"component":c,"componentLabel":t['label'],
      "region":b['region'],"country":b['country'],"agency":b.get('agency','Unknown'),"platform":b.get('platform',''),"category":b.get('category',''),
      "added":b['added'],"url":b.get('url',''),"tags":sorted(set(t['tags']+b.get('tags',[])+[b.get('category','').lower()])),
      "note":note,"brandWhy":b.get('why',''),"images":imgs})
items.sort(key=lambda x:(x['added'],x['region']=='India'),reverse=True)
brands=[dict(slug=k,**v,count=sum(1 for i in items if i['brand']==k)) for k,v in B.items()]
brands=[x for x in brands if x['count']]
AG=json.load(open("data/agencies.json")) if os.path.exists("data/agencies.json") else []
json.dump({"agencies":AG,"built":datetime.datetime.now(__import__('zoneinfo').ZoneInfo('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M IST'),"types":T,"brands":brands,"items":items},open('site/data.json','w'),ensure_ascii=False)
print(len(brands),'brands',len(items),'components',sum(len(i['images']) for i in items),'images')
