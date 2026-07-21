// Superglue Nozzle & Cap Generator — browser port.
// Geometry mirrors the CadQuery reference implementation in ../src/
// (dimensions.py, thread_socket.py, nozzle.py, cap.py). Keep the two in
// sync if you edit one — constants and formulas should match line-for-line.

import opencascade from "https://cdn.jsdelivr.net/npm/replicad-opencascadejs@0.20.0/src/replicad_single.js";
import * as replicad from "https://cdn.jsdelivr.net/npm/replicad@0.21.0/dist/replicad.js";
import * as THREE from "https://esm.sh/three@0.160.0";
import { OrbitControls } from "https://esm.sh/three@0.160.0/examples/jsm/controls/OrbitControls.js";

const DEG = Math.PI / 180;

// ── Constants (mirror src/dimensions.py) ────────────────────────────────────
// Female bottle-socket profile (asymmetric buttress: 45° self-supporting
// ridge underside, gentle up-facing top flank).
const SOCKET_WALL = 2.6;            // skirt wall behind the thread
const RIDGE_TIP_FLAT = 0.4;         // axial flat on the ridge tip
const RIDGE_TOP_SLOPE_DEG = 15.0;   // up-facing top flank, from horizontal
const OVERSHOOT = 0.25;             // valley cut past the bore wall
const TAN_TOP = Math.tan(RIDGE_TOP_SLOPE_DEG * DEG);

// Nozzle ↔ cap thread — HALF-TURN (2-start, 8 mm lead). Cross-section =
// the print-proven Ø13/Ø11 pitch-4 profile; clearance on the male side.
const CAP_THREAD_MAJOR_D = 13.0;
const CAP_THREAD_MINOR_D = 11.0;
const CAP_THREAD_LEAD = 8.0;
const CAP_THREAD_STARTS = 2;
const CAP_THREAD_SPACING = CAP_THREAD_LEAD / CAP_THREAD_STARTS; // 4.0
const CAP_THREAD_CLR = 0.6;
const COLLAR_MAJOR_D = CAP_THREAD_MAJOR_D - CAP_THREAD_CLR;     // 12.4
const COLLAR_MINOR_D = CAP_THREAD_MINOR_D - CAP_THREAD_CLR;     // 10.4
const COLLAR_LEN = 6.0;

// Dispenser above the shoulder (identical for every bottle; the cap only
// ever meets this part, so one cap fits every generated nozzle).
const THROAT_D = 7.3;               // continuous internal cone base Ø
const DISPENSER_H = 34.5;           // shoulder → tip
const CONE_BASE_D = 10.0;           // exterior cone base
const TIP_OD = 2.4;                 // flat tip rim (0.8 wall at the orifice)
const ORIFICE_D = 0.8;

// Cap — a 1.6 mm shell following the dispensing cone.
const CAP_WALL = 1.6;
const CAP_BOSS_OD = CAP_THREAD_MAJOR_D + 2 * CAP_WALL;          // 16.2
const CAP_NUT_H = COLLAR_LEN;                                   // 6.0
const NUT_OVER = 0.5;
const CAP_SEAL_PRELOAD = 0.15;
const CAP_CONE_CLR = 0.5;
const CAP_TOP_FLAT_D = 2.0;

// Cap interior stack (cap coords: z=0 at the mouth = the nozzle shoulder).
const NECK_Z0 = CAP_NUT_H;                                      // 6.0
const CAVITY_D0 = CONE_BASE_D + 2 * CAP_CONE_CLR;               // 11.0
const NECK_H = (CAP_THREAD_MAJOR_D - CAVITY_D0) / 2;            // 1.0
const CAVITY_Z0 = NECK_Z0 + NECK_H;                             // 7.0
const TIP_Z_CAP = DISPENSER_H;                                  // 34.5
const POCKET_D0 = TIP_OD + 1.9;                                 // 4.3
const POCKET_TIP_D = 1.4;
const POCKET_Z0 = TIP_Z_CAP - CAP_SEAL_PRELOAD - (POCKET_D0 - TIP_OD) / 2;
const POCKET_H = (POCKET_D0 - POCKET_TIP_D) / 2;
const POCKET_TOP_Z = POCKET_Z0 + POCKET_H;

