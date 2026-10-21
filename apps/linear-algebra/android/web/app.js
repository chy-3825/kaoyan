'use strict';

const bank = window.QUESTIONS || [];
const byId = new Map(bank.map(q => [q.id, q]));
const KEY = 'yanxi-linear-v1';
const EXAMS = ['数学一', '数学二', '数学三'];
const EXAM_SHORT = { 数学一: '数一', 数学二: '数二', 数学三: '数三' };
const CHAPTER_ORDER = ['行列式', '矩阵', '向量', '线性方程组', '矩阵的特征值与特征向量', '二次型'];
const TOPIC_ORDER = {
  行列式: ['行列式'],
  矩阵: ['矩阵的运算与变换', '伴随矩阵与可逆矩阵', '矩阵的秩', '置换矩阵与伴随矩阵', '伴随矩阵与矩阵幂', '矩阵恒等式与幂零矩阵', '矩阵恒等式与特征值'],
  向量: ['向量组之间的线性表示', '向量组的线性相关性', '极大线性无关组与矩阵秩', '向量内积与向量正交'],
  线性方程组: ['线性方程组', '矩阵方程有解条件', '列向量组表示与方程组有解性'],
  矩阵的特征值与特征向量: ['特征值与特征向量', '矩阵的相似与相似对角化', '含参数矩阵的实特征值比较'],
  二次型: ['二次型', '二次型的秩与规范形', '二次型标准形与柱面判定']
};
const TYPE_LABEL = { single: '选择题', fill: '填空题', solve: '解答题' };
const SUBJECT_SHORT = { '线性代数': '线代' };
const DEFAULT_STATE = {
  exam: '', subject: '线性代数', chapter: '', topicKey: '', cursorByTopic: {}, attempts: {}, mistakes: {},
  drafts: {}, revealed: {}, hints: {}, explanationCache: {}
};

let state = { ...DEFAULT_STATE };
let page = 'home';
let review = null;
let typeFilter = 'all';
let statusFilter = 'all';
let confirmImport = false;
const dialog = document.getElementById('explanation');
const app = document.getElementById('app');
const aiResults = new Map();
const aiPending = new Set();
const aiRequests = new Map();
let explanationId = null;
let imageZoomScale = 1;
let toastTimer;

try {
  const saved = JSON.parse(localStorage.getItem(KEY));
  if (saved && saved.attempts && saved.mistakes) state = { ...state, ...saved };
} catch { /* use a clean local state */ }
state = {
  ...DEFAULT_STATE,
  ...state,
  subject: '线性代数',
  cursorByTopic: state.cursorByTopic && typeof state.cursorByTopic === 'object' ? state.cursorByTopic : {},
  attempts: state.attempts && typeof state.attempts === 'object' ? state.attempts : {},
  mistakes: state.mistakes && typeof state.mistakes === 'object' ? state.mistakes : {},
  drafts: state.drafts && typeof state.drafts === 'object' ? state.drafts : {},
  revealed: state.revealed && typeof state.revealed === 'object' ? state.revealed : {},
  hints: state.hints && typeof state.hints === 'object' ? state.hints : {},
  explanationCache: state.explanationCache && typeof state.explanationCache === 'object' ? state.explanationCache : {}
};
for (const [id, item] of Object.entries(state.explanationCache || {})) aiResults.set(id, item);

const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
}[c]));
const examSource = q => q.isSupplemental
  ? '专题补充'
  : [q.examYear, q.questionNo].filter(value => value !== null && value !== undefined && value !== '').join(' · ');
const questionKey = q => `${q.subject}::${q.topicPath || `${q.chapter}::${q.topic}`}`;
const cursorKey = () => `${state.subject}::${state.topicKey}`;

