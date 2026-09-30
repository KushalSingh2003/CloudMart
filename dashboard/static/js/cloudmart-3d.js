document.addEventListener("DOMContentLoaded", function () {

    const container = document.getElementById("cloudmart3D");

    if (!container || typeof THREE === "undefined") {
        return;
    }

    const reduceMotion =
        window.matchMedia &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;


    // =====================================================
    // ARCHITECTURE DEFINITION
    // Same 7 services and 7 connections as the original scene.
    // Only the layout (left -> right request flow) is new.
    // =====================================================

    const SERVICES = [
        { id: "api",         name: "API Gateway",    tag: "API",           icon: "api",      color: "#8b6cff", pos: [-9,    0,   0] },
        { id: "product",     name: "Product Lambda", tag: "Compute",       icon: "lambda",   color: "#ff8a3d", pos: [-4.5,  2.2, 0] },
        { id: "order",       name: "Order Lambda",   tag: "Compute",       icon: "lambda",   color: "#ff8a3d", pos: [-4.5, -2.2, 0] },
        { id: "rds",         name: "RDS MySQL",      tag: "Database",      icon: "database", color: "#4c7dff", pos: [ 0,    0,   0] },
        { id: "eventbridge", name: "EventBridge",    tag: "Events",        icon: "events",   color: "#b45cff", pos: [ 4.5,  2.2, 0] },
        { id: "s3",          name: "S3 Reports",     tag: "Storage",       icon: "bucket",   color: "#22b8e8", pos: [ 4.5, -2.2, 0] },
        { id: "sns",         name: "SNS",            tag: "Notifications", icon: "bell",     color: "#e9569c", pos: [ 9,    2.2, 0] }
    ];

    // [from, to] — direction matches the original connectNodes() calls
    const CONNECTIONS = [
        ["api", "product"],
        ["api", "order"],
        ["product", "rds"],
        ["order", "rds"],
        ["rds", "eventbridge"],
        ["rds", "s3"],
        ["eventbridge", "sns"]
    ];

    const SLAB = 2.0;           // node size
    const HALF_W = 10.9;        // scene half-width used to fit camera
    const HALF_H = 4.5;         // scene half-height used to fit camera
    const LOOK_Y = 0.2;
    const FLOOR_Y = -3.45;

    const FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif";


    // =====================================================
    // RENDERER / SCENE / CAMERA
    // =====================================================

    let renderer;

    try {
        renderer = new THREE.WebGLRenderer({
            antialias: true,
            alpha: true,
            powerPreference: "high-performance"
        });
    } catch (e) {
        return;
    }

    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.domElement.style.touchAction = "pan-y";
    renderer.domElement.style.cursor = "grab";
    container.appendChild(renderer.domElement);

    // Transparent scene: the existing dark gradient on .cloudmart-3d shows through
    const scene = new THREE.Scene();
    scene.fog = new THREE.Fog(0x14132b, 22, 46);

    const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 200);

    const architecture = new THREE.Group();
    scene.add(architecture);


    // =====================================================
    // LIGHTING
    // =====================================================

    scene.add(new THREE.HemisphereLight(0xc9c2ff, 0x1a1838, 1.0));

    const keyLight = new THREE.DirectionalLight(0xffffff, 2.2);
    keyLight.position.set(4, 11, 9);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.set(1024, 1024);
    keyLight.shadow.camera.left = -16;
    keyLight.shadow.camera.right = 16;
    keyLight.shadow.camera.top = 10;
    keyLight.shadow.camera.bottom = -10;
    keyLight.shadow.bias = -0.0005;
    keyLight.shadow.radius = 4;
    scene.add(keyLight);

    const rimCyan = new THREE.PointLight(0x22b8e8, 60, 34, 2);
    rimCyan.position.set(-11, 4, 5);
    scene.add(rimCyan);

    const rimOrange = new THREE.PointLight(0xff8a3d, 50, 34, 2);
    rimOrange.position.set(11, -2, 6);
    scene.add(rimOrange);


    // =====================================================
    // HELPERS
    // =====================================================

    function roundedRectPath(ctx, x, y, w, h, r) {
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.arcTo(x + w, y, x + w, y + h, r);
        ctx.arcTo(x + w, y + h, x, y + h, r);
        ctx.arcTo(x, y + h, x, y, r);
        ctx.arcTo(x, y, x + w, y, r);
        ctx.closePath();
    }

    function shade(hex, amount) {
        const c = new THREE.Color(hex);
        const target = amount >= 0 ? 1 : 0;
        const t = Math.abs(amount);
        c.r += (target - c.r) * t;
        c.g += (target - c.g) * t;
        c.b += (target - c.b) * t;
        return "#" + c.getHexString();
    }

    function makeTexture(canvas) {
        const texture = new THREE.CanvasTexture(canvas);
        texture.colorSpace = THREE.SRGBColorSpace;
        texture.anisotropy = renderer.capabilities.getMaxAnisotropy();
        texture.needsUpdate = true;
        return texture;
    }

    // Soft radial glow used for particles and node halos
    const glowTexture = (function () {
        const c = document.createElement("canvas");
        c.width = c.height = 128;
        const g = c.getContext("2d");
        const grad = g.createRadialGradient(64, 64, 0, 64, 64, 64);
        grad.addColorStop(0, "rgba(255,255,255,1)");
        grad.addColorStop(0.25, "rgba(255,255,255,0.55)");
        grad.addColorStop(1, "rgba(255,255,255,0)");
        g.fillStyle = grad;
        g.fillRect(0, 0, 128, 128);
        return makeTexture(c);
    })();


    // =====================================================
    // SERVICE ICONS (drawn on a 256 x 256 grid)
    // =====================================================

    const ICONS = {

        api: function (g) {
            g.beginPath();
            g.moveTo(92, 78); g.lineTo(46, 128); g.lineTo(92, 178);
            g.moveTo(164, 78); g.lineTo(210, 128); g.lineTo(164, 178);
            g.moveTo(141, 66); g.lineTo(115, 190);
            g.stroke();
        },

        lambda: function (g) {
            g.beginPath();
            g.moveTo(84, 58); g.lineTo(122, 58);
            g.lineTo(178, 198);
            g.moveTo(138, 118); g.lineTo(80, 198);
            g.stroke();
        },

        database: function (g) {
            g.beginPath();
            g.ellipse(128, 82, 60, 20, 0, 0, Math.PI * 2);
            g.moveTo(68, 82); g.lineTo(68, 174);
            g.ellipse(128, 174, 60, 20, 0, Math.PI, 0, true);
            g.lineTo(188, 82);
            g.moveTo(68, 128);
            g.ellipse(128, 128, 60, 20, 0, Math.PI, 0, true);
            g.stroke();
        },

        events: function (g) {
            const nodes = [[64, 68], [192, 68], [128, 200]];
            g.beginPath();
            nodes.forEach(function (n) {
                g.moveTo(128, 128); g.lineTo(n[0], n[1]);
            });
            g.stroke();
            nodes.forEach(function (n) {
                g.beginPath(); g.arc(n[0], n[1], 17, 0, Math.PI * 2);
                g.fillStyle = "rgba(255,255,255,0.18)"; g.fill(); g.stroke();
            });
            g.beginPath(); g.arc(128, 128, 26, 0, Math.PI * 2);
            g.fillStyle = "#ffffff"; g.fill();
        },

        bucket: function (g) {
            g.beginPath();
            g.ellipse(128, 84, 64, 20, 0, 0, Math.PI * 2);
            g.moveTo(64, 84); g.lineTo(84, 192);
            g.ellipse(128, 192, 44, 14, 0, Math.PI, 0, true);
            g.lineTo(192, 84);
            g.stroke();
        },

        bell: function (g) {
            g.beginPath();
            g.moveTo(66, 172);
            g.quadraticCurveTo(90, 160, 90, 112);
            g.bezierCurveTo(90, 60, 166, 60, 166, 112);
            g.quadraticCurveTo(166, 160, 190, 172);
            g.closePath();
            g.moveTo(128, 60); g.lineTo(128, 48);
            g.stroke();
            g.beginPath();
            g.arc(128, 190, 14, 0, Math.PI);
            g.stroke();
        }
    };

    function createFaceTexture(svc) {
        const canvas = document.createElement("canvas");
        canvas.width = canvas.height = 512;
        const g = canvas.getContext("2d");
        g.scale(2, 2);

        // gradient tile
        const grad = g.createLinearGradient(0, 0, 256, 256);
        grad.addColorStop(0, shade(svc.color, 0.22));
        grad.addColorStop(1, shade(svc.color, -0.38));
        roundedRectPath(g, 6, 6, 244, 244, 46);
        g.fillStyle = grad;
        g.fill();

        // soft top sheen
        const sheen = g.createLinearGradient(0, 0, 0, 140);
        sheen.addColorStop(0, "rgba(255,255,255,0.20)");
        sheen.addColorStop(1, "rgba(255,255,255,0)");
        roundedRectPath(g, 6, 6, 244, 244, 46);
        g.fillStyle = sheen;
        g.fill();

        // glyph
        g.strokeStyle = "#ffffff";
        g.lineWidth = 12;
        g.lineCap = "round";
        g.lineJoin = "round";
        ICONS[svc.icon](g);

        return makeTexture(canvas);
    }


    // =====================================================
    // LABELS (crisp canvas sprites, sized to their text)
    // =====================================================

    const WORLD_PER_PX = 0.34 / 60;

    function createLabelTexture(name, tag, color) {
        const measure = document.createElement("canvas").getContext("2d");
        measure.font = "600 60px " + FONT;
        const nameW = measure.measureText(name).width;
        measure.font = "500 34px " + FONT;
        const tagW = measure.measureText(tag.toUpperCase()).width + tag.length * 3;

        const w = Math.ceil(Math.max(nameW, tagW) + 130);
        const h = 190;

        const canvas = document.createElement("canvas");
        canvas.width = w;
        canvas.height = h;
        const g = canvas.getContext("2d");

        roundedRectPath(g, 6, 18, w - 12, h - 36, 34);
        g.fillStyle = "rgba(20, 19, 43, 0.90)";
        g.fill();
        g.lineWidth = 2;
        g.strokeStyle = "rgba(255,255,255,0.14)";
        g.stroke();

        // accent dot
        g.beginPath();
        g.arc(44, h / 2, 9, 0, Math.PI * 2);
        g.fillStyle = color;
        g.fill();

        g.textAlign = "center";
        g.textBaseline = "alphabetic";
        const cx = (w + 30) / 2;

        g.fillStyle = "#ffffff";
        g.font = "600 60px " + FONT;
        g.fillText(name, cx, 92);

        g.fillStyle = "#a9a5cc";
        g.font = "500 34px " + FONT;
        if (g.letterSpacing !== undefined) { g.letterSpacing = "3px"; }
        g.fillText(tag.toUpperCase(), cx, 138);

        return { texture: makeTexture(canvas), w: w, h: h };
    }

    function createLabel(svc, x, y, z) {
        const t = createLabelTexture(svc.name, svc.tag, svc.color);
        const sprite = new THREE.Sprite(new THREE.SpriteMaterial({
            map: t.texture,
            transparent: true,
            opacity: 0.9,
            depthTest: false
        }));
        sprite.scale.set(t.w * WORLD_PER_PX, t.h * WORLD_PER_PX, 1);
        sprite.position.set(x, y, z);
        sprite.renderOrder = 10;
        architecture.add(sprite);
        return { sprite: sprite, baseScale: sprite.scale.clone() };
    }

    (function createTitle() {
        const canvas = document.createElement("canvas");
        canvas.width = 700;
        canvas.height = 150;
        const g = canvas.getContext("2d");
        g.fillStyle = "#ffffff";
        g.font = "700 60px " + FONT;
        g.textAlign = "center";
        g.textBaseline = "middle";
        g.fillText("CloudMart", 350, 75);

        const title = new THREE.Sprite(new THREE.SpriteMaterial({
            map: makeTexture(canvas),
            transparent: true,
            opacity: 0.95,
            depthTest: false
        }));
        title.position.set(0, 4.15, 0);
        title.scale.set(3.6, 0.77, 1);
        title.renderOrder = 10;
        architecture.add(title);
    })();


    // =====================================================
    // FLOOR (shadow catcher + fading grid for depth)
    // =====================================================

    (function createFloor() {
        const floor = new THREE.Mesh(
            new THREE.PlaneGeometry(60, 40),
            new THREE.ShadowMaterial({ opacity: 0.32 })
        );
        floor.rotation.x = -Math.PI / 2;
        floor.position.y = FLOOR_Y;
        floor.receiveShadow = true;
        architecture.add(floor);

        const grid = new THREE.GridHelper(44, 44, 0x3d3878, 0x2b2860);
        grid.position.y = FLOOR_Y + 0.01;
        grid.material.transparent = true;
        grid.material.opacity = 0.32;
        architecture.add(grid);
    })();


    // =====================================================
    // NODES
    // =====================================================

    const nodes = {};
    const pickables = [];

    function createSlabGeometry() {
        const r = 0.34;
        const s = SLAB / 2;
        const shape = new THREE.Shape();
        shape.moveTo(-s + r, -s);
        shape.lineTo(s - r, -s);
        shape.quadraticCurveTo(s, -s, s, -s + r);
        shape.lineTo(s, s - r);
        shape.quadraticCurveTo(s, s, s - r, s);
        shape.lineTo(-s + r, s);
        shape.quadraticCurveTo(-s, s, -s, s - r);
        shape.lineTo(-s, -s + r);
        shape.quadraticCurveTo(-s, -s, -s + r, -s);

        const geo = new THREE.ExtrudeGeometry(shape, {
            depth: 0.34,
            bevelEnabled: true,
            bevelSize: 0.05,
            bevelThickness: 0.05,
            bevelSegments: 4,
            curveSegments: 10
        });
        geo.center();
        return geo;
    }

    const slabGeometry = createSlabGeometry();
    const faceGeometry = new THREE.PlaneGeometry(SLAB * 0.86, SLAB * 0.86);
    const FACE_Z = 0.17 + 0.05 + 0.006;

    SERVICES.forEach(function (svc) {

        const accent = new THREE.Color(svc.color);
        const group = new THREE.Group();
        group.position.set(svc.pos[0], svc.pos[1], svc.pos[2]);
        architecture.add(group);

        // halo behind the node
        const halo = new THREE.Sprite(new THREE.SpriteMaterial({
            map: glowTexture,
            color: accent,
            transparent: true,
            opacity: 0.28,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        }));
        halo.scale.set(4.2, 4.2, 1);
        halo.position.z = -0.45;
        group.add(halo);

        // body
        const bodyMaterial = new THREE.MeshStandardMaterial({
            color: 0x2a2660,
            roughness: 0.38,
            metalness: 0.35,
            emissive: accent,
            emissiveIntensity: 0.05
        });
        const body = new THREE.Mesh(slabGeometry, bodyMaterial);
        body.castShadow = true;
        group.add(body);

        // icon face
        const faceTexture = createFaceTexture(svc);
        const faceMaterial = new THREE.MeshStandardMaterial({
            map: faceTexture,
            transparent: true,
            roughness: 0.45,
            metalness: 0.05,
            emissive: 0xffffff,
            emissiveMap: faceTexture,
            emissiveIntensity: 0.32
        });
        const face = new THREE.Mesh(faceGeometry, faceMaterial);
        face.position.z = FACE_Z;
        group.add(face);

        const label = createLabel(
            svc,
            svc.pos[0],
            svc.pos[1] - SLAB / 2 - 0.55,
            svc.pos[2]
        );

        const node = {
            svc: svc,
            group: group,
            base: group.position.clone(),
            halo: halo,
            body: body,
            face: face,
            label: label,
            hover: 0,
            seed: Math.random() * Math.PI * 2
        };

        body.userData.node = node;
        face.userData.node = node;
        pickables.push(body, face);
        nodes[svc.id] = node;
    });


    // =====================================================
    // CONNECTIONS + DATA FLOW
    // =====================================================

    const EDGE_BASE = new THREE.Color(0x6a62c4);
    const EDGE_HOT = new THREE.Color(0x22b8e8);
    const DOT_BASE = new THREE.Color(0x7fe3ff);
    const DOT_HOT = new THREE.Color(0xff8a3d);

    const edges = [];
    const PARTICLES_PER_EDGE = 3;
    const UP = new THREE.Vector3(0, 1, 0);

    CONNECTIONS.forEach(function (pair, index) {

        const from = nodes[pair[0]];
        const to = nodes[pair[1]];
        const half = SLAB / 2 + 0.16;

        const start = new THREE.Vector3(from.base.x + half, from.base.y, from.base.z);
        const end = new THREE.Vector3(to.base.x - half, to.base.y, to.base.z);
        const dx = (end.x - start.x) * 0.5;

        const curve = new THREE.CubicBezierCurve3(
            start,
            new THREE.Vector3(start.x + dx, start.y, start.z),
            new THREE.Vector3(end.x - dx, end.y, end.z),
            end
        );

        // line
        const lineMaterial = new THREE.MeshBasicMaterial({
            color: EDGE_BASE.clone(),
            transparent: true,
            opacity: 0.5
        });
        const line = new THREE.Mesh(
            new THREE.TubeGeometry(curve, 56, 0.026, 8, false),
            lineMaterial
        );
        architecture.add(line);

        // arrowhead shows direction
        const tangent = curve.getTangent(1).normalize();
        const arrowMaterial = new THREE.MeshBasicMaterial({
            color: EDGE_BASE.clone(),
            transparent: true,
            opacity: 0.8
        });
        const arrow = new THREE.Mesh(
            new THREE.ConeGeometry(0.1, 0.26, 16),
            arrowMaterial
        );
        arrow.position.copy(end).addScaledVector(tangent, -0.13);
        arrow.quaternion.setFromUnitVectors(UP, tangent);
        architecture.add(arrow);

        // particles
        const particles = [];
        for (let i = 0; i < PARTICLES_PER_EDGE; i++) {
            const material = new THREE.SpriteMaterial({
                map: glowTexture,
                color: DOT_BASE.clone(),
                transparent: true,
                opacity: 0.9,
                blending: THREE.AdditiveBlending,
                depthWrite: false
            });
            const sprite = new THREE.Sprite(material);
            sprite.scale.set(0.34, 0.34, 1);
            architecture.add(sprite);
            particles.push({ sprite: sprite, offset: i / PARTICLES_PER_EDGE });
        }

        edges.push({
            from: from,
            to: to,
            curve: curve,
            lineMaterial: lineMaterial,
            arrowMaterial: arrowMaterial,
            particles: particles,
            phase: (index * 0.13) % 1,
            hover: 0
        });
    });


    // =====================================================
    // CAMERA FIT (keeps the whole scene inside the card)
    // =====================================================

    function fitToContainer() {
        const w = Math.max(container.clientWidth, 1);
        const h = Math.max(container.clientHeight, 1);

        renderer.setSize(w, h, false);
        camera.aspect = w / h;

        const tanHalf = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
        const dist = Math.max(
            HALF_H / tanHalf,
            HALF_W / (tanHalf * camera.aspect)
        ) * 1.05;

        camera.position.set(0, LOOK_Y + dist * 0.09, dist);
        camera.lookAt(0, LOOK_Y, 0);
        camera.updateProjectionMatrix();
    }

    fitToContainer();

    if (typeof ResizeObserver !== "undefined") {
        new ResizeObserver(fitToContainer).observe(container);
    } else {
        window.addEventListener("resize", fitToContainer);
    }


    // =====================================================
    // ORBIT-STYLE INTERACTION
    // Drag to rotate (clamped), double-click to reset,
    // gentle parallax on hover, subtle idle sway.
    // =====================================================

    const view = {
        yaw: 0, pitch: 0.1,
        targetYaw: 0, targetPitch: 0.1,
        dragging: false,
        lastX: 0, lastY: 0,
        lastInteraction: -10,
        parallaxX: 0, parallaxY: 0
    };

    const YAW_LIMIT = 0.6;
    const PITCH_MIN = -0.12;
    const PITCH_MAX = 0.42;
    const RESET_PITCH = 0.1;

    const pointer = new THREE.Vector2();
    let pointerInside = false;
    let hovered = null;
    const raycaster = new THREE.Raycaster();
    const clock = new THREE.Clock();

    const dom = renderer.domElement;

    function updatePointer(event) {
        const rect = dom.getBoundingClientRect();
        const nx = (event.clientX - rect.left) / rect.width;
        const ny = (event.clientY - rect.top) / rect.height;
        pointer.set(nx * 2 - 1, -(ny * 2 - 1));
        view.parallaxX = nx - 0.5;
        view.parallaxY = ny - 0.5;
    }

    dom.addEventListener("pointerdown", function (event) {
        if (event.button !== 0) { return; }
        view.dragging = true;
        view.lastX = event.clientX;
        view.lastY = event.clientY;
        view.lastInteraction = clock.elapsedTime;
        dom.style.cursor = "grabbing";
        try { dom.setPointerCapture(event.pointerId); } catch (e) { /* ignore */ }
    });

    dom.addEventListener("pointermove", function (event) {
        pointerInside = true;
        updatePointer(event);

        if (view.dragging) {
            const dx = event.clientX - view.lastX;
            const dy = event.clientY - view.lastY;
            view.lastX = event.clientX;
            view.lastY = event.clientY;
            view.lastInteraction = clock.elapsedTime;

            view.targetYaw = THREE.MathUtils.clamp(
                view.targetYaw + dx * 0.005, -YAW_LIMIT, YAW_LIMIT
            );
            view.targetPitch = THREE.MathUtils.clamp(
                view.targetPitch + dy * 0.004, PITCH_MIN, PITCH_MAX
            );
        }
    });

    function endDrag(event) {
        if (!view.dragging) { return; }
        view.dragging = false;
        dom.style.cursor = hovered ? "pointer" : "grab";
        try { dom.releasePointerCapture(event.pointerId); } catch (e) { /* ignore */ }
    }

    dom.addEventListener("pointerup", endDrag);
    dom.addEventListener("pointercancel", endDrag);

    dom.addEventListener("pointerleave", function () {
        pointerInside = false;
        view.parallaxX = 0;
        view.parallaxY = 0;
    });

    dom.addEventListener("dblclick", function () {
        view.targetYaw = 0;
        view.targetPitch = RESET_PITCH;
        view.lastInteraction = clock.elapsedTime;
    });

    // Small, non-blocking hint (created here so no HTML/CSS change is needed)
    const hint = document.createElement("div");
    hint.textContent = "Drag to rotate \u00B7 Double-click to reset";
    hint.style.cssText =
        "position:absolute;left:14px;bottom:10px;padding:4px 10px;" +
        "font:500 11px " + FONT + ";letter-spacing:.02em;color:#a9a5cc;" +
        "background:rgba(20,19,43,.6);border:1px solid rgba(255,255,255,.08);" +
        "border-radius:999px;pointer-events:none;user-select:none;";
    container.appendChild(hint);


    // =====================================================
    // ANIMATION LOOP
    // =====================================================

    const tmpColor = new THREE.Color();

    function updateHover() {
        let next = null;

        if (pointerInside && !view.dragging) {
            raycaster.setFromCamera(pointer, camera);
            const hits = raycaster.intersectObjects(pickables, false);
            if (hits.length) { next = hits[0].object.userData.node; }
        } else if (view.dragging) {
            next = hovered;
        }

        if (next !== hovered) {
            hovered = next;
            if (!view.dragging) {
                dom.style.cursor = hovered ? "pointer" : "grab";
            }
        }
    }

    function animate() {

        const dt = Math.min(clock.getDelta(), 0.05);
        const t = clock.elapsedTime;

        // ---- camera-like rotation of the architecture ----
        const idleFactor = reduceMotion
            ? 0
            : THREE.MathUtils.clamp((t - view.lastInteraction - 4) / 3, 0, 1);

        const swayYaw = Math.sin(t * 0.3) * 0.09 * idleFactor;
        const swayPitch = Math.sin(t * 0.22 + 1.3) * 0.02 * idleFactor;

        const wantYaw = view.targetYaw + view.parallaxX * 0.10 + swayYaw;
        const wantPitch = view.targetPitch + view.parallaxY * 0.06 + swayPitch;

        view.yaw += (wantYaw - view.yaw) * 0.07;
        view.pitch += (wantPitch - view.pitch) * 0.07;

        architecture.rotation.y = view.yaw;
        architecture.rotation.x = view.pitch;

        // ---- hover ----
        updateHover();

        for (const id in nodes) {
            const n = nodes[id];
            const goal = n === hovered ? 1 : 0;
            n.hover += (goal - n.hover) * 0.14;
            const h = n.hover;

            const bob = reduceMotion ? 0 : Math.sin(t * 0.8 + n.seed) * 0.05;
            n.group.position.set(n.base.x, n.base.y + bob, n.base.z + h * 0.35);
            n.group.scale.setScalar(1 + h * 0.07);

            n.body.material.emissiveIntensity = 0.05 + h * 0.3;
            n.face.material.emissiveIntensity = 0.32 + h * 0.3;
            n.halo.material.opacity = 0.28 + h * 0.3;
            n.label.sprite.material.opacity = 0.9 + h * 0.1;
            n.label.sprite.scale.set(
                n.label.baseScale.x * (1 + h * 0.05),
                n.label.baseScale.y * (1 + h * 0.05),
                1
            );
        }

        // ---- connections + particles ----
        edges.forEach(function (edge) {
            const connected = hovered && (edge.from === hovered || edge.to === hovered);
            edge.hover += ((connected ? 1 : 0) - edge.hover) * 0.14;
            const h = edge.hover;

            tmpColor.copy(EDGE_BASE).lerp(EDGE_HOT, h);
            edge.lineMaterial.color.copy(tmpColor);
            edge.arrowMaterial.color.copy(tmpColor);
            edge.lineMaterial.opacity = 0.5 + h * 0.45;

            if (!reduceMotion) {
                edge.phase = (edge.phase + dt * 0.14 * (1 + h * 0.9)) % 1;
            }

            edge.particles.forEach(function (p) {
                const u = (edge.phase + p.offset) % 1;
                p.sprite.position.copy(edge.curve.getPointAt(u));

                const fade = Math.pow(Math.sin(Math.PI * u), 0.6);
                p.sprite.material.opacity = (0.85 + h * 0.15) * fade;
                p.sprite.material.color.copy(DOT_BASE).lerp(DOT_HOT, h);

                const s = 0.34 + h * 0.12;
                p.sprite.scale.set(s, s, 1);
            });
        });

        renderer.render(scene, camera);
    }

    let rafId = null;

    function loop() {
        rafId = requestAnimationFrame(loop);
        animate();
    }

    function start() { if (rafId === null) { clock.getDelta(); loop(); } }
    function stop() { if (rafId !== null) { cancelAnimationFrame(rafId); rafId = null; } }

    // Only render while the card is on screen / tab is visible
    let inView = true;

    function sync() {
        if (inView && !document.hidden) { start(); } else { stop(); }
    }

    if (typeof IntersectionObserver !== "undefined") {
        new IntersectionObserver(function (entries) {
            inView = entries[0].isIntersecting;
            sync();
        }, { threshold: 0.01 }).observe(container);
    }

    document.addEventListener("visibilitychange", sync);

    sync();

});