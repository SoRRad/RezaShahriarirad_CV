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
  const authorText = String(authors || '');
  if(/Shahriarirad R\*/.test(authorText)) tags.push('corresponding');
  const parts     = authorText.split(',').map(s=>s.trim()).filter(s=>s.length>0);
  const realParts = parts.filter(s=>!/^et\s+al/i.test(s));
  const pos       = realParts.findIndex(s=>s.includes('Shahriarirad R'));
  if(pos===0) tags.push('first');
  else if(pos===1) tags.push('co-first');
  if(realParts.length>0 && realParts[realParts.length-1].includes('Shahriarirad R') && pos!==0)
    tags.push('last');
  return tags;
}

function uniqueValues(values){
  return [...new Set(values.filter(Boolean))];
}

function normalizedArray(values){
  return Array.isArray(values)
    ? values.map(v => String(v || '').trim().toLowerCase()).filter(Boolean)
    : [];
}

function getPubTags(pub){
  const aliases = {'senior':'last','last/senior':'last','cofirst':'co-first','co_first':'co-first'};
  const explicit = normalizedArray(pub.tags).map(tag => aliases[tag] || tag);
  return uniqueValues([...explicit, ...computeTags(pub.authors)]);
}

function getCategoryLabel(cat){
  return (typeof categoryLabels !== 'undefined' && categoryLabels[cat]) ? categoryLabels[cat] : cat;
}

function pubCategoryText(pub){
  return uniqueValues([...normalizedArray(pub.cat), ...normalizedArray(pub.highlight_topics)])
    .map(cat => `${cat} ${getCategoryLabel(cat)}`)
    .join(' ');
}

function pubMatchesCurrentHighlight(pub){
  if(currentCat === 'all') return false;
  const highlights = normalizedArray(pub.highlight_topics);
  if(currentCat.startsWith('main:')){
    const groupSubs = mainGroupSubs[currentCat.slice(5)] || [];
    return highlights.some(cat => groupSubs.includes(cat));
  }
  return highlights.includes(currentCat);
}

function escapeHtml(value){
  return String(value ?? '').replace(/[&<>"']/g, ch => ({
    '&':'&amp;',
    '<':'&lt;',
    '>':'&gt;',
    '"':'&quot;',
    "'":'&#39;'
  }[ch]));
}

function safeUrl(value){
  const url = String(value || '').trim();
  return /^https?:\/\//i.test(url) ? url : '';
}

function normalizeSearch(value){
  return String(value ?? '')
    .toLowerCase()
    .replace(/&/g, ' and ')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
}

function textMatchesSearch(text, query){
  const normalizedText = normalizeSearch(text);
  const terms = normalizeSearch(query).split(/\s+/).filter(Boolean);
  return terms.length === 0 || terms.every(term => normalizedText.includes(term));
}

function stopFilterEvent(event){
  event?.preventDefault?.();
  event?.stopPropagation?.();
}

function preserveScroll(callback){
  const x = window.scrollX;
  const y = window.scrollY;
  callback();
  window.requestAnimationFrame(() => window.scrollTo({top: y, left: x, behavior: 'auto'}));
}

function dedupeDisplayTags(values, limit=6){
  const out = [];
  const seen = new Set();
  (values || []).forEach(value => {
    const text = String(value || '').replace(/\s+/g, ' ').trim();
    if(!text) return;
    const key = text.toLowerCase();
    if(seen.has(key)) return;
    seen.add(key);
    out.push(text);
  });
  return out.slice(0, limit);
}

function pubDisplayTags(pub, typeMap){
  const cats = normalizedArray(pub.cat).map(getCategoryLabel);
  const highlights = normalizedArray(pub.highlight_topics).map(getCategoryLabel);
  const keywords = Array.isArray(pub.keywords) ? pub.keywords : [];
  const typeLabel = typeMap[String(pub.type || '').toLowerCase()] || '';
  return dedupeDisplayTags([...keywords, ...cats, ...highlights, typeLabel], 6);
}

const pubTypeFilterLabels = {original:'Original',review:'Review',case:'Case Report',letter:'Letter'};
const pubAuthFilterLabels = {first:'1st Author','co-first':'Co-first',corresponding:'Corresponding',last:'Last/Senior'};
const presTypeFilterLabels = {poster:'Poster',oral:'Oral'};

