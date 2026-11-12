/* DTC Library — gallery app. Routes:
   #/ (home tab) #/collection #/product #/search #/menu #/cart #/checkout  [+ /<component-type>]
   #/all  #/saved  #/brands  #/agencies  #/brand/<slug>  #/brand/<slug>/<component> (lightbox) */
let D,TYPES,GROUPS,ITEM={},BR={},rendered=null,pageList=[],shown=0,io;
const PAGE=48,$=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const ls=(k,v)=>{try{if(v===undefined)return JSON.parse(localStorage.getItem(k));localStorage.setItem(k,JSON.stringify(v))}catch(e){return null}};
const S=Object.assign({q:'',dev:'desktop',region:'all',agency:'all',ind:'all',sort:'latest'},{dev:ls('dtcDev')||(matchMedia('(max-width:640px)').matches?'mobile':'desktop')});
let SAVED=new Set(ls('dtcSaved')||[]);
const toast=m=>{const t=$('#toast');t.textContent=m;t.classList.add('on');clearTimeout(toast.t);toast.t=setTimeout(()=>t.classList.remove('on'),1700)};
const daysAgo=d=>(Date.now()-new Date(d+'T12:00:00+05:30'))/864e5;
const isNew=i=>daysAgo(i.added)<8;
const known=a=>a&&!/^unknown/i.test(a);
const fmtDate=d=>{try{return new Date(d+'T12:00:00+05:30').toLocaleDateString('en-IN',{day:'numeric',month:'long',year:'numeric'})}catch(e){return d}};
const ICON={desktop:'<svg viewBox="0 0 24 24" width="16"><rect x="3" y="4.5" width="18" height="12" rx="2" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M9 20h6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
 mobile:'<svg viewBox="0 0 24 24" width="16"><rect x="7" y="3" width="10" height="18" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>',
 combined:'<svg viewBox="0 0 24 24" width="16"><rect x="2.5" y="5" width="13" height="10" rx="1.6" fill="none" stroke="currentColor" stroke-width="1.7"/><rect x="16" y="8" width="5.5" height="11" rx="1.4" fill="none" stroke="currentColor" stroke-width="1.7"/></svg>',
 bm:'<svg viewBox="0 0 24 24" width="18"><path fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" d="M6.5 3.5h11v17l-5.5-4-5.5 4z"/></svg>'};
const H1={home:'Best designed D2C homepage examples',collection:'Best designed collection pages and product cards',product:'Best designed ecommerce product page examples',
 search:'Best designed ecommerce search examples',menu:'Best designed headers, mega menus and mobile navigation',cart:'Best designed cart drawers and cart pages',checkout:'Best designed checkout examples',all:'Every component, screenshotted and sorted',saved:'Saved screens'};

fetch('data.json?v='+Date.now()).then(r=>r.json()).then(d=>{D=d;TYPES=d.types;GROUPS=d.groups||[['home','Home'],['collection','Collection'],['product','Product'],['search','Search'],['menu','Menu'],['cart','Cart'],['checkout','Checkout']];
 D.items.forEach(i=>{const t=TYPES[i.component]||{};i.group=i.group||t.group||'home';i.short=i.short||t.short||i.componentLabel;i.order=i.order??t.order??99;
  i._s=[i.brandName,i.component,i.componentLabel,i.short,i.group,i.region,i.country,i.agency,i.platform,i.category,i.industry,i.note,i.brandWhy,...(i.tags||[])].join(' ').toLowerCase();i._k=[i.component,i.componentLabel,i.short,...(i.tags||[])].join(' ').toLowerCase();i._b=[i.brandName,i.agency,i.category,i.industry,i.country].join(' ').toLowerCase();ITEM[i.id]=i});
 D.brands.forEach(b=>BR[b.slug]=b);
 const p=new URLSearchParams(location.search);if(p.get('q'))S.q=p.get('q');$('#q').value=S.q;
 $('#built').textContent='Updated '+D.built;updSaved();route()}).catch(e=>{$('#app').innerHTML='<p class="empty">Could not load data.json</p>'});

