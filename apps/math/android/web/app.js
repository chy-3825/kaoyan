'use strict';

const bank = window.QUESTIONS || [];
const byId = new Map(bank.map(q => [q.id, q]));
const KEY = 'yanxi-math-v1';
const EXAMS = ['数学一', '数学二', '数学三'];
const SUBJECT_ORDER = ['高等数学', '线性代数', '概率论与数理统计'];
const TYPE_LABEL = { single: '选择题', fill: '填空题', solve: '解答题' };
const SUBJECT_SHORT = { '高等数学': '高数', '线性代数': '线代', '概率论与数理统计': '概率统计' };
const DEFAULT_STATE = {
  exam: '', subject: '', topicKey: '', cursorByTopic: {}, attempts: {}, mistakes: {},
  drafts: {}, revealed: {}, hints: {}, explanationCache: {}
};

let state = { ...DEFAULT_STATE };
let page = 'home';
let review = null;
let typeFilter = 'all';
let statusFilter = 'all';
let chapterFilter = 'all';
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
for (const [id, item] of Object.entries(state.explanationCache || {})) aiResults.set(id, item);

const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
}[c]));
const examSource = q => q.isSupplemental ? '专题补充' : q.examYear && q.questionNo ? `${q.examYear} · ${q.questionNo}` : '';
const questionKey = q => `${q.subject}::${q.topicPath || `${q.chapter}::${q.topic}`}`;
const cursorKey = () => `${state.exam}::${state.subject}::${state.topicKey}`;

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

function byTopic(exam = state.exam, subject = state.subject, key = state.topicKey) {
  return bank.filter(q => q.exam === exam && q.subject === subject && questionKey(q) === key)
    .sort((a, b) => (a.examYear || 9999) - (b.examYear || 9999) || (a.questionNo || 9999) - (b.questionNo || 9999));
}

function topicsFor(exam, subject) {
  const found = new Map();
  for (const q of bank) {
    if (q.exam !== exam || q.subject !== subject) continue;
    const key = questionKey(q);
    if (!found.has(key)) found.set(key, { key, subject: q.subject, chapter: q.chapter, name: q.topic, rows: [] });
    found.get(key).rows.push(q);
  }
  return [...found.values()].sort((a, b) => a.chapter.localeCompare(b.chapter, 'zh-CN') || a.name.localeCompare(b.name, 'zh-CN'));
}

