# Three.js — Best Practices for Web UI

Reference guide for integrating Three.js into a web project without regressing in performance, accessibility, or maintainability.

---

## 1. Setup & Versioning

**Pin the CDN version.** Never use `@latest` — it breaks silently.

```html
<!-- ✅ Pinned version -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>

<!-- ❌ Floating — breaks as soon as cdnjs updates -->
<script src="https://unpkg.com/three@latest"></script>
```

**One renderer per page.** Browsers limit you to 8–16 GPU contexts.

```js
// ✅ Created once, lifetime = page
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // Mandatory cap

// ❌ Recreated on every call — exhausts GPU contexts
function initScene() {
  const renderer = new THREE.WebGLRenderer(); // context leak
}
```

---

## 2. Pixel Ratio — Cap at 2

Retina 3x = 9 pixels per CSS pixel = 2.25× GPU cost with no visible gain.

```js
// ✅ Always capped
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

// ❌ Bare — on iPhone Pro Max: 3× = wasted GPU cost
renderer.setPixelRatio(window.devicePixelRatio);
```

---

## 3. Geometry — Critical Rules

**Never inside `animate()`.** Each `new THREE.XxxGeometry()` in the loop = a new GPU buffer = VRAM exhausted in seconds.

```js
// ✅ Created once before the loop
const geo = new THREE.SphereGeometry(1, 32, 32);
const mesh = new THREE.Mesh(geo, mat);
scene.add(mesh);

function animate() {
  requestAnimationFrame(animate);
  mesh.rotation.y += 0.01;       // ✅ Mutate, don't recreate
  renderer.render(scene, camera);
}

// ❌ Critical VRAM leak
function animate() {
  requestAnimationFrame(animate);
  const geo = new THREE.SphereGeometry(1, 32, 32); // new GPU buffer every frame
}
```

**Segment budget.**

| Role | Segments |
| :--- | :--- |
| Hero foreground | 32–64 |
| Background / ambient | 8–16 |
| Particles stand-in | 6–8 |

**Share geometry** across identical meshes.

```js
// ✅ One GPU buffer for 200 objects
const geo = new THREE.BoxGeometry(1, 1, 1);
for (let i = 0; i < 200; i++) {
  const m = new THREE.Mesh(geo, mat); // same geo, different transforms
  scene.add(m);
}

// ❌ 200 identical GPU buffers
for (let i = 0; i < 200; i++) {
  const geo = new THREE.BoxGeometry(1, 1, 1);
  scene.add(new THREE.Mesh(geo, mat));
}
```

**`CapsuleGeometry` does not exist in r128** (added in r142).

```js
// ✅ Capsule built by hand
const body = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 1, 16), mat);
const top  = new THREE.Mesh(new THREE.SphereGeometry(0.5, 16, 8), mat);
const bot  = new THREE.Mesh(new THREE.SphereGeometry(0.5, 16, 8), mat);
top.position.y = 0.5; bot.position.y = -0.5;
const capsule = new THREE.Group();
capsule.add(body, top, bot);

// ❌ TypeError: CapsuleGeometry is not a constructor (r128)
const cap = new THREE.CapsuleGeometry(0.5, 1, 4, 8);
```

---

## 4. Materials & Textures

**Share identical materials.**

```js
// ✅ One shared instance
const mat = new THREE.MeshStandardMaterial({ color: 0x4f46e5, roughness: 0.4 });
meshA.material = mat;
meshB.material = mat;

// ❌ N unnecessary instances
for (const m of meshes) {
  m.material = new THREE.MeshStandardMaterial({ color: 0x4f46e5 });
}
```

**`MeshBasicMaterial`** for flat decorative elements — no lights needed.

**Explicit dispose.** Three.js never releases VRAM automatically.

```js
function removeMesh(mesh) {
  scene.remove(mesh);
  mesh.geometry.dispose();
  mesh.material.dispose();
  if (mesh.material.map)       mesh.material.map.dispose();
  if (mesh.material.normalMap) mesh.material.normalMap.dispose();
  if (mesh.material.envMap)    mesh.material.envMap.dispose();
}
```

---

## 5. Camera

**Always `lookAt()` before the first render.**

```js
camera.position.set(0, 1.5, 5);
camera.lookAt(new THREE.Vector3(0, 0, 0)); // scene visible from the first frame
```

**Update aspect on resize.**

