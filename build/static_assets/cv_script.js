/* MOBILE MENU */
function toggleMenu(){
  const menu = document.getElementById('mobile-menu');
  const btn = document.querySelector('.hamburger');
  if(!menu) return;
  const isOpen = menu.classList.toggle('open');
  if(btn) btn.setAttribute('aria-expanded', String(isOpen));
}
function closeMenu(){
  document.getElementById('mobile-menu')?.classList.remove('open');
  document.querySelector('.hamburger')?.setAttribute('aria-expanded','false');
}

function syncPressed(container){
  document.querySelectorAll(container + ' .filter-btn').forEach(btn => {
    btn.setAttribute('aria-pressed', btn.classList.contains('active') ? 'true' : 'false');
  });
}

/* Metrics are cached at build time from data/profile.csv. */

/* ── CACHED METRICS ───────────────────────────────────────────────────────────
   Citation metrics are injected at build time from data/profile.csv.
   The public page does not scrape metrics in the browser.
──────────────────────────────────────────────────────────────────────────────── */
function initCachedMetrics(){
  document.querySelectorAll('.metrics-updated').forEach(el => {
    el.setAttribute('aria-live', 'polite');
  });
}

/* ── PUBLICATIONS ─────────────────────────────────────────────────────────────
   The `publications` array is injected by build_html.py immediately before this
   script block. Each entry: {n, year, type, title, authors, journal, url,
   tags[], cat[], keywords[], highlight_topics[], featured}
──────────────────────────────────────────────────────────────────────────────── */

const mainGroupSubs = {
  'surgery':          ['bariatric','endocrine','gi','oncology','ortho','plastic','thoracic','transplant','urosurg','vascular'],
  'internal_medicine':['derm','infectious','neuro','pulm','urology'],
  'ai':               ['computer_vision','machine_learning'],
  'health_sciences':  ['education','epidemiology','health_systems','pubhealth'],
};

/* Multi-select dropdown filter state */
let pubTypeSelections  = [];  // [] = all
let pubTagSelections   = [];  // [] = all
let currentCat         = 'all';
let currentSearch      = '';
let showingAll         = false;
const SHOW             = 25;

function boldName(str){
  return str.replace(/(Shahriarirad R\*?)/g,'<b>$1</b>');
}

function computeTags(authors){
  const tags = [];
  if(/Shahriarirad R\*/.test(authors)) tags.push('corresponding');
  const parts     = authors.split(',').map(s=>s.trim()).filter(s=>s.length>0);
  const realParts = parts.filter(s=>!/^et\s+al/i.test(s));
  const pos       = realParts.findIndex(s=>s.includes('Shahriarirad R'));
  if(pos===0) tags.push('first');
  else if(pos===1) tags.push('co-first');
  if(realParts.length>0 && realParts[realParts.length-1].includes('Shahriarirad R') && pos!==0)
    tags.push('last');
  return tags;
}