/* ---------- routing ---------- */
const parse=()=>location.hash.replace(/^#\/?/,'').split('?')[0].split('/').filter(Boolean).map(decodeURIComponent);
addEventListener('hashchange',route);
function route(){const p=parse();
 if(p[0]=='brand'&&p[2]){ // lightbox deep link
  if(LB.url===location.hash&&rendered)return;
  if(rendered!=='brand/'+p[1]){renderBase(['brand',p[1]]);scrollTo(0,0)}
  const it=ITEM[p[1]+'--'+p[2]];if(it)openLb(it.id,brandItems(p[1]).map(i=>i.id),false);return}
 if(!$('#lb').hidden)hideLb();
 const key=p.join('/')||'home';if(key!==rendered){renderBase(p);scrollTo(0,0)}}
function renderBase(p){const k=p.join('/')||'home';rendered=k;
 $$('[data-nav]').forEach(a=>a.classList.toggle('on',a.dataset.nav==p[0]||(p[0]=='brand'&&a.dataset.nav=='brands')));
 if(p[0]=='brand')brandPage(p[1]);else if(p[0]=='brands')brandsPage();else if(p[0]=='agencies')agenciesPage();
 else if(p[0]=='saved')gallery('saved');else if(p[0]=='all')gallery('all',p[1]);
 else{const g=GROUPS.find(x=>x[0]==p[0]);gallery(g?g[0]:'home',g?p[1]:null)}}
const rerender=()=>{const y=scrollY;renderBase(parse().slice(0,parse()[0]=='brand'?2:3));scrollTo(0,Math.min(y,scrollY+1e6))};

/* ---------- search ---------- */
$('#q').addEventListener('input',e=>{const was=S.q;S.q=e.target.value.trim();const p=parse();
 if(p[0]=='brands'){brandsPage();return}
 if(!S.q&&!was)return;
 if(p[0]=='all'||p[0]=='saved'||(GROUPS.some(g=>g[0]==p[0])&&was)){renderBase(p);return}
 location.hash='#/all'});
addEventListener('keydown',e=>{const lb=!$('#lb').hidden;
 if(e.key=='/'&&!/INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)){e.preventDefault();$('#q').focus()}
 if(e.key=='Escape'){if(lb)closeLb();else document.activeElement.blur()}
 if(lb&&e.key=='ArrowRight')step(1);if(lb&&e.key=='ArrowLeft')step(-1)});

/* ---------- helpers ---------- */
function match(i,o={}){if(S.region!='all'&&i.region!=S.region)return false;
 if(S.agency=='known'&&!known(i.agency))return false;if(S.agency!='all'&&S.agency!='known'&&i.agency!=S.agency)return false;
 if(S.ind!='all'&&i.industry!=S.ind)return false;
 return S.q.toLowerCase().split(/\s+/).filter(Boolean).every(w=>i._s.includes(w))}
const score=i=>S.q.toLowerCase().split(/\s+/).filter(Boolean).reduce((n,w)=>n+(i._k.includes(w)?3:i._b.includes(w)?2:0),0);
function sorted(a){if(S.q&&S.sort=='latest'){const sc=new Map(a.map(i=>[i.id,score(i)]));return [...a].sort((x,y)=>sc.get(y.id)-sc.get(x.id)||y.added.localeCompare(x.added)||x.order-y.order)}const by=S.sort=='az'?(x,y)=>x.brandName.localeCompare(y.brandName)||x.order-y.order:
 (x,y)=>y.added.localeCompare(x.added)||(y.region=='India')-(x.region=='India')||x.brandName.localeCompare(y.brandName)||x.order-y.order;return [...a].sort(by)}
const brandItems=s=>D.items.filter(i=>i.brand==s).sort((a,b)=>a.order-b.order);
function pick(i,dev){const im=i.images,o=dev=='mobile'?['mobile','combined','desktop']:['desktop','combined','mobile'];
 const k=o.find(x=>im[x]);return {k,src:im[k],wh:(i.dims||{})[k],fb:k!==dev&&!(k=='combined')}}