function getDropdownOptionLabel(panelId, value){
  const panel = document.getElementById(panelId);
  const key = String(value || '');
  if(!panel || !key) return '';
  const opt = [...panel.querySelectorAll('.custom-dropdown-option')]
    .find(option => option.dataset.value === key);
  const label = opt?.querySelector('.opt-label');
  return label ? label.textContent.trim() : '';
}

function selectedFilterLabels(values, labelsMap, panelId){
  return (values || [])
    .map(value => labelsMap[value] || getDropdownOptionLabel(panelId, value) || String(value || '').trim())
    .filter(Boolean);
}

function activeTopicLabel(value){
  if(!value || value === 'all') return '';
  const key = value.startsWith('main:') ? value.slice(5) : value;
  return getCategoryLabel(key);
}

function formatActiveFilterLabel(labels){
  return labels.filter(Boolean).join(' · ');
}

function setSearchPrefix(prefixId, inputId, label, defaultPlaceholder){
  const prefix = document.getElementById(prefixId);
  const input = document.getElementById(inputId);
  const hasLabel = Boolean(label);
  if(prefix){
    prefix.hidden = !hasLabel;
    prefix.textContent = hasLabel ? `/${label}:` : '';
  }
  if(input){
    input.placeholder = hasLabel ? 'Search within active filters...' : defaultPlaceholder;
    input.closest('.search-shell')?.classList.toggle('has-filter-prefix', hasLabel);
  }
}

function getPubActiveFilterLabel(){
  return formatActiveFilterLabel([
    ...selectedFilterLabels(pubTypeSelections, pubTypeFilterLabels, 'pub-type-panel'),
    ...selectedFilterLabels(pubTagSelections, pubAuthFilterLabels, 'pub-auth-panel'),
    activeTopicLabel(currentCat),
  ]);
}

function updatePubSearchPrefix(){
  setSearchPrefix('pub-search-prefix', 'pub-search', getPubActiveFilterLabel(), 'Search title, author, journal, keyword...');
}

function getPresActiveFilterLabel(){
  return formatActiveFilterLabel([
    ...selectedFilterLabels(presDropFilters.type, presTypeFilterLabels, 'pres-type-panel'),
    ...selectedFilterLabels(presDropFilters.location, {}, 'pres-loc-panel'),
    activeTopicLabel(presFilters.cat),
  ]);
}

function updatePresSearchPrefix(){
  setSearchPrefix('pres-search-prefix', 'pres-search', getPresActiveFilterLabel(), 'Search title or conference...');
}

function applyPubSearchTag(event, source){
  stopFilterEvent(event);
  const tag = source?.dataset?.tag || source?.textContent || '';
  const search = document.getElementById('pub-search');
  if(search) search.value = tag;
  currentSearch = tag;
  showingAll = false;
  updatePubSearchPrefix();
  preserveScroll(renderPubs);
}

function handlePubSearchInput(value){
  currentSearch = value;
  showingAll = false;
  updatePubSearchPrefix();
  preserveScroll(renderPubs);
}

function applyPresSearchTag(event, source){
  stopFilterEvent(event);
  const tag = source?.dataset?.tag || source?.textContent || '';
  const search = document.getElementById('pres-search');
  if(search) search.value = tag;
  presFilters.search = tag.toLowerCase();
  presShowingAll = false;
  updatePresSearchPrefix();
  preserveScroll(applyPresFilters);
}

