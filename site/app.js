let D,S={q:'',type:'all',region:'all',agency:'all',device:'all',cat:'all'};
const $=s=>document.querySelector(s),esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const toast=m=>{const t=$('#toast');t.textContent=m;t.classList.add('on');setTimeout(()=>t.classList.remove('on'),1600)};
const daysAgo=d=>(Date.now()-new Date(d))/864e5;
fetch('data.json?v='+Date.now()).then(r=>r.json()).then(d=>{D=d;D.items.forEach(i=>i._s=[i.brandName,i.component,i.componentLabel,i.region,i.country,i.agency,i.platform,i.category,i.note,i.brandWhy,...i.tags].join(' ').toLowerCase());
 const p=new URLSearchParams(location.search);if(p.get('q'))S.q=p.get('q');$('#q').value=S.q;route()});
addEventListener('hashchange',route);
$('#q').addEventListener('input',e=>{S.q=e.target.value;if(!location.hash.startsWith('#/')||location.hash.length>2&&location.hash!=='#/'){location.hash='#/'}else render()});
addEventListener('keydown',e=>{if(e.key=='/'&&document.activeElement!==$('#q')){e.preventDefault();$('#q').focus()}if(e.key=='Escape')closeLb()});
function route(){const h=location.hash.slice(2);if(h.startsWith('brand/'))brandPage(h.slice(6));else if(h=='brands')brandsPage();else if(h=='agencies')agenciesPage();else render();scrollTo(0,0)}
function match(i){if(S.type!='all'&&i.component!=S.type)return false;if(S.region!='all'&&i.region!=S.region)return false;
 if(S.agency=='known'&&/^unknown/i.test(i.agency))return false;if(S.agency!='all'&&S.agency!='known'&&i.agency!=S.agency)return false;
 if(S.device!='all'&&!i.images[S.device])return false;if(S.cat!='all'&&i.category!=S.cat)return false;
 return S.q.toLowerCase().split(/\s+/).filter(Boolean).every(w=>i._s.includes(w))}
function card(i){const im=i.images,dv=S.device;let sh='';
 const one=(k,cls)=>`<div class="shot ${cls}" data-src="${im[k]}" data-cap="${esc(i.brandName+' · '+i.componentLabel+' · '+k)}"><img loading="lazy" src="${im[k]}" alt="${esc(i.brandName+' '+i.componentLabel+' '+k)}"><i>${k}</i></div>`;
 if(dv!='all'&&im[dv])sh=one(dv,'');else{if(im.desktop)sh+=one('desktop','');if(im.mobile)sh+=one('mobile',im.desktop?'m':'');if(im.combined)sh+=one('combined','')}
 const ag=/^unknown/i.test(i.agency)?'':`<span class="tag ag">by ${esc(i.agency)}</span>`;
 return `<article class="card"><div class="shots">${sh}</div><div class="cb"><div class="ct"><b>${esc(i.componentLabel)}</b><a href="#/brand/${i.brand}">${esc(i.brandName)} →</a></div>
 <div class="meta"><span class="tag ${i.region=='India'?'in':''}">${i.region=='India'?'🇮🇳 India':esc(i.country)}</span>${ag}<span class="tag">${esc(i.category)}</span>${daysAgo(i.added)<8?'<span class="tag in">NEW</span>':''}</div>
 <p class="note">${esc(i.note)}</p><div class="acts"><button class="btn p" data-copy="${i.id}">Copy notes</button>${Object.keys(im).map(k=>`<a class="btn" href="${im[k]}" download>⬇ ${k}</a>`).join('')}</div></div></article>`}
function bind(){document.querySelectorAll('.shot').forEach(s=>s.onclick=()=>openLb(s.dataset.src,s.dataset.cap));
 document.querySelectorAll('[data-copy]').forEach(b=>b.onclick=()=>{const i=D.items.find(x=>x.id==b.dataset.copy);
  const t=`${i.brandName} — ${i.componentLabel}\n${i.url}\nRegion: ${i.country} | Agency: ${i.agency} | Platform: ${i.platform}\nWhy it converts: ${i.note}\nBrand notes: ${i.brandWhy}\nImages: ${Object.values(i.images).map(p=>location.origin+location.pathname.replace(/[^/]*$/,'')+p).join(' , ')}`;
  navigator.clipboard.writeText(t).then(()=>toast('Notes copied'),()=>toast('Copy failed'))})}
