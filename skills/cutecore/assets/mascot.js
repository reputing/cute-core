/* mascot.js: a zero dependency WebGL mascot that lives on the page.
 *
 *   import { createMascot } from "./mascot.js";
 *   const kuro = createMascot({ species: "cat", behavior: "wander", perch: ".cc-card",
 *     colors: { body: "#fff6fb", belly: "#ffe3ef", ear: "#ffc2d9", blush: "#ff9cc2", ink: "#3d2230", accessory: "#f47fa6" },
 *     accessory: "bow" });
 *   kuro.say("hi hi!"); kuro.celebrate(); kuro.setBehavior("follow"); kuro.destroy();
 *
 * species    cat | bunny | bear | ghost | blob | frog
 * behavior   follow  walks after the cursor and keeps a polite distance
 *            wander  strolls along the bottom of the viewport, or along `perch`
 *            perch   sits on top of the `perch` element and watches the cursor
 *            peek    hides behind the top edge of `perch`, rises when it is hovered
 * accessory  none | bow | flower | sprout | star
 * size       css px (120)
 * hearts     glyph used for the click burst ("♡")
 *
 * The body is ray marched signed distance fields with a toon light, a sticker
 * outline and a ground shadow, so it renders crisp at any size with no assets.
 * Eyes track the cursor, it blinks, bobs when walking, squashes when it lands.
 * Respects prefers-reduced-motion and html[data-motion=off] (stays put, still looks).
 */

const SPECIES = { cat: 0, bunny: 1, bear: 2, ghost: 3, blob: 4, frog: 5 };
const ACCESSORY = { none: 0, bow: 1, flower: 2, sprout: 3, star: 4 };

