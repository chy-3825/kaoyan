'use strict';

const bank = window.QUESTIONS;
const byId = new Map(bank.map(q => [q.id, q]));
const KEY = 'yanxi-politics-v1';
const VERSION = '1.6.1';
const TAGS = [
  '马克思主义基本原理',
  '思想道德与法治',
  '毛泽东思想和中国特色社会主义理论体系概论',
  '中国近现代史纲要',
  '习近平新时代中国特色社会主义思想概论'
];
const LEGACY_TAGS = {
  '马哲': TAGS[0], '思修': TAGS[1], '毛概': TAGS[2], '史纲': TAGS[3], '习概': TAGS[4]
};
const tagBanks = new Map(TAGS.map(tag => [tag, bank.filter(q => q.topicTag === tag)]));
let state = { index: 0, topicTag: null, categoryIndexes: {}, attempts: {}, mistakes: {}, drafts: {}, settings: {}, explanationCache: {} };
let page = 'home', review = null, filter = 'pending', directoryFilter = 'all', mistakeTopicFilter = 'all', storageOK = true, pendingRestore = null;
const expandedMistakeGroups = new Set();

try {
  const saved = JSON.parse(localStorage.getItem(KEY));
  if (saved && saved.attempts && saved.mistakes) {
    state = { ...state, ...saved };
    state.index = Math.max(0, Math.min(bank.length - 1, Number(state.index) || 0));
    state.drafts = state.drafts || {};
    state.categoryIndexes = state.categoryIndexes || {};
    state.settings = state.settings || {};
    state.explanationCache = state.explanationCache || {};
    if (Array.isArray(saved.draft) && !saved.submitted && saved.draft.length) {
      const oldQuestion = bank[state.index];
      if (oldQuestion) state.drafts[oldQuestion.id] = saved.draft;
    }
    delete state.draft;
    delete state.submitted;
    delete state.correct;
  }
} catch { storageOK = false; }

if (LEGACY_TAGS[state.topicTag]) state.topicTag = LEGACY_TAGS[state.topicTag];
for (const [oldTag, newTag] of Object.entries(LEGACY_TAGS)) {
  if (state.categoryIndexes[oldTag] !== undefined) {
    if (state.categoryIndexes[newTag] === undefined) state.categoryIndexes[newTag] = state.categoryIndexes[oldTag];
    delete state.categoryIndexes[oldTag];
  }
}

const app = document.getElementById('app');
const dialog = document.getElementById('explanation');
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const aiResults = new Map(Object.entries(state.explanationCache || {})), aiPending = new Set(), aiRequests = new Map();
let explanationId = null, toastTimer;

function toast(message) {
  const el = document.getElementById('toast');
  el.textContent = message;
  el.style.display = 'block';
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.style.display = 'none', 3500);
}

function save() {
  try { localStorage.setItem(KEY, JSON.stringify(state)); storageOK = true; }
  catch { storageOK = false; toast('无法保存进度，请检查手机存储空间'); }
}

function byTag(tag) { return tagBanks.get(tag) || []; }
const SHORT_TAGS = new Map([
  [TAGS[0], '马原'], [TAGS[1], '思修法治'], [TAGS[2], '毛中特'],
  [TAGS[3], '近代史纲要'], [TAGS[4], '习思想']
]);
function shortTag(tag) { return SHORT_TAGS.get(tag) || tag; }
function examSource(q) { return q.sourceType === 'past_exam' && q.examYear && q.questionNo ? `${q.examYear} · ${q.questionNo}` : ''; }
function pending() {
  return Object.keys(state.mistakes).filter(id => byId.has(id) && !state.mistakes[id].mastered)
    .sort((a, b) => state.mistakes[b].count - state.mistakes[a].count);
}
function current() {
  if (review) return byId.get(review.ids[review.index]);
  const list = byTag(state.topicTag || TAGS[0]);
  return list[Math.min(activeIndex(), Math.max(0, list.length - 1))];
}
function activeIndex() {
  const list = byTag(state.topicTag || TAGS[0]);
  return Math.max(0, Math.min(Math.max(0, list.length - 1), Number(state.categoryIndexes?.[state.topicTag]) || 0));
}
function ensureTopicPosition(tag) {
  if (!Number.isInteger(state.categoryIndexes[tag])) {
    const list = byTag(tag);
    const first = list.findIndex(q => !state.attempts[q.id]);
    state.categoryIndexes[tag] = first < 0 ? 0 : first;
  }
}
function go(pageName) {
  if (!['home', 'categories', 'training', 'directory', 'mistakes', 'settings'].includes(pageName)) return;
  dialog.close();
  document.getElementById('question-image-view').close();
  const restoreDialog = document.getElementById('restore-dialog');
  if (restoreDialog.open) restoreDialog.close();
  pendingRestore = null;
  page = pageName;
  review = null;
  render();
  window.scrollTo(0, 0);
}
function openTopicDirectory(tag) {
  if (!TAGS.includes(tag)) return;
  if (state.topicTag !== tag) directoryFilter = 'all';
  state.topicTag = tag;
  ensureTopicPosition(tag);
  page = 'directory';
  review = null;
  save();
  render();
  window.scrollTo(0, 0);
}
function openQuestion(tag, index) {
  const list = byTag(tag);
  if (!TAGS.includes(tag) || !list.length) return;
  const safeIndex = Math.max(0, Math.min(list.length - 1, Number(index) || 0));
  review = null;
  page = 'training';
  state.topicTag = tag;
  state.categoryIndexes[tag] = safeIndex;
  state.index = bank.indexOf(list[safeIndex]);
  save();
  render();
  window.scrollTo(0, 0);
}
function continueTraining() {
  if (TAGS.includes(state.topicTag) && byTag(state.topicTag).length) {
    ensureTopicPosition(state.topicTag);
    openQuestion(state.topicTag, state.categoryIndexes[state.topicTag]);
  } else go('categories');
}

