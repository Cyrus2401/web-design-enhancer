# Three.js — Best Practices pour UI Web

Guide de référence pour intégrer Three.js dans un projet web sans régresser en termes de performance, accessibilité ou maintenabilité.

---

## 1. Setup & Versioning

**Épingler la version CDN.** Ne jamais utiliser `@latest` — il casse silencieusement.

```html
<!-- ✅ Version épinglée -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>

<!-- ❌ Flottant — casse dès que cdnjs met à jour -->
<script src="https://unpkg.com/three@latest"></script>
```

**Un seul renderer par page.** Les navigateurs limitent à 8–16 contextes GPU.

```js
// ✅ Créé une fois, lifetime = page
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // Cap obligatoire

// ❌ Recréé à chaque appel — épuise les contextes GPU
function initScene() {
  const renderer = new THREE.WebGLRenderer(); // context leak
}
```

---

## 2. Pixel Ratio — Cap à 2

Retina 3x = 9 pixels par CSS pixel = coût GPU ×2.25 sans gain visible.

```js
// ✅ Toujours capé
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

// ❌ Nu — sur iPhone Pro Max : 3× = coût GPU inutile
renderer.setPixelRatio(window.devicePixelRatio);
```

---

## 3. Géométrie — Règles critiques

**Jamais dans `animate()`.** Chaque `new THREE.XxxGeometry()` dans la boucle = nouveau buffer GPU = VRAM exhausted en secondes.

```js
// ✅ Créé une fois avant la boucle
const geo = new THREE.SphereGeometry(1, 32, 32);
const mesh = new THREE.Mesh(geo, mat);
scene.add(mesh);

function animate() {
  requestAnimationFrame(animate);
  mesh.rotation.y += 0.01;       // ✅ Muter, pas recréer
  renderer.render(scene, camera);
}

// ❌ VRAM leak critique
function animate() {
  requestAnimationFrame(animate);
  const geo = new THREE.SphereGeometry(1, 32, 32); // nouveau buffer GPU chaque frame
}
```

**Budget segments.**

| Rôle | Segments |
| :--- | :--- |
| Hero foreground | 32–64 |
| Background / ambient | 8–16 |
| Particles stand-in | 6–8 |

**Partager la géométrie** entre meshes identiques.

```js
// ✅ Un buffer GPU pour 200 objets
const geo = new THREE.BoxGeometry(1, 1, 1);
for (let i = 0; i < 200; i++) {
  const m = new THREE.Mesh(geo, mat); // même géo, transforms différents
  scene.add(m);
}

// ❌ 200 buffers GPU identiques
for (let i = 0; i < 200; i++) {
  const geo = new THREE.BoxGeometry(1, 1, 1);
  scene.add(new THREE.Mesh(geo, mat));
}
```

**`CapsuleGeometry` n'existe pas en r128** (ajouté en r142).

```js
// ✅ Capsule construite à la main
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

**Partager les materials** identiques.

```js
// ✅ Une instance partagée
const mat = new THREE.MeshStandardMaterial({ color: 0x4f46e5, roughness: 0.4 });
meshA.material = mat;
meshB.material = mat;

// ❌ N instances inutiles
for (const m of meshes) {
  m.material = new THREE.MeshStandardMaterial({ color: 0x4f46e5 });
}
```

**`MeshBasicMaterial`** pour les éléments décoratifs plats — pas besoin de lights.

**Dispose explicite.** Three.js ne libère jamais la VRAM automatiquement.

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

## 5. Caméra

**Toujours `lookAt()` avant le premier render.**

```js
camera.position.set(0, 1.5, 5);
camera.lookAt(new THREE.Vector3(0, 0, 0)); // scène visible dès le premier frame
```

**Mettre à jour l'aspect sur resize.**

```js
window.addEventListener('resize', () => {
  camera.aspect = canvas.clientWidth / canvas.clientHeight;
  camera.updateProjectionMatrix();             // obligatoire après aspect change
  renderer.setSize(canvas.clientWidth, canvas.clientHeight);
});
```

**FOV :** 45–75°. En dessous = compression télé, au-dessus = fisheye.

---

## 6. Lighting

Minimum pour `MeshStandardMaterial` ou `MeshPhongMaterial` :

```js
scene.add(new THREE.AmbientLight(0xffffff, 0.4));  // fill
const key = new THREE.DirectionalLight(0xffffff, 1.0);
key.position.set(5, 10, 7.5);
scene.add(key);
```

Shadows — coûteux, activer sélectivement :

```js
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
key.castShadow = true;               // seulement la key light
heroMesh.castShadow = true;          // seulement le hero
ground.receiveShadow = true;
// particles, background meshes : pas de shadow
```

---

## 7. Raycasting

**Un seul `Raycaster` réutilisé.** Stocker les coords dans `pointermove`, caster dans `animate()`.

```js
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