// Cap exterior shell (boss → 45° blend → shell cone → top cone).
const BOSS_R = CAP_BOSS_OD / 2;                                 // 8.1
const BOSS_TOP = CAVITY_Z0 + 1.0;                               // 8.0
const TOP_Z = POCKET_TOP_Z + CAP_WALL;
const SHELL_M = ((CAVITY_D0 - POCKET_D0) / 2) / (POCKET_Z0 - CAVITY_Z0);
const SHELL_C = CAVITY_D0 / 2 + SHELL_M * CAVITY_Z0 + CAP_WALL;
const JOIN_Z = (BOSS_R + BOSS_TOP - SHELL_C) / (1 - SHELL_M);
const JOIN_R = BOSS_R - (JOIN_Z - BOSS_TOP);
const SHELL_END_R = SHELL_C - SHELL_M * POCKET_Z0;

// Grip ribs.
const GRIP_RIB_D = 1.2;
const CAP_RIB_N = 16;

const COUPON_TURNS = 2;

// ── Derived bottle spec (mirror BottleSpec) ─────────────────────────────────
function deriveSpec(p) {
  for (const [k, v] of Object.entries(p)) {
    if (Number.isNaN(v)) throw new Error(`"${k}" is not a number.`);
  }
  const bore = p.threadOD + p.clearance;      // socket ID at groove roots
  const tip = p.threadRootD + p.clearance;    // socket ID across ridge tips
  const pitch = p.pitch;
  const depth = p.capDepth;

  if (tip >= bore - 0.3)
    throw new Error(
      "Thread root Ø must be at least 0.3 mm smaller than the outer Ø — " +
      "check the two diameter measurements.");
  if (bore <= THROAT_D + 1.2)
    throw new Error(
      `This neck is too narrow for the dispenser design (socket bore ` +
      `${bore.toFixed(1)} mm; needs > ${(THROAT_D + 1.2).toFixed(1)} mm).`);

  // Valley width at the overshoot must stay under the pitch, or adjacent
  // thread turns merge (the printable-profile limit).
  const dOs = bore / 2 + OVERSHOOT - tip / 2;
  const valleyW = RIDGE_TIP_FLAT + dOs * (1 + TAN_TOP);
  if (valleyW >= pitch)
    throw new Error(
      `Pitch ${pitch} mm is too fine for a ${((bore - tip) / 2).toFixed(2)} mm ` +
      `deep thread — the printable profile needs pitch > ${valleyW.toFixed(2)} mm. ` +
      `Re-check the pitch (measure across several ridges and divide).`);

  // Helix start BELOW the floor: maximizes the printed bed-contact ring
  // (the first ridge emerges through the mouth face).
  const wallDepth = (bore - tip) / 2;
  const threadZ0 = -(RIDGE_TIP_FLAT / 2 + wallDepth * TAN_TOP + 0.25);
  // Last ridge's top flank must stay below the socket ceiling.
  const topRise = RIDGE_TIP_FLAT / 2 + dOs * TAN_TOP;
  const turns = Math.floor((depth - threadZ0 - topRise) / pitch);
  if (turns < 2)
    throw new Error(
      `Cap depth ${depth} mm only fits ${turns} thread turn(s) at pitch ` +
      `${pitch} mm — needs at least 2. Increase the depth or re-check the pitch.`);

  const skirtOD = bore + 2 * SOCKET_WALL;
  const shoulderZ = depth + (bore - THROAT_D) / 2;
  const tipZ = shoulderZ + DISPENSER_H;
  const couponH = threadZ0 + COUPON_TURNS * pitch + topRise + 0.3;
  const ribN = Math.max(12, Math.round((Math.PI * skirtOD) / 3.3));
  return { bore, tip, pitch, depth, threadZ0, topRise, turns,
           skirtOD, shoulderZ, tipZ, couponH, ribN };
}