function attempt(q = current()) { return review ? review.answers[q.id] : state.attempts[q.id]; }
function drafts() { return review ? review.drafts : state.drafts; }
function selection(q = current()) { return attempt(q) ? attempt(q).answer.split('') : (drafts()[q.id] || []); }

function choose(letter) {
  const q = current();
  if (attempt() || !Object.prototype.hasOwnProperty.call(q.options, letter)) return;
  const choices = selection();
  drafts()[q.id] = q.questionType === 'single'
    ? [letter]
    : choices.includes(letter) ? choices.filter(x => x !== letter) : [...choices, letter].sort();
  if (q.questionType === 'single') submit();
  else { save(); render(); }
}

function submit() {
  const q = current();
  if (attempt() || !selection().length) return;
  const answer = selection().slice().sort().join('');
  const record = { answer, correct: answer === q.answer };
  if (review) review.answers[q.id] = record;
  else state.attempts[q.id] = record;
  delete drafts()[q.id];
  if (!record.correct) {
    const previous = state.mistakes[q.id];
    state.mistakes[q.id] = { count: (previous?.count || 0) + 1, mastered: false, lastAnswer: answer };
  }
  save();
  render();
}

function move(delta) {
  if (review) {
    const next = review.index + delta;
    if (next < 0) return;
    if (next >= review.ids.length) { go('mistakes'); return; }
    review.index = next;
  } else {
    const list = byTag(state.topicTag || TAGS[0]);
    const next = activeIndex() + delta;
    if (next < 0 || next >= list.length) return;
    state.categoryIndexes[state.topicTag] = next;
    state.index = bank.indexOf(list[next]);
    save();
  }
  dialog.close();
  render();
  window.scrollTo(0, 0);
}

function startReview(ids = pending()) {
  ids = ids.filter(id => byId.has(id) && state.mistakes[id]);
  if (!ids.length) return;
  review = { ids, index: 0, answers: {}, drafts: {} };
  page = 'mistakes';
  render();
  window.scrollTo(0, 0);
}

function progress(list) {
  return list.filter(q => state.attempts[q.id]).length;
}
function questionStatus(q) {
  const result = state.attempts[q.id];
  return result ? (result.correct ? 'correct' : 'wrong') : state.drafts[q.id]?.length ? 'draft' : 'unseen';
}
function homeView() {
  const totalDone = Object.keys(state.attempts).filter(id => byId.has(id)).length;
  const selectedTag = TAGS.includes(state.topicTag) ? state.topicTag : null;
  const selectedList = selectedTag ? byTag(selectedTag) : [];
  const selectedIndex = selectedTag ? Math.min(Number(state.categoryIndexes[selectedTag]) || 0, selectedList.length - 1) : 0;
  const nextQuestion = selectedList[selectedIndex];
  const continueTitle = selectedTag ? '继续训练' : '开始训练';
  const continueDetails = selectedTag && nextQuestion ? `${shortTag(selectedTag)} · ${selectedIndex + 1} / ${selectedList.length}` : '';
  const overall = Math.round(totalDone / bank.length * 100);
  return `<div class="home-screen">
    <header class="brand-bar">
      <div class="brand-lockup"><div class="brand-mark" aria-hidden="true"><svg viewBox="0 0 48 48"><path d="M8 11.5c6-2.2 11.3-1.3 16 2.8v25c-4.7-4.1-10-5-16-2.8z"/><path d="M40 11.5c-6-2.2-11.3-1.3-16 2.8v25c4.7-4.1 10-5 16-2.8z"/><path d="M34 7v12l-3.5-2.5L27 19V9"/></svg></div><div><strong>研习政治</strong></div></div>
      <button class="icon-button" data-action="settings" aria-label="设置"><svg viewBox="0 0 24 24"><path d="M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Z"/><path d="m19.4 15 .1.1a1.7 1.7 0 0 1-2.4 2.4l-.1-.1a1.7 1.7 0 0 0-2.9 1.2v.2a1.7 1.7 0 0 1-3.4 0v-.2a1.7 1.7 0 0 0-2.9-1.2l-.1.1a1.7 1.7 0 0 1-2.4-2.4l.1-.1a1.7 1.7 0 0 0-1.2-2.9H4a1.7 1.7 0 0 1 0-3.4h.2a1.7 1.7 0 0 0 1.2-2.9l-.1-.1a1.7 1.7 0 0 1 2.4-2.4l.1.1a1.7 1.7 0 0 0 2.9-1.2V2a1.7 1.7 0 0 1 3.4 0v.2a1.7 1.7 0 0 0 2.9 1.2l.1-.1a1.7 1.7 0 0 1 2.4 2.4l-.1.1a1.7 1.7 0 0 0 1.2 2.9h.2a1.7 1.7 0 0 1 0 3.4h-.2a1.7 1.7 0 0 0-1.2 2.9Z"/></svg></button>
    </header>
    <section class="home-hero" aria-hidden="true"><span class="hero-circle"></span><div class="hero-art"><svg viewBox="0 0 160 160"><path d="M29 47c18-7 34-4 51 9v65c-17-13-33-16-51-9z"/><path d="M131 47c-18-7-34-4-51 9v65c17-13 33-16 51-9z"/><path d="M112 27v37l-12-8-12 8V32"/><path d="M40 68c9-2 18-1 27 4M40 82c9-2 18-1 27 4M120 68c-9-2-18-1-27 4M120 82c-9-2-18-1-27-4"/></svg></div><span class="hero-deco deco-one"></span><span class="hero-deco deco-two"></span></section>
    <button class="continue-card" data-action="continue"><span class="continue-icon"><svg viewBox="0 0 24 24"><path d="M8 5.5v13l10-6.5z"/></svg></span><span class="continue-copy"><strong>${continueTitle}</strong>${continueDetails ? `<small>${esc(continueDetails)}</small>` : ''}</span><span class="continue-chevron" aria-hidden="true">›</span></button>
    ${totalDone ? `<section class="home-progress" aria-label="学习进度"><div class="progress-heading"><span>已答 ${totalDone} / ${bank.length}</span></div><div class="progress-track"><span style="width:${overall}%"></span></div></section>` : ''}
    <div class="home-actions"><button class="home-action" data-action="categories"><span class="action-symbol course-symbol"><svg viewBox="0 0 24 24"><path d="M4 5.5h6.5A2.5 2.5 0 0 1 13 8v11H6.5A2.5 2.5 0 0 0 4 21zM20 5.5h-4A3 3 0 0 0 13 8v11h4.5A2.5 2.5 0 0 1 20 21z"/></svg></span><strong>课程目录</strong><span class="action-arrow">›</span></button><button class="home-action" data-action="mistakes"><span class="action-symbol mistake-symbol"><svg viewBox="0 0 24 24"><path d="M6 4.5h12a2 2 0 0 1 2 2v13l-4-2.5-4 2.5-4-2.5-4 2.5v-13a2 2 0 0 1 2-2Z"/><path d="M9 9h6M9 13h6"/></svg></span><strong>错题本</strong><span class="action-count">${pending().length}</span><span class="action-arrow">›</span></button></div>
  </div>`;
}