function progress(list) { return list.filter(q => state.attempts[q.id]).length; }
function pendingMistakes() {
  return Object.entries(state.mistakes).filter(([id, item]) => byId.has(id) && !item.mastered)
    .map(([id]) => id).sort((a, b) => (state.mistakes[b]?.count || 0) - (state.mistakes[a]?.count || 0));
}
function status(q) {
  if (state.attempts[q.id]) return state.attempts[q.id].correct === null ? 'checked' : state.attempts[q.id].correct ? 'correct' : 'wrong';
  return state.drafts[q.id] ? 'draft' : 'unseen';
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

function selectExam(exam) {
  state.exam = exam;
  state.subject = '';
  state.topicKey = '';
  chapterFilter = 'all';
  save();
  go('subjects');
}

function selectSubject(subject) {
  state.subject = subject;
  state.topicKey = '';
  chapterFilter = 'all';
  save();
  go('directory');
}

function openTopic(key) {
  state.topicKey = key;
  const list = byTopic(state.exam, state.subject, key);
  const first = list.findIndex(q => !state.attempts[q.id]);
  if (!(cursorKey() in state.cursorByTopic)) state.cursorByTopic[cursorKey()] = first < 0 ? 0 : first;
  save();
  review = null;
  page = 'training';
  render();
  window.scrollTo(0, 0);
}

function continueTraining() {
  if (state.exam && state.subject && state.topicKey && byTopic().length) {
    review = null;
    page = 'training';
    render();
    return;
  }
  if (state.exam) go('subjects');
  else go('exams');
}

function openQuestion(key, index) {
  const list = byTopic(state.exam, state.subject, key);
  if (!list.length) return;
  state.topicKey = key;
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
  const context = selected && state.topicKey ? `${state.exam} · ${SUBJECT_SHORT[state.subject] || state.subject}` : '';
  const pct = bank.length ? Math.round(done / bank.length * 100) : 0;
  return `<section class="home-screen">
    <header class="brand-bar"><div class="brand-lockup"><span class="brand-mark" aria-hidden="true"><svg viewBox="0 0 48 48"><path d="M8 37h33M13 8v30M14 31c5-2 6-13 11-14s6 13 11 4 5-9 8-10"/><circle cx="25" cy="17" r="2"/></svg></span><strong>研习数学</strong></div><button class="icon-button" data-action="settings" aria-label="设置"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-1.7 1.7-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-2.4v-.2a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L8 17l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.6-1H6.6v-2.4h.2a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L8 8.6l1.7-1.7.1.1a1.7 1.7 0 0 0 1.9.3 1.7 1.7 0 0 0 1-1.6v-.2h2.4v.2a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1 1.7 1.7-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2V14h-.2a1.7 1.7 0 0 0-1.5 1z"/></svg></button></header>
    <section class="math-hero" aria-hidden="true"><div class="hero-graph"><span class="axis-x"></span><span class="axis-y"></span><svg viewBox="0 0 210 130"><path d="M7 103C32 99 42 22 74 24s27 68 58 68 36-52 70-58"/></svg><i class="graph-dot dot-a"></i><i class="graph-dot dot-b"></i><i class="graph-dot dot-c"></i></div><span class="hero-grid"></span></section>
    <button class="continue-card" data-action="continue"><span class="continue-icon"><svg viewBox="0 0 24 24"><path d="M8 5.5v13l10-6.5z"/></svg></span><span class="continue-copy"><strong>${title}</strong>${context ? `<small>${esc(context)}</small>` : ''}</span><span class="continue-chevron">›</span></button>
    ${done ? `<section class="home-progress"><div class="progress-heading"><span>已练 ${done} / ${bank.length}</span><small>${pct}%</small></div><div class="progress-track"><span style="width:${pct}%"></span></div></section>` : ''}
    <div class="home-actions"><button class="home-action" data-action="exams"><span class="action-symbol course-symbol"><svg viewBox="0 0 24 24"><path d="M4 5.5h6.5A2.5 2.5 0 0 1 13 8v11H6.5A2.5 2.5 0 0 0 4 21zM20 5.5h-4A3 3 0 0 0 13 8v11h4.5A2.5 2.5 0 0 1 20 21z"/></svg></span><strong>考点目录</strong><span class="action-arrow">›</span></button><button class="home-action" data-action="mistakes"><span class="action-symbol mistake-symbol"><svg viewBox="0 0 24 24"><path d="M6 4.5h12a2 2 0 0 1 2 2v13l-4-2.5-4 2.5-4-2.5-4 2.5v-13a2 2 0 0 1 2-2Z"/><path d="M9 9h6M9 13h6"/></svg></span><strong>错题本</strong><span class="action-count">${mistakes}</span><span class="action-arrow">›</span></button></div>
  </section>`;
}

function examsView() {
  return `<div class="page-screen"><header class="page-header"><button class="back-button" data-action="home"><span>‹</span>首页</button></header><div class="page-intro"><h1>选择考试科目</h1></div><div class="exam-list">${EXAMS.map((exam, i) => {
    const rows = bank.filter(q => q.exam === exam);
    const done = progress(rows), pct = rows.length ? Math.round(done / rows.length * 100) : 0;
    return `<button class="exam-card" data-exam="${exam}"><span class="exam-number">0${i + 1}</span><span class="exam-card-main"><strong>${exam}</strong><small>${rows.length} 题 · ${done} 已练</small><i class="course-meter"><b style="width:${pct}%"></b></i></span><span class="course-card-arrow">›</span></button>`;
  }).join('')}</div></div>`;
}

function subjectsView() {
  const subjects = SUBJECT_ORDER.filter(subject => bank.some(q => q.exam === state.exam && q.subject === subject));
  const labels = { '高等数学': '函数、微积分与常微分方程', '线性代数': '矩阵、向量与线性方程组', '概率论与数理统计': '随机变量、统计量与估计' };
  return `<div class="page-screen"><header class="page-header"><button class="back-button" data-action="exams"><span>‹</span>考试科目</button></header><div class="page-intro"><h1>${esc(state.exam)} · 考点目录</h1></div><div class="subject-list">${subjects.map((subject, i) => {
    const rows = bank.filter(q => q.exam === state.exam && q.subject === subject), done = progress(rows);
    const topicCount = topicsFor(state.exam, subject).length;
    return `<button class="subject-card" data-subject="${esc(subject)}"><span class="subject-symbol subject-${i}">${['∫', 'A', 'P'][i]}</span><span class="subject-card-main"><strong>${esc(subject)}</strong><small>${esc(labels[subject])}</small><small>${topicCount} 个考点 · ${rows.length} 题 · 已练 ${done}</small></span><span class="course-card-arrow">›</span></button>`;
  }).join('')}</div></div>`;
}

function directoryView() {
  const allTopics = topicsFor(state.exam, state.subject);
  const chapters = [...new Set(allTopics.map(t => t.chapter))];
  const visible = allTopics.filter(topic => chapterFilter === 'all' || topic.chapter === chapterFilter).map(topic => {
    const rows = topic.rows;
    const typed = rows.filter(q => typeFilter === 'all' || q.questionType === typeFilter);
    const filtered = typed.filter(q => statusFilter === 'all' || (statusFilter === 'unseen' ? !state.attempts[q.id] : status(q) === 'wrong'));
    return { ...topic, rows: filtered, allRows: rows, allCount: rows.length, done: progress(rows) };
  }).filter(t => t.rows.length || (typeFilter === 'all' && statusFilter === 'all'));
  const counts = { all: bank.filter(q => q.exam === state.exam && q.subject === state.subject).length,
    unseen: bank.filter(q => q.exam === state.exam && q.subject === state.subject && !state.attempts[q.id]).length,
    wrong: bank.filter(q => q.exam === state.exam && q.subject === state.subject && status(q) === 'wrong').length };
  return `<div class="page-screen directory-screen"><header class="page-header"><button class="back-button" data-action="subjects"><span>‹</span>${esc(state.exam)}</button><button class="icon-button small-icon" data-action="home" aria-label="首页"><span>⌂</span></button></header><div class="page-intro directory-intro"><h1>${esc(state.subject)}</h1><p>${counts.all} 题 · ${allTopics.length} 个考点</p></div>
    <div class="directory-filters type-filters">${[['all','全部题型'],['single','选择'],['fill','填空'],['solve','解答']].map(([key,label]) => `<button class="directory-filter ${typeFilter===key?'active':''}" data-type-filter="${key}">${label}</button>`).join('')}</div>
    <div class="directory-filters status-filters">${[['all','全部'],['unseen','未答'],['wrong','错题']].map(([key,label]) => `<button class="directory-filter ${statusFilter===key?'active':''}" data-status-filter="${key}">${label}<span>${counts[key]}</span></button>`).join('')}</div>
    <div class="chapter-filters">${['all',...chapters].map(ch => `<button class="chapter-chip ${chapterFilter===ch?'active':''}" data-chapter-filter="${esc(ch)}">${ch==='all'?'全部考点':esc(ch)}</button>`).join('')}</div>
    <div class="topic-list">${visible.map(topic => `<section class="topic-card"><div class="topic-card-head"><div><small>${esc(topic.chapter)}</small><strong>${esc(topic.name)}</strong></div><span>${topic.done}/${topic.allCount}</span></div><div class="topic-question-grid">${topic.rows.map(q => {
      const s=status(q), active = state.topicKey===topic.key && (current()?.id===q.id);
      const source = examSource(q);
      return `<button class="topic-question ${s} ${q.isSupplemental?'supplemental':''} ${active?'current':''}" data-open-topic="${esc(topic.key)}" data-open-index="${topic.allRows.findIndex(row => row.id === q.id)}" aria-label="${esc(source || `${q.examYear} · ${q.questionNo}`)}，${TYPE_LABEL[q.questionType]}"><strong>${esc(source)}</strong><small>${q.isSupplemental?'原创练习 · ':''}${TYPE_LABEL[q.questionType]}　难度 ${q.difficulty}/5</small></button>`;
    }).join('') || '<p class="directory-empty">当前筛选下没有题目</p>'}</div></section>`).join('') || '<div class="empty-state">当前筛选下没有题目</div>'}</div>
  </div>`;
}

function rating(value) { return `<span class="difficulty">难度 <b>${value}</b> / 5</span>`; }

function questionView() {
  const q = current();
  if (!q) return `<div class="empty-state">这组题目暂不可用<button class="secondary" data-action="directory">返回目录</button></div>`;
  const list = activeList(), index = activeIndex(), attempt = attemptFor(q);
  const qstate = status(q), type = TYPE_LABEL[q.questionType] || '解答题';
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
  const answerContent = showAnswer ? `<section class="answer-panel"><div class="answer-heading">${q.answer ? `<span>参考答案　<strong>${esc(q.answer)}</strong></span>` : '<span>参考答案</span>'}</div>${q.answerText ? `<div class="answer-text">${esc(q.answerText)}</div>` : ''}${q.answerImage ? `<img class="answer-image" src="${esc(q.answerImage)}" loading="lazy" alt="第 ${q.questionNo} 题参考答案" data-action="zoom-answer">` : (!q.answer && !q.answerText ? '<p class="answer-unavailable">暂无离线参考答案，可用 DeepSeek 看题解析。</p>' : '')}<div class="self-assess"><button class="self-correct" data-action="self-correct">我已掌握</button><button class="self-wrong" data-action="self-wrong">还需重练</button></div></section>` : '';
  const answerLabel = q.questionType === 'single' && q.options ? `${q.answer} · ${q.options[q.answer] || ''}` : q.answer;
  const result = q.questionType === 'single' && attempt ? `<div class="result ${correct===true?'correct':correct===false?'wrong':'unknown'}"><strong>${correct===true?'回答正确':correct===false?'回答错误 · 已加入错题本':'答案待核对'}</strong><span>${q.answer?`参考答案：${esc(answerLabel)}`:'可查看解析或自我核对'}</span>${correct===null?'<div class="self-assess"><button class="self-correct" data-action="self-correct">我答对了</button><button class="self-wrong" data-action="self-wrong">还需重练</button></div>':''}${correct===true&&state.mistakes[q.id]&&!state.mistakes[q.id].mastered?'<button class="master-button" data-action="mastered">标记已掌握</button>':''}</div>` : '';
  const backAction = review ? 'mistakes' : 'directory';
  const backLabel = review ? '错题本' : '目录';
  const heading = review ? '错题复习' : `${SUBJECT_SHORT[q.subject] || q.subject} · ${q.topic}`;
  return `<div class="training-screen"><header class="training-head"><button class="back-button" data-action="${backAction}"><span>‹</span>${backLabel}</button><div class="training-course"><span>${esc(heading)}</span><button class="directory-shortcut" data-action="directory" aria-label="打开考点目录"><svg viewBox="0 0 24 24"><rect x="4" y="4" width="6" height="6" rx="1"/><rect x="14" y="4" width="6" height="6" rx="1"/><rect x="4" y="14" width="6" height="6" rx="1"/><rect x="14" y="14" width="6" height="6" rx="1"/></svg></button></div></header>
    <div class="question-progress"><span>${index + 1} / ${list.length}</span><div class="progress-track"><span style="width:${Math.round((index + 1) / Math.max(1,list.length) * 100)}%"></span></div></div>
    <article class="question-card"><div class="question-meta"><strong>${esc(source)}</strong><span>${type}</span>${rating(q.difficulty)}</div><div class="question-topic">${esc(q.topic)}</div><button class="hint-toggle" data-action="hint">${state.hints[q.id]?'收起考点提示':'查看考点提示'}　${state.hints[q.id]?'⌃':'⌄'}</button>${state.hints[q.id]?`<div class="study-hint">${esc(q.studyTip || `围绕“${q.topic}”识别题目条件，选用对应定义、定理或公式推导；注意检验适用条件并回代核对。`)}</div>`:''}
      ${q.image ? `<button class="question-image-button" data-action="zoom-question"><img class="question-image" src="${esc(q.image)}" alt="${esc(`${source} ${type}`)}" fetchpriority="high"></button>` : q.questionText ? `<div class="text-question">${esc(q.questionText)}</div>` : `<div class="missing-question">原题图片暂不可用 <a href="${esc(q.sourceUrl)}">查看来源</a></div>`}
      ${options}${fill}${responseAction}${result}${answerContent}
      <div class="question-tools"><button class="tool-button" data-action="explain"><span class="tool-icon">✳</span>DeepSeek 解析</button><button class="tool-button" data-action="share"><span class="tool-icon">${q.isSupplemental?'▣':'↗'}</span>${q.isSupplemental?'复制整题':'分享原题图'}</button></div>
    </article><nav class="bottom-nav"><button class="secondary" data-action="previous" ${index===0?'disabled':''}>上一题</button><button class="primary" data-action="next" ${index===list.length-1?'disabled':''}>下一题</button></nav></div>`;
}

function mistakesView() {
  const ids = pendingMistakes();
  const rows = ids.map(id => ({ q: byId.get(id), item: state.mistakes[id] })).filter(x => x.q)
    .sort((a,b) => b.item.at - a.item.at);
  const groups = new Map();
  for (const item of rows) {
    const k = `${item.q.exam}::${item.q.subject}::${item.q.chapter}`;
    if (!groups.has(k)) groups.set(k, { exam:item.q.exam, subject:item.q.subject, chapter:item.q.chapter, rows:[] });
    groups.get(k).rows.push(item);
  }
  return `<div class="page-screen"><header class="page-header"><button class="back-button" data-action="home"><span>‹</span>首页</button></header><div class="page-intro"><h1>错题本</h1><p>${rows.length} 道待复习</p></div>${rows.length ? `<button class="review-all" data-action="review-all">开始复习 <span>›</span></button><div class="mistake-groups">${[...groups.values()].map(group => `<section class="mistake-group"><h2>${esc(group.exam)} · ${esc(group.subject)}<small>${esc(group.chapter)}</small></h2>${group.rows.map(({q,item}) => `<button class="mistake-row" data-review-id="${esc(q.id)}"><span class="mistake-row-main"><strong>${esc(examSource(q))}　${esc(q.topic)}</strong><small>${TYPE_LABEL[q.questionType]} · 错 ${item.count} 次</small></span><span class="course-card-arrow">›</span></button>`).join('')}</section>`).join('')}</div>` : `<div class="empty-card"><span class="empty-check">✓</span><strong>暂时没有待复习的错题</strong><small>练习中标记的题目会收在这里</small><button class="secondary" data-action="exams">去练习</button></div>`}</div>`;
}

function settingsView() {
  const supplemental = bank.filter(q => q.isSupplemental).length;
  return `<div class="page-screen"><header class="page-header"><button class="back-button" data-action="home"><span>‹</span>首页</button></header><div class="page-intro"><h1>设置</h1></div><section class="settings-card"><div class="settings-row"><span><strong>DeepSeek 解析</strong><small>逐步讲解题目，使用你自己的 API Key</small></span><button class="secondary" data-action="configure">配置</button></div><p class="settings-note">真题保留原卷图，专题补充题以文字呈现。无需配置 API，也可以离线训练、查看答案和记录错题。</p></section><section class="settings-card"><div class="settings-row"><span><strong>题库</strong><small>2009–2026 真题 · 含原创高频专题补充</small></span><span class="settings-count">${bank.length} 题</span></div><div class="settings-row"><span><strong>其中专题补充</strong><small>原创练习，不作为历年真题</small></span><span class="settings-count">${supplemental} 题</span></div><div class="settings-row"><span><strong>难度星级</strong><small>公开反馈估算与人工标注，均为非官方参考</small></span><span class="settings-count">1–5</span></div></section><button class="text-button settings-link" data-action="home">返回首页</button></div>`;
}

function render() {
  if (page === 'home') app.innerHTML = homeView();
  else if (page === 'exams') app.innerHTML = examsView();
  else if (page === 'subjects') app.innerHTML = subjectsView();
  else if (page === 'directory') app.innerHTML = directoryView();
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
  document.getElementById('explanation-content').innerHTML = `<div class="sheet-grip"></div><div class="sheet-head"><div><small>${esc(q.exam)} · ${esc(examSource(q))}</small><h2>题目解析</h2></div><button class="image-close" data-action="close-explanation" aria-label="关闭">×</button></div><div class="sheet-topic">${esc(q.subject)} · ${esc(q.topic)} <span>难度 ${q.difficulty}/5</span></div>${q.answer?`<div class="reference-answer">参考答案 <strong>${esc(answerLabel)}</strong></div>`:''}${result ? `<div class="ai-result ${result.error?'ai-error':''}">${esc(result.text)}</div>` : `<p class="sheet-note">${q.questionText?'DeepSeek 会根据题干和选项生成逐步解析。':'DeepSeek 会读取原题图中的公式和选项，生成逐步解析。'}模型调用可能产生 API 费用。</p>`}<button class="primary generate-button" data-action="generate" ${loading?'disabled':''}>${loading?'正在解析…':result&&!result.error?'重新解析':result?.error?'重试':'DeepSeek 解析'}</button><div class="sheet-footer"><button class="text-button" data-action="configure">设置 API Key</button><button class="text-button" data-action="share">${q.isSupplemental?'复制整题':'分享原题图'}</button></div>`;
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
  const text = `${q.exam}真题 ${examSource(q)}\n${q.subject} · ${q.chapter} · ${q.topic}\n${TYPE_LABEL[q.questionType]} · 难度 ${q.difficulty}/5\n原题图：${q.sourceImageUrl || q.sourceUrl}\n题库来源：${q.sourceUrl}`;
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
  const text = `${q.exam}真题 ${examSource(q)}\n${q.subject} · ${q.chapter} · ${q.topic}\n${TYPE_LABEL[q.questionType]} · 难度 ${q.difficulty}/5\n原题图：${q.sourceImageUrl || q.sourceUrl}\n题库来源：${q.sourceUrl}`;
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

function handleClick(event) {
  const el = event.target.closest('[data-action],[data-choice],[data-exam],[data-subject],[data-type-filter],[data-status-filter],[data-chapter-filter],[data-open-topic],[data-review-id]');
  if (!el) return;
  if (el.dataset.choice) { const q = current(); if (q) choice(q, el.dataset.choice); return; }
  if (el.dataset.exam) { selectExam(el.dataset.exam); return; }
  if (el.dataset.subject) { selectSubject(el.dataset.subject); return; }
  if (el.dataset.typeFilter) { typeFilter = el.dataset.typeFilter; render(); return; }
  if (el.dataset.statusFilter) { statusFilter = el.dataset.statusFilter; render(); return; }
  if (el.dataset.chapterFilter !== undefined) { chapterFilter = el.dataset.chapterFilter; render(); return; }
  if (el.dataset.openTopic) { openQuestion(el.dataset.openTopic, Number(el.dataset.openIndex)); return; }
  if (el.dataset.reviewId) { startMistakes([el.dataset.reviewId]); return; }
  switch (el.dataset.action) {
    case 'home': go('home'); break;
    case 'exams': go('exams'); break;
    case 'subjects': go('subjects'); break;
    case 'directory': go('directory'); break;
    case 'mistakes': go('mistakes'); break;
    case 'settings': go('settings'); break;
    case 'continue': continueTraining(); break;
    case 'previous': move(-1); break;
    case 'next': move(1); break;
    case 'reveal': revealAnswer(); break;
    case 'hint': { const q=current(); if(q){state.hints[q.id]=!state.hints[q.id];save();render();} break; }
    case 'self-correct': markSelf(true); break;
    case 'self-wrong': markSelf(false); break;
    case 'mastered': markMastered(); break;
    case 'explain': showExplanation(); break;
    case 'generate': generateExplanation(); break;
    case 'configure': window.AndroidApp?.configureApi(); break;
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
  if (page === 'training') { go('directory'); return true; }
  if (page === 'directory') { go('subjects'); return true; }
  if (page === 'subjects') { go('exams'); return true; }
  if (page !== 'home') { go('home'); return true; }
  return false;
}

window.handleAndroidBack = handleAndroidBack;
render();