// ── Geometry helpers ────────────────────────────────────────────────────────
function cyl(d, h, z = 0) {
  return replicad.drawCircle(d / 2).sketchOnPlane("XY", z).extrude(h);
}

// Truncated cone via a linear extrusion profile (avoids loft).
function cone(dBottom, dTop, h, z = 0) {
  return replicad
    .drawCircle(dBottom / 2)
    .sketchOnPlane("XY", z)
    .extrude(h, {
      extrusionProfile: { profile: "linear", endFactor: dTop / dBottom },
    });
}

// Closed 4-point profile wire in the XZ plane from [r, z] pairs, built
// from explicit 3D points so no plane-orientation convention can flip it.
function profileWire(ptsRZ) {
  const pts = ptsRZ.map(([r, z]) => [r, 0, z]);
  const edges = [];
  for (let i = 0; i < pts.length; i++) {
    edges.push(replicad.makeLine(pts[i], pts[(i + 1) % pts.length]));
  }
  return replicad.assembleWire(edges);
}

// Sweep a profile wire one-or-more whole turns along a helix. Whole-turn
// heights and frenet sweeps are the OCCT-reliable recipe (see the
// THREADS_README in the cadkit library this is ported from).
function helixSweep(ptsRZ, lead, height, rMid) {
  const spine = replicad.makeHelix(lead, height, rMid, [0, 0, 0], [0, 0, 1], false);
  return replicad.genericSweep(profileWire(ptsRZ), spine, {
    frenet: true,
    transitionMode: "transformed",
  });
}

// Asymmetric socket valley cutter (becomes the female ridge): 45° underside
// flank, gentle top flank. One whole-turn-multiple sweep based at z0.
function socketValleySweep(spec, z0, turns) {
  const rTip = spec.tip / 2;
  const rOs = spec.bore / 2 + OVERSHOOT;
  const dOs = rOs - rTip;
  const f = RIDGE_TIP_FLAT;
  const pts = [
    [rTip, -f / 2],
    [rOs, -f / 2 - dOs],          // 45° underside flank
    [rOs, f / 2 + dOs * TAN_TOP], // gentle top flank
    [rTip, f / 2],
  ];
  const h = Math.ceil(turns - 1e-6) * spec.pitch;
  const rMid = (rTip + spec.bore / 2) / 2;
  return helixSweep(pts, spec.pitch, h, rMid).translate([0, 0, z0]);
}

// Symmetric multi-start valley cutters (the nozzle↔cap thread). Mirrors
// cadkit.threads.multistart_valleys for the single-chunk case.
function multistartValleys(minorD, majorD, spacing, starts, length, z) {
  const lead = spacing * starts;
  const coreR = minorD / 2;
  const crestR = majorD / 2;
  const depth = crestR - coreR;
  const flat = (spacing - 2 * depth) / 2;
  const hwRoot = flat / 2;
  const hwOut = flat / 2 + depth + 0.3;
  const pts = [
    [coreR, -hwRoot],
    [crestR + 0.3, -hwOut],
    [crestR + 0.3, hwOut],
    [coreR, hwRoot],
  ];
  const h = Math.ceil(length / lead - 1e-6) * lead;
  const rMid = (coreR + crestR) / 2;
  const base = helixSweep(pts, lead, h, rMid);
  const out = [];
  for (let i = 0; i < starts; i++) {
    const phase = (360 * z) / lead + (360 * i) / starts;
    const seg = (i === starts - 1 ? base : base.clone());
    out.push(seg.rotate(phase, [0, 0, 0], [0, 0, 1]).translate([0, 0, z]));
  }
  return out;
}

// The complete bottle-socket cutter (mirror socket_cutter): smooth bore
// blank (+ optional 45° ceiling cone for a blind socket), thread cut last.
function socketCutter(spec, totalLen, { coneCeiling = false, turns = null } = {}) {
  const t = turns ?? spec.turns;
  const overHi = coneCeiling ? 0 : 0.5;
  let blank = cyl(spec.bore, totalLen + 0.5 + overHi, -0.5);
  if (coneCeiling) {
    blank = blank.fuse(cone(spec.bore, 0.2, (spec.bore - 0.2) / 2, totalLen));
  }
  return blank.cut(socketValleySweep(spec, spec.threadZ0, t));
}