function categoriesView() {
  return `<div class="page-screen"><header class="page-header"><button class="back-button" data-action="home"><span>‹</span>首页</button><span class="header-spacer"></span></header><div class="page-intro"><h1>课程目录</h1></div><div class="course-list">${TAGS.map((tag, index) => {
    const list = byTag(tag), done = progress(list), pct = Math.round(done / list.length * 100);
    return `<button class="course-card" data-topic="${esc(tag)}"><span class="course-number">${String(index + 1).padStart(2, '0')}</span><span class="course-card-main"><strong>${esc(tag)}</strong><small>${done} / ${list.length}</small><span class="course-meter"><i style="width:${pct}%"></i></span></span><span class="course-card-arrow">›</span></button>`;
  }).join('')}</div></div>`;
}

function questionDirectoryView() {
  const tag = state.topicTag, list = byTag(tag), done = progress(list), index = activeIndex();
  const counts = {
    all: list.length,
    unseen: list.filter(q => ['unseen', 'draft'].includes(questionStatus(q))).length,
    wrong: list.filter(q => questionStatus(q) === 'wrong').length
  };
  const shown = list.map((q, i) => ({ q, i, status: questionStatus(q) })).filter(item =>
    directoryFilter === 'all' || (directoryFilter === 'unseen' ? ['unseen', 'draft'].includes(item.status) : item.status === directoryFilter));
  const filterNames = { all: '全部', unseen: '未答', wrong: '错题' };
  return `<div class="page-screen directory-screen"><header class="page-header"><button class="back-button" data-action="categories"><span>‹</span>课程</button><span class="header-spacer"></span></header><div class="page-intro directory-intro"><h1>${esc(tag)}</h1><p>${done} / ${list.length}</p></div><button class="directory-continue" data-action="continue-topic"><span><strong>继续训练</strong><small>${shortTag(tag)} · ${index + 1} / ${list.length}</small></span><span>›</span></button><div class="directory-filters">${Object.entries(filterNames).map(([key, label]) => `<button class="directory-filter ${directoryFilter === key ? 'active' : ''}" data-directory-filter="${key}" aria-pressed="${directoryFilter === key}">${label}<span>${counts[key]}</span></button>`).join('')}</div><div class="question-grid">${shown.map(({ q, i, status }) => {
    const result = state.attempts[q.id], draft = state.drafts[q.id];
    const label = result ? (result.correct ? '答对' : '答错') : draft?.length ? '有未提交答案' : '未做';
    return `<button class="question-number ${status} ${i === index ? 'current' : ''}" data-question-index="${i}" aria-label="第 ${i + 1} 题，${label}" title="第 ${i + 1} 题 · ${label}">${i + 1}</button>`;
  }).join('') || '<p class="directory-empty">没有题目</p>'}</div><div class="status-legend"><span><i class="legend-dot unseen"></i>未答</span><span><i class="legend-dot draft"></i>待提交</span><span><i class="legend-dot correct"></i>答对</span><span><i class="legend-dot wrong"></i>答错</span></div></div>`;
}