const FRAG = `precision highp float;
uniform vec2 uRes; uniform float uTime;
uniform vec2 uLook; uniform float uWalk; uniform float uYaw; uniform float uSquash; uniform float uBlink; uniform float uJump; uniform float uHappy;
uniform vec3 uBody; uniform vec3 uBelly; uniform vec3 uEar; uniform vec3 uBlush; uniform vec3 uInk; uniform vec3 uAcc;
uniform float uSpecies; uniform float uAccessory;

float sdEll(vec3 p, vec3 r){ float k0 = length(p / r); float k1 = length(p / (r * r)); return k0 * (k0 - 1.0) / max(k1, 1e-5); }
float smin(float a, float b, float k){ float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0); return mix(b, a, h) - k * h * (1.0 - h); }
mat2 rot(float a){ float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }
float sdRoundCone(vec3 p, float r1, float r2, float h){
  vec2 q = vec2(length(p.xz), p.y); float b = (r1 - r2) / h; float a = sqrt(1.0 - b * b); float k = dot(q, vec2(-b, a));
  if (k < 0.0) return length(q) - r1; if (k > a * h) return length(q - vec2(0.0, h)) - r2; return dot(q, vec2(a, b)) - r1; }
bool isSp(float s){ return abs(uSpecies - s) < 0.5; }

// returns (distance, material) ; materials: 1 body 2 eye 3 glint 4 ear 5 accessory 6 nose
vec2 opU(vec2 a, vec2 b){ return a.x < b.x ? a : b; }

vec3 headLocal(vec3 p, float bob){
  vec3 q = p - vec3(0.0, 0.22 + bob, 0.0);
  q.xz *= rot(-uLook.x * 0.45);
  q.yz *= rot(uLook.y * 0.3);
  q.xy *= rot(uLook.x * 0.08 + sin(uTime * 1.3) * 0.03 * (1.0 - uWalk));
  return q;
}

vec2 map(vec3 p){
  p.y -= uJump;
  float sy = 1.0 - uSquash * 0.22, sxz = 1.0 + uSquash * 0.14;
  p.y = (p.y + 0.9) / sy - 0.9; p.xz /= sxz;
  float scaleFix = min(sy, sxz);
  p.xz *= rot(uYaw);
  float t = uTime;
  float bob = abs(sin(t * 9.0)) * 0.05 * uWalk + sin(t * 2.0) * 0.012;
  bool ghost = isSp(3.0);
  if (ghost) bob += sin(t * 2.2) * 0.05;

  vec3 q = headLocal(p, bob);
  float head = sdEll(q, vec3(0.62, 0.5, 0.52));
  vec3 bp = p - vec3(0.0, -0.48 + bob * 0.6, 0.0);
  float body;
  if (ghost) {
    vec3 g = p - vec3(0.0, -0.4 + bob, 0.0);
    body = sdEll(g, vec3(0.5, 0.58, 0.44));
    if (g.y < -0.3) body += sin(atan(g.z, g.x) * 7.0 + t * 4.0) * 0.03 * smoothstep(-0.3, -0.55, g.y);
  } else {
    body = sdEll(bp, vec3(0.42, 0.36, 0.36));
  }
  float d = smin(head, body, 0.14);
  vec2 res = vec2(d, 1.0);

  // arms
  for (int i = 0; i < 2; i++) {
    float s = i == 0 ? -1.0 : 1.0;
    float swing = sin(t * 9.0 + s * 1.57) * 0.12 * uWalk + uHappy * 0.5 * (0.6 + 0.4 * sin(t * 18.0));
    vec3 ap = p - vec3(s * 0.38, -0.42 + bob + uHappy * 0.12, 0.08);
    ap.xy *= rot(s * (0.3 + swing));
    res.x = smin(res.x, sdEll(ap, vec3(0.09, 0.14, 0.09)), 0.05);
  }
  // feet
  if (!ghost) {
    for (int i = 0; i < 2; i++) {
      float s = i == 0 ? -1.0 : 1.0;
      float ph = sin(t * 9.0 + s * 1.57) * uWalk;
      vec3 fp = p - vec3(s * 0.2, -0.84 + max(ph, 0.0) * 0.08, ph * 0.09 + 0.04);
      res.x = smin(res.x, sdEll(fp, vec3(0.15, 0.09, 0.17)), 0.04);
    }
  }
  // tail (cat, bear nub)
  if (isSp(0.0)) {
    vec3 tp = p - vec3(0.0, -0.55 + bob, -0.38);
    tp.xy *= rot(sin(t * 2.5) * 0.35);
    tp.yz *= rot(-0.7);
    res.x = smin(res.x, sdRoundCone(tp, 0.07, 0.05, 0.38), 0.05);
  }

  // ears / head features
  for (int i = 0; i < 2; i++) {
    float s = i == 0 ? -1.0 : 1.0;
    float ear = 1e3;
    if (isSp(0.0)) { vec3 e = q - vec3(s * 0.32, 0.28, -0.02); e.xy *= rot(s * 0.42); e.z *= 1.7; ear = sdRoundCone(e, 0.17, 0.035, 0.3) / 1.7; }
    else if (isSp(1.0)) { vec3 e = q - vec3(s * 0.19, 0.38, -0.04); e.xy *= rot(s * (0.16 + 0.05 * sin(t * 1.7 + s))); e.yz *= rot(-0.15); ear = sdEll(e - vec3(0.0, 0.3, 0.0), vec3(0.1, 0.34, 0.07)); }
    else if (isSp(2.0)) { ear = sdEll(q - vec3(s * 0.4, 0.36, -0.05), vec3(0.16, 0.15, 0.09)); }
    else if (isSp(5.0)) { ear = sdEll(q - vec3(s * 0.25, 0.38, 0.12), vec3(0.17, 0.15, 0.15)); }
    if (ear < 1e2) { float merged = smin(res.x, ear, 0.06); res = vec2(merged, ear < res.x ? 4.0 : res.y); }

    // eyes: bead eyes that follow the look direction
    vec3 ec = isSp(5.0) ? vec3(s * 0.25, 0.44, 0.24) : vec3(s * 0.2, 0.02, 0.45);
    ec.xy += uLook * vec2(0.03, 0.02);
    float openY = mix(0.095, 0.012, uBlink);
    float eye;
    if (uHappy > 0.5) { // ^ ^ happy eyes
      vec3 hp = q - ec - vec3(0.0, -0.02, 0.0);
      eye = max(abs(length(hp.xy) - 0.06) - 0.016, abs(hp.z) - 0.05);
      eye = max(eye, -hp.y);
    } else {
      eye = sdEll(q - ec, vec3(0.072, openY, 0.05));
    }
    res = opU(res, vec2(eye, 2.0));
    if (uHappy < 0.5 && uBlink < 0.5) res = opU(res, vec2(length(q - ec - vec3(-0.022 + uLook.x * 0.01, 0.034, 0.04)) - 0.022, 3.0));
  }
  // nose
  if (isSp(0.0) || isSp(2.0) || isSp(1.0)) res = opU(res, vec2(sdEll(q - vec3(0.0, -0.06, 0.515), vec3(0.035, 0.022, 0.02)), 6.0));
  // accessories
  if (abs(uAccessory - 1.0) < 0.5) { // bow
    vec3 b = q - vec3(0.3, 0.4, 0.12); b.xy *= rot(-0.5);
    float bow = min(sdEll(b - vec3(-0.09, 0.0, 0.0), vec3(0.09, 0.065, 0.04)), sdEll(b - vec3(0.09, 0.0, 0.0), vec3(0.09, 0.065, 0.04)));
    bow = min(bow, length(b) - 0.045);
    res = opU(res, vec2(bow, 5.0));
  } else if (abs(uAccessory - 2.0) < 0.5) { // flower
    vec3 b = q - vec3(-0.3, 0.42, 0.1); float f = 1e3;
    for (int k = 0; k < 5; k++) { float a = float(k) * 1.2566 + 0.3; f = min(f, length(b - vec3(cos(a), sin(a), 0.0) * 0.07) - 0.05); }
    res = opU(res, vec2(f, 5.0)); res = opU(res, vec2(length(b - vec3(0, 0, 0.03)) - 0.04, 6.0));
  } else if (abs(uAccessory - 3.0) < 0.5) { // sprout
    vec3 b = q - vec3(0.0, 0.5, 0.0); b.xy *= rot(sin(t * 2.0) * 0.15);
    float stem = sdRoundCone(b, 0.022, 0.018, 0.16);
    vec3 l1 = b - vec3(-0.07, 0.18, 0.0); l1.xy *= rot(0.6); vec3 l2 = b - vec3(0.07, 0.18, 0.0); l2.xy *= rot(-0.6);
    float leaf = min(sdEll(l1, vec3(0.08, 0.04, 0.025)), sdEll(l2, vec3(0.08, 0.04, 0.025)));
    res = opU(res, vec2(min(stem, leaf), 5.0));
  } else if (abs(uAccessory - 4.0) < 0.5) { // star clip
    vec3 b = q - vec3(0.3, 0.38, 0.14); float a = atan(b.y, b.x); float r = 0.05 + 0.03 * cos(a * 5.0 + 1.57);
    res = opU(res, vec2(max(length(b.xy) - r, abs(b.z) - 0.025), 5.0));
  }
  res.x *= scaleFix;
  return res;
}

vec3 calcNormal(vec3 p){ vec2 e = vec2(0.0015, -0.0015);
  return normalize(e.xyy * map(p + e.xyy).x + e.yyx * map(p + e.yyx).x + e.yxy * map(p + e.yxy).x + e.xxx * map(p + e.xxx).x); }

void main(){
  vec2 uv = (gl_FragCoord.xy - 0.5 * uRes) / uRes.y * 2.35 + vec2(0.0, 0.08);
  vec3 ro = vec3(uv, 3.0), rd = vec3(0.0, 0.0, -1.0);
  float t = 0.0, minD = 1e3; vec2 h = vec2(1e3, 0.0);
  for (int i = 0; i < 72; i++) {
    h = map(ro + rd * t);
    minD = min(minD, h.x);
    if (h.x < 0.0015 || t > 6.0) break;
    t += h.x * 0.9;
  }
  vec4 col = vec4(0.0);
  if (h.x < 0.0015) {
    vec3 p = ro + rd * t; vec3 n = calcNormal(p);
    vec3 base = uBody;
    float bob = abs(sin(uTime * 9.0)) * 0.05 * uWalk;
    vec3 pp = p; pp.y -= uJump; pp.xz *= rot(uYaw);
    vec3 q = headLocal(pp, bob);
    if (h.y > 3.5 && h.y < 4.5) base = mix(uBody, uEar, smoothstep(0.0, 0.6, n.z) );
    if (h.y > 0.5 && h.y < 1.5) {
      // belly patch
      vec3 bp = pp - vec3(0.0, -0.52, 0.28);
      base = mix(base, uBelly, smoothstep(0.26, 0.2, length(bp.xy * vec2(1.0, 1.25))) * step(0.0, n.z) * 0.8);
      // blush
      for (int i = 0; i < 2; i++) { float s = i == 0 ? -1.0 : 1.0; float bl = length((q - vec3(s * 0.34, -0.1, 0.36)).xy);
        base = mix(base, uBlush, smoothstep(0.1, 0.05, bl) * step(0.25, q.z) * 0.85); }
      // mouth: a little w (or an open smile when happy)
      vec2 m = vec2(abs(q.x) - 0.04, q.y + 0.12);
      float arc = abs(length(m) - 0.04);
      float mouth = (uHappy > 0.5) ? smoothstep(0.012, 0.0, length(vec2(q.x, (q.y + 0.15) * 1.6)) - 0.05) * step(q.y, -0.11)
                                   : smoothstep(0.011, 0.004, arc) * step(m.y, 0.0) * step(abs(q.x), 0.09);
      base = mix(base, uInk, mouth * step(0.3, q.z));
    }
    if (h.y > 1.5 && h.y < 2.5) base = uInk;
    if (h.y > 2.5 && h.y < 3.5) base = vec3(1.0);
    if (h.y > 4.5 && h.y < 5.5) base = uAcc;
    if (h.y > 5.5) base = mix(uInk, uBlush, 0.5);
    vec3 l = normalize(vec3(-0.45, 0.75, 0.6));
    float dif = dot(n, l) * 0.5 + 0.5;
    float toon = mix(0.72, 1.0, smoothstep(0.42, 0.58, dif));
    float rim = pow(1.0 - max(n.z, 0.0), 3.0);
    vec3 c = base * toon + rim * 0.18;
    if (h.y > 1.5 && h.y < 2.5) c += pow(max(dot(reflect(-l, n), vec3(0, 0, 1)), 0.0), 30.0) * 0.6;
    col = vec4(c, 1.0);
  } else {
    // sticker outline around the silhouette
    float ol = smoothstep(0.03, 0.018, minD);
    col = vec4(uInk, ol);
    // ground shadow
    float gy = -0.95 - 0.0; float sh = 0.0;
    vec2 s = vec2(uv.x / 0.55, (uv.y - gy) / 0.07);
    sh = smoothstep(1.0, 0.2, length(s)) * 0.18 * (1.0 - clamp(uJump * 2.0, 0.0, 0.8));
    col = col.a > 0.01 ? col : vec4(uInk, sh);
  }
  gl_FragColor = vec4(col.rgb * col.a, col.a);
}`;