// 2D circle ring: base circle fused with n rib circles on its rim —
// extruded once, body + grip ribs come out as a single solid.
function ribbedCircle(od, n) {
  let d = replicad.drawCircle(od / 2);
  const r = od / 2;
  for (let i = 0; i < n; i++) {
    const a = (2 * Math.PI * i) / n;
    d = d.fuse(
      replicad.drawCircle(GRIP_RIB_D / 2).translate(r * Math.cos(a), r * Math.sin(a))
    );
  }
  return d;
}

// ── Part builders (mirror nozzle.py / cap.py / thread_socket.py) ────────────
function buildNozzle(spec) {
  const shoulder = spec.shoulderZ;
  const coneZ0 = shoulder + COLLAR_LEN;

  // Smooth blank: ribbed skirt → collar → exterior cone. Flat bottoms
  // everywhere (bed adhesion); ribs run to the bed.
  let body = ribbedCircle(spec.skirtOD, spec.ribN)
    .sketchOnPlane("XY", 0)
    .extrude(shoulder);
  body = body.fuse(cyl(COLLAR_MAJOR_D, COLLAR_LEN, shoulder));
  body = body.fuse(cone(CONE_BASE_D, TIP_OD, spec.tipZ - coneZ0, coneZ0));

  // Continuous internal cone (throat → orifice) + orifice overshoot.
  body = body.cut(cone(THROAT_D, ORIFICE_D, spec.tipZ - shoulder, shoulder));
  body = body.cut(cyl(ORIFICE_D, 1.5, spec.tipZ - 0.5));

  // Threads LAST: half-turn collar valleys, then the bottle socket.
  for (const v of multistartValleys(
    COLLAR_MINOR_D, COLLAR_MAJOR_D, CAP_THREAD_SPACING, CAP_THREAD_STARTS,
    COLLAR_LEN, shoulder)) {
    body = body.cut(v);
  }
  body = body.cut(socketCutter(spec, spec.depth, { coneCeiling: true }));
  return body;
}

function buildCap() {
  // Exterior: ribbed boss → 45° blend → shell cone (cavity + CAP_WALL) →
  // top cone to a small flat. Stacked cone-extrudes, all flat-bottomed.
  let body = ribbedCircle(CAP_BOSS_OD, CAP_RIB_N)
    .sketchOnPlane("XY", 0)
    .extrude(BOSS_TOP);
  body = body.fuse(cone(CAP_BOSS_OD, 2 * JOIN_R, JOIN_Z - BOSS_TOP, BOSS_TOP));
  body = body.fuse(cone(2 * JOIN_R, 2 * SHELL_END_R, POCKET_Z0 - JOIN_Z, JOIN_Z));
  body = body.fuse(cone(2 * SHELL_END_R, CAP_TOP_FLAT_D, TOP_Z - POCKET_Z0, POCKET_Z0));

  // Smooth interior: 45° neck-down, cone-hugging cavity, 45° seal pocket.
  body = body.cut(cone(CAP_THREAD_MAJOR_D, CAVITY_D0, NECK_H, NECK_Z0));
  body = body.cut(cone(CAVITY_D0, POCKET_D0, POCKET_Z0 - CAVITY_Z0, CAVITY_Z0));
  body = body.cut(cone(POCKET_D0, POCKET_TIP_D, POCKET_H, POCKET_Z0));

  // Nut thread LAST (mirror multistart_rod, bevel=0): nominal-size crest
  // rod minus the two valley sweeps, overshot past the mouth.
  let rod = cyl(CAP_THREAD_MAJOR_D, CAP_NUT_H + NUT_OVER, -NUT_OVER);
  for (const v of multistartValleys(
    CAP_THREAD_MINOR_D, CAP_THREAD_MAJOR_D, CAP_THREAD_SPACING,
    CAP_THREAD_STARTS, CAP_NUT_H + NUT_OVER + 2 * CAP_THREAD_SPACING,
    -NUT_OVER - CAP_THREAD_SPACING)) {
    rod = rod.cut(v);
  }
  return body.cut(rod);
}

