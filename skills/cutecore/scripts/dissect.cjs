#!/usr/bin/env node
/*
 * dissect: reverse engineer a live web page into a rebuildable blueprint.
 *
 *   node dissect.cjs <url> [--out dir] [--wait 4000] [--no-mobile] [--interact]
 *
 * Writes into <out> (default ./.cutecore/dissect/<host>/):
 *   blueprint.md      human/Claude readable summary: layout tree, tokens, motion, libs, APIs
 *   blueprint.json    everything below in machine form
 *   desktop.png       full page at 1440 wide
 *   mobile.png        full page at 390 wide (unless --no-mobile)
 *   hover-*.png       hover states of the first interactive elements (with --interact)
 *   source/           page html, every stylesheet and script, for close study
 *
 * Needs Playwright with Chromium. If missing:
 *   npm i -D playwright && npx playwright install chromium
 *
 * The blueprint describes structure, styling, motion and behaviour so a layout can
 * be rebuilt faithfully. It deliberately does not download images, audio or fonts:
 * rebuilds use the target project's own art and content.
 */
'use strict';
const fs = require('fs');
const path = require('path');

let chromium;
try { ({ chromium } = require('playwright')); } catch (e) {
  try { ({ chromium } = require('@playwright/test')); } catch (e2) {
    console.error('dissect: Playwright not found. Install with:\n  npm i -D playwright && npx playwright install chromium');
    process.exit(2);
  }
}

const args = process.argv.slice(2);
const url = args.find(a => /^https?:\/\//.test(a));
if (!url) { console.error('usage: node dissect.cjs <url> [--out dir] [--wait ms] [--no-mobile] [--interact]'); process.exit(1); }
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const host = new URL(url).host.replace(/[^a-z0-9.-]/gi, '_');
const slugPath = new URL(url).pathname.replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '');
const out = path.resolve(opt('--out', path.join('.cutecore', 'dissect', host + (slugPath ? '__' + slugPath : ''))));
const wait = +opt('--wait', 4000);
const doMobile = !args.includes('--no-mobile');
const interact = args.includes('--interact');
fs.mkdirSync(path.join(out, 'source'), { recursive: true });

