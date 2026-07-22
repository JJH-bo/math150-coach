const specification = JSON.parse(document.getElementById("scene-spec").textContent);
const mount = document.getElementById("scene-mount");
const azimuthInput = document.getElementById("camera-azimuth");
const elevationInput = document.getElementById("camera-elevation");
const azimuthOutput = document.getElementById("camera-azimuth-value");
const elevationOutput = document.getElementById("camera-elevation-value");
const scene = new THREE.Scene();
scene.background = new THREE.Color(specification.theme === "dark" ? 0x101923 : 0xffffff);
const camera = new THREE.PerspectiveCamera(38, 1, 0.05, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true;
mount.append(renderer.domElement);

const mapPoint = ([x, y, z]) => new THREE.Vector3(x, z, -y);
const target = mapPoint(specification.camera.target);
let azimuth = specification.camera.azimuth;
let elevation = specification.camera.elevation;

scene.add(new THREE.HemisphereLight(0xddeeff, 0x263242, 2.2));
const keyLight = new THREE.DirectionalLight(0xffffff, 2.8);
keyLight.position.set(5, 8, 5);
keyLight.castShadow = true;
scene.add(keyLight);
const rimLight = new THREE.DirectionalLight(0x33c3ff, 1.5);
rimLight.position.set(-5, 3, -5);
scene.add(rimLight);

const grid = new THREE.GridHelper(10, 20, 0x60758c, 0x273545);
grid.material.transparent = true;
grid.material.opacity = 0.65;
scene.add(grid);

function axis(direction, color) {
  scene.add(new THREE.ArrowHelper(mapPoint(direction).normalize(), mapPoint([0, 0, 0]), 4.6, color, 0.28, 0.16));
}
axis([1, 0, 0], 0xff6b8a);
axis([0, 1, 0], 0x68d391);
axis([0, 0, 1], 0x33c3ff);

function surfaceObject(object) {
  const geometry = new THREE.BufferGeometry();
  const positions = [];
  for (let row = 0; row < object.y.length; row += 1) {
    for (let column = 0; column < object.x.length; column += 1) {
      const point = mapPoint([object.x[column], object.y[row], object.z[row][column]]);
      positions.push(point.x, point.y, point.z);
    }
  }
  const indices = [];
  const columns = object.x.length;
  for (let row = 0; row < object.y.length - 1; row += 1) {
    for (let column = 0; column < columns - 1; column += 1) {
      const a = row * columns + column;
      const b = a + 1;
      const c = a + columns;
      const d = c + 1;
      indices.push(a, c, b, b, c, d);
    }
  }
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  const material = new THREE.MeshStandardMaterial({
    color: object.color,
    roughness: 0.48,
    metalness: 0.08,
    side: THREE.DoubleSide,
    transparent: object.opacity < 1,
    opacity: object.opacity,
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.receiveShadow = true;
  mesh.castShadow = true;
  return mesh;
}

function vectorObject(object) {
  const origin = mapPoint(object.origin);
  const direction = mapPoint(object.direction);
  const length = direction.length();
  return new THREE.ArrowHelper(direction.normalize(), origin, length, object.color, Math.min(0.35, length * 0.18), Math.min(0.22, length * 0.1));
}

function pointObject(object) {
  const geometry = new THREE.SphereGeometry(object.size, 32, 20);
  const material = new THREE.MeshStandardMaterial({ color: object.color, roughness: 0.3 });
  const sphere = new THREE.Mesh(geometry, material);
  sphere.position.copy(mapPoint(object.position));
  sphere.castShadow = true;
  return sphere;
}

const renderedObjects = [];
for (const object of specification.objects) {
  const rendered = object.type === "surface" ? surfaceObject(object) : object.type === "vector" ? vectorObject(object) : pointObject(object);
  rendered.userData = { objectId: object.id, label: object.label };
  scene.add(rendered);
  renderedObjects.push(rendered);
  const item = document.createElement("li");
  item.innerHTML = `<span style="background:${object.color}"></span>${object.label}`;
  document.getElementById("scene-legend").append(item);
}

function positionCamera() {
  const azimuthRadians = THREE.MathUtils.degToRad(azimuth);
  const elevationRadians = THREE.MathUtils.degToRad(elevation);
  const horizontal = specification.camera.distance * Math.cos(elevationRadians);
  camera.position.set(
    target.x + horizontal * Math.cos(azimuthRadians),
    target.y + specification.camera.distance * Math.sin(elevationRadians),
    target.z + horizontal * Math.sin(azimuthRadians),
  );
  camera.lookAt(target);
  azimuthOutput.textContent = `${azimuth}°`;
  elevationOutput.textContent = `${elevation}°`;
}

function resize() {
  const bounds = mount.getBoundingClientRect();
  renderer.setSize(Math.max(1, Math.round(bounds.width)), Math.max(1, Math.round(bounds.height)), false);
  camera.aspect = bounds.width / Math.max(bounds.height, 1);
  camera.updateProjectionMatrix();
}

function render() {
  positionCamera();
  resize();
  renderer.render(scene, camera);
}

azimuthInput.addEventListener("input", () => {
  azimuth = Number(azimuthInput.value);
  render();
});
elevationInput.addEventListener("input", () => {
  elevation = Number(elevationInput.value);
  render();
});
window.addEventListener("resize", render);
render();
requestAnimationFrame(() => {
  render();
  const gl = renderer.getContext();
  const debug = gl.getExtension("WEBGL_debug_renderer_info");
  window.sceneStudio = {
    ready: true,
    snapshot: () => JSON.stringify({ azimuth, elevation, camera: camera.position.toArray() }),
    setAzimuth: (value) => {
      azimuthInput.value = String(value);
      azimuthInput.dispatchEvent(new Event("input", { bubbles: true }));
    },
    restore: () => {
      azimuth = specification.camera.azimuth;
      elevation = specification.camera.elevation;
      azimuthInput.value = String(azimuth);
      elevationInput.value = String(elevation);
      render();
    },
    report: () => ({
      renderedObjectCount: renderedObjects.length,
      triangles: renderer.info.render.triangles,
      calls: renderer.info.render.calls,
      webglRenderer: debug ? gl.getParameter(debug.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER),
      ...(() => {
        const bounds = new THREE.Box3();
        for (const object of renderedObjects) bounds.expandByObject(object);
        const corners = [];
        for (const x of [bounds.min.x, bounds.max.x]) {
          for (const y of [bounds.min.y, bounds.max.y]) {
            for (const z of [bounds.min.z, bounds.max.z]) {
              corners.push(new THREE.Vector3(x, y, z).project(camera));
            }
          }
        }
        const projectedBounds = {
          min_x: Math.min(...corners.map((point) => point.x)),
          max_x: Math.max(...corners.map((point) => point.x)),
          min_y: Math.min(...corners.map((point) => point.y)),
          max_y: Math.max(...corners.map((point) => point.y)),
          min_z: Math.min(...corners.map((point) => point.z)),
          max_z: Math.max(...corners.map((point) => point.z)),
        };
        return {
          projectedBounds,
          frustumClipped:
            projectedBounds.min_x < -0.98 || projectedBounds.max_x > 0.98 ||
            projectedBounds.min_y < -0.98 || projectedBounds.max_y > 0.98 ||
            projectedBounds.min_z < -1 || projectedBounds.max_z > 1,
        };
      })(),
    }),
  };
});