function toast(message) {
  const el = document.getElementById('toast');
  el.textContent = message;
  el.classList.add('visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('visible'), 3000);
}

function save() {
  try {
    state.explanationCache = Object.fromEntries([...aiResults.entries()].filter(([, x]) => !x.error).slice(-40));
    localStorage.setItem(KEY, JSON.stringify(state));
  } catch { toast('无法保存学习记录，请检查手机存储空间'); }
}

function byTopic(key = state.topicKey, subject = state.subject) {
  return bank.filter(q => q.subject === subject && questionKey(q) === key)
    .sort((a, b) => (a.examYear || 9999) - (b.examYear || 9999)
      || EXAMS.indexOf(a.exam) - EXAMS.indexOf(b.exam)
      || (a.questionNo || 9999) - (b.questionNo || 9999)
      || a.id.localeCompare(b.id));
}

function normalizedChapter(chapter) {
  return chapter.replace('矩阵的特征值和特征向量', '矩阵的特征值与特征向量');
}

function topicsFor(subject = state.subject) {
  const found = new Map();
  for (const q of bank) {
    if (q.subject !== subject) continue;
    const key = questionKey(q);
    const chapter = normalizedChapter(q.chapter);
    if (!found.has(key)) found.set(key, { key, subject: q.subject, chapter, name: q.topic, rows: [] });
    found.get(key).rows.push(q);
  }
  const rank = (list, value) => {
    const index = list.indexOf(value);
    return index < 0 ? list.length : index;
  };
  return [...found.values()].sort((a, b) => rank(CHAPTER_ORDER, a.chapter) - rank(CHAPTER_ORDER, b.chapter)
    || rank(TOPIC_ORDER[a.chapter] || [], a.name) - rank(TOPIC_ORDER[a.chapter] || [], b.name)
    || a.name.localeCompare(b.name, 'zh-CN'));
}

function chapterRows(chapter) {
  return topicsFor().filter(topic => topic.chapter === chapter).flatMap(topic => topic.rows);
}

function topicFor(key = state.topicKey) { return topicsFor().find(topic => topic.key === key); }

function progress(list) { return list.filter(q => state.attempts[q.id]).length; }
function pendingMistakes() {
  return Object.entries(state.mistakes).filter(([id, item]) => byId.has(id) && !item.mastered)
    .map(([id]) => id).sort((a, b) => (state.mistakes[b]?.count || 0) - (state.mistakes[a]?.count || 0));
}
function status(q) {
  if (state.attempts[q.id]) return state.attempts[q.id].correct === null ? 'checked' : state.attempts[q.id].correct ? 'correct' : 'wrong';
  return state.drafts[q.id] ? 'draft' : 'unseen';
}
function mistakeStatus(q) { return Boolean(state.mistakes[q.id] && !state.mistakes[q.id].mastered); }
function visibleStatus(q) {
  if (mistakeStatus(q)) return 'wrong';
  if (state.mistakes[q.id]?.mastered) return 'correct';
  return status(q);
}
function activeList() { return review ? review.ids.map(id => byId.get(id)).filter(Boolean) : byTopic(); }
function activeIndex() {
  if (review) return Math.max(0, Math.min(review.index, review.ids.length - 1));
  const list = byTopic();
  return Math.max(0, Math.min(Number(state.cursorByTopic[cursorKey()]) || 0, Math.max(0, list.length - 1)));
}
function current() { return activeList()[activeIndex()]; }
function attemptFor(q) { return review ? (review.attempts[q.id] || null) : (state.attempts[q.id] || null); }

function go(nextPage) {
  page = nextPage;
  review = null;
  if (dialog.open) dialog.close();
  render();
  window.scrollTo(0, 0);
}

function openChapter(chapter) {
  if (!CHAPTER_ORDER.includes(chapter) || !chapterRows(chapter).length) return;
  state.chapter = chapter;
  state.topicKey = '';
  typeFilter = 'all';
  statusFilter = 'all';
  save();
  go('topics');
}

function openTopic(key) {
  state.topicKey = key;
  const found = topicFor(key);
  if (!found) { go('directory'); return; }
  state.chapter = found.chapter;
  typeFilter = 'all';
  statusFilter = 'all';
  save();
  go('topicQuestions');
}

function ensureCursor() {
  if (!state.topicKey || cursorKey() in state.cursorByTopic) return;
  const list = byTopic();
  const first = list.findIndex(q => !state.attempts[q.id]);
  state.cursorByTopic[cursorKey()] = first < 0 ? 0 : first;
}

function continueTraining() {
  if (state.topicKey && byTopic().length) {
    ensureCursor();
    save();
    review = null;
    page = 'training';
    render();
    return;
  }
  if (state.chapter && chapterRows(state.chapter).length) go('topics');
  else go('directory');
}

function openQuestion(key, index) {
  const list = byTopic(key, state.subject);
  if (!list.length) return;
  state.topicKey = key;
  state.chapter = topicFor(key)?.chapter || '';
  state.cursorByTopic[cursorKey()] = Math.max(0, Math.min(index, list.length - 1));
  review = null;
  page = 'training';
  save();
  render();
  window.scrollTo(0, 0);
}

function choice(q, letter) {
  if (attemptFor(q) || !'ABCD'.includes(letter)) return;
  const correct = q.answer ? letter === q.answer : null;
  const record = { answer: letter, correct, at: Date.now() };
  state.attempts[q.id] = record;
  if (review) review.attempts[q.id] = record;
  if (correct === false) addMistake(q, letter);
  save();
  render();
}

function addMistake(q, answer) {
  const old = state.mistakes[q.id] || { count: 0, mastered: false };
  state.mistakes[q.id] = { ...old, count: old.count + 1, lastAnswer: answer || '', mastered: false, at: Date.now() };
}

function toggleManualMistake() {
  const q = current();
  if (!q || q.questionType !== 'solve') return;
  const old = state.mistakes[q.id];
  if (old?.manual && !old.mastered) {
    if (old.count > 0) {
      state.mistakes[q.id] = { ...old, manual: false, at: Date.now() };
      toast('主动标记已撤销，答错记录仍保留');
    } else {
      delete state.mistakes[q.id];
      toast('已从错题本移除');
    }
  } else {
    state.mistakes[q.id] = { ...(old || {}), count: old?.count || 0, manual: true, mastered: false, at: Date.now() };
    toast(old?.mastered ? '已重新加入错题本' : '已加入错题本');
  }
  save();
  render();
}

function markSelf(correct) {
  const q = current();
  if (!q) return;
  const response = state.drafts[q.id] || state.attempts[q.id]?.answer || '';
  const record = { answer: response, correct, self: true, at: Date.now() };
  state.attempts[q.id] = record;
  if (review) review.attempts[q.id] = record;
  delete state.drafts[q.id];
  if (!correct) addMistake(q, response);
  else if (state.mistakes[q.id]) {
    state.mistakes[q.id].mastered = true;
    if (review) {
      review.ids.splice(review.index, 1);
      if (!review.ids.length) { save(); go('mistakes'); return; }
      review.index = Math.min(review.index, review.ids.length - 1);
    }
  }
  save();
  render();
}

function markMastered() {
  const q = current();
  if (!q || !state.mistakes[q.id]) return;
  state.mistakes[q.id].mastered = true;
  save();
  if (review) {
    review.ids.splice(review.index, 1);
    if (!review.ids.length) { go('mistakes'); return; }
    review.index = Math.min(review.index, review.ids.length - 1);
  }
  render();
}

function revealAnswer() {
  const q = current();
  if (!q) return;
  state.revealed[q.id] = true;
  if (q.questionType === 'fill' && !state.attempts[q.id]) {
    state.drafts[q.id] = document.getElementById('fill-answer')?.value || state.drafts[q.id] || '';
  }
  save();
  render();
}

function move(delta) {
  const list = activeList(), next = activeIndex() + delta;
  if (next < 0) return;
  if (next >= list.length) {
    if (review) go('mistakes');
    return;
  }
  if (review) review.index = next;
  else state.cursorByTopic[cursorKey()] = next;
  save();
  if (dialog.open) dialog.close();
  render();
  window.scrollTo(0, 0);
}

function startMistakes(ids = pendingMistakes()) {
  const valid = ids.filter(id => byId.has(id) && state.mistakes[id] && !state.mistakes[id].mastered);
  if (!valid.length) return;
  review = { ids: valid, index: 0, attempts: {} };
  page = 'training';
  render();
  window.scrollTo(0, 0);
}

function homeView() {
  const done = Object.keys(state.attempts).filter(id => byId.has(id)).length;
  const mistakes = pendingMistakes().length;
  const selected = current();
  const title = state.topicKey && selected ? '继续训练' : '开始训练';
  const selectedTopic = selected && state.topicKey ? topicFor(state.topicKey) : null;
  const context = selectedTopic ? `${selectedTopic.chapter} · ${selectedTopic.name}` : state.chapter || '';
  const pct = bank.length ? Math.round(done / bank.length * 100) : 0;
  return `<section class="home-screen">
    <header class="brand-bar"><div class="brand-lockup"><span class="brand-mark" aria-hidden="true"><svg viewBox="0 0 48 48"><path d="M13 10h22v28H13zM24 10v28M13 24h22"/></svg></span><strong>研习线代</strong></div><button class="icon-button" data-action="settings" aria-label="设置"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-1.7 1.7-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-2.4v-.2a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L8 17l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.6-1H6.6v-2.4h.2a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L8 8.6l1.7-1.7.1.1a1.7 1.7 0 0 0 1.9.3 1.7 1.7 0 0 0 1-1.6v-.2h2.4v.2a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1 1.7 1.7-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2V14h-.2a1.7 1.7 0 0 0-1.5 1z"/></svg></button></header>
    <section class="math-hero" aria-hidden="true"><div class="hero-graph"><svg viewBox="0 0 210 130"><path d="M70 25h-15v82h15M140 25h15v82h-15M82 43h20v17H82zM108 43h20v17h-20zM82 70h20v17H82zM108 70h20v17h-20z"/></svg></div><span class="hero-grid"></span></section>
    <button class="continue-card" data-action="continue"><span class="continue-icon"><svg viewBox="0 0 24 24"><path d="M8 5.5v13l10-6.5z"/></svg></span><span class="continue-copy"><strong>${title}</strong>${context ? `<small>${esc(context)}</small>` : ''}</span><span class="continue-chevron">›</span></button>
    ${done ? `<section class="home-progress"><div class="progress-heading"><span>已练 ${done} / ${bank.length}</span><small>${pct}%</small></div><div class="progress-track"><span style="width:${pct}%"></span></div></section>` : ''}
    <div class="home-actions"><button class="home-action" data-action="directory"><span class="action-symbol course-symbol"><svg viewBox="0 0 24 24"><path d="M4 5.5h6.5A2.5 2.5 0 0 1 13 8v11H6.5A2.5 2.5 0 0 0 4 21zM20 5.5h-4A3 3 0 0 0 13 8v11h4.5A2.5 2.5 0 0 1 20 21z"/></svg></span><strong>考点目录</strong><span class="action-arrow">›</span></button><button class="home-action" data-action="mistakes"><span class="action-symbol mistake-symbol"><svg viewBox="0 0 24 24"><path d="M6 4.5h12a2 2 0 0 1 2 2v13l-4-2.5-4 2.5-4-2.5-4 2.5v-13a2 2 0 0 1 2-2Z"/><path d="M9 9h6M9 13h6"/></svg></span><strong>错题本</strong><span class="action-count">${mistakes}</span><span class="action-arrow">›</span></button></div>
  </section>`;
}

function directoryView() {
  const topics = topicsFor();
  const chapters = [...new Set(topics.map(topic => topic.chapter))];
  const total = bank.filter(q => q.subject === state.subject).length;
  return `<div class="page-screen directory-screen"><header class="page-header"><button class="back-button" data-action="home"><span>‹</span>首页</button><button class="icon-button small-icon" data-action="settings" aria-label="设置">⚙</button></header><div class="page-intro directory-intro"><h1>线性代数</h1><p>${total} 道题 · ${chapters.length} 个章节 · 按教材顺序</p></div>
    <div class="chapter-list">${chapters.map((chapter, index) => {
      const rows = chapterRows(chapter), done = progress(rows), pct = rows.length ? Math.round(done / rows.length * 100) : 0;
      const pending = rows.filter(mistakeStatus).length;
      return `<button class="chapter-card" data-open-chapter="${esc(chapter)}"><span class="chapter-number">${String(index + 1).padStart(2, '0')}</span><span class="chapter-card-main"><strong>${esc(chapter)}</strong><small>${topics.filter(topic => topic.chapter === chapter).length} 个考点 · ${rows.length} 题 · 已练 ${done}${pending ? ` · 待复习 ${pending}` : ''}</small><i class="course-meter"><b style="width:${pct}%"></b></i></span><span class="course-card-arrow">›</span></button>`;
    }).join('')}</div>
  </div>`;
}

function topicsView() {
  const topics = topicsFor().filter(topic => topic.chapter === state.chapter);
  if (!topics.length) return `<div class="empty-state">这个章节暂时没有题目<button class="secondary" data-action="directory">返回目录</button></div>`;
  const count = topics.reduce((sum, topic) => sum + topic.rows.length, 0);
  return `<div class="page-screen directory-screen"><header class="page-header"><button class="back-button" data-action="directory"><span>‹</span>章节目录</button><button class="icon-button small-icon" data-action="home" aria-label="首页">⌂</button></header><div class="page-intro directory-intro"><h1>${esc(state.chapter)}</h1><p>${topics.length} 个考点 · ${count} 道题</p></div><div class="subtopic-list">${topics.map((topic, index) => {
    const done = progress(topic.rows), pending = topic.rows.filter(mistakeStatus).length;
    const pct = topic.rows.length ? Math.round(done / topic.rows.length * 100) : 0;
    return `<button class="subtopic-card" data-open-topic="${esc(topic.key)}"><span class="subtopic-number">${String(index + 1).padStart(2, '0')}</span><span class="subtopic-card-main"><strong>${esc(topic.name)}</strong><small>${topic.rows.length} 题 · 已练 ${done}${pending ? ` · 待复习 ${pending}` : ''}</small><i class="course-meter"><b style="width:${pct}%"></b></i></span><span class="course-card-arrow">›</span></button>`;
  }).join('')}</div></div>`;
}

function topicQuestionsView() {
  const topic = topicFor();
  if (!topic) return `<div class="empty-state">请先选择一个考点<button class="secondary" data-action="directory">返回目录</button></div>`;
  const allRows = byTopic(topic.key);
  const counts = {
    all: allRows.length,
    unseen: allRows.filter(q => !state.attempts[q.id]).length,
    wrong: allRows.filter(mistakeStatus).length
  };
  const visible = allRows.filter(q => (typeFilter === 'all' || q.questionType === typeFilter)
    && (statusFilter === 'all' || (statusFilter === 'unseen' ? !state.attempts[q.id] : mistakeStatus(q))));
  const label = q => {
    const item = state.mistakes[q.id];
    if (item && !item.mastered) return item.count ? `答错 ${item.count} 次${item.manual ? ' · 主动加入' : ''}` : '主动加入错题本';
    if (item?.mastered) return '已掌握';
    if (status(q) === 'correct') return '已掌握';
    if (status(q) === 'wrong') return '已答错';
    if (status(q) === 'checked') return '已核对';
    if (status(q) === 'draft') return '有草稿';
    return '未作答';
  };
  return `<div class="page-screen directory-screen"><header class="page-header"><button class="back-button" data-action="topics"><span>‹</span>${esc(topic.chapter)}</button><button class="icon-button small-icon" data-action="home" aria-label="首页">⌂</button></header><div class="page-intro directory-intro"><h1>${esc(topic.name)}</h1><p>${allRows.length} 道题 · 按年份顺序排列</p></div>
    <div class="directory-filters type-filters">${[['all','全部题型'],['single','选择'],['fill','填空'],['solve','解答']].map(([key,text]) => `<button class="directory-filter ${typeFilter === key ? 'active' : ''}" data-type-filter="${key}">${text}</button>`).join('')}</div>
    <div class="directory-filters status-filters">${[['all','全部'],['unseen','未答'],['wrong','错题本']].map(([key,text]) => `<button class="directory-filter ${statusFilter === key ? 'active' : ''}" data-status-filter="${key}">${text}<span>${counts[key]}</span></button>`).join('')}</div>
    <div class="question-index-list">${visible.map(q => {
      const s = visibleStatus(q), index = allRows.findIndex(row => row.id === q.id), active = state.topicKey === topic.key && current()?.id === q.id;
      return `<button class="question-index-row ${s} ${active ? 'current' : ''}" data-open-question="${esc(topic.key)}" data-open-index="${index}"><span class="question-index-main"><strong>${esc(examSource(q))}</strong><small>${q.isSupplemental ? '专题补充' : (EXAM_SHORT[q.exam] || q.exam)} · ${TYPE_LABEL[q.questionType]} · 难度 ${q.difficulty}/5</small></span><span class="question-status-pill ${s}">${label(q)}</span><span class="course-card-arrow">›</span></button>`;
    }).join('') || '<div class="empty-state">当前筛选下没有题目</div>'}</div></div>`;
}

function rating(value) { return `<span class="difficulty">难度 <b>${value}</b> / 5</span>`; }

function questionView() {
  const q = current();
  if (!q) return `<div class="empty-state">这组题目暂不可用<button class="secondary" data-action="topicQuestions">返回题目列表</button></div>`;
  const list = activeList(), index = activeIndex(), attempt = attemptFor(q);
  const type = TYPE_LABEL[q.questionType] || '解答题';
  const correct = attempt?.correct;
  const showAnswer = Boolean(state.revealed[q.id]);
  const source = examSource(q);
  const options = q.questionType === 'single' && q.options && Object.keys(q.options).length ? `<div class="written-options" aria-label="选择答案">${['A','B','C','D'].map(letter => {
    const selected = attempt?.answer === letter, right = q.answer === letter;
    const cls = attempt ? (right ? 'correct' : selected ? 'wrong' : '') : '';
    return `<button class="written-option ${cls} ${selected?'selected':''}" data-choice="${letter}" ${attempt?'disabled':''}><strong>${letter}</strong><span>${esc(q.options[letter] || '')}</span></button>`;
  }).join('')}</div>` : q.questionType === 'single' ? `<div class="choice-row" aria-label="选择答案">${['A','B','C','D'].map(letter => {
    const selected = attempt?.answer === letter, right = q.answer === letter;
    const cls = attempt ? (right ? 'correct' : selected ? 'wrong' : '') : '';
    return `<button class="choice-chip ${cls} ${selected?'selected':''}" data-choice="${letter}" ${attempt?'disabled':''} aria-label="选 ${letter}">${letter}</button>`;
  }).join('')}</div>` : '';
  const fill = q.questionType === 'fill' && !attempt ? `<label class="answer-input-label" for="fill-answer">你的答案</label><input id="fill-answer" class="answer-input" value="${esc(state.drafts[q.id] || '')}" placeholder="写下你的答案" autocomplete="off">` : '';
  const responseAction = q.questionType !== 'single' && !showAnswer && !attempt
    ? `<button class="primary response-submit" data-action="reveal">${q.questionType==='fill'?'核对答案':'完成作答 · 查看答案'}</button>` : '';
  const answerContent = showAnswer ? `<section class="answer-panel"><div class="answer-heading">${q.answer ? `<span>参考答案　<strong>${esc(q.answer)}</strong></span>` : '<span>参考答案</span>'}</div>${q.answerText ? `<div class="answer-text">${esc(q.answerText)}</div>` : ''}${q.answerImage ? `<img class="answer-image" src="${esc(q.answerImage)}" loading="lazy" alt="第 ${q.questionNo} 题参考答案" data-action="zoom-answer">` : (!q.answer && !q.answerText ? '<p class="answer-unavailable">暂无离线参考答案，可用 DeepSeek 看题解析。</p>' : '')}${q.questionType === 'single' ? '' : `<div class="self-assess"><button class="self-correct" data-action="self-correct">我已掌握</button><button class="self-wrong" data-action="self-wrong">还需重练</button></div>`}</section>` : '';
  const answerLabel = q.questionType === 'single' && q.options ? `${q.answer} · ${q.options[q.answer] || ''}` : q.answer;
  const result = q.questionType === 'single' && attempt ? `<div class="result ${correct===true?'correct':correct===false?'wrong':'unknown'}"><strong>${correct===true?'回答正确':correct===false?'回答错误 · 已加入错题本':'答案待核对'}</strong><span>${q.answer?`参考答案：${esc(answerLabel)}`:'可查看解析或自我核对'}</span>${q.answerText||q.answerImage?`<button class="answer-toggle" data-action="toggle-answer">${showAnswer?'收起参考解析':'查看参考解析'}</button>`:''}${correct===null?'<div class="self-assess"><button class="self-correct" data-action="self-correct">我答对了</button><button class="self-wrong" data-action="self-wrong">还需重练</button></div>':''}${correct===true&&state.mistakes[q.id]&&!state.mistakes[q.id].mastered?'<button class="master-button" data-action="mastered">标记已掌握</button>':''}</div>` : '';
  const mistakeItem = state.mistakes[q.id];
  const manualSaved = mistakeItem?.manual && !mistakeItem.mastered;
  const mistakeButton = q.questionType === 'solve' ? `<button class="mistake-toggle ${manualSaved ? 'saved' : ''}" data-action="toggle-manual-mistake" ${!manualSaved && mistakeItem && !mistakeItem.mastered && mistakeItem.count > 0 ? 'disabled' : ''}>${manualSaved ? (mistakeItem.count ? '已加入错题本 · 撤销主动标记' : '已加入错题本 · 撤销') : mistakeItem && !mistakeItem.mastered ? '已因答错收录' : mistakeItem?.mastered ? '重新加入错题本' : '加入错题本'}</button>` : '';
  const backAction = review ? 'mistakes' : 'topicQuestions';
  const backLabel = review ? '错题本' : '题目列表';
  const heading = review ? '错题复习' : `${SUBJECT_SHORT[q.subject] || q.subject} · ${q.topic}`;
  return `<div class="training-screen"><header class="training-head"><button class="back-button" data-action="${backAction}"><span>‹</span>${backLabel}</button><div class="training-course"><span>${esc(heading)}</span><button class="directory-shortcut" data-action="topicQuestions" aria-label="打开本考点题目列表"><svg viewBox="0 0 24 24"><path d="M5 6h14M5 12h14M5 18h9"/></svg></button></div></header>
    <div class="question-progress"><span>${index + 1} / ${list.length}</span><div class="progress-track"><span style="width:${Math.round((index + 1) / Math.max(1,list.length) * 100)}%"></span></div></div>
    <article class="question-card"><div class="question-meta">${q.isSupplemental ? '' : `<span class="source-exam">${esc(EXAM_SHORT[q.exam] || q.exam)}</span>`}<strong>${esc(source)}</strong><span>${type}</span>${rating(q.difficulty)}</div><div class="question-topic">${esc(q.topic)}</div><button class="hint-toggle" data-action="hint">${state.hints[q.id]?'收起考点提示':'查看考点提示'}　${state.hints[q.id]?'⌃':'⌄'}</button>${state.hints[q.id]?`<div class="study-hint">${esc(q.studyTip || `围绕“${q.topic}”识别题目条件，选用对应定义、定理或公式推导；注意检验适用条件并回代核对。`)}</div>`:''}
      ${q.image ? `<button class="question-image-button" data-action="zoom-question"><img class="question-image" src="${esc(q.image)}" alt="${esc(`${source} ${type}`)}" fetchpriority="high"></button>` : q.questionText ? `<div class="text-question">${esc(q.questionText)}</div>` : `<div class="missing-question">原题图片暂不可用 <a href="${esc(q.sourceUrl)}">查看来源</a></div>`}
      ${options}${fill}${responseAction}${result}${answerContent}${mistakeButton}
      <div class="question-tools"><button class="tool-button" data-action="explain"><span class="tool-icon">✳</span>DeepSeek 解析</button><button class="tool-button" data-action="share"><span class="tool-icon">${q.isSupplemental?'▣':'↗'}</span>${q.isSupplemental?'复制整题':'分享原题图'}</button></div>
    </article><nav class="bottom-nav"><button class="secondary" data-action="previous" ${index===0?'disabled':''}>上一题</button><button class="primary" data-action="next" ${index===list.length-1?'disabled':''}>下一题</button></nav></div>`;
}

function mistakesView() {
  const ids = pendingMistakes();
  const rows = ids.map(id => ({ q: byId.get(id), item: state.mistakes[id] })).filter(x => x.q)
    .sort((a,b) => b.item.at - a.item.at);
  const groups = new Map();
  for (const item of rows) {
    const chapter = normalizedChapter(item.q.chapter);
    const k = chapter;
    if (!groups.has(k)) groups.set(k, { chapter, rows:[] });
    groups.get(k).rows.push(item);
  }
  const orderedGroups = [...groups.values()].sort((a, b) => CHAPTER_ORDER.indexOf(a.chapter) - CHAPTER_ORDER.indexOf(b.chapter));
  const mistakeSummary = item => [item.count ? `答错 ${item.count} 次` : '', item.manual ? '主动加入' : ''].filter(Boolean).join(' · ') || '待复习';
  return `<div class="page-screen"><header class="page-header"><button class="back-button" data-action="home"><span>‹</span>首页</button></header><div class="page-intro"><h1>错题本</h1><p>${rows.length} 道待复习</p></div>${rows.length ? `<button class="review-all" data-action="review-all">开始复习 <span>›</span></button><div class="mistake-groups">${orderedGroups.map(group => `<section class="mistake-group"><h2>${esc(group.chapter)}</h2>${group.rows.map(({q,item}) => `<button class="mistake-row" data-review-id="${esc(q.id)}"><span class="mistake-row-main"><strong>${esc(examSource(q))}　${esc(q.topic)}</strong><small>${q.isSupplemental ? '专题补充' : (EXAM_SHORT[q.exam] || q.exam)} · ${TYPE_LABEL[q.questionType]} · ${mistakeSummary(item)}</small></span><span class="course-card-arrow">›</span></button>`).join('')}</section>`).join('')}</div>` : `<div class="empty-card"><span class="empty-check">✓</span><strong>暂时没有待复习的错题</strong><small>答错的题和主动收录的解答题会显示在这里</small><button class="secondary" data-action="directory">去练习</button></div>`}</div>`;
}

function settingsView() {
  const supplemental = bank.filter(q => q.isSupplemental).length;
  const past = bank.length - supplemental;
  return `<div class="page-screen"><header class="page-header"><button class="back-button" data-action="home"><span>‹</span>首页</button></header><div class="page-intro"><h1>设置</h1></div><section class="settings-card"><div class="settings-row"><span><strong>DeepSeek 解析</strong><small>逐步讲解题目，使用你自己的 API Key</small></span><button class="secondary" data-action="configure">配置</button></div><p class="settings-note">历年真题保留原卷图，专题练习以文字呈现。无需配置 API，也可以离线训练、查看答案和记录错题。</p></section><section class="settings-card"><div class="settings-row"><span><strong>题库</strong><small>完整线代题库 · 按教材顺序编排</small></span><span class="settings-count">${bank.length} 题</span></div><div class="settings-row"><span><strong>历年真题</strong><small>来源与授权说明见项目 README</small></span><span class="settings-count">${past} 题</span></div><div class="settings-row"><span><strong>专题练习</strong><small>补充练习，不作为历年真题</small></span><span class="settings-count">${supplemental} 题</span></div></section><section class="settings-card backup-card"><div class="settings-row"><span><strong>学习记录备份</strong><small>包含答题进度、错题、草稿和解析缓存，不含 API Key</small></span></div><div class="backup-actions"><button class="secondary" data-action="export-backup">导出备份</button><button class="secondary" data-action="import-backup">导入备份</button></div>${confirmImport ? `<div class="backup-confirm"><p>导入后会替换本机现有学习记录。</p><div class="backup-actions"><button class="primary" data-action="confirm-import-backup">选择备份文件</button><button class="secondary" data-action="cancel-import-backup">取消</button></div></div>` : ''}</section><button class="text-button settings-link" data-action="home">返回首页</button></div>`;
}

function render() {
  if (page === 'home') app.innerHTML = homeView();
  else if (page === 'directory') app.innerHTML = directoryView();
  else if (page === 'topics') app.innerHTML = topicsView();
  else if (page === 'topicQuestions') app.innerHTML = topicQuestionsView();
  else if (page === 'training') app.innerHTML = questionView();
  else if (page === 'mistakes') app.innerHTML = mistakesView();
  else if (page === 'settings') app.innerHTML = settingsView();
}

function explanationPrompt(q) {
  const attempt = state.attempts[q.id];
  const answer = q.answer ? `已知参考答案：${q.answer}。` : q.answerText ? `题库已有参考解析：${q.answerText}` : q.answerImage ? '第二张附图包含该题参考答案或原卷解析，请准确读取后据此讲解。' : '题库未提供机器可读的标准答案，请先独立求解并明确说明你的判断依据。';
  const userAnswer = attempt?.answer ? `我作答为：${attempt.answer}。` : '';
  if (q.questionText) {
    const options = q.options ? `\n选项：${Object.entries(q.options).map(([key,value]) => `${key}. ${value}`).join('；')}` : '';
    return `你是一位严谨的中国考研数学教师。请针对下面的原创高频考点练习独立推导，核对给出的参考答案；不要把它称为历年真题。\n考试范围：${q.exam}；考点：${q.topic}；题型：${TYPE_LABEL[q.questionType]}。\n题目：${q.questionText}${options}\n${answer}${userAnswer}\n请用中文说明考点和关键条件、分步推导或计算；若为选择题，请逐项判断选项，并指出常见误区。`;
  }
  return `你是一位严谨的中国考研数学教师。请先准确识别这张原题图片中的题干、公式、选项与设问，不要猜测看不清的符号。\n考试：${q.exam}；年份：${q.examYear}；题号：${q.questionNo}；题型：${TYPE_LABEL[q.questionType]}；考点：${q.topic}。\n${answer}${userAnswer}\n请用中文给出：1. 考点和关键条件；2. 分步推导或计算；3. 若为选择题，逐项说明选项；4. 核对参考答案并指出常见误区。若图片有无法确认之处，先指出具体位置，不要编造。`;
}

function renderExplanation() {
  const q = byId.get(explanationId);
  if (!q) return;
  const result = aiResults.get(q.id);
  const loading = aiPending.has(q.id);
  const answerLabel = q.questionType === 'single' && q.options ? `${q.answer} · ${q.options[q.answer] || ''}` : q.answer;
  document.getElementById('explanation-content').innerHTML = `<div class="sheet-grip"></div><div class="sheet-head"><div><small>${esc(examSource(q))}</small><h2>题目解析</h2></div><button class="image-close" data-action="close-explanation" aria-label="关闭">×</button></div><div class="sheet-topic">${esc(q.subject)} · ${esc(q.topic)} <span>难度 ${q.difficulty}/5</span></div>${q.answer?`<div class="reference-answer">参考答案 <strong>${esc(answerLabel)}</strong></div>`:''}${result ? `<div class="ai-result ${result.error?'ai-error':''}">${esc(result.text)}</div>` : `<p class="sheet-note">${q.questionText?'DeepSeek 会根据题干和选项生成逐步解析。':'DeepSeek 会读取原题图中的公式和选项，生成逐步解析。'}模型调用可能产生 API 费用。</p>`}<button class="primary generate-button" data-action="generate" ${loading?'disabled':''}>${loading?'正在解析…':result&&!result.error?'重新解析':result?.error?'重试':'DeepSeek 解析'}</button><div class="sheet-footer"><button class="text-button" data-action="configure">设置 API Key</button><button class="text-button" data-action="share">${q.isSupplemental?'复制整题':'分享原题图'}</button></div>`;
  if (!dialog.open) dialog.showModal();
}

async function imageDataUrl(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error('image');
  const blob = await response.blob();
  return await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

async function explanationImage(q) {
  if (!q.answerImage) return imageDataUrl(q.image);
  const sources = await Promise.all([q.image, q.answerImage].map(path => new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = reject;
    image.src = path;
  })));
  const maxWidth = Math.min(1400, ...sources.map(image => image.naturalWidth));
  const scale = Math.min(1, maxWidth / Math.max(...sources.map(image => image.naturalWidth)), 6500 / sources.reduce((sum, image) => sum + image.naturalHeight * maxWidth / image.naturalWidth, 0));
  const width = Math.round(Math.max(...sources.map(image => image.naturalWidth)) * scale);
  const heights = sources.map(image => Math.round(image.naturalHeight * scale));
  const gap = Math.max(12, Math.round(width * 0.015));
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = heights.reduce((sum, height) => sum + height, 0) + gap;
  const context = canvas.getContext('2d');
  context.fillStyle = '#fff';
  context.fillRect(0, 0, canvas.width, canvas.height);
  let y = 0;
  for (const [index, image] of sources.entries()) {
    context.drawImage(image, 0, y, Math.round(image.naturalWidth * scale), heights[index]);
    y += heights[index] + gap;
  }
  return canvas.toDataURL('image/jpeg', 0.9);
}