```js
window.addEventListener('resize', () => {
  camera.aspect = canvas.clientWidth / canvas.clientHeight;
  camera.updateProjectionMatrix();             // mandatory after aspect change
  renderer.setSize(canvas.clientWidth, canvas.clientHeight);
});
```

**FOV:** 45–75°. Below = telephoto compression, above = fisheye.

---

## 6. Lighting

Minimum for `MeshStandardMaterial` or `MeshPhongMaterial`:

```js
scene.add(new THREE.AmbientLight(0xffffff, 0.4));  // fill
const key = new THREE.DirectionalLight(0xffffff, 1.0);
key.position.set(5, 10, 7.5);
scene.add(key);
```

Shadows — expensive, enable selectively:

```js
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
key.castShadow = true;               // only the key light
heroMesh.castShadow = true;          // only the hero
ground.receiveShadow = true;
// particles, background meshes: no shadow
```

---

## 7. Raycasting

**One reusable `Raycaster`.** Store coords in `pointermove`, cast inside `animate()`.

```js
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

canvas.addEventListener('pointermove', e => {
  // ✅ Only store — no raycasting here
  mouse.x =  (e.clientX / canvas.clientWidth)  * 2 - 1;
  mouse.y = -(e.clientY / canvas.clientHeight) * 2 + 1; // Y inverted
});

function animate() {
  requestAnimationFrame(animate);
  raycaster.setFromCamera(mouse, camera);          // update ray
  const hits = raycaster.intersectObjects(targets, true); // recursive for Groups
  document.body.style.cursor = hits.length > 0 ? 'pointer' : 'auto';
  renderer.render(scene, camera);
}
```

---

## 8. GSAP + Three.js (Scroll-Driven)

The ≤ 400ms rule from DESIGN.md applies to **UI transitions**, not to scroll-driven Three.js animations.

```js
// ✅ Scroll-driven camera — not a UI transition
gsap.to(camera.position, {
  z: 2,
  scrollTrigger: { trigger: '.scene', scrub: 1 }
});

// ✅ UI transition — the 400ms rule applies
gsap.to('.overlay', { opacity: 0, duration: 0.3 });
```

**OrbitControls vs GSAP rig:**
- `OrbitControls` → model viewer, free exploration
- GSAP scroll rig → product reveal, scripted storytelling

---

## 9. prefers-reduced-motion

```js
const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

function animate() {
  requestAnimationFrame(animate);
  if (!prefersReduced) {
    mesh.rotation.y += clock.getDelta() * 0.8; // normal animation
  }
  // renderer still active — the scene is visible but frozen
  renderer.render(scene, camera);
}
```

---

## 10. WebGL Accessibility

```html
<!-- Canvas with role and label -->
<canvas id="three-canvas"
        role="img"
        aria-label="3D visualization of the network infrastructure"
        aria-describedby="three-desc">
</canvas>
<p id="three-desc" class="sr-only">
  Interactive diagram of network nodes. Hover to explore.
</p>
```

---

## 11. WebGL Fallback

```js
function hasWebGL() {
  try {
    const c = document.createElement('canvas');
    return !!(c.getContext('webgl2') || c.getContext('webgl'));
  } catch { return false; }
}

if (!hasWebGL()) {
  document.getElementById('three-canvas').style.display = 'none';
  document.getElementById('static-fallback').style.display = 'block';
}
```

---

## Antipatterns automatically detected by `detect_ai_slop.py`

| Pattern | Severity | Rule |
| :--- | :--- | :--- |
| `new THREE.XxxGeometry()` inside `animate()` | Critical | VRAM leak |
| Bare `setPixelRatio(window.devicePixelRatio)` | High | Cap at 2 mandatory |
| `new THREE.WebGLRenderer()` inside a function | High | GPU context leak |
| `new THREE.Raycaster()` inside `mousemove` | High | 200+ allocations/sec |
| Material recreated inside a loop | High | Share instances |
| `THREE.CapsuleGeometry` (r128) | Critical | Does not exist before r142 |
| `scene.remove()` without `dispose()` | High | Permanent VRAM leak |
| SphereGeometry 128+ segments | Medium | Excessive budget |
| `castShadow` looped over every object | High | Double GPU pass |
| Unversioned `@latest` CDN | Critical | Silent breakage |
| `PerspectiveCamera` without `lookAt()` | Medium | Scene potentially empty |
