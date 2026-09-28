document.addEventListener("DOMContentLoaded", function () {

    const container = document.getElementById("cloudmart3D");

    if (!container || typeof THREE === "undefined") {
        return;
    }


    // =====================================================
    // SCENE
    // =====================================================

    const scene = new THREE.Scene();

    scene.background = new THREE.Color(0xf1f3f6);


    // =====================================================
    // CAMERA
    // =====================================================

    const camera = new THREE.PerspectiveCamera(
        45,
        container.clientWidth / container.clientHeight,
        0.1,
        1000
    );

    camera.position.set(0, 5, 15);


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

    scene.add(architecture);


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
                color: 0x252a34,
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
                color: 0x9aa0aa
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


        return cube;
    }


    // =====================================================
    // CLOUDMART CORE
    // =====================================================

    createNode(
        "CloudMart",
        0,
        0,
        0,
        1.2
    );


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