function thumb(i,dev,href){const p=pick(i,dev),R=dev=='mobile'?16/9:3/4,r=p.wh?p.wh[1]/p.wh[0]:R;const fit=p.fb||r<R*.8;
 const tag=p.fb?`<span class="badge l">${p.k=='mobile'?'Mobile only':'Desktop only'}</span>`:'';
 return `<a class="thumb ${fit?'fit':''}" href="${href}" data-open="${i.id}">${tag}${isNew(i)?'<span class="badge">New</span>':''}<img loading="lazy" src="${p.src}" alt="${esc(i.brandName+' '+i.short+' ('+p.k+')')}"></a>`}
const bmBtn=id=>`<button class="bm ${SAVED.has(id)?'on':''}" data-bm="${id}" aria-label="Save" title="Save">${ICON.bm}</button>`;
function card(i,ctx){const dev=S.dev,href=`#/brand/${i.brand}/${i.component}`;
 const reg=i.region=='India'?'India':esc(i.country);
 if(ctx=='brand')return `<article class="card">${thumb(i,dev,href)}<div class="cm"><div><div class="t"><span style="color:var(--ink);font-weight:600;font-size:16px">${esc(i.short)}</span></div><div class="s">${esc(i.componentLabel)} · ${esc(i.industry||i.category)}</div></div>${bmBtn(i.id)}</div></article>`;
 return `<article class="card">${thumb(i,dev,href)}<div class="cm"><div><div class="t"><a href="#/brand/${i.brand}">${esc(i.brandName)}</a><span>${esc(i.short)}</span></div><div class="s" title="${esc(i.category)}">${reg} · ${esc(i.industry||i.category)}${known(i.agency)?' · by '+esc(i.agency):''}</div></div>${bmBtn(i.id)}</div></article>`}
const opts=(arr,cur)=>arr.map(([v,l])=>`<option value="${esc(v)}" ${v==cur?'selected':''}>${esc(l)}</option>`).join('');
const devSeg=(cur,cls='dev')=>`<div class="seg ${cls}" role="group" aria-label="Device">${['desktop','mobile'].map(d=>`<button data-dev="${d}" class="${cur==d?'on':''}" aria-label="${d}" title="${d[0].toUpperCase()+d.slice(1)}">${ICON[d]}</button>`).join('')}</div>`;
function filterBar(n,label='Screens',sortOpts=[['latest','Latest'],['az','Brand A–Z']]){
 const ags=[...new Set(D.items.map(i=>i.agency).filter(known))].sort(),inds=[...new Set(D.brands.map(b=>b.industry))].sort();
 const any=S.region!='all'||S.agency!='all'||S.ind!='all'||S.q;
 return `<div class="filters">${devSeg(S.dev)}
  <div class="seg" role="group" aria-label="Region">${[['all','All'],['India','India'],['International','International']].map(([v,l])=>`<button data-r="${v}" class="${S.region==v?'on':''}">${l}</button>`).join('')}</div>
  <div class="dd"><select id="fag" class="${S.agency!='all'?'set':''}" aria-label="Agency">${opts([['all','Agency'],['known','Any verified agency'],...ags.map(a=>[a,a])],S.agency)}</select></div>
  <div class="dd"><select id="find" class="${S.ind!='all'?'set':''}" aria-label="Industry">${opts([['all','Industries'],...inds.map(a=>[a,a])],S.ind)}</select></div>
  ${any?'<button class="clear" id="fclr">Clear</button>':''}
  <div class="fr"><span class="n">${n} ${label}</span><div class="dd"><select id="fsort" aria-label="Sort">${opts(sortOpts.map(([v,l])=>[v,'Sort: '+(v=='latest'&&S.q&&label=='Screens'?'Best match':l)]),S.sort)}</select></div></div></div>`}
