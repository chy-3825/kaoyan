/* Presentation layer shared by the browser and Android politics app. */
'use strict';
const PoliticsDesign=(()=>{
  const paths={book:'M12 5v15M3 4c4-1 6 0 9 1 3-1 5-2 9-1v15c-4-1-6 0-9 1-3-1-5-2-9-1Z',copy:'M9 8h11v13H9zM5 16H3V3h11v2',list:'M8 6h13M8 12h13M8 18h13M3 6h.1M3 12h.1M3 18h.1',back:'m14 5-7 7 7 7',next:'m9 5 7 7-7 7',check:'m5 12 4 4L19 6',close:'m6 6 12 12M18 6 6 18',mistake:'M5 3h14v18H5zM9 7h6M9 11h6M9 15h3',settings:'M9 3h6l1 3 3 1 2 5-2 5-3 1-1 3H9l-1-3-3-1-2-5 2-5 3-1Z',play:'m8 4 12 8-12 8Z',ai:'m12 3 2.4 6.6L21 12l-6.6 2.4L12 21l-2.4-6.6L3 12l6.6-2.4Z',backup:'M7 3v14m-4-4 4 4 4-4M17 21V7m-4 4 4-4 4 4',edit:'m4 15 12-12 5 5-12 12H4zM13 6l5 5'};
  function icon(name){return `<svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[name]||paths.list}"/>${name==='settings'?'<circle cx="12" cy="12" r="3"/>':''}</svg>`;}
  function dock(index,total){return `<div class="study-dock"><div class="dock-tools"><button class="dock-tool" data-action="explain">${icon('book')}查看解析</button><button class="dock-tool" data-action="copy">${icon('copy')}复制题目</button></div><nav class="dock-navigation"><button class="secondary" data-action="previous" ${index===0?'disabled':''}>${icon('back')}上一题</button><span>${index+1} / ${total}</span><button class="primary" data-action="next" ${!review&&index===total-1?'disabled':''}>${review&&index===total-1?'完成复习':'下一题'}${icon('next')}</button></nav></div>`;}
  function polish(){
    document.body.classList.toggle('is-training',!!review||page==='training');
    document.querySelectorAll('.back-button').forEach(b=>{const s=b.querySelector('span');if(s)s.outerHTML=icon('back');});
    document.querySelectorAll('.icon-button[data-action="settings"]').forEach(b=>b.innerHTML=icon('settings'));
    document.querySelectorAll('.directory-shortcut').forEach(b=>b.innerHTML=icon('list'));
    document.querySelectorAll('.home-action').forEach(b=>{const s=b.querySelector('.action-symbol');if(s)s.innerHTML=icon(b.dataset.action==='categories'?'book':'mistake');});
    document.querySelectorAll('.action-arrow,.continue-chevron,.course-card-arrow').forEach(e=>e.innerHTML=icon('next'));
    document.querySelectorAll('.continue-icon').forEach(e=>e.innerHTML=icon('play'));
    document.querySelectorAll('.option-state').forEach(e=>{const t=e.textContent.trim();e.innerHTML=t?icon(t==='×'?'close':'check'):'';});
    for(const [selector,name] of [['.api-icon','ai'],['.backup-icon','backup'],['.feedback-icon','edit']])document.querySelectorAll(selector).forEach(e=>e.innerHTML=icon(name));
  }
  return {icon,dock,polish};
})();