function meta(q) {
  const source = examSource(q);
  return `<span class="question-kind">${q.questionType === 'single' ? '单选' : '多选'}</span>${source ? `<span class="source-year">${esc(source)}</span>` : ''}`;
}

function questionView() {
  const q = current();
  if (!q) return '<div class="empty-state">题目暂不可用<button class="secondary" data-action="categories">返回课程目录</button></div>';
  const answer = attempt(), choices = selection(), index = review ? review.index : activeIndex();
  const total = review ? review.ids.length : byTag(state.topicTag || TAGS[0]).length;
  const heading = review ? '错题复习' : shortTag(state.topicTag || q.topicTag);
  const backAction = review ? 'mistakes' : 'directory';
  const backLabel = review ? '错题本' : '目录';
  const fullHeading = review ? '错题复习' : (state.topicTag || q.topicTag);
  return `<div class="training-screen"><header class="training-head"><button class="back-button" data-action="${backAction}"><span>‹</span>${backLabel}</button><div class="training-course"><span title="${esc(fullHeading)}" aria-label="${esc(fullHeading)}">${esc(heading)}</span>${review ? '' : `<button class="directory-shortcut" data-action="directory" aria-label="打开题目目录"><svg viewBox="0 0 24 24"><rect x="4" y="4" width="6" height="6" rx="1"/><rect x="14" y="4" width="6" height="6" rx="1"/><rect x="4" y="14" width="6" height="6" rx="1"/><rect x="14" y="14" width="6" height="6" rx="1"/></svg></button>`}</div></header>
    <div class="question-progress"><span>${index + 1} / ${total}</span><div class="progress-track"><span style="width:${Math.round((index + 1) / total * 100)}%"></span></div></div>
    <article class="question-card"><div class="question-meta">${meta(q)}</div><h1 class="stem">${esc(q.stem)}</h1>${q.image ? `<figure class="question-figure"><button class="question-figure-button" data-action="zoom-question" aria-label="放大原卷配图"><img class="question-figure-image" src="${esc(q.image)}" alt="${esc(q.imageAlt || '原卷配图')}"></button><figcaption>原卷配图 · 点按放大</figcaption></figure>` : ''}<div class="options ${q.questionType}">${Object.entries(q.options).map(([letter, text]) => {
      const isSelected = choices.includes(letter), correct = answer && q.answer.includes(letter), wrong = answer && isSelected && !q.answer.includes(letter);
      const stateClass = answer ? (correct ? 'correct' : wrong ? 'wrong' : '') : isSelected ? 'selected' : '';
      return `<button class="option ${stateClass}" data-choice="${letter}" aria-pressed="${isSelected}" ${answer ? 'disabled' : ''}><span class="letter">${letter}</span><span class="option-text">${esc(text)}</span><span class="option-state" aria-hidden="true">${answer && correct ? '✓' : answer && wrong ? '×' : isSelected ? '✓' : ''}</span></button>`;
    }).join('')}</div>${q.questionType === 'multiple' && !answer ? `<button class="primary confirm" data-action="submit" ${choices.length ? '' : 'disabled'}>确认答案 <span>${choices.length ? `已选 ${choices.length} 项` : '请选择所有正确项'}</span></button>` : ''}
    ${answer ? `<div class="result ${answer.correct ? 'correct' : 'wrong'}"><strong>${answer.correct ? '回答正确' : '回答错误 · 已加入错题本'}</strong><span>正确答案：${q.answer.split('').join('、')}　你的答案：${answer.answer.split('').join('、')}</span>${review && answer.correct && state.mistakes[q.id] && !state.mistakes[q.id].mastered ? `<button class="master-button" data-master="${esc(q.id)}">标记已掌握</button>` : ''}</div>` : ''}
    <div class="question-tools"><button class="tool-button" data-action="explain"><span class="tool-icon">文</span>解析</button><button class="tool-button" data-action="copy"><span class="tool-icon copy-icon">▢</span>复制题目</button></div></article>
    ${storageOK ? '' : '<p class="storage-error">当前进度无法保存</p>'}
    <nav class="bottom-nav"><button class="secondary" data-action="previous" ${index === 0 ? 'disabled' : ''}><span>‹</span>上一题</button><button class="primary" data-action="next" ${!review && index === total - 1 ? 'disabled' : ''}>${review && index === review.ids.length - 1 ? '完成复习' : '下一题'}<span>›</span></button></nav></div>`;
}