function bindFilters(after){$$('[data-r]').forEach(b=>b.onclick=()=>{S.region=b.dataset.r;after()});
 $$('.filters [data-dev],.bbar [data-dev]').forEach(b=>b.onclick=()=>{S.dev=b.dataset.dev;ls('dtcDev',S.dev);after()});
 const on=(id,k)=>{const e=$(id);if(e)e.onchange=()=>{S[k]=e.value;after()}};on('#fag','agency');on('#find','ind');on('#fsort','sort');
 const c=$('#fclr');if(c)c.onclick=()=>{Object.assign(S,{region:'all',agency:'all',ind:'all',q:''});$('#q').value='';after()}}
function stats(){const ags=new Set(D.items.map(i=>i.agency).filter(known));
 return `<div class="stats"><span><b>${D.brands.length}</b> brands</span><span><b>${D.items.length}</b> components</span><span><b>${D.brands.filter(b=>b.region=='India').length}</b> Indian D2C brands</span><span><b>${ags.size}</b> verified agencies</span><span>Updated ${esc(D.built)}</span></div>`}

/* ---------- gallery (tabs) ---------- */
function gallery(g,type){const base=D.items.filter(i=>match(i)&&(g!='saved'||SAVED.has(i.id)));
 const inG=x=>g=='all'||g=='saved'?base:base.filter(i=>i.group==x);
 const gi=inG(g),tc={};gi.forEach(i=>tc[i.component]=(tc[i.component]||0)+1);
 if(type&&!TYPES[type])type=null;
 const list=sorted(type?gi.filter(i=>i.component==type):gi);
 const types=Object.keys(TYPES).filter(k=>(g=='all'||g=='saved'?tc[k]||k==type:TYPES[k].group==g)).sort((a,b)=>(tc[b]||0)-(tc[a]||0)||TYPES[a].order-TYPES[b].order);
 const pre=g=='all'||g=='saved'?'#/'+g:'#/'+(g=='home'?'home':g);
 const title=g=='all'&&S.q?`Results for “${esc(S.q)}”`:H1[g];
 $('#app').innerHTML=`<section class="ph"><h1>${title}</h1>${g=='saved'?'<p>Screens you bookmarked on this device.</p>':stats()}</section>
 <nav class="tabs" aria-label="Page types">${GROUPS.map(([k,l])=>{const n=base.filter(i=>i.group==k).length;return `<a href="#/${k}" class="${g==k?'on':''}">${l}<sup>${n}</sup></a>`}).join('')}<span class="sp"></span><a href="#/all" class="${g=='all'?'on':''}">All<sup>${base.length}</sup></a>${SAVED.size?`<a href="#/saved" class="${g=='saved'?'on':''}">Saved<sup>${SAVED.size}</sup></a>`:''}</nav>
 ${types.length?`<div class="chips"><a class="chip ${!type?'on':''}" href="${pre}">All<small>${gi.length}</small></a>${types.map(k=>`<a class="chip ${type==k?'on':''} ${tc[k]?'':'zero'}" href="${pre}/${k}">${esc(TYPES[k].short||TYPES[k].label)}<small>${tc[k]||0}</small></a>`).join('')}</div>`:''}
 ${filterBar(list.length)}
 <div class="grid ${S.dev=='mobile'?'m':''}" id="grid"></div><div id="sent"></div>`;
 bindFilters(()=>renderBase(parse()));
 if(!list.length)$('#grid').innerHTML=`<div class="empty">${g=='saved'?'Nothing saved yet — tap the bookmark on any screen.':S.q||S.region!='all'||S.agency!='all'||S.ind!='all'?'No screens match these filters.':type?'No '+esc((TYPES[type].short||'').toLowerCase())+' screens yet. This component type is captured from the next daily brand onward.':'No '+esc((GROUPS.find(x=>x[0]==g)||[,''])[1].toLowerCase())+' screens yet. New brands are captured one per day with every component — this tab fills as they land.'}</div>`;
 paginate(list,'')}
function paginate(list,ctx){pageList=list;shown=0;more(ctx);if(io)io.disconnect();
 io=new IntersectionObserver(e=>{if(e[0].isIntersecting)more(ctx)},{rootMargin:'1200px'});const s=$('#sent');if(s)io.observe(s)}
