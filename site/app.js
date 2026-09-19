/* 车牌库 · 前端逻辑
 * 零依赖。数据来自 data/index.js（window.__CODES__），
 * 取不到时回退到 fetch('./data/index.json')。
 */
(() => {
  'use strict';

  // ------------------------------------------------- 站点配置
  const CFG = window.__SITE_CONFIG__ || {};
  const REPO = (CFG.repo || 'https://github.com/derecat/codes-index').replace(/\/+$/, '');
  const GISCUS = CFG.giscus || {};
  // 四项缺一不可，缺了就当没配置 —— 免得把 iframe 塞进去变成一片空白
  const GISCUS_ON = Boolean(GISCUS.repo && GISCUS.repoId && GISCUS.category && GISCUS.categoryId);

  const state = { q: '', tag: '', sort: 'new' };
  let DATA = { entries: [], tags: [], count: 0, recommenderCount: 0, generatedAt: '' };

  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
  const fmtDate = (s) => (s ? String(s).slice(0, 10).replace(/-/g, '.') : '');

  /* ---------------------------------------------------- 数据加载 */
  async function loadData() {
    if (window.__CODES__) return window.__CODES__;
    const res = await fetch('./data/index.json', { cache: 'no-store' });
    if (!res.ok) throw new Error('index.json ' + res.status);
    return res.json();
  }

  /* -------------------------------------------------- 检索与排序 */
  function haystack(e) {
    return [
      e.code, e.title, e.studio, e.releaseDate,
      (e.actors || []).join(' '),
      (e.tags || []).join(' '),
      (e.recommendations || []).map((r) => r.reason).join(' '),
    ].join(' ').toLowerCase();
  }

  function filtered() {
    const terms = state.q.toLowerCase().split(/\s+/).filter(Boolean);
    let list = DATA.entries.filter((e) => {
      if (state.tag && !(e.tags || []).includes(state.tag)) return false;
      if (!terms.length) return true;
      const hay = e._hay;
      return terms.every((t) => hay.includes(t));
    });

    const sorters = {
      new: (a, b) => (b.updatedAt || '').localeCompare(a.updatedAt || ''),
      code: (a, b) => (a.code || '').localeCompare(b.code || ''),
      score: (a, b) => (b.score || 0) - (a.score || 0),
      hot: (a, b) => (b.recommendations || []).length - (a.recommendations || []).length,
    };
    list = list.slice().sort(sorters[state.sort] || sorters.new);
    return list;
  }

  function highlight(text, terms) {
    let out = esc(text);
    terms.forEach((t) => {
      if (t.length < 2) return;
      out = out.replace(new RegExp('(' + t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi'), '<mark>$1</mark>');
    });
    return out;
  }

  /* ------------------------------------------------------- 渲染卡片 */
  function cardHTML(e, terms) {
    const recs = e.recommendations || [];
    const top = recs[recs.length - 1] || {};
    const actorLine = (e.actors || []).length ? e.actors.join(' / ') : '';
    const metaBits = [actorLine, e.studio, e.releaseDate].filter(Boolean);

    return `
    <article class="card" data-code="${esc(e.code)}" tabindex="0">
      <div class="card-top">
        <span class="code">${highlight(e.code, terms)}</span>
        <span class="spacer"></span>
        ${e.score != null ? `<span class="score">${e.score}<span>/10</span></span>` : ''}
      </div>
      ${e.title
        ? `<h3>${highlight(e.title, terms)}</h3>`
        : `<h3 class="untitled">（未填标题）</h3>`}
      ${metaBits.length ? `<div class="meta">${metaBits.map((m) => highlight(m, terms)).join('<span class="sep">·</span>')}</div>` : ''}
      ${(e.tags || []).length
        ? `<div class="card-tags">${e.tags.map((t) => `<span class="tag">${esc(t)}</span>`).join('')}</div>`
        : ''}
      <p class="quote">${highlight(top.reason || '', terms)}</p>
      <div class="card-foot">
        <span class="who">@${esc(top.login || 'anonymous')}</span>
        <span class="spacer"></span>
        ${recs.length > 1 ? `<span class="multi">×${recs.length} 人推荐</span>` : ''}
      </div>
    </article>`;
  }

  function render() {
    const terms = state.q.toLowerCase().split(/\s+/).filter(Boolean);
    const list = filtered();
    const grid = $('#grid');
    $('#loading').hidden = true;

    grid.innerHTML = list.map((e) => cardHTML(e, terms)).join('');
    $('#empty').hidden = list.length > 0;

    // 有筛选条件时给出「清除」入口
    const bar = $('#activeBar');
    const activeBits = [];
    if (state.q) activeBits.push(`关键词「${esc(state.q)}」`);
    if (state.tag) activeBits.push(`标签「${esc(state.tag)}」`);
    bar.hidden = activeBits.length === 0;
    bar.innerHTML = `<span>筛选中：${activeBits.join(' + ')} · 命中 ${list.length} / ${DATA.count}</span>
      <button id="resetAll">清除筛选</button>`;
    if (activeBits.length) {
      $('#resetAll').onclick = () => { state.q = ''; state.tag = ''; $('#q').value = ''; syncURL(); render(); };
    }

    if (DATA.entries.length === 0) {
      $('#emptyText').textContent = '库里还一条记录都没有';
    } else if (list.length === 0) {
      $('#emptyText').textContent = '没有匹配的记录';
    }
  }

  /* ------------------------------------------------------- 标签栏 */
  function renderTags() {
    const box = $('#tagChips');
    box.innerHTML = (DATA.tags || []).slice(0, 24).map(([t, c]) => `
      <button class="chip${state.tag === t ? ' on' : ''}" data-tag="${esc(t)}">${esc(t)}<em>${c}</em></button>
    `).join('');
    box.querySelectorAll('.chip').forEach((btn) => {
      btn.onclick = () => {
        state.tag = state.tag === btn.dataset.tag ? '' : btn.dataset.tag;
        syncURL(); renderTags(); render();
      };
    });
  }

  function renderStats() {
    $('#countBadge').textContent = DATA.count + ' 条';
    $('#stats').innerHTML =
      `<b>${DATA.count}</b> 条记录 · <b>${DATA.recommenderCount || 0}</b> 位推荐人 · ` +
      `<b>${(DATA.tags || []).length}</b> 个标签` +
      (DATA.generatedAt ? ` · 索引更新于 ${fmtDate(DATA.generatedAt)}` : '');
    $('#generatedAt').textContent = DATA.generatedAt ? '索引 ' + fmtDate(DATA.generatedAt) : '';
  }

  /* ------------------------------------------------------- 评论区
   * 用 giscus 把 GitHub Discussions 当评论后端：
   * 免服务器、免数据库、有 GitHub 账号就能发言，还能防机器人。
   * 每个番号对应一个 Discussion，标题就是番号本身。
   */
  function commentsFallbackHTML(code) {
    const q = encodeURIComponent(code);
    return `
      <div class="comments-fallback">
        <div class="cf-title">💬 评论区还没启用</div>
        <div>
          维护者去 <code>site/config.js</code> 填上 giscus 的
          <code>repoId</code> 和 <code>categoryId</code> 就能开启，
          全程免费，不需要任何服务器。<br>
          想现在就聊？直接去
          <a href="${REPO}/discussions" target="_blank" rel="noopener">Discussions</a>
          或者
          <a href="${REPO}/issues/new?title=${q}&labels=discussion" target="_blank" rel="noopener">开一个讨论帖</a>。
        </div>
      </div>`;
  }

  function mountComments(code) {
    const box = document.getElementById('comments');
    if (!box) return;
    box.innerHTML = '';

    if (!GISCUS_ON) {
      box.innerHTML = commentsFallbackHTML(code);
      return;
    }

    box.innerHTML = '<div class="comments-loading">正在连接评论…</div>';

    const s = document.createElement('script');
    s.src = 'https://giscus.app/client.js';
    s.async = true;
    s.crossOrigin = 'anonymous';
    s.setAttribute('data-repo', GISCUS.repo);
    s.setAttribute('data-repo-id', GISCUS.repoId);
    s.setAttribute('data-category', GISCUS.category);
    s.setAttribute('data-category-id', GISCUS.categoryId);
    s.setAttribute('data-mapping', 'specific');
    s.setAttribute('data-term', code);          // 讨论标题 = 番号
    s.setAttribute('data-strict', '1');         // 精确匹配，避免 ABC-1 撞上 ABC-10
    s.setAttribute('data-reactions-enabled', '1');
    s.setAttribute('data-emit-metadata', '0');
    s.setAttribute('data-input-position', 'top'); // 输入框放上面，鼓励发言
    s.setAttribute('data-theme', 'light');
    s.setAttribute('data-lang', 'zh-CN');
    s.setAttribute('data-loading', 'lazy');
    box.appendChild(s);
  }

  function unmountComments() {
    // 清掉 iframe 和 giscus 注入的脚本，避免关掉弹窗后还在后台跑
    const box = document.getElementById('comments');
    if (box) box.innerHTML = '';
  }

  /* -------------------------------------------------------- 详情弹窗 */
  function openDialog(code) {
    const e = DATA.entries.find((x) => x.code === code);
    if (!e) return;
    const recs = e.recommendations || [];
    const rows = [
      ['番号', `<span style="font-family:var(--mono)">${esc(e.code)}</span>`],
      ['演员', (e.actors || []).join(' / ')],
      ['厂牌', e.studio],
      ['发行', e.releaseDate],
      ['标签', (e.tags || []).join(' / ')],
      ['评分', e.score != null ? `${e.score} / 10` : ''],
      ['来源', e.sourceUrl ? `<a href="${esc(e.sourceUrl)}" target="_blank" rel="noopener">${esc(e.sourceUrl)}</a>` : ''],
    ].filter(([, v]) => v);

    $('#dialog').innerHTML = `
      <div class="dialog-head">
        <h2>${esc(e.title || '（未填标题）')}</h2>
        <button class="closeBtn" id="closeBtn" aria-label="关闭">✕</button>
      </div>
      <div class="big-code" id="copyCode" title="点击复制">${esc(e.code)} ⧉</div>
      ${rows.map(([k, v]) => `<div class="kv"><b>${k}</b><span>${v}</span></div>`).join('')}
      <div class="recs">
        <h4>推荐理由 · ${recs.length} 条</h4>
        ${recs.slice().reverse().map((r) => `
          <div class="rec">
            <p>${esc(r.reason)}</p>
            <div class="by">@${esc(r.login)}${r.score != null ? ` · 给了 <em>${r.score}</em> 分` : ''} · ${fmtDate(r.at)}</div>
          </div>`).join('')}
      </div>
      <div class="comments">
        <h4>💬 评论区</h4>
        <div id="comments"></div>
      </div>`;

    $('#overlay').hidden = false;
    document.body.style.overflow = 'hidden';
    $('#closeBtn').onclick = closeDialog;
    $('#copyCode').onclick = async () => {
      const el = $('#copyCode');
      try {
        await navigator.clipboard.writeText(e.code);
        el.textContent = e.code + ' 已复制';
      } catch {
        el.textContent = e.code;
      }
      setTimeout(() => { el.textContent = e.code + ' ⧉'; }, 1400);
    };

    mountComments(e.code);
  }

  function closeDialog() {
    unmountComments();
    $('#overlay').hidden = true;
    document.body.style.overflow = '';
    history.replaceState(null, '', location.pathname + location.search + hashString());
  }

  /* -------------------------------------------------- URL 状态同步 */
  function hashString() {
    const p = new URLSearchParams();
    if (state.q) p.set('q', state.q);
    if (state.tag) p.set('tag', state.tag);
    if (state.sort !== 'new') p.set('sort', state.sort);
    const s = p.toString();
    return s ? '#' + s : '';
  }

  function syncURL() {
    try { history.replaceState(null, '', location.pathname + hashString()); } catch {}
  }

  function readURL() {
    const p = new URLSearchParams(location.hash.slice(1));
    state.q = p.get('q') || '';
    state.tag = p.get('tag') || '';
    state.sort = p.get('sort') || 'new';
    $('#q').value = state.q;
    $('#sortSel').value = state.sort;
  }

  /* ------------------------------------------------------------ 启动 */
  async function main() {
    try {
      DATA = await loadData();
    } catch (err) {
      $('#loading').textContent = '索引加载失败：' + err.message + '（先跑一次 python3 scripts/build_index.py）';
      return;
    }

    DATA.entries.forEach((e) => { e._hay = haystack(e); });
    readURL();
    renderStats();
    renderTags();
    render();

    // 搜索：防抖，避免每敲一个字就重排整个网格
    let timer;
    $('#q').addEventListener('input', (ev) => {
      clearTimeout(timer);
      const v = ev.target.value;
      $('#clearBtn').hidden = !v;
      timer = setTimeout(() => { state.q = v.trim(); syncURL(); render(); }, 140);
    });
    $('#clearBtn').onclick = () => {
      $('#q').value = ''; $('#clearBtn').hidden = true;
      state.q = ''; syncURL(); render(); $('#q').focus();
    };

    $('#sortSel').onchange = (ev) => { state.sort = ev.target.value; syncURL(); render(); };

    $('#randomBtn').onclick = () => {
      const pool = filtered().length ? filtered() : DATA.entries;
      if (!pool.length) return;
      openDialog(pool[Math.floor(Math.random() * pool.length)].code);
    };

    $('#grid').addEventListener('click', (ev) => {
      const card = ev.target.closest('.card');
      if (card) openDialog(card.dataset.code);
    });
    $('#grid').addEventListener('keydown', (ev) => {
      if (ev.key !== 'Enter' && ev.key !== ' ') return;
      const card = ev.target.closest('.card');
      if (card) { ev.preventDefault(); openDialog(card.dataset.code); }
    });

    $('#overlay').addEventListener('click', (ev) => { if (ev.target.id === 'overlay') closeDialog(); });
    document.addEventListener('keydown', (ev) => {
      if (ev.key === 'Escape') { closeDialog(); return; }
      if (ev.key === '/' && document.activeElement !== $('#q')) {
        ev.preventDefault(); $('#q').focus();
      }
    });

    $('#newIssue').href = REPO + '/issues/new/choose';
    $('#repoLink').href = REPO;
    const dl = $('#discussLink');
    if (dl) dl.href = REPO + '/discussions';
  }

  document.addEventListener('DOMContentLoaded', main);
})();