const LIBS = {
  three: 'window.THREE || document.querySelector("script[src*=three]")',
  gsap: 'window.gsap',
  lenis: 'window.Lenis || document.documentElement.classList.contains("lenis")',
  framerMotion: '!!document.querySelector("[style*=\\"--motion\\"],[data-framer-appear-id]")',
  react: '!!document.querySelector("[data-reactroot]") || !!window.__NEXT_DATA__ || !!document.getElementById("__next") || !!self.__next_f',
  nextjs: '!!window.__NEXT_DATA__ || !!self.__next_f',
  vue: '!!window.__VUE__',
  svelte: '!!document.querySelector("[class*=svelte-]")',
  astro: '!!document.querySelector("astro-island")',
  tailwind: '!!document.querySelector("[class*=\\"px-\\"],[class*=\\"flex \\"],[class*=\\"rounded-\\"]")',
  jquery: 'window.jQuery',
  pixi: 'window.PIXI',
  ogl: '!!document.querySelector("script[src*=ogl]")',
  howler: 'window.Howl',
  matter: 'window.Matter',
  p5: 'window.p5',
  oneko: '!!document.getElementById("oneko")',
  lottie: 'window.lottie || !!document.querySelector("lottie-player,dotlottie-player")',
  spline: '!!document.querySelector("spline-viewer,canvas[data-spline]")',
};

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  const requests = [];
  const sources = [];
  page.on('request', r => requests.push({ url: r.url(), type: r.resourceType(), method: r.method() }));
  page.on('response', async r => {
    const t = r.request().resourceType();
    if (t === 'stylesheet' || t === 'script' || t === 'document') {
      try {
        const body = await r.text();
        sources.push({ url: r.url(), type: t, bytes: body.length });
        const name = (t + '-' + sources.length + '-' + (r.url().split('/').pop().split('?')[0] || 'index')).slice(0, 90).replace(/[^a-z0-9._-]/gi, '_');
        fs.writeFileSync(path.join(out, 'source', name), body);
      } catch (e) { /* streamed or redirected */ }
    }
  });
  const ws = [];
  page.on('websocket', w => ws.push(w.url()));

  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(e => console.error('goto:', e.message));
  await page.waitForTimeout(wait);
  // scroll through to trigger lazy content and scroll-driven animation
  await page.evaluate(async () => {
    const h = document.documentElement.scrollHeight;
    for (let y = 0; y < h; y += 500) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); }
    window.scrollTo(0, 0);
  });
  await page.waitForTimeout(800);

  const data = await page.evaluate((LIBS) => {
    const round = n => Math.round(n);
    const count = (m, k) => { if (!k || k === 'none' || k === 'normal' || k === 'auto') return; m[k] = (m[k] || 0) + 1; };
    const top = (m, n = 14) => Object.entries(m).sort((a, b) => b[1] - a[1]).slice(0, n);
    const tokens = { color: {}, background: {}, border: {}, font: {}, size: {}, weight: {}, radius: {}, shadow: {}, backdrop: {}, filter: {}, transition: {}, animation: {}, cursor: {}, gradient: {}, blend: {} };
    const els = [...document.querySelectorAll('body *')].filter(e => !['SCRIPT', 'STYLE', 'NOSCRIPT', 'META', 'LINK', 'TEMPLATE'].includes(e.tagName));
    const layouts = [];
    for (const e of els) {
      const s = getComputedStyle(e);
      if (s.display === 'none' || s.visibility === 'hidden') continue;
      count(tokens.color, s.color);
      if (s.backgroundColor !== 'rgba(0, 0, 0, 0)') count(tokens.background, s.backgroundColor);
      if (s.backgroundImage.includes('gradient')) count(tokens.gradient, s.backgroundImage.slice(0, 220));
      if (s.borderTopWidth !== '0px') count(tokens.border, `${s.borderTopWidth} ${s.borderTopStyle} ${s.borderTopColor}`);
      count(tokens.font, s.fontFamily.split(',').slice(0, 2).join(','));
      count(tokens.size, s.fontSize); count(tokens.weight, s.fontWeight);
      if (s.borderRadius !== '0px') count(tokens.radius, s.borderRadius);
      count(tokens.shadow, s.boxShadow); count(tokens.backdrop, s.backdropFilter); count(tokens.filter, s.filter);
      if (s.transitionDuration !== '0s') count(tokens.transition, `${s.transitionProperty} ${s.transitionDuration} ${s.transitionTimingFunction}`.slice(0, 120));
      if (s.animationName !== 'none') count(tokens.animation, `${s.animationName} ${s.animationDuration} ${s.animationTimingFunction} ${s.animationIterationCount}`);
      count(tokens.cursor, s.cursor === 'auto' ? null : s.cursor.slice(0, 120));
      count(tokens.blend, s.mixBlendMode);
      if ((s.display.includes('grid') || s.display.includes('flex')) && e.children.length > 1) {
        const r = e.getBoundingClientRect();
        if (r.width > 200 && r.height > 60) layouts.push({
          sel: sel(e), display: s.display, cols: s.gridTemplateColumns !== 'none' ? s.gridTemplateColumns : undefined,
          rows: s.gridTemplateRows !== 'none' ? s.gridTemplateRows : undefined, areas: s.gridTemplateAreas !== 'none' ? s.gridTemplateAreas : undefined,
          dir: s.flexDirection, gap: s.gap, children: e.children.length, w: round(r.width), h: round(r.height), x: round(r.x), y: round(r.y + scrollY),
        });
      }
    }
    function sel(e) {
      let s = e.tagName.toLowerCase();
      if (e.id) s += '#' + e.id;
      const c = (typeof e.className === 'string' ? e.className : (e.className && e.className.baseVal) || '').trim().split(/\s+/).filter(Boolean).slice(0, 3);
      if (c.length) s += '.' + c.join('.');
      return s;
    }
    // Box tree: significant boxes only, so the structure reads like a wireframe
    function tree(e, depth) {
      if (depth > 9) return null;
      const r = e.getBoundingClientRect();
      const s = getComputedStyle(e);
      if (s.display === 'none' || r.width < 24 || r.height < 12) return null;
      const kids = [...e.children].map(c => tree(c, depth + 1)).filter(Boolean);
      const own = [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join(' ').trim();
      const node = { sel: sel(e), box: [round(r.x), round(r.y + scrollY), round(r.width), round(r.height)] };
      if (own) node.text = own.slice(0, 80);
      if (s.position === 'fixed' || s.position === 'absolute' || s.position === 'sticky') node.pos = s.position;
      if (s.zIndex !== 'auto') node.z = s.zIndex;
      if (e.tagName === 'IMG') node.img = (e.currentSrc || e.src).slice(0, 160);
      if (e.tagName === 'CANVAS') node.canvas = true;
      if (e.tagName === 'VIDEO') node.video = true;
      if (e.tagName === 'IFRAME') node.iframe = e.src.slice(0, 160);
      if (kids.length) node.kids = kids;
      // collapse single-child wrappers that add nothing
      if (!own && kids.length === 1 && !node.pos && !node.canvas && !node.img) return Object.assign(kids[0], { via: node.sel + ' > ' + (kids[0].via || '') });
      return node;
    }
    const keyframes = {}; const fontFaces = []; const cssVars = {}; const mediaQueries = new Set();
    for (const sh of document.styleSheets) {
      let rules; try { rules = sh.cssRules; } catch (e) { continue; }
      const walk = rs => { for (const r of rs) {
        if (r.type === 7) keyframes[r.name] = r.cssText.slice(0, 900);
        else if (r.type === 5) fontFaces.push(r.style.getPropertyValue('font-family') + ' ' + (r.style.getPropertyValue('src') || '').slice(0, 120));
        else if (r.type === 4) { mediaQueries.add(r.conditionText || r.media.mediaText); walk(r.cssRules); }
        else if (r.type === 1 && /^(:root|html|body)/.test(r.selectorText)) for (const p of r.style) if (p.startsWith('--')) cssVars[p] = r.style.getPropertyValue(p).trim();
        else if (r.cssRules) walk(r.cssRules);
      } };
      walk(rules);
    }
    const interactive = [...document.querySelectorAll('a,button,input,textarea,select,[role=button],[onclick],[contenteditable=true],label,form,details,dialog')]
      .slice(0, 160).map(e => ({
        sel: sel(e), tag: e.tagName.toLowerCase(), text: (e.innerText || e.value || e.placeholder || e.getAttribute('aria-label') || '').trim().slice(0, 60),
        href: e.getAttribute('href') || undefined, type: e.getAttribute('type') || undefined, name: e.getAttribute('name') || undefined,
      }));
    const libs = {}; for (const [k, expr] of Object.entries(LIBS)) { try { libs[k] = !!eval(expr); } catch (e) { libs[k] = false; } }
    const canvases = [...document.querySelectorAll('canvas')].map(c => {
      const r = c.getBoundingClientRect(); let ctx = 'unknown';
      try { ctx = c.getContext('webgl2') ? 'webgl2?' : c.getContext('webgl') ? 'webgl?' : '2d?'; } catch (e) {}
      return { sel: sel(c), w: round(r.width), h: round(r.height), pos: getComputedStyle(c).position, ctx };
    });
    const audio = [...document.querySelectorAll('audio,video')].map(m => ({ tag: m.tagName.toLowerCase(), src: (m.currentSrc || m.src || '').slice(0, 160), autoplay: m.autoplay, loop: m.loop }));
    const imgs = [...document.querySelectorAll('img')].map(i => ({ src: (i.currentSrc || i.src).slice(0, 200), alt: i.alt, w: i.naturalWidth, h: i.naturalHeight, pixelated: getComputedStyle(i).imageRendering }));
    const bodyText = document.body.innerText.replace(/\s+/g, ' ').trim();
    const deco = (bodyText.match(/[☀-➿⭐♡-♥˖-˚இාᴀ-ᶿ✩-❋⋆✧✿❀♪-♬。-ヿ̀-ͯ＀-￯\u{1F300}-\u{1FAFF}\u{10000}-\u{1FFFF}]/gu) || []);
    const decoCount = {}; deco.forEach(c => decoCount[c] = (decoCount[c] || 0) + 1);
    return {
      title: document.title, lang: document.documentElement.lang, meta: { themeColor: document.querySelector('meta[name=theme-color]')?.content, description: document.querySelector('meta[name=description]')?.content },
      docSize: [document.documentElement.scrollWidth, document.documentElement.scrollHeight],
      tokens: Object.fromEntries(Object.entries(tokens).map(([k, v]) => [k, top(v)])),
      cssVars, keyframes, fontFaces: [...new Set(fontFaces)].slice(0, 30), loadedFonts: [...document.fonts].filter(f => f.status === 'loaded').map(f => `${f.family} ${f.weight} ${f.style}`),
      mediaQueries: [...mediaQueries].slice(0, 40), layouts: layouts.slice(0, 60), tree: tree(document.body, 0), interactive, libs, canvases, audio,
      images: imgs.slice(0, 80), decorativeGlyphs: Object.entries(decoCount).sort((a, b) => b[1] - a[1]).slice(0, 40), textSample: bodyText.slice(0, 1500),
    };
  }, LIBS);

  // Event listeners on interactive and large elements via CDP
  try {
    const cdp = await ctx.newCDPSession(page);
    const { result } = await cdp.send('Runtime.evaluate', { expression: 'window', objectGroup: 'd' });
    const wl = await cdp.send('DOMDebugger.getEventListeners', { objectId: result.objectId });
    data.windowListeners = [...new Set(wl.listeners.map(l => l.type))];
    const { result: docRes } = await cdp.send('Runtime.evaluate', { expression: 'document', objectGroup: 'd' });
    const dl = await cdp.send('DOMDebugger.getEventListeners', { objectId: docRes.objectId });
    data.documentListeners = [...new Set(dl.listeners.map(l => l.type))];
  } catch (e) { data.listenerError = e.message; }

  await page.screenshot({ path: path.join(out, 'desktop.png'), fullPage: true });
  await page.screenshot({ path: path.join(out, 'desktop-fold.png') });

  if (interact) {
    const targets = await page.$$('a, button, [role=button]');
    let n = 0;
    for (const t of targets.slice(0, 12)) {
      try {
        const box = await t.boundingBox(); if (!box || box.width < 8 || box.y > 2400) continue;
        await t.hover({ timeout: 1500 }); await page.waitForTimeout(350);
        await page.screenshot({ path: path.join(out, `hover-${++n}.png`), clip: { x: Math.max(0, box.x - 40), y: Math.max(0, box.y - 40), width: Math.min(1440, box.width + 80), height: box.height + 80 } });
      } catch (e) {}
    }
  }

  if (doMobile) {
    const m = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, isMobile: true, hasTouch: true });
    const mp = await m.newPage();
    await mp.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(() => {});
    await mp.waitForTimeout(wait);
    await mp.screenshot({ path: path.join(out, 'mobile.png'), fullPage: true }).catch(() => {});
    await m.close();
  }
  await browser.close();

  const origin = new URL(url).origin;
  const apis = [...new Set(requests.filter(r => ['fetch', 'xhr', 'eventsource'].includes(r.type)).map(r => r.method + ' ' + r.url.split('?')[0]))];
  data.apis = apis.slice(0, 60); data.websockets = [...new Set(ws)];
  data.thirdParty = [...new Set(requests.map(r => { try { return new URL(r.url).origin; } catch (e) { return ''; } }).filter(o => o && o !== origin))];
  data.sources = sources; data.url = url; data.dissectedAt = new Date().toISOString();
  fs.writeFileSync(path.join(out, 'blueprint.json'), JSON.stringify(data, null, 2));
  fs.writeFileSync(path.join(out, 'blueprint.md'), toMd(data));
  console.log(out);
})().catch(e => { console.error(e); process.exit(1); });

