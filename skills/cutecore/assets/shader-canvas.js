/* shader-canvas.js: zero dependency WebGL backgrounds in the cutecore palette.
 *
 *   import { mountShader } from "./shader-canvas.js";
 *   const s = mountShader("#hero", { preset: "cotton-sky", colors: ["#ffd0df", "#e6d3ff", "#cfe4ff", "#fff6f8"] });
 *   s.set({ preset: "jelly-blobs" }); s.destroy();
 *
 * Options
 *   preset     cotton-sky | jelly-blobs | sparkle-field | dither-dream | holo-foil | cotton-mesh | pixel-hearts
 *   colors     up to 4 css hex colours (defaults read --accent-soft, --alt, --alt-2, --bg from the page)
 *   speed      time multiplier (1)
 *   intensity  preset specific strength 0..1 (0.6)
 *   pixel      render scale divisor for chunky retro output (1 = sharp, 4 = pixel art)
 *   mouse      cursor reactive (true)
 *   dpr        max device pixel ratio (1.5)
 *   fragment   your own GLSL body: `vec4 shade(vec2 uv, vec2 px)` (see shaders.md)
 *
 * Behaviour: pauses off screen and in hidden tabs, renders one still frame under
 * prefers-reduced-motion or html[data-motion=off], falls back to a CSS gradient
 * when WebGL is missing. The canvas is aria-hidden and pointer-events: none.
 */

const HEADER = `precision highp float;
uniform vec2 uRes; uniform float uTime; uniform vec2 uMouse; uniform float uIntensity;
uniform vec3 uC0; uniform vec3 uC1; uniform vec3 uC2; uniform vec3 uC3;
float hash(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float noise(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1,0)), f.x), mix(hash(i + vec2(0,1)), hash(i + vec2(1,1)), f.x), f.y); }
float fbm(vec2 p){ float v = 0.0, a = 0.5; for (int i = 0; i < 5; i++) { v += a * noise(p); p = p * 2.03 + 17.1; a *= 0.5; } return v; }
vec3 pal4(float t){ t = fract(t) * 4.0; vec3 a = t < 1.0 ? uC0 : t < 2.0 ? uC1 : t < 3.0 ? uC2 : uC3; vec3 b = t < 1.0 ? uC1 : t < 2.0 ? uC2 : t < 3.0 ? uC3 : uC0; return mix(a, b, smoothstep(0.0, 1.0, fract(t))); }
float sparkle(vec2 p, float r){ p = abs(p); float d = pow(p.x, 0.5) + pow(p.y, 0.5); return smoothstep(pow(r, 0.5) * 1.1, 0.0, d); }
`;