function mistakesView() {
  const all = Object.keys(state.mistakes).filter(id => byId.has(id));
  const mastered = all.filter(id => state.mistakes[id].mastered);
  const sourceItems = filter === 'pending' ? pending() : mastered;
  const items = sourceItems.filter(id => mistakeTopicFilter === 'all' || byId.get(id).topicTag === mistakeTopicFilter);
  const count = pending().length;
  const emptyTitle = sourceItems.length && !items.length ? '当前课程没有这类错题' : filter === 'pending' ? '暂时没有待复习的题目' : '还没有已掌握的错题';
  return `<div class="page-screen"><header class="page-header"><button class="back-button" data-action="home"><span>‹</span>首页</button><span class="header-spacer"></span></header><div class="page-intro"><h1>错题本</h1></div><div class="mistake-tabs"><button data-filter="pending" class="${filter === 'pending' ? 'active' : ''}">待复习 <strong>${count}</strong></button><button data-filter="mastered" class="${filter === 'mastered' ? 'active' : ''}">已掌握 <strong>${mastered.length}</strong></button></div><label class="mistake-course-filter"><span>课程</span><select data-mistake-course>${[['all','全部课程'],...TAGS.map(tag=>[tag,tag])].map(([value,label])=>`<option value="${esc(value)}" ${mistakeTopicFilter===value?'selected':''}>${esc(label)}</option>`).join('')}</select></label>
    ${!items.length ? `<div class="empty-state"><span class="empty-icon">${filter === 'pending' ? '✓' : '书'}</span><strong>${emptyTitle}</strong>${filter === 'pending' && mistakeTopicFilter === 'all' ? '<button class="secondary" data-action="categories">开始训练</button>' : ''}</div>` : TAGS.map(tag => {
      const group = items.filter(id => byId.get(id).topicTag === tag);
      if (!group.length) return '';
      return `<details class="mistake-group" ${expandedMistakeGroups.has(tag) ? 'open' : ''}><summary><span class="mistake-group-title">${esc(tag)}</span><span class="mistake-group-count">${group.length}</span><span class="group-chevron">⌄</span></summary><div class="group-body">${filter === 'pending' ? `<button class="text-button group-review" data-group-review="${esc(tag)}">重练本组</button>` : ''}${group.map(id => {
        const q = byId.get(id), mistake = state.mistakes[id], source = examSource(q);
        return `<article class="mistake-item">${source ? `<div class="mistake-item-meta">${esc(source)}</div>` : ''}<p>${esc(q.stem)}</p><div class="mistake-footer"><span>错 ${mistake.count} 次</span><span class="mistake-item-actions"><button class="secondary" ${mistake.mastered ? `data-restore="${esc(id)}"` : `data-review="${esc(id)}"`}>${mistake.mastered ? '移回待复习' : '重练'}</button>${mistake.mastered ? '' : `<button class="text-button" data-master="${esc(id)}">已掌握</button>`}</span></div></article>`;
      }).join('')}</div></details>`;
    }).join('')}</div>`;
}

function apiConfigured() { try { return !!window.AndroidApp?.hasApiKey?.(); } catch { return false; } }
function settingsView() {
  const size = Number(state.settings.questionFontSize) || 19;
  return `<div class="page-screen settings-screen"><header class="page-header"><button class="back-button" data-action="home"><span>‹</span>首页</button><span class="header-spacer"></span></header><div class="page-intro"><h1>设置</h1></div>
    <section class="settings-card"><div class="settings-card-heading"><span class="settings-icon api-icon">AI</span><div><strong>DeepSeek 解析</strong><small>${apiConfigured() ? 'API Key 已保存在本机' : '使用自己的 API Key'}</small></div></div><button class="settings-row" data-action="configure"><span>${apiConfigured() ? 'API 设置' : '配置 API Key'}</span><span>›</span></button><p class="settings-note">解析使用个人账户额度，也可复制题目自行提问。</p></section>
    <section class="settings-card"><div class="settings-card-heading"><span class="settings-icon type-icon">Aa</span><div><strong>题目字号</strong><small>${size} px</small></div></div><div class="font-controls"><button class="font-control" data-action="font-dec" aria-label="缩小字号" ${size <= 17 ? 'disabled' : ''}>A−</button><span>${size} px</span><button class="font-control" data-action="font-inc" aria-label="放大字号" ${size >= 23 ? 'disabled' : ''}>A＋</button></div></section>
    <section class="settings-card"><div class="settings-card-heading"><span class="settings-icon backup-icon">↕</span><div><strong>学习记录</strong><small>更换手机前导出备份</small></div></div><div class="backup-actions"><button class="secondary" data-action="export-backup">导出记录</button><button class="secondary" data-action="import-backup">恢复记录</button></div><p class="settings-note">备份包含进度与错题，不包含 API Key。</p></section>
    <section class="settings-card"><div class="settings-card-heading"><span class="settings-icon feedback-icon">✎</span><div><strong>意见与题目纠错</strong><small>分享题目编号与问题描述</small></div></div><button class="settings-row" data-action="feedback"><span>填写反馈模板</span><span>›</span></button></section>
    <section class="settings-card app-info"><div><strong>版本</strong><span>研习政治 ${VERSION}</span></div><div><strong>题库</strong><span>${bank.length} 道选择题</span></div><div><strong>学习记录</strong><span>保存在本机，覆盖安装保留</span></div></section><p class="settings-footnote">题库仅供个人备考使用。题源与授权信息可在每题解析中查看。</p></div>`;
}

function applyQuestionFont() {
  const size = Math.max(17, Math.min(23, Number(state.settings.questionFontSize) || 19));
  document.documentElement.style.setProperty('--question-font-size', `${size}px`);
}
function render() {
  applyQuestionFont();
  app.innerHTML = review || page === 'training' ? questionView()
    : page === 'home' ? homeView()
      : page === 'categories' ? categoriesView()
        : page === 'directory' ? questionDirectoryView()
          : page === 'settings' ? settingsView() : mistakesView();
}

