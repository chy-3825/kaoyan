/* Shared offline text, source provenance, favorites, and legacy-record migration. */
'use strict';
const StudyUI = (() => {
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const cache = new Map();
  let favoriteChapter = '', favoriteType = 'all';
  let removedFavorite = null, undoTimer;
  const paths = {
    star:'M12 3l2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9Z',
    copy:'M9 8h11v13H9z M5 16H3V3h11v2',
    book:'M12 5v15 M3 4c4-1 6 0 9 1 3-1 5-2 9-1v15c-4-1-6 0-9 1-3-1-5-2-9-1Z',
    list:'M8 6h13M8 12h13M8 18h13M3 6h.1M3 12h.1M3 18h.1',
    back:'m14 5-7 7 7 7', next:'m9 5 7 7-7 7',
    check:'m5 12 4 4L19 6', close:'m6 6 12 12M18 6 6 18',
    mistake:'M5 3h14v18H5z M9 7h6M9 11h6M9 15h3',
    ai:'m12 3 2.4 6.6L21 12l-6.6 2.4L12 21l-2.4-6.6L3 12l6.6-2.4Z',
    zoom:'M20 20l-5-5M6 10h8M10 6v8',
    settings:'M9 3h6l1 3 3 1 2 5-2 5-3 1-1 3H9l-1-3-3-1-2-5 2-5 3-1Z',
    play:'m8 4 12 8-12 8Z'
  };
  function icon(name){return `<svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[name]||paths.list}"/>${name==='zoom'?'<circle cx="10" cy="10" r="7"/>':name==='settings'?'<circle cx="12" cy="12" r="3"/>':''}</svg>`;}
  function meta(q){
    const refs=q.sources||[q], years=[...new Set(refs.map(s=>s.examYear))].join(' / ');
    const exams=[...new Set(refs.map(s=>({'数学一':'数一','数学二':'数二','数学三':'数三'})[s.exam]||s.exam))].join(' / ');
    return `<div class="question-meta"><details class="source-details"><summary>${escape(years)} · ${escape(exams)} ${icon('next')}</summary><p>${escape(sourceLabel(q))}</p></details><span class="type-tag">${TYPE_LABEL[q.questionType]}</span></div>`;
  }
  function dock(q,index,total){return `<div class="study-dock"><div class="dock-tools"><button data-action="toggle-answer" class="dock-tool ${state.revealed[q.id]?'selected':''}">${icon('book')}<span>${state.revealed[q.id]?'收起解析':'查看解析'}</span></button><button data-action="share" class="dock-tool">${icon('copy')}<span>复制题目</span></button>${star(q)}</div><nav class="dock-navigation"><button class="secondary" data-action="previous" ${index===0?'disabled':''}>${icon('back')}上一题</button><span>${index+1} / ${total}</span><button class="primary" data-action="next" ${index===total-1?'disabled':''}>下一题${icon('next')}</button></nav></div>`;}
  function polish(){
    document.body.classList.toggle('is-training',page==='training');
    document.querySelectorAll('.back-button').forEach(b=>{const s=b.querySelector('span');if(s)s.outerHTML=icon('back');});
    document.querySelectorAll('.icon-button[data-action="settings"]').forEach(b=>b.innerHTML=icon('settings'));
    document.querySelectorAll('.directory-shortcut').forEach(b=>b.innerHTML=icon('list'));
    document.querySelectorAll('.home-action').forEach(b=>{const s=b.querySelector('.action-symbol');if(s)s.innerHTML=icon({favorites:'star',directory:'book',mistakes:'mistake'}[b.dataset.action]);const a=b.querySelector('.action-arrow');if(a)a.innerHTML=icon('next');});
    document.querySelectorAll('.continue-icon').forEach(b=>b.innerHTML=icon('play'));
    document.querySelectorAll('.continue-chevron,.course-card-arrow').forEach(b=>b.innerHTML=icon('next'));
    const home=document.querySelector('.home-actions');if(home){for(const action of ['directory','mistakes','favorites']){const b=home.querySelector(`[data-action="${action}"]`);if(b)home.append(b);}}
    document.querySelectorAll('.favorite-row').forEach(row=>{const q=byId.get(row.querySelector('[data-open-favorite]')?.dataset.openFavorite);const preview=row.querySelector('.favorite-preview');if(q?.image&&preview)preview.innerHTML=`<img src="${escape(q.image)}" alt="题图预览" loading="lazy">`;const remove=row.querySelector('.favorite-remove');if(remove)remove.innerHTML=icon('star');});
    document.querySelectorAll('.empty-check').forEach(e=>e.innerHTML=icon(page==='favorites'?'star':'check'));
    document.querySelectorAll('.reference-analysis').forEach(e=>e.open=true);
    const answer=document.querySelector('.answer-panel');if(answer&&!answer.querySelector('.ai-followup')){const b=document.createElement('button');b.className='ai-followup';b.dataset.action='explain';b.innerHTML=icon('ai')+'AI 进一步讲解';answer.append(b);}
    if(page==='favorites')document.querySelectorAll('.empty-card small').forEach(e=>e.textContent='点击做题页底部的星标，即可收藏题目');
    document.querySelectorAll('.image-close').forEach(e=>e.innerHTML=icon('close'));
  }

  function rich(value) {
    const text = String(value || '');
    if (cache.has(text)) return cache.get(text);
    const pattern = /\$\$([\s\S]*?)\$\$|\$([^$]*?)\$/g;
    let html = '', end = 0, match;
    while ((match = pattern.exec(text))) {
      html += escape(text.slice(end, match.index)).replace(/\n/g, '<br>');
      const formula = match[1] ?? match[2];
      const block = match[1] !== undefined || /\\begin\{|\\tag\{|\\displaystyle|\\(?:iint|iiint)/.test(formula) || formula.length > 85;
      try {
        html += `<span class="${block ? 'formula-block' : 'formula-inline'}">${katex.renderToString(formula, {displayMode:block, throwOnError:true, strict:'ignore', trust:false, maxExpand:1000, output:'htmlAndMathml'})}</span>`;
      } catch {
        html += `<span class="formula-fallback">${escape(formula)}</span>`;
      }
      end = pattern.lastIndex;
    }
    html += escape(text.slice(end)).replace(/\n/g, '<br>');
    cache.set(text, html);
    return html;
  }

  function migrate(source, questions) {
    source = source && typeof source === 'object' && !Array.isArray(source) ? source : {};
    const aliases = new Map(questions.flatMap(q => (q.aliases || [q.id]).map(id => [id,q.id])));
    const output = {...source};
    for (const field of ['attempts','mistakes','drafts','revealed','hints','explanationCache','favorites']) {
      const entries = source[field] && typeof source[field] === 'object' && !Array.isArray(source[field]) ? Object.entries(source[field]) : [];
      output[field] = {};
      for (const [oldId,value] of entries) {
        const id = aliases.get(oldId);
        if (!id || value == null) continue;
        const previous = output[field][id];
        if (field === 'mistakes' && value && typeof value === 'object') {
          const latest = !previous || (value.at || 0) >= (previous.at || 0) ? value : previous;
          output[field][id] = {...latest, count:(previous?.count || 0)+(value.count || 0), manual:!!(previous?.manual || value.manual)};
        } else if (field === 'revealed' || field === 'hints') output[field][id] = !!(previous || value);
        else if (!previous || (value.at || 0) >= (previous.at || 0)) output[field][id] = value;
      }
    }
    return output;
  }

  function sourceLabel(q) {
    const refs = q.sources || [q];
    const short = {'数学一':'数一','数学二':'数二','数学三':'数三'};
    return refs.map(s => `${s.examYear} ${short[s.exam] || s.exam} · 第${s.questionNo}题`).join(' / ');
  }

  function question(q) {
    if (!q.image) return `<div class="rich-question">${rich(q.questionText)}</div>`;
    return `<button class="question-image-button" data-action="zoom-question" aria-label="点击放大原题图片"><img class="question-image" src="${escape(q.image)}" alt="${escape(sourceLabel(q))} 原卷题图，点击放大" fetchpriority="high"></button><p class="image-zoom-hint">点击题图可放大查看</p>`;
  }

  function reference(q) {
    const answer = q.answerRich || q.answerText || '';
    const analysis = q.analysisRich || '';
    const answerHtml = rich(answer), analysisHtml = rich(analysis);
    const broken = answerHtml.includes('formula-fallback') || analysisHtml.includes('formula-fallback');
    return `${answer && !answerHtml.includes('formula-fallback') ? `<div class="rich-answer">${answerHtml}</div>` : ''}${analysis && !broken ? `<details class="reference-analysis"><summary>参考解析</summary><div class="rich-answer">${analysisHtml}</div></details>` : ''}${broken?'<p class="settings-note">文字解析公式格式待校对，请以原卷答案为准。</p>':''}${q.answerImage ? `<details class="original-answer" ${broken||!answer&&!analysis?'open':''}><summary>查看原卷答案图</summary><img class="answer-image" src="${escape(q.answerImage)}" alt="原卷参考答案，点击放大" data-action="zoom-answer" loading="lazy"></details>` : ''}`;
  }

  function favoriteRows() {
    return bank.filter(q => state.favorites?.[q.id] && (!favoriteChapter || q.chapter===favoriteChapter) && (favoriteType==='all' || q.questionType===favoriteType))
      .sort((a,b)=>(state.favorites[b.id]?.at||0)-(state.favorites[a.id]?.at||0) || a.id.localeCompare(b.id));
  }

  function favoritesView() {
    const rows = favoriteRows();
    const total = bank.filter(q=>state.favorites?.[q.id]).length;
    return `<div class="page-screen"><header class="page-header"><button class="back-button" data-action="home"><span>‹</span>首页</button></header><div class="page-intro"><h1>收藏夹</h1><p>${total} 道收藏 · 当前显示 ${rows.length} 道</p></div><div class="favorite-filters"><label>章节<select id="favorite-chapter"><option value="">全部章节</option>${CHAPTER_ORDER.filter(c=>bank.some(q=>q.chapter===c)).map(c=>`<option value="${escape(c)}" ${c===favoriteChapter?'selected':''}>${escape(c)}</option>`).join('')}</select></label><label>题型<select id="favorite-type">${[['all','全部题型'],['single','选择题'],['fill','填空题'],['solve','解答题']].map(([v,label])=>`<option value="${v}" ${v===favoriteType?'selected':''}>${label}</option>`).join('')}</select></label></div>${rows.length?`<button class="review-all" data-action="review-favorites">开始练习收藏题 <span>›</span></button><div class="favorite-list">${rows.map(q=>`<article class="favorite-row"><button data-open-favorite="${escape(q.id)}"><strong>${escape(q.topic)}</strong><small>${escape(sourceLabel(q))}</small><div class="favorite-preview">${rich(q.questionText)}</div></button><button class="favorite-remove" data-remove-favorite="${escape(q.id)}" aria-label="取消收藏">★</button></article>`).join('')}</div>`:`<div class="empty-card"><span class="empty-check">☆</span><strong>${total?'当前筛选下没有收藏题':'还没有收藏题目'}</strong><small>题目右上角点星标即可收藏，答对答错都能收藏</small><button class="secondary" data-action="directory">去练习</button></div>`}</div>`;
  }

  function toggleFavorite(id=current()?.id) {
    if (!id || !byId.has(id)) return;
    state.favorites = state.favorites || {};
    if (state.favorites[id]) {removedFavorite={id,item:state.favorites[id]};delete state.favorites[id];showUndo();}
    else {state.favorites[id]={at:Date.now()};toast('已收藏');}
    save();render();
  }

  function startFavorites(id) {
    const rows = favoriteRows();
    if (!rows.length) return;
    review = {kind:'favorites', ids:rows.map(q=>q.id), index:Math.max(0,rows.findIndex(q=>q.id===id)), attempts:{}};
    page='training';render();window.scrollTo(0,0);
  }

  function star(q) {
    const active = !!state.favorites?.[q.id];
    return `<button class="favorite-toggle dock-tool ${active?'active':''}" data-action="toggle-favorite" aria-label="${active?'取消收藏':'收藏题目'}" aria-pressed="${active}">${icon('star')}<span>${active?'已收藏':'收藏'}</span></button>`;
  }
  function showUndo(){
    let bar=document.getElementById('favorite-undo');if(!bar){bar=document.createElement('div');bar.id='favorite-undo';document.body.append(bar);}
    bar.innerHTML='已取消收藏 <button type="button" data-undo-favorite>撤销</button>';bar.hidden=false;
    clearTimeout(undoTimer);undoTimer=setTimeout(()=>{bar.hidden=true;removedFavorite=null;},6000);
  }

  document.addEventListener('change',event=>{
    if(event.target.id==='favorite-chapter'){favoriteChapter=event.target.value;render();}
    if(event.target.id==='favorite-type'){favoriteType=event.target.value;render();}
    if(event.target.id==='reading-size'){state.fontSize=Number(event.target.value);save();applyFont();}
  });
  document.addEventListener('click',event=>{
    if(event.target.closest('[data-action="toggle-answer"],[data-action="reveal"]'))requestAnimationFrame(()=>document.querySelector('.answer-panel')?.scrollIntoView({block:'start',behavior:'auto'}));
    if(event.target.closest('[data-undo-favorite]')&&removedFavorite){state.favorites[removedFavorite.id]=removedFavorite.item;removedFavorite=null;clearTimeout(undoTimer);document.getElementById('favorite-undo').hidden=true;save();render();return;}
    const open=event.target.closest('[data-open-favorite]'), remove=event.target.closest('[data-remove-favorite]');
    if(open)startFavorites(open.dataset.openFavorite);
    if(remove)toggleFavorite(remove.dataset.removeFavorite);
  });
  function applyFont(){document.documentElement.style.setProperty('--reading-size',`${[18,20,22].includes(state.fontSize)?state.fontSize:18}px`);}
  function readingSettings(){return `<section class="settings-card"><label class="settings-row"><span><strong>解析字号</strong><small>调整解析文字与公式大小，题图可点击放大</small></span><select id="reading-size">${[18,20,22].map(n=>`<option value="${n}" ${(state.fontSize||18)===n?'selected':''}>${n}px</option>`).join('')}</select></label></section>`;}
  return {rich,migrate,sourceLabel,question,reference,favoriteRows,favoritesView,toggleFavorite,startFavorites,star,applyFont,readingSettings,icon,meta,dock,polish};
})();