function renderPubs(){
  const list    = document.getElementById('pub-list');
  const countEl = document.getElementById('pub-count');
  const moreEl  = document.getElementById('pub-more');

  const typeMap  = {original:'Original Article',review:'Review / Meta-analysis',case:'Case Report',letter:'Letter'};
  const classMap = {original:'badge-original',review:'badge-review',case:'badge-case',letter:'badge-letter'};

  const sorted = [...publications].sort((a,b) => {
    const yd = parseInt(b.year) - parseInt(a.year);
    if(yd!==0) return yd;
    const monthOrd={Jan:1,Feb:2,Mar:3,Apr:4,May:5,Jun:6,Jul:7,Aug:8,Sep:9,Oct:10,Nov:11,Dec:12};
    return (monthOrd[b.month]||0)-(monthOrd[a.month]||0);
  });

  let filtered = sorted.filter(p => {
    /* ── Type filter (multi-select OR) ── */
    let matchType = true;
    if(pubTypeSelections.length > 0){
      matchType = pubTypeSelections.some(sel => {
        if(sel==='original') return p.type==='original';
        if(sel==='review')   return p.type==='review';
        if(sel==='case')     return p.type==='case';
        if(sel==='letter')   return p.type==='letter';
        return false;
      });
    }

    /* ── Authorship filter (multi-select OR) ── */
    let matchTag = true;
    if(pubTagSelections.length > 0){
      const tags = (p.tags && p.tags.length > 0) ? p.tags : computeTags(p.authors);
      matchTag = pubTagSelections.some(sel => tags.includes(sel));
    }

    /* ── Category filter ── */
    let matchCat = true;
    if(currentCat !== 'all'){
      if(currentCat.startsWith('main:')){
        const groupSubs = mainGroupSubs[currentCat.slice(5)] || [];
        matchCat = Array.isArray(p.cat) && p.cat.some(c => groupSubs.includes(c));
      } else {
        matchCat = Array.isArray(p.cat) && p.cat.includes(currentCat);
      }
    }

    /* ── Search (title + authors + journal + keywords) ── */
    const q = currentSearch.toLowerCase();
    let matchSearch = true;
    if(q){
      const kw = Array.isArray(p.keywords) ? p.keywords.join(' ') : (p.keywords||'');
      matchSearch = p.title.toLowerCase().includes(q)
                 || p.authors.toLowerCase().includes(q)
                 || p.journal.toLowerCase().includes(q)
                 || kw.toLowerCase().includes(q);
    }

    return matchType && matchTag && matchCat && matchSearch;
  });

  /* ── Highlight topics: sort matching pubs to top when cat filter active ── */
  if(currentCat !== 'all' && !currentCat.startsWith('main:')){
    const activeCat = currentCat;
    filtered = [
      ...filtered.filter(p => Array.isArray(p.highlight_topics) && p.highlight_topics.includes(activeCat)),
      ...filtered.filter(p => !(Array.isArray(p.highlight_topics) && p.highlight_topics.includes(activeCat))),
    ];
  }

  const displayed = showingAll ? filtered : filtered.slice(0, SHOW);
  countEl.textContent = `Showing ${displayed.length} of ${filtered.length}`;
  moreEl.style.display = (filtered.length > SHOW && !showingAll) ? 'block' : 'none';

  list.innerHTML = displayed.map(p => {
    const ym    = p.month ? `${p.month} ${p.year}` : p.year;
    const badge = `<span class="pub-type-badge ${classMap[p.type]||'badge-original'}">${typeMap[p.type]||p.type}</span>`;
    const star  = p.featured === 'yes' ? '<span class="pub-star-badge" title="Featured publication">&#11088;</span>' : '';
    const titleHtml = p.url ? `<a href="${p.url}" target="_blank" rel="noopener noreferrer">${p.title}</a>` : p.title;
    const authHtml  = boldName(p.authors);
    return `<div class="pub-item">
      <div class="pub-year-col">${ym}${badge}${star}</div>
      <div>
        <div class="pub-title">${titleHtml}</div>
        <div class="pub-authors">${authHtml}</div>
        <div class="pub-journal"><em>${p.journal}</em></div>
      </div>
    </div>`;
  }).join('');
}

function showAllPubs(){ showingAll=true; renderPubs(); }

function resetPubFilters(){
  pubTypeSelections=[]; pubTagSelections=[]; currentCat='all'; currentSearch=''; showingAll=false;
  ['pub-type-panel','pub-auth-panel'].forEach(id=>{
    const panel=document.getElementById(id);
    if(!panel) return;
    panel.querySelectorAll('input[type=checkbox]').forEach(c=>{
      c.checked=false;
      const opt=c.closest('.custom-dropdown-option');
      if(opt){ opt.classList.remove('selected'); opt.setAttribute('aria-selected','false'); }
    });
  });
  ['pub-type-btn','pub-auth-btn'].forEach(id=>{
    const btn=document.getElementById(id);
    if(!btn) return;
    btn.classList.remove('has-selection','open');
    btn.setAttribute('aria-expanded','false');
    const lbl=btn.querySelector('.dropdown-label');
    if(lbl) lbl.textContent=lbl.dataset.default||lbl.textContent;
  });
  document.querySelectorAll('.pub-filter-sidebar .filter-main-btn,.pub-filter-sidebar .filter-sub-btn')
    .forEach(b=>b.classList.remove('active','has-active','open'));
  document.querySelectorAll('.pub-filter-sidebar .filter-sub-group')
    .forEach(g=>g.style.display='none');
  document.getElementById('cat-all-btn')?.classList.add('active');
  const s=document.getElementById('pub-search');
  if(s) s.value='';
  syncPressed('.pub-filter-sidebar');
  renderPubs();
}