function buildCoupon(spec) {
  let body = cyl(spec.bore + 2 * SOCKET_WALL, spec.couponH);
  try {
    body = body.chamfer(0.6, (e) => e.inPlane("XY", spec.couponH));
  } catch (err) {
    console.warn("[coupon] top chamfer skipped:", err);
  }
  return body.cut(socketCutter(spec, spec.couponH, { turns: COUPON_TURNS }));
}

// ── Kernel boot ─────────────────────────────────────────────────────────────
let kernelReady = false;

async function bootKernel() {
  const OC = await opencascade({
    locateFile: (path) =>
      `https://cdn.jsdelivr.net/npm/replicad-opencascadejs@0.20.0/src/${path}`,
  });
  replicad.setOC(OC);
  kernelReady = true;
}

// ── 3D preview (three.js) ───────────────────────────────────────────────────
let scene, camera, renderer, controls;
const previewParts = { nozzle: [], cap: [], coupon: [] };

function initPreview() {
  const canvas = document.getElementById("preview");
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0d0d0d);
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  camera = new THREE.PerspectiveCamera(45, 1, 1, 5000);
  camera.up.set(0, 0, 1);
  scene.add(new THREE.AmbientLight(0xffffff, 0.55));
  const keyLight = new THREE.DirectionalLight(0xffffff, 0.7);
  keyLight.position.set(80, -120, 200);
  scene.add(keyLight);
  const fillLight = new THREE.DirectionalLight(0xffffff, 0.25);
  fillLight.position.set(-100, 80, 50);
  scene.add(fillLight);
  controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  camera.position.set(80, -120, 70);
  controls.target.set(0, 0, 30);
  resizePreview();
  window.addEventListener("resize", resizePreview);
  for (const partKey of Object.keys(previewParts)) {
    const cb = document.getElementById("show-" + partKey);
    if (!cb) continue;
    const handler = () => setPartVisibility(partKey, cb.checked);
    cb.addEventListener("change", handler);
    cb.addEventListener("input", handler);
  }
  (function animate() {
    controls.update();
    renderer.render(scene, camera);
    requestAnimationFrame(animate);
  })();
}

function resizePreview() {
  if (!renderer) return;
  const canvas = renderer.domElement;
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  if (w === 0 || h === 0) return;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}

function clearPreview() {
  for (const key of Object.keys(previewParts)) {
    for (const obj of previewParts[key]) {
      scene.remove(obj);
      obj.geometry?.dispose();
      obj.material?.dispose();
    }
    previewParts[key] = [];
  }
}

function addShapeToPreview(shape, color, partKey, offset = [0, 0, 0]) {
  const m = shape.mesh({ tolerance: 0.05, angularTolerance: 30 });
  const indices = m.triangles || m.indices;
  const geom = new THREE.BufferGeometry();
  geom.setAttribute("position",
    new THREE.BufferAttribute(new Float32Array(m.vertices), 3));
  if (m.normals) {
    geom.setAttribute("normal",
      new THREE.BufferAttribute(new Float32Array(m.normals), 3));
  }
  if (indices) geom.setIndex(new THREE.BufferAttribute(new Uint32Array(indices), 1));
  if (!m.normals) geom.computeVertexNormals();
  const mat = new THREE.MeshStandardMaterial({
    color, roughness: 0.55, metalness: 0.05,
  });
  const visible = isPartVisible(partKey);
  const mesh = new THREE.Mesh(geom, mat);
  mesh.position.set(...offset);
  mesh.visible = visible;
  scene.add(mesh);
  previewParts[partKey].push(mesh);
  try {
    const e = shape.meshEdges();
    if (e?.lines?.length) {
      const eGeom = new THREE.BufferGeometry();
      eGeom.setAttribute("position",
        new THREE.BufferAttribute(new Float32Array(e.lines), 3));
      const edges = new THREE.LineSegments(
        eGeom, new THREE.LineBasicMaterial({ color: 0x000000 }));
      edges.position.set(...offset);
      edges.visible = visible;
      scene.add(edges);
      previewParts[partKey].push(edges);
    }
  } catch (_) { /* edges unavailable on this replicad version */ }
}