const PRESETS = {
  // soft domain warped pastel sky with grain: the default page backdrop
  "cotton-sky": `vec4 shade(vec2 uv, vec2 px){
    vec2 p = uv * vec2(uRes.x / uRes.y, 1.0) * 1.4;
    vec2 m = (uMouse - 0.5) * 0.25;
    float t = uTime * 0.04;
    vec2 q = vec2(fbm(p + t), fbm(p + vec2(5.2, 1.3) - t));
    float f = fbm(p + 2.2 * q + m + t * 0.5);
    vec3 col = pal4(f * 0.9 + q.x * 0.35 + 0.1);
    col = mix(col, uC3, 0.25 + 0.2 * (1.0 - uIntensity));
    col += (hash(px + fract(uTime)) - 0.5) * 0.025;
    return vec4(col, 1.0); }`,

  // gummy metaballs that follow the cursor, candy specular, less glass more jelly
  "jelly-blobs": `vec4 shade(vec2 uv, vec2 px){
    vec2 a = vec2(uRes.x / uRes.y, 1.0); vec2 p = uv * a;
    float field = 0.0; vec2 grad = vec2(0.0); float hue = 0.0;
    for (int i = 0; i < 6; i++) {
      float fi = float(i);
      vec2 c = vec2(0.5 + 0.34 * sin(uTime * (0.21 + fi * 0.05) + fi * 1.7), 0.5 + 0.3 * cos(uTime * (0.17 + fi * 0.04) + fi * 2.3)) * a;
      if (i == 0) c = mix(c, uMouse * a, 0.8);
      float r = 0.11 + 0.03 * sin(fi * 3.1 + uTime * 0.6);
      vec2 d = p - c; float k = r * r / max(dot(d, d), 1e-4);
      field += k; grad += -2.0 * k * d / max(dot(d, d), 1e-4); hue += k * fi / 6.0;
    }
    hue /= max(field, 1e-3);
    float inside = smoothstep(0.95, 1.05, field);
    vec3 n = normalize(vec3(-grad * 0.035, 1.0));
    vec3 l = normalize(vec3(-0.4, 0.6, 0.8));
    vec3 base = pal4(hue);
    float diff = 0.75 + 0.25 * dot(n, l);
    float spec = pow(max(dot(reflect(-l, n), vec3(0,0,1)), 0.0), 24.0) * 0.8;
    float rim = smoothstep(1.0, 1.6, field) * 0.0 + (1.0 - smoothstep(1.0, 1.35, field)) * inside * 0.35;
    vec3 jelly = base * diff + spec + rim * vec3(1.0);
    vec3 bg = mix(uC3, base, 0.12);
    return vec4(mix(bg, jelly, inside * (0.55 + 0.45 * uIntensity)), 1.0); }`,

  // drifting 4 point sparkles and twinkle dust with mouse parallax
  "sparkle-field": `vec4 shade(vec2 uv, vec2 px){
    vec2 a = vec2(uRes.x / uRes.y, 1.0);
    vec3 col = mix(uC3, mix(uC0, uC2, uv.x), 0.35 + uv.y * 0.25);
    for (int layer = 0; layer < 3; layer++) {
      float L = float(layer);
      float scale = 4.0 + L * 3.5;
      vec2 p = uv * a * scale + (uMouse - 0.5) * (0.4 + L * 0.5) + vec2(0.0, uTime * (0.04 + L * 0.025));
      vec2 id = floor(p), f = fract(p) - 0.5;
      float h = hash(id + L * 13.0);
      if (h > 0.55) {
        vec2 o = (vec2(hash(id + 3.1), hash(id + 7.7)) - 0.5) * 0.5;
        float tw = 0.5 + 0.5 * sin(uTime * (1.2 + h * 2.5) + h * 40.0);
        vec2 q = (f - o); q *= mat2(cos(h * 6.0), -sin(h * 6.0), sin(h * 6.0), cos(h * 6.0)) * (1.0 + L * 0.35);
        float size = (0.16 + 0.14 * tw) * (1.0 - L * 0.22);
        float glow = sparkle(q, size);
        float core = sparkle(q, size * 0.45);
        vec3 tint = pal4(h * 3.0 + L * 0.3) * 0.7;
        col = mix(col, tint, glow * (0.6 + 0.4 * uIntensity));
        col = mix(col, vec3(1.0), core * 0.9);
      }
    }
    return vec4(col, 1.0); }`,

  // Bayer dithered gradient waves with cursor repel (retro, inspired by paper shaders dithering)
  "dither-dream": `float bayer(vec2 p){ vec2 q = mod(floor(p), 4.0);
      int i = int(q.x + q.y * 4.0);
      float m[16]; m[0]=0.;m[1]=8.;m[2]=2.;m[3]=10.;m[4]=12.;m[5]=4.;m[6]=14.;m[7]=6.;m[8]=3.;m[9]=11.;m[10]=1.;m[11]=9.;m[12]=15.;m[13]=7.;m[14]=13.;m[15]=5.;
      for (int k = 0; k < 16; k++) { if (k == i) return m[k] / 16.0; } return 0.0; }
    vec4 shade(vec2 uv, vec2 px){
    vec2 a = vec2(uRes.x / uRes.y, 1.0); vec2 p = uv * a;
    vec2 d = p - uMouse * a; float push = exp(-dot(d, d) * 18.0) * 0.25;
    float v = 0.5 + 0.5 * sin(p.x * 5.0 + uTime * 0.6 + fbm(p * 2.0 + uTime * 0.1) * 4.0 + push * 10.0);
    v = v * 0.7 + uv.y * 0.3 + push;
    float cell = 3.0;
    float t = bayer(px / cell);
    float lv = clamp(v * 3.0, 0.0, 2.999);
    float band = floor(lv), fr = fract(lv);
    float pick = band + step(t, fr);
    vec3 col = pick < 1.0 ? uC3 : pick < 2.0 ? uC0 : pick < 3.0 ? uC1 : uC2;
    return vec4(col, 1.0); }`,

  // iridescent sticker foil that tilts with the cursor
  "holo-foil": `vec4 shade(vec2 uv, vec2 px){
    vec2 m = uMouse - 0.5;
    float ang = dot(uv - 0.5, normalize(vec2(1.0, 0.6) + m)) * 3.0;
    float band = ang + fbm(uv * 3.0 + uTime * 0.05) * 0.8 + m.x * 1.5 + uTime * 0.03;
    vec3 holo = pal4(band);
    float glint = pow(sparkle((fract(uv * vec2(uRes.x / uRes.y, 1.0) * 9.0) - 0.5), 0.12), 1.0) * step(0.7, hash(floor(uv * vec2(uRes.x / uRes.y, 1.0) * 9.0)));
    float sheen = smoothstep(0.35, 0.0, abs(uv.x + uv.y - 1.0 - m.x * 1.2)) * 0.35;
    vec3 col = mix(uC3, holo, 0.55 + 0.35 * uIntensity) + sheen + glint * 0.6;
    return vec4(col, 1.0); }`,

  // slow animated mesh gradient (lwsg style) in the triad
  "cotton-mesh": `vec4 shade(vec2 uv, vec2 px){
    vec2 p = uv * vec2(uRes.x / uRes.y, 1.0);
    float t = uTime * 0.08;
    vec2 c0 = vec2(0.2 + 0.15 * sin(t * 1.3), 0.3 + 0.2 * cos(t));
    vec2 c1 = vec2(0.8 + 0.1 * cos(t * 0.9), 0.25 + 0.2 * sin(t * 1.1));
    vec2 c2 = vec2(0.6 + 0.2 * sin(t * 0.7), 0.8 + 0.1 * cos(t * 1.4)) ;
    vec2 c3 = mix(vec2(0.3, 0.75), uMouse, 0.35);
    vec2 a = vec2(uRes.x / uRes.y, 1.0);
    float w0 = 1.0 / pow(length(p - c0 * a) + 0.05, 2.0), w1 = 1.0 / pow(length(p - c1 * a) + 0.05, 2.0);
    float w2 = 1.0 / pow(length(p - c2 * a) + 0.05, 2.0), w3 = 1.0 / pow(length(p - c3 * a) + 0.05, 2.0);
    vec3 col = (uC0 * w0 + uC1 * w1 + uC2 * w2 + uC3 * w3) / (w0 + w1 + w2 + w3);
    col += (hash(px + fract(uTime)) - 0.5) * 0.03;
    return vec4(col, 1.0); }`,

  // tamagotchi lcd: scrolling pixel hearts, best with pixel: 3..5
  "pixel-hearts": `float dot2(vec2 v){ return dot(v, v); }
    float sdHeart(vec2 p){ p.x = abs(p.x);
      if (p.y + p.x > 1.0) return sqrt(dot2(p - vec2(0.25, 0.75))) - sqrt(2.0) / 4.0;
      return sqrt(min(dot2(p - vec2(0.0, 1.0)), dot2(p - 0.5 * max(p.x + p.y, 0.0)))) * sign(p.x - p.y); }
    vec4 shade(vec2 uv, vec2 px){
    vec2 a = vec2(uRes.x / uRes.y, 1.0);
    vec2 p = uv * a * 3.5 + vec2(uTime * 0.2, uTime * 0.12);
    vec2 id = floor(p); vec2 f = fract(p) - 0.5;
    float bounce = 0.04 * sin(uTime * 3.0 + hash(id) * 6.28);
    float on = step(sdHeart(f * 1.7 + vec2(0.0, 0.42 + bounce)), 0.0) * step(0.35, hash(id));
    vec3 col = mix(uC3, uC0, 0.2 + 0.15 * mod(id.x + id.y, 2.0));
    col = mix(col, mix(uC1, uC2, step(0.5, hash(id + 2.0))) * 0.92, on * (0.7 + 0.3 * uIntensity));
    return vec4(col, 1.0); }`,
};