async function generateExplanation() {
  const q = byId.get(explanationId);
  if (!q) return;
  if (q.questionText && window.AndroidApp?.requestExplanation) {
    const requestId = `${q.id}-${Date.now()}`;
    aiPending.add(q.id);
    aiRequests.set(requestId, q.id);
    renderExplanation();
    AndroidApp.requestExplanation(requestId, explanationPrompt(q));
    return;
  }
  if (!q.image) { toast('原题图暂不可用'); return; }
  if (!window.AndroidApp?.requestImageExplanation) { toast('请在安卓 App 内使用 DeepSeek 解析'); return; }
  const requestId = `${q.id}-${Date.now()}`;
  aiPending.add(q.id);
  aiRequests.set(requestId, q.id);
  renderExplanation();
  try {
    const dataUrl = await explanationImage(q);
    AndroidApp.requestImageExplanation(requestId, explanationPrompt(q), dataUrl);
  } catch {
    aiPending.delete(q.id);
    aiRequests.delete(requestId);
    aiResults.set(q.id, { text: '原题图读取失败，请重新进入题目后重试。', error: true });
    renderExplanation();
  }
}

window.onNativeExplanation = result => {
  const id = aiRequests.get(result.id);
  if (!id) return;
  aiRequests.delete(result.id);
  aiPending.delete(id);
  aiResults.set(id, { text: result.error || result.text, error: Boolean(result.error) });
  if (!result.error) save();
  if (dialog.open && explanationId === id) renderExplanation();
};
window.onApiConfigured = () => { toast('API 设置已保存'); if (dialog.open) renderExplanation(); if (page === 'settings') render(); };