function toMd(d) {
  const L = [];
  const list = (t, a, f = x => x) => { if (a && a.length) { L.push(`\n## ${t}`); a.forEach(x => L.push('- ' + f(x))); } };
  L.push(`# Blueprint: ${d.title || d.url}`, `${d.url}  (dissected ${d.dissectedAt})`, `document ${d.docSize.join('x')}, lang=${d.lang || '?'}, theme-color=${d.meta.themeColor || '-'}`);
  L.push('\nFiles: desktop.png, desktop-fold.png, mobile.png, source/ (html, css, js). Look at the screenshots before reading further.');
  L.push('\n## Libraries detected', Object.entries(d.libs).filter(([, v]) => v).map(([k]) => k).join(', ') || 'none detected (likely hand written)');
  list('Canvas / WebGL', d.canvases, c => `${c.sel} ${c.w}x${c.h} ${c.pos} ${c.ctx}`);
  list('Network APIs (live data the layout depends on)', d.apis);
  list('WebSockets', d.websockets);
  list('Third party origins', d.thirdParty);
  L.push('\n## Tokens (most used first)');
  for (const [k, v] of Object.entries(d.tokens)) if (v.length) L.push(`- **${k}**: ` + v.map(([a, n]) => `\`${a}\` x${n}`).join(', '));
  if (Object.keys(d.cssVars).length) { L.push('\n## CSS custom properties'); Object.entries(d.cssVars).slice(0, 80).forEach(([k, v]) => L.push(`- ${k}: ${v}`)); }
  list('Fonts loaded', d.loadedFonts); list('@font-face', d.fontFaces);
  if (Object.keys(d.keyframes).length) { L.push('\n## Keyframes'); Object.entries(d.keyframes).forEach(([k, v]) => L.push('```css\n' + v + '\n```')); }
  list('Layout containers (grid/flex)', d.layouts, l => `${l.sel} ${l.display}${l.cols ? ' cols=' + l.cols : ''}${l.areas ? ' areas=' + l.areas : ''}${l.dir && l.display.includes('flex') ? ' dir=' + l.dir : ''} gap=${l.gap} kids=${l.children} @${l.x},${l.y} ${l.w}x${l.h}`);
  list('Media queries', d.mediaQueries);
  L.push('\n## Box tree (wireframe)');
  const walk = (n, depth) => { if (!n || depth > 8) return; L.push(`${'  '.repeat(depth)}- ${n.sel} [${n.box.join(',')}]${n.pos ? ' ' + n.pos : ''}${n.z ? ' z' + n.z : ''}${n.canvas ? ' CANVAS' : ''}${n.img ? ' img' : ''}${n.text ? ' "' + n.text + '"' : ''}`); (n.kids || []).forEach(k => walk(k, depth + 1)); };
  walk(d.tree, 0);
  list('Interactive elements', d.interactive, i => `${i.tag} ${i.sel}${i.text ? ' "' + i.text + '"' : ''}${i.href ? ' -> ' + i.href : ''}${i.type ? ' type=' + i.type : ''}${i.name ? ' name=' + i.name : ''}`);
  list('Window listeners', d.windowListeners); list('Document listeners', d.documentListeners);
  list('Images (reference only, rebuild with your own art)', d.images, i => `${i.src} ${i.w}x${i.h}${i.pixelated !== 'auto' ? ' ' + i.pixelated : ''}${i.alt ? ' alt="' + i.alt + '"' : ''}`);
  list('Audio / video', d.audio, a => `${a.tag} ${a.src} autoplay=${a.autoplay} loop=${a.loop}`);
  list('Decorative glyphs', d.decorativeGlyphs, ([c, n]) => `${c} x${n}`);
  L.push('\n## Text sample', d.textSample);
  return L.join('\n') + '\n';
}