/* ── Topic category filter (tree buttons in sidebar) ── */
function filterPubsMain(btn){
  const groupKey = btn.dataset.group;
  const isActive = btn.classList.contains('active') && currentCat === 'main:'+groupKey;
  showingAll = false;
  document.querySelectorAll('.pub-filter-sidebar .filter-main-btn,.pub-filter-sidebar .filter-sub-btn')
    .forEach(b=>b.classList.remove('active','has-active','open'));
  document.getElementById('cat-all-btn')?.classList.remove('active');
  const sub = document.getElementById('grp-'+groupKey);
  if(isActive){
    if(sub) sub.style.display = 'none';
    currentCat = 'all';
    document.getElementById('cat-all-btn')?.classList.add('active');
  } else {
    if(sub) sub.style.display = 'block';
    btn.classList.add('active','has-active','open');
    currentCat = 'main:'+groupKey;
  }
  syncPressed('.pub-filter-sidebar');
  renderPubs();
}

function filterPubs(val, btn, dimension){
  showingAll = false;
  if(dimension === 'cat'){
    currentCat = val;
    document.querySelectorAll('.pub-filter-sidebar .filter-main-btn,.pub-filter-sidebar .filter-sub-btn')
      .forEach(b=>b.classList.remove('active','has-active'));
    document.getElementById('cat-all-btn')?.classList.remove('active');
    if(val === 'all'){
      document.getElementById('cat-all-btn')?.classList.add('active');
    } else {
      btn.classList.add('active');
      const parent = btn.closest('.filter-main-group')?.querySelector('.filter-main-btn');
      if(parent) parent.classList.add('has-active');
      const sub = btn.closest('.filter-sub-group');
      if(sub){ sub.style.display='block'; sub.previousElementSibling?.classList.add('open'); }
    }
  }
  syncPressed('.pub-filter-sidebar');
  renderPubs();
}

/* ── Custom multi-select dropdown ─────────────────────────────────────────── */
function initCustomDropdown(btnId, panelId, defaultLabel, onChangeCallback){
  const btn   = document.getElementById(btnId);
  const panel = document.getElementById(panelId);
  if(!btn || !panel) return;

  btn.addEventListener('click', e => {
    e.stopPropagation();
    const isOpen = panel.classList.contains('open');
    document.querySelectorAll('.custom-dropdown-panel.open').forEach(p=>p.classList.remove('open'));
    document.querySelectorAll('.custom-dropdown-btn.open').forEach(b=>b.classList.remove('open'));
    if(!isOpen){
      panel.classList.add('open');
      btn.classList.add('open');
    }
    btn.setAttribute('aria-expanded', String(!isOpen));
  });

  panel.addEventListener('click', e => {
    const opt = e.target.closest('.custom-dropdown-option');
    if(!opt) return;
    const val = opt.dataset.value;
    const chk = opt.querySelector('input[type=checkbox]');
    if(val === 'all'){
      panel.querySelectorAll('input[type=checkbox]').forEach(c=>{c.checked=false;c.closest('.custom-dropdown-option').classList.remove('selected')});
    } else {
      if(chk){
        chk.checked = !chk.checked;
        opt.classList.toggle('selected', chk.checked);
        opt.setAttribute('aria-selected', chk.checked ? 'true' : 'false');
      }
      panel.querySelector('[data-value=all]')?.classList.remove('selected');
    }
    const selected = [...panel.querySelectorAll('input[type=checkbox]:checked')].map(c=>c.value);
    btn.classList.toggle('has-selection', selected.length > 0);
    const label = btn.querySelector('.dropdown-label');
    if(label) label.textContent = selected.length === 0 ? defaultLabel : (selected.length === 1 ? panel.querySelector(`[data-value="${selected[0]}"] .opt-label`)?.textContent||defaultLabel : `${selected.length} selected`);
    onChangeCallback(selected);
  });
}

document.addEventListener('click', () => {
  document.querySelectorAll('.custom-dropdown-panel.open').forEach(p=>p.classList.remove('open'));
  document.querySelectorAll('.custom-dropdown-btn.open').forEach(b=>{b.classList.remove('open'); b.setAttribute('aria-expanded','false');});
});