function showExplanation() {
  const q = current();
  if (!q) return;
  explanationId = q.id;
  renderExplanation();
}

async function shareQuestion() {
  const q = current();
  if (!q) return;
  if (q.isSupplemental && q.questionText) {
    const options = q.options ? `\n${Object.entries(q.options).map(([key,value]) => `${key}. ${value}`).join('\n')}` : '';
    const text = `【${q.exam} · 原创高频考点补充题（非真题）】\n${q.subject} · ${q.chapter} · ${q.topic}\n${TYPE_LABEL[q.questionType]} · 难度 ${q.difficulty}/5\n\n${q.questionText}${options}`;
    try {
      if (window.AndroidApp?.copyText) { if (!AndroidApp.copyText(text)) throw new Error('clipboard'); }
      else await navigator.clipboard.writeText(text);
      toast('整道题目已复制');
    } catch { toast('复制失败'); }
    return;
  }
  if (!q.image) { toast('原题图暂不可用'); return; }
  const text = `${examSource(q)}（历年真题）\n${q.subject} · ${q.chapter} · ${q.topic}\n${TYPE_LABEL[q.questionType]} · 难度 ${q.difficulty}/5\n原题图：${q.sourceImageUrl || q.sourceUrl}\n题库来源：${q.sourceUrl}`;
  if (window.AndroidApp?.shareQuestionImage) {
    try {
      const dataUrl = await imageDataUrl(q.image);
      AndroidApp.shareQuestionImage(q.id, text, dataUrl);
      return;
    } catch { toast('分享题目图失败，请重试'); return; }
  }
  if (navigator.share) {
    try {
      const blob = await (await fetch(q.image)).blob();
      const file = new File([blob], `${q.exam}-${q.examYear}-${q.questionNo}.webp`, { type: 'image/webp' });
      await navigator.share({ title: `${q.exam} ${examSource(q)}`, text, files: [file] });
      return;
    } catch { /* use a text fallback */ }
  }
  try { await navigator.clipboard.writeText(text); toast('题目信息已复制；原题图可长按保存'); }
  catch { toast('请使用安卓分享题目图'); }
}

