document.addEventListener("DOMContentLoaded", function () {

    const container = document.getElementById("cloudmart3D");

    if (!container || typeof THREE === "undefined") {
        return;
    }


    // =====================================================
    // SCENE
    // =====================================================

    const scene = new THREE.Scene();

    scene.background = new THREE.Color(0x171633);


    // =====================================================
    // CAMERA
    // =====================================================

    const camera = new THREE.PerspectiveCamera(
        45,
        container.clientWidth / container.clientHeight,
        0.1,
        1000
    );

    camera.position.set(0, 0, 15);


    // =====================================================
    // RENDERER
    // =====================================================

    const renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true
    });

    renderer.setPixelRatio(
        Math.min(window.devicePixelRatio, 2)
    );

    renderer.setSize(
        container.clientWidth,
        container.clientHeight
    );

    container.appendChild(renderer.domElement);


    // =====================================================
    // LIGHTING
    // =====================================================

    const ambientLight = new THREE.AmbientLight(
        0xffffff,
        1.8
    );

    scene.add(ambientLight);


    const directionalLight = new THREE.DirectionalLight(
        0xffffff,
        2
    );

    directionalLight.position.set(
        5,
        10,
        8
    );

    scene.add(directionalLight);


    // =====================================================
    // MAIN GROUP
    // =====================================================

    const architecture = new THREE.Group();
    architecture.scale.set(
    0.85,
    0.85,
    0.85
);

architecture.position.set(
    0,
    0.4,
    0
);

    scene.add(architecture);
    createTitle("CloudMart");
    // =====================================================