function more(ctx){if(shown>=pageList.length)return;const g=$('#grid');if(!g)return;
 g.insertAdjacentHTML('beforeend',pageList.slice(shown,shown+PAGE).map(i=>card(i,ctx)).join(''));shown+=PAGE}

/* ---------- brand page ---------- */
function brandPage(slug){const b=BR[slug];if(!b){gallery('home');return}const it=brandItems(slug);
 const ag=D.agencies.find(a=>a.name==b.agency||a.clients.includes(slug));
 $('#app').innerHTML=`<section class="bh"><div><a class="back" href="#/brands">← All brands</a><h1>${esc(b.name)}</h1>
  <div class="links">${b.url?`<a href="${esc(b.url)}" target="_blank" rel="noopener">Visit the website</a>`:''}${known(b.agency)&&b.agency_source&&/^http/.test(b.agency_source)?`<a href="${esc(b.agency_source)}" target="_blank" rel="noopener">${esc(b.agency)} case study</a>`:''}${ag&&ag.url?`<a href="${esc(ag.url)}" target="_blank" rel="noopener">Agency site</a>`:''}</div>
  <div class="facts"><span class="fact ${b.region=='India'?'in':''}">${esc(b.country)}</span><span class="fact">${esc(b.category)}</span>${b.platform?`<span class="fact">${esc(b.platform)}</span>`:''}<span class="fact">${known(b.agency)?'Built by '+esc(b.agency):'Agency not verified'}</span><span class="fact">Added ${fmtDate(b.added)}</span></div></div>
  <div class="bmeta"><div class="r"><span>Last Updated ${fmtDate(b.updated||b.added)}</span><span>${it.length} Screens</span></div></div></section>
 ${b.why?`<p class="why">${esc(b.why)}</p>`:''}
 <div class="bbar">${devSeg(S.dev)}</div>
 <div class="grid ${S.dev=='mobile'?'m':''}" id="grid"></div>`;
 bindFilters(()=>brandPage(slug));pageList=it;shown=0;$('#grid').innerHTML=it.map(i=>card(i,'brand')).join('')}

/* ---------- brands + agencies ---------- */
function brandCard(b){const h=brandItems(b.slug),i=h.find(x=>x.component=='hero')||h[0];
 return `<article class="card">${i?thumb(Object.assign({},i,{added:b.added}),S.dev,'#/brand/'+b.slug).replace(/data-open="[^"]*"/,'').replace('class="thumb ','class="thumb nz '):''}<div class="cm"><div><div class="t"><a href="#/brand/${b.slug}">${esc(b.name)}</a><span>${b.count} screens</span></div><div class="s" title="${esc(b.category)}">${b.region=='India'?'India':esc(b.country)} · ${esc(b.industry)}${known(b.agency)?' · by '+esc(b.agency):''}</div></div></div></article>`}
function brandsPage(){const q=S.q.toLowerCase();
 let bs=D.brands.filter(b=>(S.region=='all'||b.region==S.region)&&(S.ind=='all'||b.industry==S.ind)&&(S.agency=='all'||(S.agency=='known'?known(b.agency):b.agency==S.agency))&&(!q||[b.name,b.category,b.agency,b.country,b.industry].join(' ').toLowerCase().includes(q)));
 bs.sort(S.sort=='az'?(a,b)=>a.name.localeCompare(b.name):S.sort=='most'?(a,b)=>b.count-a.count:(a,b)=>b.added.localeCompare(a.added)||(b.region=='India')-(a.region=='India'));
 $('#app').innerHTML=`<section class="ph"><h1>Brands</h1><p>Every brand in the library, with all of its captured components on one page. Agency credits appear only when the agency's own portfolio or case study names the brand.</p></section>
 ${filterBar(bs.length,'Brands',[['latest','Latest'],['az','A–Z'],['most','Most screens']])}<div class="bgrid ${S.dev=='mobile'?'grid m':''}">${bs.map(brandCard).join('')||'<div class="empty">No brands match.</div>'}</div>`;
 bindFilters(brandsPage)}