function renderPubs(){
  const list    = document.getElementById('pub-list');
  const countEl = document.getElementById('pub-count');
  const moreEl  = document.getElementById('pub-more');
  if(!list) return;
  updatePubSearchPrefix();

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
      const tags = getPubTags(p);
      matchTag = pubTagSelections.some(sel => tags.includes(sel));
    }

    /* ── Category filter ── */
    let matchCat = true;
    if(currentCat !== 'all'){
      const cats = normalizedArray(p.cat);
      if(currentCat.startsWith('main:')){
        const groupSubs = mainGroupSubs[currentCat.slice(5)] || [];
        matchCat = cats.some(c => groupSubs.includes(c));
      } else {
        matchCat = cats.includes(currentCat);
      }
    }

    /* ── Search (title + authors + journal + keywords) ── */
    const q = normalizeSearch(currentSearch);
    let matchSearch = true;
    if(q){
      const searchText = [
        p.title,
        p.authors,
        p.journal,
        Array.isArray(p.keywords) ? p.keywords.join(' ') : '',
        getPubTags(p).join(' '),
        pubCategoryText(p),
      ].join(' ');
      matchSearch = textMatchesSearch(searchText, q);
    }

    return matchType && matchTag && matchCat && matchSearch;
  });

  /* ── Highlight topics: sort matching pubs to top when cat filter active ── */
  if(currentCat !== 'all'){
    filtered = [
      ...filtered.filter(pubMatchesCurrentHighlight),
      ...filtered.filter(p => !pubMatchesCurrentHighlight(p)),
    ];
  }

  const displayed = showingAll ? filtered : filtered.slice(0, SHOW);
  if(countEl) countEl.textContent = `Showing ${displayed.length} of ${filtered.length}`;
  if(moreEl) moreEl.style.display = (filtered.length > SHOW && !showingAll) ? 'block' : 'none';

  list.innerHTML = displayed.map(p => {
    const typeKey = String(p.type || '').toLowerCase();
    const ym    = p.month ? `${escapeHtml(p.month)} ${escapeHtml(p.year)}` : escapeHtml(p.year);
    const badge = `<span class="pub-type-badge ${classMap[typeKey]||'badge-original'}">${escapeHtml(typeMap[typeKey]||typeKey)}</span>`;
    const star  = p.featured === 'yes' ? '<span class="pub-star-badge" title="Featured publication" aria-label="Featured publication">&#9733;</span>' : '';
    const href = safeUrl(p.url);
    const title = escapeHtml(p.title);
    const titleHtml = href ? `<a href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">${title}</a>` : title;
    const authHtml  = boldName(escapeHtml(p.authors));
    const tagChips = pubDisplayTags(p, typeMap).map(tag =>
      `<button type="button" class="pub-tag-chip" data-tag="${escapeHtml(tag)}" onclick="applyPubSearchTag(event,this)">${escapeHtml(tag)}</button>`
    ).join('');
    const tagRow = tagChips ? `<div class="pub-tags-row">${tagChips}</div>` : '';
    return `<div class="pub-item">
      <div class="pub-year-col">${ym}${badge}${star}</div>
      <div>
        <div class="pub-title">${titleHtml}</div>
        <div class="pub-authors">${authHtml}</div>
        <div class="pub-journal"><em>${escapeHtml(p.journal)}</em></div>
        ${tagRow}
      </div>
    </div>`;
  }).join('');
}

function showAllPubs(event){
  stopFilterEvent(event);
  showingAll=true;
  preserveScroll(renderPubs);
}