// 3D LABEL CREATOR
// =====================================================
function createLabel(text, x, y, z) {

    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d");

    canvas.width = 512;
    canvas.height = 128;

    // Label background
    context.fillStyle = "rgba(23, 22, 51, 0.92)";
    context.beginPath();
    context.roundRect(10, 20, 492, 88, 18);
    context.fill();

    // Label text
    context.fillStyle = "#ffffff";
    context.font = "bold 32px Arial";
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillText(text, 256, 64);

    const texture = new THREE.CanvasTexture(canvas);
    texture.needsUpdate = true;

    const material = new THREE.SpriteMaterial({
        map: texture,
        transparent: true,
        depthTest: false
    });

    const sprite = new THREE.Sprite(material);

    sprite.position.set(x, y, z);

    // Size of label
    sprite.scale.set(2.6, 0.65, 1);

    architecture.add(sprite);

    return sprite;
}
function createTitle(text) {

    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d");

    canvas.width = 700;
    canvas.height = 150;

    context.clearRect(0, 0, canvas.width, canvas.height);

    context.fillStyle = "#ffffff";
    context.font = "bold 52px Arial";
    context.textAlign = "center";
    context.textBaseline = "middle";

    context.fillText(
        text,
        canvas.width / 2,
        canvas.height / 2
    );

    const texture = new THREE.CanvasTexture(canvas);
    texture.needsUpdate = true;

    const material = new THREE.SpriteMaterial({
        map: texture,
        transparent: true,
        depthTest: false
    });

    const title = new THREE.Sprite(material);

    title.position.set(0, 4.6, 0);

    title.scale.set(4.8, 1.05, 1);

    architecture.add(title);

    return title;
}


    // =====================================================
    // NODE CREATOR
    // =====================================================

    function createNode(
        name,
        x,
        y,
        z,
        size = 0.7
    ) {

        const geometry =
            new THREE.BoxGeometry(
                size,
                size,
                size
            );

        const material =
            new THREE.MeshStandardMaterial({
                color: 0x5b2cff,
                roughness: 0.35,
                metalness: 0.25
            });

        const cube =
            new THREE.Mesh(
                geometry,
                material
            );

        cube.position.set(
            x,
            y,
            z
        );

        architecture.add(cube);


        // Small glowing ring around node

        const ringGeometry =
            new THREE.TorusGeometry(
                size * 0.72,
                0.035,
                8,
                32
            );

        const ringMaterial =
            new THREE.MeshBasicMaterial({
                color: 0x22b8e8
            });

        const ring =
            new THREE.Mesh(
                ringGeometry,
                ringMaterial
            );

        ring.rotation.x =
            Math.PI / 2;

        ring.position.set(
            x,
            y,
            z
        );

        architecture.add(ring);
        createLabel(
    name,
    x,
    y + size + 0.55,
    z
);


        return cube;
    }


    // =====================================================
    // CLOUDMART CORE
    // =====================================================

    


    // =====================================================
    // AWS SERVICES
    // =====================================================

    createNode(
        "API Gateway",
        0,
        3.2,
        0
    );

    createNode(
        "Product Lambda",
        -3.5,
        1.5,
        0
    );

    createNode(
        "Order Lambda",
        3.5,
        1.5,
        0
    );

    createNode(
        "RDS MySQL",
        0,
        -3.0,
        0
    );

    createNode(
        "EventBridge",
        -3.5,
        -1.5,
        0
    );

    createNode(
        "S3 Reports",
        3.5,
        -1.5,
        0
    );

    createNode(
        "SNS",
        0,
        -4.8,
        0
    );


    // =====================================================
    // CONNECTIONS
    // =====================================================

    function connectNodes(
        start,
        end
    ) {

        const points = [
            new THREE.Vector3(
                start.x,
                start.y,
                start.z
            ),

            new THREE.Vector3(
                end.x,
                end.y,
                end.z
            )
        ];

        const geometry =
            new THREE.BufferGeometry()
                .setFromPoints(points);

        const material =
            new THREE.LineBasicMaterial({
                color: 0x9aa0aa,
                transparent: true,
                opacity: 0.65
            });

        const line =
            new THREE.Line(
                geometry,
                material
            );

        architecture.add(line);
    }


    // API → Lambdas

    connectNodes(
        new THREE.Vector3(0, 3.2, 0),
        new THREE.Vector3(-3.5, 1.5, 0)
    );

    connectNodes(
        new THREE.Vector3(0, 3.2, 0),
        new THREE.Vector3(3.5, 1.5, 0)
    );


    // Lambdas → RDS

    connectNodes(
        new THREE.Vector3(-3.5, 1.5, 0),
        new THREE.Vector3(0, -3, 0)
    );

    connectNodes(
        new THREE.Vector3(3.5, 1.5, 0),
        new THREE.Vector3(0, -3, 0)
    );


    // RDS → EventBridge

    connectNodes(
        new THREE.Vector3(0, -3, 0),
        new THREE.Vector3(-3.5, -1.5, 0)
    );


    // RDS → S3

    connectNodes(
        new THREE.Vector3(0, -3, 0),
        new THREE.Vector3(3.5, -1.5, 0)
    );


    // EventBridge → SNS

    connectNodes(
        new THREE.Vector3(-3.5, -1.5, 0),
        new THREE.Vector3(0, -4.8, 0)
    );


    // =====================================================
    // MOUSE INTERACTION
    // =====================================================

    let mouseX = 0;
    let mouseY = 0;

    container.addEventListener(
        "mousemove",
        function (event) {

            const rect =
                container.getBoundingClientRect();

            mouseX =
                ((event.clientX - rect.left)
                    / rect.width) - 0.5;

            mouseY =
                ((event.clientY - rect.top)
                    / rect.height) - 0.5;
        }
    );


    // =====================================================
    // RESIZE
    // =====================================================

    window.addEventListener(
        "resize",
        function () {

            const width =
                container.clientWidth;

            const height =
                container.clientHeight;

            camera.aspect =
                width / height;

            camera.updateProjectionMatrix();

            renderer.setSize(
                width,
                height
            );
        }
    );


    // =====================================================
    // ANIMATION
    // =====================================================

    function animate() {

        requestAnimationFrame(
            animate
        );

        architecture.rotation.y +=
            0.0015;

        architecture.rotation.x +=
            (mouseY * 0.15 -
                architecture.rotation.x) * 0.03;

        architecture.rotation.y +=
            (mouseX * 0.15) * 0.002;

        renderer.render(
            scene,
            camera
        );
    }


    animate();

});