function agenciesPage(){
 $('#app').innerHTML=`<section class="ph"><h1>Indian Shopify agencies</h1><p>${D.agencies.length} agencies. A client is listed only when the agency's own portfolio, case study or testimonial page names it — the source is linked on each brand page.</p></section>
 ${D.agencies.map(a=>{const cl=a.clients.map(s=>BR[s]).filter(Boolean);return `<section class="ag"><div class="agh"><div><h2>${esc(a.name)}</h2><p>${esc(a.focus)}</p></div><div style="display:flex;gap:8px;align-items:center"><span class="fact">${cl.length} brands</span><a class="btn p" href="${esc(a.url)}" target="_blank" rel="noopener">Agency site ↗</a></div></div>
 <div class="bgrid">${cl.map(brandCard).join('')||'<p class="empty" style="padding:10px 0;text-align:left">No verified client captured yet.</p>'}</div></section>`}).join('')}`}

/* ---------- lightbox ---------- */
const LB={id:null,list:[],dev:'desktop',url:null,pushed:false};
document.addEventListener('click',e=>{const bm=e.target.closest('[data-bm]');
 if(bm){e.preventDefault();const id=bm.dataset.bm;SAVED.has(id)?SAVED.delete(id):SAVED.add(id);ls('dtcSaved',[...SAVED]);updSaved();
  $$(`[data-bm="${id}"]`).forEach(x=>x.classList.toggle('on',SAVED.has(id)));toast(SAVED.has(id)?'Saved':'Removed from saved');return}
 const o=e.target.closest('[data-open]');if(o&&!e.metaKey&&!e.ctrlKey){e.preventDefault();openLb(o.dataset.open,pageList.map(i=>i.id),true)}});
document.addEventListener('load',e=>{if(e.target.tagName=='IMG'&&e.target.parentElement.classList.contains('thumb')){e.target.classList.add('ld');e.target.parentElement.classList.add('done')}},true);
function updSaved(){$('#savedn').textContent=SAVED.size||''}
function openLb(id,list,push){const i=ITEM[id];if(!i)return;LB.id=id;LB.list=list.includes(id)?list:[id];
 LB.dev=i.images[S.dev]?S.dev:pick(i,S.dev).k;const url=`#/brand/${i.brand}/${i.component}`;
 if(push){if(LB.pushed&&!$('#lb').hidden)history.replaceState(null,'',url);else{history.pushState(null,'',url);LB.pushed=true}}
 LB.url=location.hash;drawLb();$('#lb').hidden=false;document.body.style.overflow='hidden'}