const VERT = `attribute vec2 aPos; varying vec2 vUv; void main(){ vUv = aPos * 0.5 + 0.5; gl_Position = vec4(aPos, 0.0, 1.0); }`;

function hexToRgb(hex) {
  const h = (hex || "#ffffff").trim().replace("#", "");
  const n = h.length === 3 ? h.split("").map((c) => c + c).join("") : h.slice(0, 6);
  const v = parseInt(n, 16);
  return [((v >> 16) & 255) / 255, ((v >> 8) & 255) / 255, (v & 255) / 255];
}

function cssColors() {
  const cs = getComputedStyle(document.documentElement);
  const read = (v, d) => (cs.getPropertyValue(v).trim() || d);
  return [read("--accent-soft", "#ffd0df"), read("--alt", "#e6d3ff"), read("--alt-2", "#cfe4ff"), read("--bg", "#fff6f8")];
}

const reducedMotion = () =>
  document.documentElement.dataset.motion === "off" ||
  (matchMedia("(prefers-reduced-motion: reduce)").matches && document.documentElement.dataset.motion !== "on");

export const SHADER_PRESETS = Object.keys(PRESETS);

export function mountShader(target, options = {}) {
  const host = typeof target === "string" ? document.querySelector(target) : target;
  if (!host) throw new Error("mountShader: target not found");
  let opts = { preset: "cotton-sky", speed: 1, intensity: 0.6, pixel: 1, mouse: true, dpr: 1.5, ...options };
  let canvas = host;
  if (host.tagName !== "CANVAS") {
    canvas = document.createElement("canvas");
    canvas.setAttribute("aria-hidden", "true");
    canvas.dataset.cutecore = "shader";
    Object.assign(canvas.style, { position: "absolute", inset: "0", width: "100%", height: "100%", pointerEvents: "none", zIndex: "0", display: "block" });
    if (getComputedStyle(host).position === "static") host.style.position = "relative";
    host.prepend(canvas);
  }
  const gl = canvas.getContext("webgl", { premultipliedAlpha: false, antialias: false, alpha: true });
  const colors = () => (opts.colors && opts.colors.length ? opts.colors : cssColors());
  if (!gl) {
    const c = colors();
    canvas.style.background = `linear-gradient(115deg, ${c[0]}, ${c[1]} 45%, ${c[2]} 80%, ${c[3] || c[0]})`;
    return { set() {}, destroy() { if (canvas !== host) canvas.remove(); }, canvas, fallback: true };
  }

  let prog, uni = {};
  function build() {
    const body = opts.fragment || PRESETS[opts.preset] || PRESETS["cotton-sky"];
    const frag = HEADER + body + `\nvarying vec2 vUv; void main(){ vec2 px = gl_FragCoord.xy; gl_FragColor = shade(vUv, px); }`;
    const sh = (type, src) => {
      const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error("shader-canvas: " + gl.getShaderInfoLog(s));
      return s;
    };
    const p = gl.createProgram();
    gl.attachShader(p, sh(gl.VERTEX_SHADER, VERT));
    gl.attachShader(p, sh(gl.FRAGMENT_SHADER, frag));
    gl.bindAttribLocation(p, 0, "aPos");
    gl.linkProgram(p);
    if (prog) gl.deleteProgram(prog);
    prog = p; gl.useProgram(prog);
    for (const n of ["uRes", "uTime", "uMouse", "uIntensity", "uC0", "uC1", "uC2", "uC3"]) uni[n] = gl.getUniformLocation(prog, n);
  }
  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  gl.enableVertexAttribArray(0);
  gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
  build();

  let mouse = [0.5, 0.5], smooth = [0.5, 0.5], visible = true, raf = 0, t0 = performance.now(), last = 0;
  const onMove = (e) => {
    const r = canvas.getBoundingClientRect();
    mouse = [(e.clientX - r.left) / Math.max(r.width, 1), 1 - (e.clientY - r.top) / Math.max(r.height, 1)];
  };
  if (opts.mouse) addEventListener("pointermove", onMove, { passive: true });

  function resize() {
    const r = canvas.getBoundingClientRect();
    const d = Math.min(devicePixelRatio || 1, opts.dpr) / Math.max(1, opts.pixel);
    const w = Math.max(1, Math.round(r.width * d)), h = Math.max(1, Math.round(r.height * d));
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
    canvas.style.imageRendering = opts.pixel > 1 ? "pixelated" : "auto";
    gl.viewport(0, 0, w, h);
  }
  const ro = new ResizeObserver(resize); ro.observe(canvas);
  const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; if (visible) loop(); }, { rootMargin: "100px" });
  io.observe(canvas);

  function draw(now) {
    const c = colors().map(hexToRgb);
    smooth = [smooth[0] + (mouse[0] - smooth[0]) * 0.06, smooth[1] + (mouse[1] - smooth[1]) * 0.06];
    gl.uniform2f(uni.uRes, canvas.width, canvas.height);
    gl.uniform1f(uni.uTime, ((now - t0) / 1000) * opts.speed);
    gl.uniform2f(uni.uMouse, smooth[0], smooth[1]);
    gl.uniform1f(uni.uIntensity, opts.intensity);
    gl.uniform3fv(uni.uC0, c[0]); gl.uniform3fv(uni.uC1, c[1] || c[0]); gl.uniform3fv(uni.uC2, c[2] || c[1] || c[0]); gl.uniform3fv(uni.uC3, c[3] || c[0]);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  }
  function loop(now = performance.now()) {
    cancelAnimationFrame(raf);
    if (!visible || document.hidden) return;
    draw(now);
    if (reducedMotion()) return; // one still frame
    if (opts.pixel > 1 && now - last < 1000 / 24) { raf = requestAnimationFrame(loop); return; } // retro framerate
    last = now;
    raf = requestAnimationFrame(loop);
  }
  const onVis = () => loop();
  document.addEventListener("visibilitychange", onVis);
  resize(); loop();

  return {
    canvas,
    set(next) { const rebuild = next.preset !== undefined || next.fragment !== undefined; opts = { ...opts, ...next }; if (rebuild) build(); resize(); loop(); },
    destroy() {
      cancelAnimationFrame(raf); ro.disconnect(); io.disconnect();
      removeEventListener("pointermove", onMove); document.removeEventListener("visibilitychange", onVis);
      gl.getExtension("WEBGL_lose_context")?.loseContext();
      if (canvas !== host) canvas.remove();
    },
  };
}

if (typeof window !== "undefined") window.CuteShader = { mountShader, presets: SHADER_PRESETS };