function questionText(q = current()) {
  const source = examSource(q);
  return `${q.topicTag}${source ? ` · ${source}` : ''} · ${q.questionType === 'single' ? '单选题' : '多选题'}\n\n${q.stem}\n\n${Object.entries(q.options).map(([letter, text]) => `${letter}. ${text}`).join('\n')}`;
}
async function copyQuestion() {
  const text = questionText();
  try {
    if (window.AndroidApp?.copyText) {
      if (!AndroidApp.copyText(text)) throw Error('copy');
    } else {
      try { await navigator.clipboard.writeText(text); }
      catch {
        const textarea = document.createElement('textarea');
        textarea.value = text; document.body.appendChild(textarea); textarea.select();
        const copied = document.execCommand('copy'); textarea.remove();
        if (!copied) throw Error('copy');
      }
    }
    toast('已复制完整题目');
  } catch { toast('复制失败，请长按题目选择并复制'); }
}

function showExplanation() { explanationId = current().id; renderExplanation(); dialog.showModal(); }
function renderExplanation() {
  const q = byId.get(explanationId);
  if (!q) return;
  const result = aiResults.get(q.id), loading = aiPending.has(q.id);
  const answerHint = q.explanationReviewStatus === 'answer_hint';
  const analysisLabel = q.explanationKind === 'generated' ? (answerHint ? '答案提示' : '自动预解析') : '参考解析';
  const sourceName = q.sourceName || (q.sourceType === 'past_exam' ? '历年考研政治真题' : '补充题库');
  const sourceUrl = /^https:\/\//.test(q.sourceUrl || '') ? q.sourceUrl : '';
  const attribution = q.sourceLicense || '题源授权信息未提供';
  const source = examSource(q);
  const answerInText = /(?:正确答案|参考答案|正确项为|例外项为)/.test(q.explanation || '');
  const answerLine = answerInText ? '' : `<p><strong>正确答案：${esc(q.answer.split('').join('、'))}</strong></p>`;
  const reviewNote = q.explanationKind !== 'generated' ? '' : answerHint ? '<p class="notice">暂缺逐项辨析，可用 DeepSeek 补充。</p>' : '<p class="notice">规则生成的预解析，仅供参考。</p>';
  const resultText = result?.error ? `<p class="ai-error">${esc(result.text)}</p>` : result ? `<h2 class="ai-heading">DeepSeek 解析</h2><p>${esc(result.text)}</p><div class="notice">AI 生成内容，请结合原题核对。</div>` : '';
  document.getElementById('explanation-content').innerHTML = `<div class="sheet-grip"></div><h2>${analysisLabel}</h2><div class="sheet-course">${esc(q.topicTag)}${source ? ` · ${esc(source)}` : ''}</div>${answerLine}${q.explanation ? `<p>${esc(q.explanation)}</p>` : '<p class="notice">本题暂无解析</p>'}${reviewNote}<details class="source-details"><summary>题源与授权</summary><div class="source"><strong>${esc(sourceName)}</strong><p>${esc(attribution)}</p>${sourceUrl ? `<a href="${esc(sourceUrl)}" target="_blank" rel="noopener noreferrer">查看来源</a>` : ''}</div></details>${resultText}<button class="primary generate-button" data-action="generate" ${loading ? 'disabled' : ''}>${loading ? '正在生成…' : result && !result.error ? '重新生成' : result?.error ? '重试' : 'DeepSeek 解析'}</button><div class="sheet-actions"><button class="text-button" data-action="configure">设置 API Key</button><button class="text-button" data-action="copy">复制题目</button></div>`;
}

function promptText(q) {
  return `请分析以下考研政治选择题，并按三个标题组织：\n【考点】概括对应课程知识点；\n【正确项理由】结合题干说明每个正确选项为什么成立；\n【其余选项辨析】单选题逐项说明错误选项的问题，多选题逐项说明全部选项。不要只复述选项，不确定的事实请明确说明。若题库答案可疑，请指出疑点。真题按考试当年语境分析，必要时补充与现行表述的区别。\n\n${questionText(q)}\n\n题库参考答案：${q.answer}`;
}