function openLb(src,cap){$('#lbimg').src=src;$('#lbcap').textContent=cap;$('#lbdl').href=src;$('#lb').hidden=false}
function closeLb(){$('#lb').hidden=true}$('#lb').onclick=e=>{if(e.target.id=='lb'||e.target.classList.contains('lbx'))closeLb()};
function opts(arr,cur){return arr.map(([v,l])=>`<option value="${esc(v)}" ${v==cur?'selected':''}>${esc(l)}</option>`).join('')}
function render(){const it=D.items.filter(match),T=D.types;
 const cnt={};D.items.forEach(i=>cnt[i.component]=(cnt[i.component]||0)+1);
 const ags=[...new Set(D.items.map(i=>i.agency).filter(a=>!/^unknown/i.test(a)))].sort(),cats=[...new Set(D.items.map(i=>i.category))].sort();
 const fresh=D.items.filter(i=>daysAgo(i.added)<8),filtering=S.q||S.type!='all'||S.region!='all'||S.agency!='all'||S.device!='all'||S.cat!='all';
 $('#app').innerHTML=`<section class="heroband"><div class="wrap"><h1>Find any e-commerce component in seconds.</h1><p>Hero, product cards, sticky add-to-cart, bundles, reviews… captured from India's newest D2C brands, top Indian Shopify agency builds and international award winners. Desktop + mobile, searchable, copyable, downloadable.</p>
 <div class="stats"><div><b>${D.brands.length}</b><span>brands</span></div><div><b>${D.items.length}</b><span>components</span></div><div><b>${D.brands.filter(b=>b.region=='India').length}</b><span>Indian brands</span></div><div><b>${ags.length}</b><span>verified agencies</span></div><div><b style="font-size:15px;line-height:2.1">${esc(D.built)}</b><span>last update</span></div></div></div></section>
 <div class="wrap"><div class="chips">${[['all','All',D.items.length],...Object.entries(T).filter(([k])=>cnt[k]).map(([k,v])=>[k,v.label,cnt[k]])].map(([k,l,c])=>`<button class="chip ${S.type==k?'on':''}" data-t="${k}">${esc(l)}<small>${c}</small></button>`).join('')}</div>
 <div class="filters"><div class="seg">${['all','India','International'].map(r=>`<button data-r="${r}" class="${S.region==r?'on':''}">${r=='all'?'All regions':r=='India'?'🇮🇳 India':'🌍 International'}</button>`).join('')}</div>
 <div class="seg">${['all','desktop','mobile'].map(r=>`<button data-d="${r}" class="${S.device==r?'on':''}">${r=='all'?'All devices':r}</button>`).join('')}</div>
 <select id="ag">${opts([['all','Any agency'],['known','Agency known'],...ags.map(a=>[a,a])],S.agency)}</select>
 <select id="cat">${opts([['all','Any category'],...cats.map(a=>[a,a])],S.cat)}</select><span class="count">${it.length} results</span></div>
 ${!filtering&&fresh.length?`<h2 class="sec">New this week <span class="pill">${fresh.length}</span></h2><div class="grid">${fresh.slice(0,9).map(card).join('')}</div><h2 class="sec">All components</h2>`:''}
 <div class="grid">${it.map(card).join('')||'<div class="empty">No components match. Try "card", "sticky", "bundle" or a brand name.</div>'}</div></div><footer class="f">Screenshots captured from public websites for design inspiration. Updated daily · ${esc(D.built)}</footer>`;
 document.querySelectorAll('[data-t]').forEach(b=>b.onclick=()=>{S.type=b.dataset.t;render()});document.querySelectorAll('[data-r]').forEach(b=>b.onclick=()=>{S.region=b.dataset.r;render()});
 document.querySelectorAll('[data-d]').forEach(b=>b.onclick=()=>{S.device=b.dataset.d;render()});$('#ag').onchange=e=>{S.agency=e.target.value;render()};$('#cat').onchange=e=>{S.cat=e.target.value;render()};bind()}