function resetPubFilters(event){
  stopFilterEvent(event);
  pubTypeSelections=[]; pubTagSelections=[]; currentCat='all'; currentSearch=''; showingAll=false;
  ['pub-type-panel','pub-auth-panel'].forEach(id=>{
    const panel=document.getElementById(id);
    if(!panel) return;
    panel.classList.remove('open');
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
  document.querySelectorAll('.pub-filter-sidebar .filter-btn')
    .forEach(b=>b.setAttribute('aria-pressed','false'));
  document.querySelectorAll('.pub-filter-sidebar .filter-sub-group')
    .forEach(g=>g.style.display='none');
  document.getElementById('cat-all-btn')?.classList.add('active');
  const s=document.getElementById('pub-search');
  if(s) s.value='';
  syncPressed('.pub-filter-sidebar');
  updatePubSearchPrefix();
  preserveScroll(renderPubs);
}

/* ── Topic category filter (tree buttons in sidebar) ── */
function filterPubsMain(event, btn){
  stopFilterEvent(event);
  const groupKey = btn.dataset.group;
  const isActive = btn.classList.contains('active') && currentCat === 'main:'+groupKey;
  showingAll = false;
  document.querySelectorAll('.pub-filter-sidebar .filter-main-btn,.pub-filter-sidebar .filter-sub-btn')
    .forEach(b=>b.classList.remove('active','has-active','open'));
  document.querySelectorAll('.pub-filter-sidebar .filter-sub-group')
    .forEach(g=>g.style.display='none');
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
  updatePubSearchPrefix();
  preserveScroll(renderPubs);
}

function filterPubs(event, val, btn, dimension){
  stopFilterEvent(event);
  showingAll = false;
  if(dimension === 'cat'){
    currentCat = val;
    document.querySelectorAll('.pub-filter-sidebar .filter-main-btn,.pub-filter-sidebar .filter-sub-btn')
      .forEach(b=>b.classList.remove('active','has-active'));
    document.querySelectorAll('.pub-filter-sidebar .filter-sub-group')
      .forEach(g=>g.style.display='none');
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
  updatePubSearchPrefix();
  preserveScroll(renderPubs);
}

/* ── Custom multi-select dropdown ─────────────────────────────────────────── */
function initCustomDropdown(btnId, panelId, defaultLabel, onChangeCallback){
  const btn   = document.getElementById(btnId);
  const panel = document.getElementById(panelId);
  if(!btn || !panel) return;

  btn.addEventListener('click', e => {
    e.preventDefault();
    e.stopPropagation();
    const isOpen = panel.classList.contains('open');
    document.querySelectorAll('.custom-dropdown-panel.open').forEach(p=>p.classList.remove('open'));
    document.querySelectorAll('.custom-dropdown-btn.open').forEach(b=>{
      b.classList.remove('open');
      b.setAttribute('aria-expanded','false');
    });
    if(!isOpen){
      panel.classList.add('open');
      btn.classList.add('open');
    }
    btn.setAttribute('aria-expanded', String(!isOpen));
  });

  panel.addEventListener('click', e => {
    const opt = e.target.closest('.custom-dropdown-option');
    if(!opt) return;
    e.preventDefault();
    e.stopPropagation();
    const val = opt.dataset.value;
    const chk = opt.querySelector('input[type=checkbox]');
    if(val === 'all'){
      panel.querySelectorAll('input[type=checkbox]').forEach(c=>{
        c.checked=false;
        const option = c.closest('.custom-dropdown-option');
        if(option){ option.classList.remove('selected'); option.setAttribute('aria-selected','false'); }
      });
    } else {
      if(chk){
        const nextChecked = !opt.classList.contains('selected');
        chk.checked = nextChecked;
        opt.classList.toggle('selected', nextChecked);
        opt.setAttribute('aria-selected', nextChecked ? 'true' : 'false');
      }
      panel.querySelector('[data-value=all]')?.classList.remove('selected');
    }
    const selected = [...panel.querySelectorAll('input[type=checkbox]:checked')].map(c=>c.value);
    btn.classList.toggle('has-selection', selected.length > 0);
    const label = btn.querySelector('.dropdown-label');
    if(label) label.textContent = selected.length === 0 ? defaultLabel : (selected.length === 1 ? panel.querySelector(`[data-value="${selected[0]}"] .opt-label`)?.textContent||defaultLabel : `${selected.length} selected`);
    preserveScroll(() => onChangeCallback(selected));
  });

  panel.addEventListener('keydown', e => {
    if(e.key !== 'Enter' && e.key !== ' ') return;
    const opt = e.target.closest('.custom-dropdown-option');
    if(!opt) return;
    e.preventDefault();
    opt.click();
  });
}

document.addEventListener('click', () => {
  document.querySelectorAll('.custom-dropdown-panel.open').forEach(p=>p.classList.remove('open'));
  document.querySelectorAll('.custom-dropdown-btn.open').forEach(b=>{b.classList.remove('open'); b.setAttribute('aria-expanded','false');});
});

/* ── Research topic tag click → scroll to publications + apply filter ── */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.research-tag[data-cat]').forEach(tag => {
    tag.addEventListener('click', event => {
      event.preventDefault();
      const cat = tag.dataset.cat;
      currentCat = cat;
      showingAll  = false;
      document.querySelectorAll('.pub-filter-sidebar .filter-main-btn,.pub-filter-sidebar .filter-sub-btn')
        .forEach(b=>b.classList.remove('active','has-active'));
      document.querySelectorAll('.pub-filter-sidebar .filter-sub-group')
        .forEach(g=>g.style.display='none');
      document.getElementById('cat-all-btn')?.classList.remove('active');
      const btn = document.querySelector(`.filter-sub-btn[data-cat="${cat}"]`);
      if(btn){
        btn.classList.add('active');
        const parent = btn.closest('.filter-main-group')?.querySelector('.filter-main-btn');
        if(parent){ parent.classList.add('has-active','open'); }
        const sub = btn.closest('.filter-sub-group');
        if(sub) sub.style.display = 'block';
      }
      syncPressed('.pub-filter-sidebar');
      updatePubSearchPrefix();
      renderPubs();
      document.getElementById('publications')?.scrollIntoView({behavior:'smooth'});
    });
  });

  /* ── Init publication type dropdown ── */
  initCustomDropdown('pub-type-btn','pub-type-panel','All Types', selected => {
    pubTypeSelections = selected; showingAll=false; updatePubSearchPrefix(); renderPubs();
  });

  /* ── Init authorship dropdown ── */
  initCustomDropdown('pub-auth-btn','pub-auth-panel','All Roles', selected => {
    pubTagSelections = selected; showingAll=false; updatePubSearchPrefix(); renderPubs();
  });

  /* ── Init presentation type dropdown ── */
  initCustomDropdown('pres-type-btn','pres-type-panel','All Types', selected => {
    presShowingAll = false;
    presDropFilters.type = selected; updatePresSearchPrefix(); applyPresFilters();
  });

  /* ── Init presentation location dropdown ── */
  initCustomDropdown('pres-loc-btn','pres-loc-panel','All Locations', selected => {
    presShowingAll = false;
    presDropFilters.location = selected; updatePresSearchPrefix(); applyPresFilters();
  });

  renderPubs();
  applyPresFilters();
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
let presShowingAll = false;
const PRES_INITIAL_SHOW = 8;

function filterPresMain(event, btn){
  stopFilterEvent(event);
  presShowingAll = false;
  const groupKey = btn.dataset.group;
  const isActive = btn.classList.contains('active') && presFilters.cat === 'main:'+groupKey;
  document.querySelectorAll('.pres-filter-sidebar .filter-main-btn,.pres-filter-sidebar .filter-sub-btn')
    .forEach(b=>b.classList.remove('active','has-active','open'));
  document.querySelectorAll('.pres-filter-sidebar .filter-sub-group')
    .forEach(g=>g.style.display='none');
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
  updatePresSearchPrefix();
  preserveScroll(applyPresFilters);
}

function filterPres(event, dim, val, btn){
  stopFilterEvent(event);
  presShowingAll = false;
  if(presFilters[dim] === val){
    presFilters[dim] = null; btn.classList.remove('active');
    if(dim==='cat') btn.closest('.filter-main-group')?.querySelector('.filter-main-btn')?.classList.remove('has-active');
  } else {
    if(dim === 'cat'){
      document.querySelectorAll('.pres-filter-sidebar .filter-main-btn,.pres-filter-sidebar .filter-sub-btn')
        .forEach(b=>b.classList.remove('active','has-active','open'));
      document.querySelectorAll('.pres-filter-sidebar .filter-sub-group')
        .forEach(g=>g.style.display='none');
    } else {
      btn.closest('.pres-filter-group')?.querySelectorAll('.filter-btn:not(.filter-main-btn)').forEach(b=>b.classList.remove('active'));
    }
    presFilters[dim] = val; btn.classList.add('active');
    if(dim==='cat'){
      const parent = btn.closest('.filter-main-group')?.querySelector('.filter-main-btn');
      if(parent) parent.classList.add('has-active');
      const sub = btn.closest('.filter-sub-group');
      if(sub){ sub.style.display='block'; sub.previousElementSibling?.classList.add('open'); }
    }
  }
  syncPressed('.pres-filter-sidebar');
  updatePresSearchPrefix();
  preserveScroll(applyPresFilters);
}

function resetPresFilters(event){
  stopFilterEvent(event);
  presFilters = {cat:null, search:''};
  presDropFilters = {type:[], location:[]};
  presShowingAll = false;
  document.querySelectorAll('.pres-filter-sidebar .filter-btn').forEach(b=>{
    b.classList.remove('active','has-active','open');
    b.setAttribute('aria-pressed','false');
  });
  document.querySelectorAll('.pres-filter-sidebar .filter-sub-group').forEach(g=>g.style.display='none');
  const searchEl = document.getElementById('pres-search');
  if(searchEl) searchEl.value='';
  /* Reset dropdowns */
  ['pres-type-panel','pres-loc-panel'].forEach(id=>{
    const panel=document.getElementById(id);
    if(panel){
      panel.classList.remove('open');
      panel.querySelectorAll('input[type=checkbox]').forEach(c=>{
        c.checked=false;
        const opt = c.closest('.custom-dropdown-option');
        if(opt){ opt.classList.remove('selected'); opt.setAttribute('aria-selected','false'); }
      });
    }
  });
  ['pres-type-btn','pres-loc-btn'].forEach(id=>{
    const btn=document.getElementById(id);
    if(btn){
      btn.classList.remove('has-selection','open');
      btn.setAttribute('aria-expanded','false');
      const lbl=btn.querySelector('.dropdown-label');
      if(lbl) lbl.textContent=lbl.dataset.default;
    }
  });
  syncPressed('.pres-filter-sidebar');
  updatePresSearchPrefix();
  preserveScroll(applyPresFilters);
}

function filterPresSearch(q){
  presShowingAll = false;
  presFilters.search = q.toLowerCase();
  updatePresSearchPrefix();
  preserveScroll(applyPresFilters);
}

function applyPresFilters(){
  const items = [...document.querySelectorAll('#pres-list .pres-item')];
  updatePresSearchPrefix();
  const activeFilters = presDropFilters.type.length > 0
    || presDropFilters.location.length > 0
    || Boolean(presFilters.cat)
    || Boolean(presFilters.search);
  const matches = [];
  items.forEach(item => {
    const type = item.dataset.type || '';
    const loc  = (item.dataset.location || '').toLowerCase();
    const cats = (item.dataset.cats || '').split(',').filter(Boolean);
    const text = `${item.dataset.search || ''} ${item.textContent || ''}`.toLowerCase();

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
    const locOk  = presDropFilters.location.length===0 || presDropFilters.location.some(l=>loc.includes(String(l).toLowerCase()));

    const ok = typeOk && locOk && catMatch && (!presFilters.search || textMatchesSearch(text, presFilters.search));
    if(ok) matches.push(item);
  });

  const limit = (!activeFilters && !presShowingAll) ? PRES_INITIAL_SHOW : matches.length;
  const visible = new Set(matches.slice(0, limit));
  items.forEach(item => {
    item.style.display = visible.has(item) ? '' : 'none';
  });
  const countEl = document.getElementById('pres-count');
  if(countEl){
    countEl.textContent = activeFilters
      ? `${matches.length} matching presentation${matches.length!==1?'s':''}`
      : `Showing ${visible.size} of ${matches.length}`;
  }
  const more = document.getElementById('pres-more');
  if(more){
    const btn = more.querySelector('button');
    const canToggle = !activeFilters && matches.length > PRES_INITIAL_SHOW;
    more.style.display = canToggle ? 'block' : 'none';
    if(btn) btn.textContent = presShowingAll ? 'Show fewer presentations' : 'Show more presentations';
  }
}

function togglePresMore(event){
  stopFilterEvent(event);
  presShowingAll = !presShowingAll;
  preserveScroll(applyPresFilters);
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
  const githubIcon = '<svg aria-hidden="true" viewBox="0 0 16 16" width="18" height="18"><path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>';
  const repoIcon = icon => String(icon || '').trim().toLowerCase() === 'github' ? githubIcon : escapeHtml(icon || '🔬');
  grid.innerHTML = openSourceRepos.map(r=>{
    const lc = langColor[r.language]||'#6b84a0';
    const langEl = r.language ? `<span class="repo-lang" style="border-color:${lc}50;color:${lc}">${escapeHtml(r.language)}</span>` : '';
    const links = [
      r.url   ? `<a href="${escapeHtml(r.url)}"   target="_blank" rel="noopener noreferrer" class="repo-link primary">GitHub ↗</a>` : '',
      r.demo  ? `<a href="${escapeHtml(r.demo)}"  target="_blank" rel="noopener noreferrer" class="repo-link">Webpage/Demo ↗</a>` : '',
      r.paper ? `<a href="${escapeHtml(r.paper)}" target="_blank" rel="noopener noreferrer" class="repo-link">Paper ↗</a>` : '',
    ].filter(Boolean).join('');
    return `<div class="repo-card">
      <div class="repo-card-header">
        <span class="repo-card-icon">${repoIcon(r.icon)}</span>
        <span class="repo-card-name">${r.url?`<a href="${escapeHtml(r.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(r.name)}</a>`:escapeHtml(r.name)}</span>
        ${langEl}
      </div>
      ${r.desc?`<p class="repo-desc">${escapeHtml(r.desc)}</p>`:''}
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

function pubFilterStateSnapshot(){
  return {
    types: [...pubTypeSelections],
    authorship: [...pubTagSelections],
    topic: currentCat,
    search: currentSearch,
    showingAll,
  };
}

function presFilterStateSnapshot(){
  return {
    types: [...presDropFilters.type],
    locations: [...presDropFilters.location],
    topic: presFilters.cat || 'all',
    search: presFilters.search,
    showingAll: presShowingAll,
  };
}

function countTextTotal(id){
  const text = document.getElementById(id)?.textContent || '';
  const match = text.match(/of\s+(\d+)/i) || text.match(/^(\d+)\s+matching/i);
  return match ? parseInt(match[1], 10) : 0;
}

function visibleCount(selector){
  return [...document.querySelectorAll(selector)].filter(el => el.style.display !== 'none').length;
}

window.cvDiagnostics = function(){
  const lastPublication = Array.isArray(publications) && publications.length ? publications[publications.length - 1] : null;
  const pubSearch = document.getElementById('pub-search');
  const presSearch = document.getElementById('pres-search');
  const publicationFilterElementsExist = [
    'pub-list','pub-count','pub-search','pub-more','pub-type-btn','pub-type-panel','pub-auth-btn','pub-auth-panel','cat-all-btn'
  ].every(id => Boolean(document.getElementById(id)));
  const presentationFilterElementsExist = [
    'pres-list','pres-count','pres-search','pres-more','pres-type-btn','pres-type-panel','pres-loc-btn','pres-loc-panel','pres-reset'
  ].every(id => Boolean(document.getElementById(id)));
  const publicationTopicFiltersExist = Boolean(document.querySelector('.pub-filter-sidebar [data-cat]'));
  const publicationTagChipsExist = Boolean(document.querySelector('.pub-tag-chip'));
  const presentationTagChipsExist = Boolean(document.querySelector('.pres-tag-chip'));
  const publicationSearchPrefixExists = Boolean(document.getElementById('pub-search-prefix'));
  const presentationSearchPrefixExists = Boolean(document.getElementById('pres-search-prefix'));
  const resetButtonsExist = Boolean(document.querySelector('[onclick^="resetPubFilters"]') && document.getElementById('pres-reset'));
  const tavsLogoElementExists = Boolean([...document.querySelectorAll('.lab-card')].some(card => /Thoracic and Vascular Surgery Research Center/i.test(card.textContent || '') && card.querySelector('.lab-card-logo')));
  const openSourceGithubCardExists = Boolean(document.querySelector('#opensource a[aria-label^="GitHub Profile"], #opensource a[aria-label^="View GitHub profile"]'));
  let pubTagClickSearchWorks = false;
  let presTagClickSearchWorks = false;
  const firstPubTag = document.querySelector('.pub-tag-chip');
  const firstPresTag = document.querySelector('.pres-tag-chip');
  const oldPubSearch = pubSearch ? pubSearch.value : '';
  const oldCurrentSearch = currentSearch;
  if(firstPubTag && pubSearch){
    applyPubSearchTag({preventDefault(){}, stopPropagation(){}}, firstPubTag);
    pubTagClickSearchWorks = pubSearch.value === firstPubTag.dataset.tag;
    pubSearch.value = oldPubSearch;
    currentSearch = oldCurrentSearch;
    renderPubs();
  }
  const oldPresSearch = presSearch ? presSearch.value : '';
  const oldPresFilterSearch = presFilters.search;
  if(firstPresTag && presSearch){
    applyPresSearchTag({preventDefault(){}, stopPropagation(){}}, firstPresTag);
    presTagClickSearchWorks = presSearch.value === firstPresTag.dataset.tag;
    presSearch.value = oldPresSearch;
    presFilters.search = oldPresFilterSearch;
    applyPresFilters();
  }
  const errorsFound = [];
  if(!publicationFilterElementsExist) errorsFound.push('Missing one or more publication filter elements');
  if(!presentationFilterElementsExist) errorsFound.push('Missing one or more presentation filter elements');
  if(!resetButtonsExist) errorsFound.push('Missing reset button');
  if(!publicationTagChipsExist) errorsFound.push('Missing publication tag chips');
  if(!presentationTagChipsExist) errorsFound.push('Missing presentation tag chips');
  if(!publicationSearchPrefixExists) errorsFound.push('Missing publication search prefix');
  if(!presentationSearchPrefixExists) errorsFound.push('Missing presentation search prefix');
  if(!openSourceGithubCardExists) errorsFound.push('Missing open-source GitHub card');
  if(!tavsLogoElementExists) errorsFound.push('Missing TAVS lab logo element');
  const result = {
    publicationsLoaded: Array.isArray(publications) ? publications.length : 0,
    presentationsLoaded: document.querySelectorAll('#pres-list .pres-item').length,
    lastPublicationNumber: lastPublication ? Number(lastPublication.n) : null,
    lastPublicationTitle: lastPublication ? lastPublication.title : '',
    row195Present: Array.isArray(publications) && publications.some(pub => Number(pub.n) === 195),
    publicationFilterElementsExist,
    publicationSearchFieldExists: Boolean(pubSearch),
    publicationTypeFilterExists: Boolean(document.getElementById('pub-type-btn')),
    publicationAuthorshipFilterExists: Boolean(document.getElementById('pub-auth-btn')),
    publicationTopicFiltersExist,
    publicationTagChipsExist,
    pubTagClickSearchWorks,
    presentationFilterElementsExist,
    presentationSearchFieldExists: Boolean(presSearch),
    publicationSearchPrefixExists,
    presentationSearchPrefixExists,
    presentationTagChipsExist,
    presTagClickSearchWorks,
    resetButtonsExist,
    activePublicationFilterState: JSON.stringify(pubFilterStateSnapshot()),
    activePresentationFilterState: JSON.stringify(presFilterStateSnapshot()),
    tavsLogoElementExists,
    openSourceGithubCardExists,
    errorsFound: errorsFound.join('; '),
  };
  console.table(result);
  return result;
};

window.testPubFilters = function(){
  resetPubFilters();
  const total = Array.isArray(publications) ? publications.length : 0;
  const defaultVisible = visibleCount('#pub-list .pub-item');

  pubTypeSelections = ['letter'];
  showingAll = true;
  renderPubs();
  const typeTotal = countTextTotal('pub-count');

  pubTypeSelections = [];
  pubTagSelections = ['first'];
  showingAll = true;
  renderPubs();
  const authorTotal = countTextTotal('pub-count');

  pubTagSelections = [];
  const pubWithSearch = publications.find(p => normalizedArray(p.keywords).length) || publications[publications.length - 1] || {};
  currentSearch = normalizedArray(pubWithSearch.keywords)[0] || String(pubWithSearch.title || '').split(/\s+/)[0] || '';
  showingAll = true;
  renderPubs();
  const searchTotal = countTextTotal('pub-count');
  const firstChip = document.querySelector('.pub-tag-chip');
  const chipLabel = firstChip?.dataset.tag || '';
  let tagSearchWorks = false;
  if(firstChip){
    applyPubSearchTag({preventDefault(){}, stopPropagation(){}}, firstChip);
    tagSearchWorks = document.getElementById('pub-search')?.value === chipLabel && countTextTotal('pub-count') > 0;
  }

  resetPubFilters();
  const resetVisible = visibleCount('#pub-list .pub-item');
  const result = {
    totalPublications: total,
    typeFilterChangesCount: typeTotal > 0 && typeTotal < total,
    authorshipFilterChangesCount: authorTotal > 0 && authorTotal < total,
    publicationSearchWorks: searchTotal > 0 && searchTotal <= total,
    tagChipSearchWorks: tagSearchWorks,
    resetRestoresDefaultCount: resetVisible === Math.min(SHOW, total) && resetVisible === defaultVisible,
    overallPass: false,
  };
  result.overallPass = result.typeFilterChangesCount && result.authorshipFilterChangesCount && result.publicationSearchWorks && result.tagChipSearchWorks && result.resetRestoresDefaultCount;
  console.table(result);
  return result;
};

window.testPresFilters = function(){
  resetPresFilters();
  const total = document.querySelectorAll('#pres-list .pres-item').length;
  const defaultVisible = visibleCount('#pres-list .pres-item');

  presDropFilters.type = ['poster'];
  presShowingAll = true;
  applyPresFilters();
  const typeTotal = countTextTotal('pres-count');

  presDropFilters.type = [];
  const firstLocation = document.querySelector('#pres-list .pres-item')?.dataset.location || '';
  presDropFilters.location = firstLocation ? [firstLocation] : [];
  presShowingAll = true;
  applyPresFilters();
  const locationTotal = countTextTotal('pres-count');
  const firstChip = document.querySelector('.pres-tag-chip');
  const chipLabel = firstChip?.dataset.tag || '';
  let tagSearchWorks = false;
  if(firstChip){
    applyPresSearchTag({preventDefault(){}, stopPropagation(){}}, firstChip);
    tagSearchWorks = document.getElementById('pres-search')?.value === chipLabel && countTextTotal('pres-count') > 0;
  }

  resetPresFilters();
  const resetVisible = visibleCount('#pres-list .pres-item');
  const result = {
    totalPresentations: total,
    typeFilterChangesCount: typeTotal > 0 && typeTotal < total,
    locationFilterChangesCount: locationTotal > 0 && locationTotal < total,
    tagChipSearchWorks: tagSearchWorks,
    resetRestoresDefaultCount: resetVisible === Math.min(PRES_INITIAL_SHOW, total) && resetVisible === defaultVisible,
    overallPass: false,
  };
  result.overallPass = result.typeFilterChangesCount && result.locationFilterChangesCount && result.tagChipSearchWorks && result.resetRestoresDefaultCount;
  console.table(result);
  return result;
};