/* ── Research topic tag click → scroll to publications + apply filter ── */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.research-tag[data-cat]').forEach(tag => {
    tag.addEventListener('click', () => {
      const cat = tag.dataset.cat;
      currentCat = cat;
      showingAll  = false;
      document.querySelectorAll('.pub-filter-sidebar .filter-main-btn,.pub-filter-sidebar .filter-sub-btn')
        .forEach(b=>b.classList.remove('active','has-active'));
      document.getElementById('cat-all-btn')?.classList.remove('active');
      const btn = document.querySelector(`.filter-sub-btn[data-cat="${cat}"]`);
      if(btn){
        btn.classList.add('active');
        const parent = btn.closest('.filter-main-group')?.querySelector('.filter-main-btn');
        if(parent){ parent.classList.add('has-active','open'); }
        const sub = btn.closest('.filter-sub-group');
        if(sub) sub.style.display = 'block';
      }
      renderPubs();
      document.getElementById('publications')?.scrollIntoView({behavior:'smooth'});
    });
  });

  /* ── Init publication type dropdown ── */
  initCustomDropdown('pub-type-btn','pub-type-panel','All Types', selected => {
    pubTypeSelections = selected; showingAll=false; renderPubs();
  });

  /* ── Init authorship dropdown ── */
  initCustomDropdown('pub-auth-btn','pub-auth-panel','All Roles', selected => {
    pubTagSelections = selected; showingAll=false; renderPubs();
  });

  /* ── Init presentation type dropdown ── */
  initCustomDropdown('pres-type-btn','pres-type-panel','All Types', selected => {
    presDropFilters.type = selected; applyPresFilters();
  });

  /* ── Init presentation location dropdown ── */
  initCustomDropdown('pres-loc-btn','pres-loc-panel','All Locations', selected => {
    presDropFilters.location = selected; applyPresFilters();
  });

  renderPubs();
  renderRepos();
  renderRefs();
  renderJournals();
  initCachedMetrics();
  syncPressed('.pub-filter-sidebar');
  syncPressed('.pres-filter-sidebar');
});

/* ── JOURNALS REVIEWED ── */
function renderJournals(){
  const el = document.getElementById('journal-grid');
  if(!el) return;
  el.innerHTML = journals.map(j =>
    j.url
      ? `<a href="${j.url}" target="_blank" rel="noopener noreferrer" class="journal-pill">${j.name} ↗</a>`
      : `<span class="journal-pill">${j.name}</span>`
  ).join('');
}

/* ── PRESENTATIONS FILTER ─────────────────────────────────────────────────── */
let presFilters    = {cat: null, search: ''};
let presDropFilters= {type: [], location: []};

function filterPresMain(btn){
  const groupKey = btn.dataset.group;
  const isActive = btn.classList.contains('active') && presFilters.cat === 'main:'+groupKey;
  document.querySelectorAll('.pres-filter-sidebar .filter-main-btn,.pres-filter-sidebar .filter-sub-btn')
    .forEach(b=>b.classList.remove('active','has-active','open'));
  const sub = document.getElementById('pgrp-'+groupKey);
  if(isActive){
    if(sub) sub.style.display='none';
    presFilters.cat = null;
  } else {
    if(sub) sub.style.display='block';
    btn.classList.add('active','has-active','open');
    presFilters.cat = 'main:'+groupKey;
  }
  syncPressed('.pres-filter-sidebar');
  applyPresFilters();
}

function filterPres(dim, val, btn){
  if(presFilters[dim] === val){
    presFilters[dim] = null; btn.classList.remove('active');
    if(dim==='cat') btn.closest('.filter-main-group')?.querySelector('.filter-main-btn')?.classList.remove('has-active');
  } else {
    btn.closest('.pres-filter-group')?.querySelectorAll('.filter-btn:not(.filter-main-btn)').forEach(b=>b.classList.remove('active'));
    presFilters[dim] = val; btn.classList.add('active');
    if(dim==='cat'){
      const parent = btn.closest('.filter-main-group')?.querySelector('.filter-main-btn');
      if(parent) parent.classList.add('has-active');
      const sub = btn.closest('.filter-sub-group');
      if(sub){ sub.style.display='block'; sub.previousElementSibling?.classList.add('open'); }
    }
  }
  syncPressed('.pres-filter-sidebar');
  applyPresFilters();
}