function isPartVisible(partKey) {
  const cb = document.getElementById("show-" + partKey);
  return cb ? cb.checked : true;
}

function setPartVisibility(partKey, visible) {
  for (const obj of previewParts[partKey] || []) obj.visible = visible;
}

function fitCameraToScene() {
  const box = new THREE.Box3();
  for (const key of Object.keys(previewParts)) {
    for (const obj of previewParts[key]) if (obj.isMesh) box.expandByObject(obj);
  }
  if (box.isEmpty()) return;
  const center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());
  const dist = Math.max(size.x, size.y, size.z) * 1.6;
  camera.position.set(center.x + dist * 0.5, center.y - dist, center.z + dist * 0.4);
  controls.target.copy(center);
  controls.update();
}

// ── UI plumbing ─────────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);

function readParams() {
  return {
    threadOD: parseFloat($("threadOD").value),
    threadRootD: parseFloat($("threadRootD").value),
    pitch: parseFloat($("pitch").value),
    capDepth: parseFloat($("capDepth").value),
    clearance: parseFloat($("clearance").value),
  };
}

function setStatus(msg, kind = "info") {
  const el = $("status");
  el.textContent = msg;
  el.className = `status ${kind}`;
}

function clearDownloads() {
  $("downloads").innerHTML = "";
}

function addDownload(filename, blob) {
  const url = URL.createObjectURL(blob);
  const li = document.createElement("li");
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.textContent = filename;
  li.appendChild(a);
  $("downloads").appendChild(li);
}

async function generateAll() {
  if (!kernelReady) {
    setStatus("Still loading the CAD kernel — give it a sec.", "info");
    return;
  }
  const btn = $("generate");
  btn.disabled = true;
  btn.textContent = "Generating…";
  clearDownloads();
  clearPreview();

  try {
    const spec = deriveSpec(readParams());
    const format = $("format").value === "stl" ? "stl" : "step";
    const parts = [
      ["coupon", "superglue-test-coupon", () => buildCoupon(spec), 0x6b8aab,
       [spec.skirtOD + 18, 0, 0]],
      ["nozzle", "superglue-nozzle", () => buildNozzle(spec), 0xe0973c,
       [0, 0, 0]],
      ["cap", "superglue-cap", () => buildCap(), 0x6fae54,
       [0, 0, spec.tipZ + 10]],   // floated above the tip in the preview only
    ];
    for (const [partKey, baseName, build, color, offset] of parts) {
      const filename = `${baseName}.${format}`;
      setStatus(`Building ${filename}… (threads take a moment)`, "info");
      await new Promise((r) => setTimeout(r, 0));
      const shape = build();
      const blob = format === "stl" ? await shape.blobSTL() : await shape.blobSTEP();
      addDownload(filename, blob);
      addShapeToPreview(shape, color, partKey, offset);
    }
    fitCameraToScene();
    document.getElementById("preview-overlay")?.classList.add("hidden");
    setStatus(
      `Done. Socket: Ø${spec.bore.toFixed(1)} bore / Ø${spec.tip.toFixed(1)} ` +
      `ridge tips, ${spec.turns} turns at ${spec.pitch} mm pitch. ` +
      `Nozzle ${spec.tipZ.toFixed(1)} mm tall. Print the coupon first!`,
      "ok"
    );
  } catch (e) {
    console.error(e);
    setStatus("Error: " + e.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Generate files";
  }
}

// ── Boot ────────────────────────────────────────────────────────────────────
(async () => {
  initPreview();
  setStatus("Loading CAD kernel (~5 MB) — this only happens once.", "info");
  try {
    await bootKernel();
    setStatus("Ready. Measure your bottle and click Generate.", "ok");
    const btn = $("generate");
    btn.textContent = "Generate files";
    btn.disabled = false;
    btn.addEventListener("click", generateAll);
  } catch (e) {
    console.error(e);
    setStatus("Failed to load CAD kernel: " + e.message, "error");
  }
})();