function drawLb(){const i=ITEM[LB.id],im=i.images,b=BR[i.brand]||{};
 $('#lbt').innerHTML=`<a href="#/brand/${i.brand}" id="lbbrand">${esc(i.brandName)}</a>${esc(i.componentLabel)}`;
 $('#lbdev').innerHTML=['desktop','mobile','combined'].filter(d=>d!='combined'||im.combined).map(d=>`<button data-ld="${d}" class="${LB.dev==d?'on':''}" ${im[d]?'':'disabled'} title="${d}">${ICON[d]}</button>`).join('');
 $('#lbbm').innerHTML=`<button data-bm="${i.id}" class="bm ${SAVED.has(i.id)?'on':''}" title="Save" aria-label="Save">${ICON.bm}</button>`;
 const box=$('#lbimg');box.className='lbimg '+(LB.dev=='mobile'?'mob':'');box.innerHTML=`<img src="${im[LB.dev]}" alt="${esc(i.brandName+' — '+i.componentLabel+' ('+LB.dev+')')}">`;box.scrollTop=0;
 const n=LB.list.indexOf(i.id);$('#lbprev').disabled=n<=0;$('#lbnext').disabled=n<0||n>=LB.list.length-1;
 $('#lbside').innerHTML=`<div><h4>Why it converts</h4><p class="note">${esc(i.note)}</p></div>
 <div class="acts"><button class="btn p" id="lbcopy">Copy notes</button>${Object.keys(im).map(k=>`<a class="btn" href="${im[k]}" download="${i.brand}-${i.component}-${k}.jpg">↓ ${k[0].toUpperCase()+k.slice(1)}</a>`).join('')}</div>
 <dl class="kv"><dt>Brand</dt><dd><a href="#/brand/${i.brand}">${esc(i.brandName)}</a></dd><dt>Component</dt><dd>${esc(i.componentLabel)}</dd><dt>Region</dt><dd>${esc(i.country)}</dd><dt>Category</dt><dd>${esc(i.category)}</dd>
 ${i.platform?`<dt>Platform</dt><dd>${esc(i.platform)}</dd>`:''}<dt>Agency</dt><dd>${known(i.agency)?(b.agency_source&&/^http/.test(b.agency_source)?`<a href="${esc(b.agency_source)}" target="_blank" rel="noopener">${esc(i.agency)}</a>`:esc(i.agency)):'Not verified'}</dd>
 <dt>Added</dt><dd>${fmtDate(i.added)}</dd>${i.url?`<dt>Live</dt><dd><a href="${esc(i.url)}" target="_blank" rel="noopener">Visit the website ↗</a></dd>`:''}</dl>
 ${i.brandWhy?`<div><h4>Brand notes</h4><p style="color:var(--mut)">${esc(i.brandWhy)}</p></div>`:''}
 <div><h4>Tags</h4><div class="tagl">${(i.tags||[]).filter(Boolean).slice(0,14).map(t=>`<a href="#/all" data-tag="${esc(t)}">${esc(t)}</a>`).join('')}</div></div>`;
 $('#lbcopy').onclick=()=>copyNotes(i);
 $$('#lbside [data-tag]').forEach(a=>a.onclick=e=>{e.preventDefault();S.q=a.dataset.tag;$('#q').value=S.q;closeLb(()=>{location.hash='#/all';if(rendered=='all')renderBase(['all'])})});
 $$('[data-ld]').forEach(x=>x.onclick=()=>{LB.dev=x.dataset.ld;drawLb()});
 $('#lbbrand').onclick=e=>{e.preventDefault();closeLb(()=>{location.hash='#/brand/'+i.brand})}}
function copyNotes(i){const base=location.origin+location.pathname.replace(/[^/]*$/,'');
 const t=`${i.brandName} — ${i.componentLabel}\n${i.url}\nLibrary: ${base}#/brand/${i.brand}/${i.component}\nRegion: ${i.country} | Category: ${i.category} | Agency: ${i.agency} | Platform: ${i.platform}\nWhy it converts: ${i.note}\nBrand notes: ${i.brandWhy}\nImages: ${Object.values(i.images).map(p=>base+p).join(' , ')}`;
 (navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(()=>toast('Notes copied'),()=>{const ta=document.createElement('textarea');ta.value=t;document.body.append(ta);ta.select();try{document.execCommand('copy');toast('Notes copied')}catch(e){toast('Copy failed')}ta.remove()})}
function step(d){const n=LB.list.indexOf(LB.id)+d;if(n<0||n>=LB.list.length)return;const i=ITEM[LB.list[n]];LB.id=i.id;
 LB.dev=i.images[S.dev]?S.dev:pick(i,S.dev).k;history.replaceState(null,'',`#/brand/${i.brand}/${i.component}`);LB.url=location.hash;drawLb()}
function hideLb(){$('#lb').hidden=true;document.body.style.overflow='';LB.url=null;LB.pushed=false}
function closeLb(then){if($('#lb').hidden)return;const i=ITEM[LB.id];
 if(LB.pushed){LB.pushed=false;LB.url=null;history.back();if(then)setTimeout(then,60);return}
 hideLb();if(then)then();else location.hash='#/brand/'+i.brand}
$('#lbx').onclick=()=>closeLb();$('#lbprev').onclick=()=>step(-1);$('#lbnext').onclick=()=>step(1);
$('#lb').addEventListener('click',e=>{if(e.target.id=='lb')closeLb()});