function makeBackup() {
  const keepKnown = object => Object.fromEntries(Object.entries(object || {}).filter(([id]) => byId.has(id)));
  return {
    app: 'yanxi-politics', formatVersion: 1, exportedAt: new Date().toISOString(), bankVersion: VERSION,
    state: {
      index: state.index, topicTag: state.topicTag, categoryIndexes: state.categoryIndexes,
      attempts: keepKnown(state.attempts), mistakes: keepKnown(state.mistakes), drafts: keepKnown(state.drafts),
      settings: { questionFontSize: state.settings.questionFontSize || 19 }
    }
  };
}
function exportBackup() {
  const text = JSON.stringify(makeBackup());
  try {
    if (window.AndroidApp?.exportBackup) { AndroidApp.exportBackup(text); return; }
    const a = document.createElement('a'), url = URL.createObjectURL(new Blob([text], { type: 'application/json' }));
    a.href = url; a.download = `研习政治-学习记录-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast('学习记录已导出');
  } catch { toast('导出失败，请重试'); }
}
function importBackup() {
  if (window.AndroidApp?.importBackup) { AndroidApp.importBackup(); return; }
  document.getElementById('backup-file').click();
}
function prepareBackupRestore(raw) {
  try {
    if (typeof raw !== 'string' || raw.length > 5000000) throw Error('文件过大或格式不正确');
    const parsed = JSON.parse(raw);
    if (parsed.app !== 'yanxi-politics' || parsed.formatVersion !== 1 || !parsed.state) throw Error('这不是有效的研习政治备份文件');
    const saved = parsed.state, restored = { index: 0, topicTag: null, categoryIndexes: {}, attempts: {}, mistakes: {}, drafts: {}, settings: {}, explanationCache: {} };
    const letters = value => [...new Set(String(value || '').toUpperCase().split('').filter(x => 'ABCD'.includes(x)))].sort().join('');
    for (const [id, record] of Object.entries(saved.attempts || {})) {
      const q = byId.get(id), answer = letters(record?.answer);
      if (q && answer && answer === String(record.answer).toUpperCase() && (q.questionType !== 'single' || answer.length === 1)) restored.attempts[id] = { answer, correct: answer === q.answer };
    }
    for (const [id, record] of Object.entries(saved.mistakes || {})) {
      if (!byId.has(id) || !record || !Number.isFinite(Number(record.count))) continue;
      restored.mistakes[id] = { count: Math.max(1, Math.min(100000, Math.floor(Number(record.count)))), mastered: !!record.mastered, lastAnswer: letters(record.lastAnswer) };
    }
    for (const [id, choices] of Object.entries(saved.drafts || {})) {
      const q = byId.get(id), draft = Array.isArray(choices) ? choices.filter(x => q?.options?.[x]) : [];
      if (q && !restored.attempts[id] && draft.length) restored.drafts[id] = [...new Set(draft)].sort();
    }
    restored.topicTag = LEGACY_TAGS[saved.topicTag] || (TAGS.includes(saved.topicTag) ? saved.topicTag : null);
    const categories = saved.categoryIndexes || {};
    for (const tag of TAGS) {
      const oldTag = Object.keys(LEGACY_TAGS).find(key => LEGACY_TAGS[key] === tag);
      const rawIndex = categories[tag] ?? categories[oldTag];
      if (Number.isFinite(Number(rawIndex))) restored.categoryIndexes[tag] = Math.max(0, Math.min(byTag(tag).length - 1, Math.floor(Number(rawIndex))));
    }
    if (restored.topicTag) restored.index = bank.indexOf(byTag(restored.topicTag)[restored.categoryIndexes[restored.topicTag] || 0]);
    restored.settings.questionFontSize = Math.max(17, Math.min(23, Number(saved.settings?.questionFontSize) || 19));
    pendingRestore = restored;
    const answerCount = Object.keys(restored.attempts).length, mistakeCount = Object.keys(restored.mistakes).length;
    document.getElementById('restore-summary').innerHTML = `<div class="sheet-grip"></div><h2>恢复学习记录</h2><p>备份中有 ${answerCount} 道已答题和 ${mistakeCount} 道错题记录。</p><p class="notice">恢复会替换此设备当前的学习记录。API Key 会继续保留在本机。</p><div class="restore-actions"><button class="secondary" data-action="cancel-restore">取消</button><button class="primary" data-action="confirm-restore">确认恢复</button></div>`;
    document.getElementById('restore-dialog').showModal();
  } catch (error) { pendingRestore = null; toast(error.message || '备份文件无法读取'); }
}
function confirmRestore() {
  if (!pendingRestore) return;
  state = pendingRestore; pendingRestore = null; review = null; page = 'home';
  document.getElementById('restore-dialog').close(); save(); render(); window.scrollTo(0, 0); toast('学习记录已恢复');
}
window.onBackupImported = prepareBackupRestore;

async function shareFeedback() {
  const template = `研习政治 ${VERSION} 意见反馈\n\n问题描述：\n\n题目编号（如有）：\n\n手机型号与系统版本（可选）：`;
  if (window.AndroidApp?.shareText) { AndroidApp.shareText(template); toast('已打开系统分享面板'); return; }
  try {
    if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(template);
    else if (window.AndroidApp?.copyText) AndroidApp.copyText(template);
    else throw Error('copy');
    toast('反馈模板已复制');
  } catch { toast('复制失败，请稍后重试'); }
}
function generate() {
  const q = byId.get(explanationId);
  if (!q || aiPending.has(q.id)) return;
  if (!window.AndroidApp?.requestExplanation) { toast('请在安卓 App 内使用 API 解析'); return; }
  if (!AndroidApp.hasApiKey()) { AndroidApp.configureApi(); return; }
  const requestId = `${q.id}:${Date.now()}`;
  aiRequests.set(requestId, q.id); aiPending.add(q.id); renderExplanation();
  AndroidApp.requestExplanation(requestId, promptText(q));
}

window.onNativeExplanation = result => {
  const id = aiRequests.get(result.id);
  if (!id) return;
  aiRequests.delete(result.id); aiPending.delete(id);
  const explanation = { text: result.error || result.text, error: !!result.error };
  aiResults.set(id, explanation);
  if (!explanation.error) {
    state.explanationCache = Object.fromEntries([...aiResults.entries()].filter(([, item]) => !item.error).slice(-40));
    save();
  }
  if (dialog.open && explanationId === id) renderExplanation();
};
window.onApiConfigured = () => { toast('API 设置已保存'); if (dialog.open) renderExplanation(); if (page === 'settings') render(); };

function handleAndroidBack() {
  const imageView = document.getElementById('question-image-view');
  if (imageView.open) { imageView.close(); return true; }
  const restoreDialog = document.getElementById('restore-dialog');
  if (restoreDialog.open) { restoreDialog.close(); pendingRestore = null; return true; }
  if (dialog.open) { dialog.close(); return true; }
  if (review) { go('mistakes'); return true; }
  if (page === 'training') { go('directory'); return true; }
  if (page === 'directory') { go('categories'); return true; }
  if (page !== 'home') { go('home'); return true; }
  return false;
}

document.addEventListener('click', event => {
  const button = event.target.closest('button');
  if (!button || button.disabled) return;
  if (button.dataset.topic) openTopicDirectory(button.dataset.topic);
  if (button.dataset.questionIndex !== undefined) openQuestion(state.topicTag, button.dataset.questionIndex);
  if (button.dataset.directoryFilter) { directoryFilter = button.dataset.directoryFilter; render(); }
  if (button.dataset.groupReview) startReview(pending().filter(id => byId.get(id).topicTag === button.dataset.groupReview));
  if (button.dataset.choice) choose(button.dataset.choice);
  if (button.dataset.filter) { filter = button.dataset.filter; render(); }
  if (button.dataset.review) startReview([button.dataset.review]);
  if (button.dataset.restore) { state.mistakes[button.dataset.restore].mastered = false; save(); render(); }
  if (button.dataset.master) { const item = state.mistakes[button.dataset.master]; if (item) { item.mastered = true; save(); render(); } }
  switch (button.dataset.action) {
    case 'zoom-question': {
      const q = current();
      if (!q?.image) break;
      const image = document.getElementById('question-zoom-image');
      image.onload = () => { image.style.width = `${Math.min(image.naturalWidth, window.innerWidth - 48)}px`; };
      image.src = q.image;
      image.alt = q.imageAlt || '原卷配图';
      document.getElementById('question-image-view').showModal();
      break;
    }
    case 'zoom-figure': {
      const image = document.getElementById('question-zoom-image');
      const fit = Math.min(image.naturalWidth, window.innerWidth - 48);
      image.style.width = `${parseFloat(image.style.width) > fit ? fit : fit * 2}px`;
      break;
    }
    case 'close-question-image': document.getElementById('question-image-view').close(); break;
    case 'home': go('home'); break;
    case 'categories': go('categories'); break;
    case 'mistakes': go('mistakes'); break;
    case 'settings': go('settings'); break;
    case 'directory': openTopicDirectory(state.topicTag); break;
    case 'continue': continueTraining(); break;
    case 'continue-topic': openQuestion(state.topicTag, activeIndex()); break;
    case 'submit': submit(); break;
    case 'previous': move(-1); break;
    case 'next': move(1); break;
    case 'explain': showExplanation(); break;
    case 'copy': copyQuestion(); break;
    case 'close': dialog.close(); break;
    case 'generate': generate(); break;
    case 'export-backup': exportBackup(); break;
    case 'import-backup': importBackup(); break;
    case 'confirm-restore': confirmRestore(); break;
    case 'cancel-restore':
      pendingRestore = null; document.getElementById('restore-dialog').close(); break;
    case 'configure':
      if (window.AndroidApp?.configureApi) AndroidApp.configureApi();
      else toast('请在安卓 App 内配置 API');
      break;
    case 'feedback': shareFeedback(); break;
    case 'font-dec':
      state.settings.questionFontSize = Math.max(17, (Number(state.settings.questionFontSize) || 19) - 2); save(); render(); break;
    case 'font-inc':
      state.settings.questionFontSize = Math.min(23, (Number(state.settings.questionFontSize) || 19) + 2); save(); render(); break;
  }
});

document.addEventListener('change', event => {
  if (event.target.matches('[data-mistake-course]')) {
    mistakeTopicFilter = event.target.value; render();
  }
  if (event.target.id === 'backup-file' && event.target.files?.[0]) {
    const file = event.target.files[0], reader = new FileReader();
    reader.onload = () => prepareBackupRestore(String(reader.result || ''));
    reader.onerror = () => toast('无法读取备份文件');
    reader.readAsText(file); event.target.value = '';
  }
});

document.addEventListener('toggle', event => {
  if (!event.target.matches?.('.mistake-group')) return;
  const tag = event.target.querySelector('.mistake-group-title')?.textContent;
  if (!tag) return;
  if (event.target.open) expandedMistakeGroups.add(tag);
  else expandedMistakeGroups.delete(tag);
}, true);

render();

// Image errors do not bubble; show a visible message instead of a broken icon.
document.addEventListener('error', event => {
  const image = event.target;
  if (image.matches?.('.question-figure-image')) {
    const message = document.createElement('p');
    message.className = 'notice';
    message.textContent = '原卷配图读取失败，请重新进入题目或更新安装包。';
    image.closest('figure').replaceWith(message);
  }
}, true);