function resetPresFilters(btn){
  presFilters = {cat:null, search:''};
  presDropFilters = {type:[], location:[]};
  document.querySelectorAll('.pres-filter-sidebar .filter-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  const searchEl = document.getElementById('pres-search');
  if(searchEl) searchEl.value='';
  /* Reset dropdowns */
  ['pres-type-panel','pres-loc-panel'].forEach(id=>{
    const panel=document.getElementById(id);
    if(panel) panel.querySelectorAll('input[type=checkbox]').forEach(c=>{c.checked=false;c.closest('.custom-dropdown-option').classList.remove('selected');});
  });
  ['pres-type-btn','pres-loc-btn'].forEach(id=>{
    const btn=document.getElementById(id);
    if(btn){ btn.classList.remove('has-selection','open'); const lbl=btn.querySelector('.dropdown-label'); if(lbl) lbl.textContent=lbl.dataset.default; }
  });
  syncPressed('.pres-filter-sidebar');
  applyPresFilters();
}

function filterPresSearch(q){
  presFilters.search = q.toLowerCase();
  applyPresFilters();
}

function applyPresFilters(){
  const items = document.querySelectorAll('#pres-list .pres-item');
  let shown = 0;
  items.forEach(item => {
    const type = item.dataset.type || '';
    const loc  = item.dataset.location || '';
    const cats = (item.dataset.cats || '').split(',').filter(Boolean);
    const text = item.textContent.toLowerCase();

    let catMatch = true;
    if(presFilters.cat){
      if(presFilters.cat.startsWith('main:')){
        const groupSubs = mainGroupSubs[presFilters.cat.slice(5)] || [];
        catMatch = cats.some(c=>groupSubs.includes(c));
      } else {
        catMatch = cats.includes(presFilters.cat);
      }
    }

    const typeOk = presDropFilters.type.length===0 || presDropFilters.type.includes(type);
    const locOk  = presDropFilters.location.length===0 || presDropFilters.location.some(l=>loc.includes(l));

    const ok = typeOk && locOk && catMatch && (!presFilters.search || text.includes(presFilters.search));
    item.style.display = ok ? '' : 'none';
    if(ok) shown++;
  });
  const countEl = document.getElementById('pres-count');
  if(countEl) countEl.textContent = shown + ' presentation' + (shown!==1?'s':'');
}

/* ── REFERENCES ── */
function renderRefs(){
  const el = document.getElementById('refs-grid');
  if(!el) return;
  el.innerHTML = refs.map(r=>`
  <div class="ref-card">
    <div class="ref-name">${r.name}</div>
    <div class="ref-role">${r.role}<br><em style="font-size:.73rem">${r.inst}</em></div>
    <div class="ref-links" style="margin-top:.7rem">${r.links.map(l=>`<a href="${l.url}" target="_blank" rel="noopener noreferrer" class="ref-link">${l.label} ↗</a>`).join('')}</div>
  </div>`).join('');
}

/* ── OPEN SOURCE REPOS ── */
function renderRepos(){
  const grid = document.getElementById('repos-grid');
  if(!grid) return;
  if(!openSourceRepos.length){ grid.innerHTML=''; return; }
  const langColor={Python:'#3572A5',R:'#198CE7',JavaScript:'#f1e05a',TypeScript:'#2b7489',MATLAB:'#e16737',Shell:'#89e051'};
  grid.innerHTML = openSourceRepos.map(r=>{
    const lc = langColor[r.language]||'#6b84a0';
    const langEl = r.language ? `<span class="repo-lang" style="border-color:${lc}50;color:${lc}">${r.language}</span>` : '';
    const links = [
      r.url   ? `<a href="${r.url}"   target="_blank" rel="noopener noreferrer" class="repo-link primary">GitHub ↗</a>` : '',
      r.demo  ? `<a href="${r.demo}"  target="_blank" rel="noopener noreferrer" class="repo-link">Demo ↗</a>` : '',
      r.paper ? `<a href="${r.paper}" target="_blank" rel="noopener noreferrer" class="repo-link">Paper ↗</a>` : '',
    ].filter(Boolean).join('');
    return `<div class="repo-card">
      <div class="repo-card-header">
        <span class="repo-card-icon">${r.icon||'🔬'}</span>
        <span class="repo-card-name">${r.url?`<a href="${r.url}" target="_blank" rel="noopener noreferrer">${r.name}</a>`:r.name}</span>
        ${langEl}
      </div>
      ${r.desc?`<p class="repo-desc">${r.desc}</p>`:''}
      ${links?`<div class="repo-links">${links}</div>`:''}
    </div>`;
  }).join('');
}

/* ── EMAIL PROTECTION ── */
document.addEventListener('DOMContentLoaded', function(){
  document.querySelectorAll('a.cf-email').forEach(function(a){
    const email = a.dataset.u + '@' + a.dataset.d;
    if(!a.dataset.keepContent){
      a.textContent = a.dataset.label || email;
    }
    a.href = 'mai'+'lto:'+email;
    if(!a.getAttribute('aria-label')){
      a.setAttribute('aria-label', email);
    }
  });
});