async function copyQuestionInfo() {
  const q = current();
  if (!q) return;
  if (q.isSupplemental) { shareQuestion(); return; }
  const text = `${examSource(q)}（历年真题）\n${q.subject} · ${q.chapter} · ${q.topic}\n${TYPE_LABEL[q.questionType]} · 难度 ${q.difficulty}/5\n原题图：${q.sourceImageUrl || q.sourceUrl}\n题库来源：${q.sourceUrl}`;
  try {
    if (window.AndroidApp?.copyText) AndroidApp.copyText(text);
    else await navigator.clipboard.writeText(text);
    toast('考点和题源已复制；完整原题请分享题目图');
  } catch { toast('复制失败'); }
}

function openZoom(src, alt) {
  const dialogImage = document.getElementById('image-view');
  const image = document.getElementById('zoom-image');
  imageZoomScale = 1;
  image.src = src;
  image.alt = alt;
  image.onload = applyImageZoom;
  dialogImage.showModal();
  if (image.complete) applyImageZoom();
}

function applyImageZoom() {
  const image = document.getElementById('zoom-image');
  if (!image.naturalWidth) return;
  const fitWidth = Math.min(window.innerWidth - 16, image.naturalWidth);
  image.style.width = `${Math.round(fitWidth * imageZoomScale)}px`;
}