canvas.addEventListener('pointermove', e => {
  // ✅ Seulement stocker — pas de raycasting ici
  mouse.x =  (e.clientX / canvas.clientWidth)  * 2 - 1;
  mouse.y = -(e.clientY / canvas.clientHeight) * 2 + 1; // Y inversé
});

function animate() {
  requestAnimationFrame(animate);
  raycaster.setFromCamera(mouse, camera);          // update ray
  const hits = raycaster.intersectObjects(targets, true); // recursive pour Groups
  document.body.style.cursor = hits.length > 0 ? 'pointer' : 'auto';
  renderer.render(scene, camera);
}
```

---

## 8. GSAP + Three.js (Scroll-Driven)

La règle ≤ 400ms du DESIGN.md s'applique aux **transitions UI**, pas aux animations Three.js scroll-driven.

```js
// ✅ Caméra scroll-driven — pas une transition UI
gsap.to(camera.position, {
  z: 2,
  scrollTrigger: { trigger: '.scene', scrub: 1 }
});

// ✅ UI transition — s'applique la règle 400ms
gsap.to('.overlay', { opacity: 0, duration: 0.3 });
```

**OrbitControls vs GSAP rig :**
- `OrbitControls` → model viewer, exploration libre
- GSAP scroll rig → product reveal, storytelling scripted

---

## 9. prefers-reduced-motion

```js
const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

function animate() {
  requestAnimationFrame(animate);
  if (!prefersReduced) {
    mesh.rotation.y += clock.getDelta() * 0.8; // animation normale
  }
  // renderer toujours actif — la scène est visible mais figée
  renderer.render(scene, camera);
}
```

---

## 10. Accessibilité WebGL

```html
<!-- Canvas avec rôle et label -->
<canvas id="three-canvas"
        role="img"
        aria-label="Visualisation 3D de l'infrastructure réseau"
        aria-describedby="three-desc">
</canvas>
<p id="three-desc" class="sr-only">
  Schéma interactif des nœuds réseau. Survoler pour explorer.
</p>
```

---

## 11. Fallback WebGL

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

## Antipatterns détectés automatiquement par `detect_ai_slop.py`

| Pattern | Sévérité | Règle |
| :--- | :--- | :--- |
| `new THREE.XxxGeometry()` dans `animate()` | Critique | VRAM leak |
| `setPixelRatio(window.devicePixelRatio)` nu | Haute | Cap à 2 obligatoire |
| `new THREE.WebGLRenderer()` dans une fonction | Haute | GPU context leak |
| `new THREE.Raycaster()` dans `mousemove` | Haute | 200+ allocations/sec |
| Material recréé dans une boucle | Haute | Partager les instances |
| `THREE.CapsuleGeometry` (r128) | Critique | N'existe pas avant r142 |
| `scene.remove()` sans `dispose()` | Haute | VRAM leak permanent |
| SphereGeometry 128+ segments | Moyenne | Budget excessif |
| `castShadow` en boucle sur tous les objets | Haute | Double pass GPU |
| CDN `@latest` non versionné | Critique | Casse silencieux |
| `PerspectiveCamera` sans `lookAt()` | Moyenne | Scène potentiellement vide |