const VERT = `attribute vec2 aPos; void main(){ gl_Position = vec4(aPos, 0.0, 1.0); }`;

function rgb(hex) {
  const h = hex.replace("#", "");
  const n = h.length === 3 ? h.split("").map((c) => c + c).join("") : h.slice(0, 6);
  const v = parseInt(n, 16);
  return [((v >> 16) & 255) / 255, ((v >> 8) & 255) / 255, (v & 255) / 255];
}
const reduced = () => document.documentElement.dataset.motion === "off" ||
  (matchMedia("(prefers-reduced-motion: reduce)").matches && document.documentElement.dataset.motion !== "on");

const DEFAULT_COLORS = { body: "#fff7fb", belly: "#fff1f7", ear: "#ffc4da", blush: "#ff9dc4", ink: "#3d2230", accessory: "#f47fa6" };

export function createMascot(options = {}) {
  const o = { species: "cat", behavior: "wander", size: 120, accessory: "bow", hearts: "♡", zIndex: 50, ...options };
  o.colors = { ...DEFAULT_COLORS, ...(options.colors || {}) };

  const wrap = document.createElement("div");
  wrap.dataset.cutecore = "mascot";
  Object.assign(wrap.style, { position: "fixed", left: "0", top: "0", width: o.size + "px", height: o.size + "px", zIndex: o.zIndex, pointerEvents: "none", willChange: "transform" });
  const canvas = document.createElement("canvas");
  canvas.setAttribute("role", "img");
  canvas.setAttribute("aria-label", options.label || `${o.species} mascot`);
  Object.assign(canvas.style, { width: "100%", height: "100%", display: "block", pointerEvents: "auto", cursor: "pointer" });
  wrap.appendChild(canvas);
  document.body.appendChild(wrap);

  const gl = canvas.getContext("webgl", { premultipliedAlpha: true, alpha: true, antialias: true });
  if (!gl) { wrap.remove(); return { say() {}, celebrate() {}, setBehavior() {}, destroy() {}, fallback: true }; }
  const dpr = Math.min(devicePixelRatio || 1, 2);
  canvas.width = canvas.height = Math.round(o.size * dpr);
  gl.viewport(0, 0, canvas.width, canvas.height);

  const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error("mascot: " + gl.getShaderInfoLog(s)); return s; };
  const prog = gl.createProgram();
  gl.attachShader(prog, sh(gl.VERTEX_SHADER, VERT)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FRAG));
  gl.bindAttribLocation(prog, 0, "aPos"); gl.linkProgram(prog); gl.useProgram(prog);
  const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
  gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
  const U = {}; for (const n of ["uRes", "uTime", "uLook", "uWalk", "uYaw", "uSquash", "uBlink", "uJump", "uHappy", "uBody", "uBelly", "uEar", "uBlush", "uInk", "uAcc", "uSpecies", "uAccessory"]) U[n] = gl.getUniformLocation(prog, n);
  const setColors = () => { const c = o.colors; gl.uniform3fv(U.uBody, rgb(c.body)); gl.uniform3fv(U.uBelly, rgb(c.belly)); gl.uniform3fv(U.uEar, rgb(c.ear)); gl.uniform3fv(U.uBlush, rgb(c.blush)); gl.uniform3fv(U.uInk, rgb(c.ink)); gl.uniform3fv(U.uAcc, rgb(c.accessory)); };
  setColors();

  // ---------------------------------------------------------------- state
  const S = { x: innerWidth * 0.8, y: innerHeight - 8, tx: innerWidth * 0.8, ty: innerHeight - 8, walk: 0, yaw: 0, look: [0, 0], blink: 0, nextBlink: 2,
    jump: 0, jv: 0, squash: 0, happy: 0, idleUntil: 0, peekRise: 0, hover: false, mouse: [innerWidth / 2, innerHeight / 2], rel: Math.random() };
  let behavior = o.behavior, raf = 0, t0 = performance.now(), last = t0, bubble = null;
  const perchEl = () => (o.perch ? (typeof o.perch === "string" ? document.querySelector(o.perch) : o.perch) : null);

  const onMove = (e) => { S.mouse = [e.clientX, e.clientY]; };
  addEventListener("pointermove", onMove, { passive: true });
  const onEnter = () => { S.hover = true; }, onLeave = () => { S.hover = false; };
  let hooked = null;
  function hookPerch() { const el = perchEl(); if (el === hooked) return; if (hooked) { hooked.removeEventListener("pointerenter", onEnter); hooked.removeEventListener("pointerleave", onLeave); }
    hooked = el; if (el) { el.addEventListener("pointerenter", onEnter); el.addEventListener("pointerleave", onLeave); } }
  hookPerch();
  canvas.addEventListener("click", () => api.celebrate());

  function ground() {
    const el = perchEl();
    if (el) { const r = el.getBoundingClientRect(); return { y: r.top + 4, x0: r.left + o.size * 0.35, x1: r.right - o.size * 0.35 }; }
    return { y: innerHeight - 6, x0: o.size * 0.5, x1: innerWidth - o.size * 0.5 };
  }

  function step(now) {
    const dt = Math.min(0.05, (now - last) / 1000); last = now;
    const time = (now - t0) / 1000;
    const still = reduced();
    const g = ground();
    let speed = 0;

    if (behavior === "follow" && !still) {
      const side = S.mouse[0] > S.x ? -1 : 1;
      S.tx = S.mouse[0] + side * o.size * 0.7; S.ty = Math.max(o.size, S.mouse[1] + o.size * 0.55);
    } else if (behavior === "wander" && !still) {
      if (now > S.idleUntil && Math.abs(S.tx - S.x) < 2) { S.idleUntil = now + 1800 + Math.random() * 3500; S.rel = Math.random(); }
      if (now > S.idleUntil) S.tx = g.x0 + (g.x1 - g.x0) * S.rel;
      S.ty = g.y;
    } else { // perch, peek, or reduced motion
      S.tx = g.x0 + (g.x1 - g.x0) * (perchEl() ? 0.85 : S.rel); S.ty = g.y;
      if (still) { S.x = S.tx; }
    }
    if (!S.placed) { S.x = S.tx; S.y = S.ty; S.placed = true; }
    const dx = S.tx - S.x, dy = S.ty - S.y;
    const dist = Math.hypot(dx, dy);
    if (dist > 1.5) {
      const v = Math.min(dist, behavior === "follow" ? 260 * dt + dist * 2.2 * dt : 70 * dt);
      S.x += (dx / dist) * v; S.y += (dy / dist) * v; speed = v / Math.max(dt, 1e-3);
    }
    if (behavior !== "follow") S.y = S.ty; // stick to the ground line
    S.walk += ((speed > 20 ? 1 : 0) - S.walk) * Math.min(1, dt * 8);
    const facing = Math.abs(dx) > 3 && speed > 20 ? Math.sign(dx) * 0.55 : ((S.mouse[0] - S.x) / innerWidth) * 0.9;
    S.yaw += (facing - S.yaw) * Math.min(1, dt * 6);

    // look at cursor from the head position
    const hx = S.x, hy = S.y - o.size * 0.62;
    const lx = Math.max(-1, Math.min(1, (S.mouse[0] - hx) / 320)), ly = Math.max(-1, Math.min(1, -(S.mouse[1] - hy) / 320));
    S.look = [S.look[0] + (lx - S.look[0]) * dt * 7, S.look[1] + (ly - S.look[1]) * dt * 7];

    // blink
    if (time > S.nextBlink) { S.blink = 1; S.nextBlink = time + 2 + Math.random() * 4; }
    S.blink = Math.max(0, S.blink - dt * 9);
    // jump physics
    if (S.jump > 0 || S.jv > 0) { S.jv -= 6.5 * dt; S.jump += S.jv * dt; if (S.jump <= 0) { S.jump = 0; S.jv = 0; S.squash = 1; } }
    S.squash = Math.max(0, S.squash - dt * 4);
    S.happy = Math.max(0, S.happy - dt * 0.6);

    // peek: only the head shows above the perch edge until hovered
    let clip = 0;
    if (behavior === "peek") { S.peekRise += ((S.hover ? 1 : 0.42) - S.peekRise) * Math.min(1, dt * 6); clip = 1 - S.peekRise; }
    const sink = clip * o.size * 0.62;
    wrap.style.transform = `translate3d(${S.x - o.size / 2}px, ${S.y - o.size + sink}px, 0)`;
    wrap.style.clipPath = clip > 0.01 ? `inset(0 0 ${sink + 2}px 0)` : "none";
    if (bubble) bubble.style.transform = `translate3d(${S.x - bubble.offsetWidth / 2}px, ${S.y - o.size - bubble.offsetHeight - 4 + sink - S.jump * o.size * 0.4}px, 0)`;

    gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
    gl.uniform2f(U.uRes, canvas.width, canvas.height);
    gl.uniform1f(U.uTime, still ? 0.0 : time);
    gl.uniform2f(U.uLook, S.look[0], S.look[1]);
    gl.uniform1f(U.uWalk, S.walk); gl.uniform1f(U.uYaw, S.yaw); gl.uniform1f(U.uSquash, S.squash);
    gl.uniform1f(U.uBlink, S.blink > 0.5 ? 1 : 0); gl.uniform1f(U.uJump, S.jump); gl.uniform1f(U.uHappy, S.happy > 0.05 ? 1 : 0);
    gl.uniform1f(U.uSpecies, SPECIES[o.species] ?? 0); gl.uniform1f(U.uAccessory, ACCESSORY[o.accessory] ?? 0);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    raf = requestAnimationFrame(step);
  }
  raf = requestAnimationFrame(step);
  const onVis = () => { cancelAnimationFrame(raf); if (!document.hidden) { last = performance.now(); raf = requestAnimationFrame(step); } };
  document.addEventListener("visibilitychange", onVis);

  function burst() {
    for (let i = 0; i < 7; i++) {
      const h = document.createElement("span");
      h.textContent = o.hearts; h.setAttribute("aria-hidden", "true");
      const a = (-Math.PI / 2) + (Math.random() - 0.5) * 2.2, r = 40 + Math.random() * 50;
      Object.assign(h.style, { position: "fixed", left: S.x + "px", top: S.y - o.size * 0.7 + "px", zIndex: o.zIndex + 1, pointerEvents: "none",
        color: i % 2 ? o.colors.accessory : o.colors.blush, font: `700 ${14 + Math.random() * 12}px/1 ui-rounded, system-ui`,
        transition: "transform .9s cubic-bezier(.23,1,.32,1), opacity .9s ease", transform: "translate(-50%,-50%) scale(.4)" });
      document.body.appendChild(h);
      requestAnimationFrame(() => { h.style.transform = `translate(calc(-50% + ${Math.cos(a) * r}px), calc(-50% + ${Math.sin(a) * r}px)) scale(1) rotate(${(Math.random() - 0.5) * 40}deg)`; h.style.opacity = "0"; });
      setTimeout(() => h.remove(), 950);
    }
  }

  const api = {
    el: wrap,
    say(text, ms = 2600) {
      bubble?.remove();
      bubble = document.createElement("div");
      bubble.textContent = text; bubble.setAttribute("role", "status");
      Object.assign(bubble.style, { position: "fixed", left: "0", top: "0", zIndex: o.zIndex + 1, pointerEvents: "none", padding: ".45em .8em",
        font: "600 14px/1.2 var(--font-display, ui-rounded, system-ui)", color: "var(--on-soft, " + o.colors.ink + ")", background: "var(--paper, #fff)",
        border: "3px solid var(--sticker-rim, #fff)", borderRadius: "14px", boxShadow: "0 2px 0 var(--sticker-shadow, #eea3bb)", whiteSpace: "nowrap" });
      document.body.appendChild(bubble);
      const b = bubble; setTimeout(() => { if (bubble === b) { b.remove(); bubble = null; } }, ms);
    },
    celebrate() { if (!reduced()) { S.jv = 2.4; S.jump = 0.001; } S.happy = 1.4; burst(); },
    setBehavior(b) { behavior = b; hookPerch(); },
    setPerch(sel) { o.perch = sel; hookPerch(); },
    setColors(c) { o.colors = { ...o.colors, ...c }; setColors(); },
    setSpecies(s) { o.species = s; },
    setAccessory(a) { o.accessory = a; },
    destroy() { cancelAnimationFrame(raf); removeEventListener("pointermove", onMove); document.removeEventListener("visibilitychange", onVis); bubble?.remove(); wrap.remove(); gl.getExtension("WEBGL_lose_context")?.loseContext(); },
  };
  return api;
}

if (typeof window !== "undefined") window.CuteMascot = { createMascot };