function setImageZoom(scale) {
  imageZoomScale = Math.max(1, Math.min(4, scale));
  applyImageZoom();
}

function backupPayload() {
  return JSON.stringify({
    format: 'yanxi-linear-backup',
    version: 1,
    exportedAt: new Date().toISOString(),
    questionIds: [...byId.keys()],
    state
  });
}

function exportBackup() {
  const json = backupPayload();
  if (window.AndroidApp?.exportBackup) {
    AndroidApp.exportBackup(json);
    return;
  }
  const url = URL.createObjectURL(new Blob([json], { type: 'application/json' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = '研习线代-学习记录.json';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  toast('学习记录备份已导出');
}

function restoreBackup(json) {
  try {
    const payload = JSON.parse(json);
    if (payload?.format !== 'yanxi-linear-backup' || payload.version !== 1 || !payload.state || typeof payload.state !== 'object') {
      throw new Error('format');
    }
    const source = payload.state;
    const validIds = new Set(byId.keys());
    const entriesForQuestions = (value, validValue = () => true) => Object.fromEntries(
      Object.entries(value && typeof value === 'object' && !Array.isArray(value) ? value : {})
        .filter(([id, item]) => validIds.has(id) && validValue(item))
    );
    const validTopicKeys = new Set(topicsFor().map(topic => topic.key));
    const cursors = Object.fromEntries(Object.entries(source.cursorByTopic || {})
      .filter(([key, value]) => typeof key === 'string' && Number.isInteger(value) && value >= 0));
    state = {
      ...DEFAULT_STATE,
      subject: '线性代数',
      chapter: CHAPTER_ORDER.includes(source.chapter) ? source.chapter : '',
      topicKey: validTopicKeys.has(source.topicKey) ? source.topicKey : '',
      cursorByTopic: cursors,
      attempts: entriesForQuestions(source.attempts, item => item && typeof item === 'object'),
      mistakes: entriesForQuestions(source.mistakes, item => item && typeof item === 'object'),
      drafts: entriesForQuestions(source.drafts, item => typeof item === 'string'),
      revealed: entriesForQuestions(source.revealed, item => typeof item === 'boolean'),
      hints: entriesForQuestions(source.hints, item => typeof item === 'boolean'),
      explanationCache: entriesForQuestions(source.explanationCache, item => item && typeof item === 'object')
    };
    aiResults.clear();
    for (const [id, item] of Object.entries(state.explanationCache)) aiResults.set(id, item);
    save();
    confirmImport = false;
    go('home');
    toast('学习记录已导入');
  } catch {
    toast('备份文件无效或版本不兼容');
  }
}

window.onBackupImported = restoreBackup;

function chooseBackupFile() {
  if (window.AndroidApp?.importBackup) {
    AndroidApp.importBackup();
    return;
  }
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.json,application/json';
  input.addEventListener('change', async () => {
    const file = input.files?.[0];
    if (!file) return;
    try { restoreBackup(await file.text()); }
    catch { toast('备份文件无法读取'); }
  }, { once: true });
  input.click();
}

function handleClick(event) {
  const el = event.target.closest('[data-action],[data-choice],[data-type-filter],[data-status-filter],[data-open-chapter],[data-open-topic],[data-open-question],[data-review-id]');
  if (!el) return;
  if (el.dataset.choice) { const q = current(); if (q) choice(q, el.dataset.choice); return; }
  if (el.dataset.typeFilter) { typeFilter = el.dataset.typeFilter; render(); return; }
  if (el.dataset.statusFilter) { statusFilter = el.dataset.statusFilter; render(); return; }
  if (el.dataset.openChapter) { openChapter(el.dataset.openChapter); return; }
  if (el.dataset.openTopic) { openTopic(el.dataset.openTopic); return; }
  if (el.dataset.openQuestion) { openQuestion(el.dataset.openQuestion, Number(el.dataset.openIndex)); return; }
  if (el.dataset.reviewId) { startMistakes([el.dataset.reviewId]); return; }
  switch (el.dataset.action) {
    case 'home': go('home'); break;
    case 'directory': go('directory'); break;
    case 'topics': go('topics'); break;
    case 'topicQuestions': go('topicQuestions'); break;
    case 'mistakes': go('mistakes'); break;
    case 'settings': go('settings'); break;
    case 'continue': continueTraining(); break;
    case 'previous': move(-1); break;
    case 'next': move(1); break;
    case 'reveal': revealAnswer(); break;
    case 'toggle-answer': { const q=current(); if(q){state.revealed[q.id]=!state.revealed[q.id];save();render();} break; }
    case 'hint': { const q=current(); if(q){state.hints[q.id]=!state.hints[q.id];save();render();} break; }
    case 'self-correct': markSelf(true); break;
    case 'self-wrong': markSelf(false); break;
    case 'toggle-manual-mistake': toggleManualMistake(); break;
    case 'mastered': markMastered(); break;
    case 'explain': showExplanation(); break;
    case 'generate': generateExplanation(); break;
    case 'configure': window.AndroidApp?.configureApi(); break;
    case 'export-backup': exportBackup(); break;
    case 'import-backup': confirmImport = true; render(); break;
    case 'confirm-import-backup': chooseBackupFile(); break;
    case 'cancel-import-backup': confirmImport = false; render(); break;
    case 'share': shareQuestion(); break;
    case 'copy': copyQuestionInfo(); break;
    case 'review-all': startMistakes(); break;
    case 'zoom-question': { const q=current(); if(q?.image) openZoom(q.image, examSource(q)); break; }
    case 'zoom-answer': { const q=current(); if(q?.answerImage) openZoom(q.answerImage, '参考答案'); break; }
    case 'image-zoom-in': setImageZoom(imageZoomScale * 1.4); break;
    case 'image-zoom-out': setImageZoom(imageZoomScale / 1.4); break;
    case 'image-zoom-reset': setImageZoom(1); break;
    case 'close-explanation': dialog.close(); break;
    case 'close-image': document.getElementById('image-view').close(); break;
  }
}

document.addEventListener('click', handleClick);
document.addEventListener('input', event => {
  if (event.target.id !== 'fill-answer') return;
  const q = current();
  if (!q) return;
  state.drafts[q.id] = event.target.value;
  save();
});

dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
document.getElementById('image-view').addEventListener('click', event => { if (event.target.id === 'image-view') event.currentTarget.close(); });

function handleAndroidBack() {
  const imageDialog = document.getElementById('image-view');
  if (imageDialog.open) { imageDialog.close(); return true; }
  if (dialog.open) { dialog.close(); return true; }
  if (review) { go('mistakes'); return true; }
  if (page === 'settings' && confirmImport) { confirmImport = false; render(); return true; }
  if (page === 'training') { go('topicQuestions'); return true; }
  if (page === 'topicQuestions') { go('topics'); return true; }
  if (page === 'topics') { go('directory'); return true; }
  if (page === 'directory') { go('home'); return true; }
  if (page !== 'home') { go('home'); return true; }
  return false;
}

window.handleAndroidBack = handleAndroidBack;
render();