function brandsPage(){const bs=[...D.brands].sort((a,b)=>(b.region=='India')-(a.region=='India')||b.added.localeCompare(a.added));
 const th=b=>{const i=D.items.find(x=>x.brand==b.slug&&x.component=='hero')||D.items.find(x=>x.brand==b.slug);return i?Object.values(i.images)[0]:''};
 $('#app').innerHTML=`<div class="wrap"><div class="bhead"><h1>Brands</h1><p>${bs.length} brands · Indian first. Agency shown only where verified from the agency's own case study/portfolio.</p></div><div class="bgrid">${bs.map(b=>`<a class="bcard card" href="#/brand/${b.slug}"><img loading="lazy" src="${th(b)}" alt=""><div><b>${esc(b.name)}</b><div class="meta" style="margin-top:6px"><span class="tag ${b.region=='India'?'in':''}">${b.region=='India'?'🇮🇳 India':esc(b.country)}</span>${/^unknown/i.test(b.agency||'Unknown')?'':`<span class="tag ag">by ${esc(b.agency)}</span>`}<span class="tag">${b.count} components</span></div></div></a>`).join('')}</div></div>`}
function brandPage(slug){const b=D.brands.find(x=>x.slug==slug);if(!b)return render();const it=D.items.filter(i=>i.brand==slug);
 $('#app').innerHTML=`<div class="wrap"><div class="bhead"><a href="#/brands" style="color:var(--acc);font-weight:600;font-size:13px">← All brands</a><h1>${esc(b.name)}</h1>
 <div class="meta"><span class="tag ${b.region=='India'?'in':''}">${esc(b.country)}</span><span class="tag">${esc(b.category)}</span><span class="tag">${esc(b.platform)}</span><span class="tag ag">Agency: ${esc(b.agency||'Unknown')}</span><span class="tag">Added ${esc(b.added)}</span></div>
 <p>${esc(b.why)}</p><p>${b.url?`<a class="btn p" href="${esc(b.url)}" target="_blank" rel="noopener">Visit site ↗</a>`:''} ${b.agency_source&&b.agency_source.startsWith('http')?`<a class="btn" href="${esc(b.agency_source)}" target="_blank" rel="noopener">Agency case study ↗</a>`:''}</p></div>
 <div class="grid">${it.map(card).join('')}</div></div>`;bind()}

function agenciesPage(){const th=s=>{const i=D.items.find(x=>x.brand==s&&x.component=='hero')||D.items.find(x=>x.brand==s);return i?Object.values(i.images)[0]:''};
 $('#app').innerHTML=`<div class="wrap"><div class="bhead"><h1>Indian Shopify agencies</h1><p>${D.agencies.length} agencies. Clients are shown only when the agency's own portfolio, case study or testimonial page names them; the source is linked on each brand page.</p></div>
 ${D.agencies.map(a=>{const cl=a.clients.map(s=>D.brands.find(b=>b.slug==s)).filter(Boolean);return `<section class="agency"><div class="ahead"><div><h2>${esc(a.name)}</h2><p>${esc(a.focus)}</p></div><a class="btn p" href="${esc(a.url)}" target="_blank" rel="noopener">Agency site ↗</a></div>
 <div class="bgrid">${cl.map(b=>`<a class="bcard card" href="#/brand/${b.slug}"><img loading="lazy" src="${th(b.slug)}" alt=""><div><b>${esc(b.name)}</b><div class="meta" style="margin-top:6px"><span class="tag ${b.region=='India'?'in':''}">${esc(b.country)}</span><span class="tag">${b.count} components</span></div></div></a>`).join('')||'<p class="empty">No verified client captured yet.</p>'}</div></section>`}).join('')}</div>`}
