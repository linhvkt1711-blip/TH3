// wwwroot/js/tryon-studio.js
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

export class TryOnStudio {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            phoneSlug: options.phoneSlug || '',
            phoneName: options.phoneName || '',
            initialCaseCode: options.initialCaseCode || 'OL01',
            initialCaseName: options.initialCaseName || 'Ốp Lưng MagSafe Trong Suốt',
            initialTextureUrl: options.initialTextureUrl || '',
            initialMaterialType: options.initialMaterialType || 'Silicone',
            initialCaseModelUrl: options.initialCaseModelUrl || ''
        };

        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;

        // Group gốc chứa cả thân máy và ốp lưng
        this.phoneGroup = new THREE.Group();

        // Thân máy
        this.phoneMesh = null;
        this.phoneMeshUsesRotatedAxes = false;
        this.phoneMeshAxisOrder = null;
        this.phoneModelBaseSize = null;
        this.phoneModelBaseScale = null;
        this.phoneBodyMaterial = null;
        this.backGlassMaterial = null;
        this.frameMesh = null;

        // Ốp lưng (Shell ôm sát có khoét camera chuẩn xác)
        this.caseMesh = null;
        this.caseRimMesh = null;
        this.caseLipMesh = null;
        this.caseMaterial = null;
        this.caseEdgeMaterial = null;
        this.caseModelUrl = null;
        this.caseModelRequestUrl = null;
        this.caseModelRequestId = 0;
        this.caseModelLoadPromise = Promise.resolve();
        this.isCaseVisible = true;

        this.gltfLoader = new GLTFLoader();
        this.textureLoader = new THREE.TextureLoader();

        // Canvas phục vụ vẽ hoa văn ốp (MagSafe, Da, Carbon, Khắc chữ)
        this.caseCanvas = document.createElement('canvas');
        this.caseCanvas.width = 1024;
        this.caseCanvas.height = 2048;
        this.caseCtx = this.caseCanvas.getContext('2d');
        this.caseTexture = new THREE.CanvasTexture(this.caseCanvas);
        this.caseTexture.colorSpace = THREE.SRGBColorSpace;
        this.caseTexture.flipY = true;

        this.currentCaseStyle = 'OL01'; // Preset hoặc mã sản phẩm trong database
        this.currentCaseOptions = null;
        this.currentEngraveText = "";

        // Trạng thái tách rời mô hình (Exploded View Animation)
        this.targetCaseX = 0.0;
        this.isExploded = false;

        this.ready = this.init();
    }

    async init() {
        // 1. Tạo Three.js Scene
        this.scene = new THREE.Scene();
        this.scene.add(this.phoneGroup);
        // Thiết lập góc nhìn 3/4 mặt lưng nghệ thuật cho toàn bộ nhóm máy + ốp
        this.phoneGroup.rotation.set(0.04, -0.32, 0);

        // 2. Camera: Căn góc 3/4 mặt lưng chuẩn xác 100% giống như hình ảnh mẫu
        const aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(36, aspect, 0.01, 10);
        this.camera.position.set(0.065, 0.008, 0.30);

        // 3. WebGL Renderer với ACES Filmic Tone Mapping chân thực
        this.renderer = new THREE.WebGLRenderer({
            antialias: true,
            alpha: true,
            powerPreference: 'high-performance',
            preserveDrawingBuffer: true
        });
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 3));
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.outputColorSpace = THREE.SRGBColorSpace;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.0;
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.container.appendChild(this.renderer.domElement);

        this.pmremGenerator = new THREE.PMREMGenerator(this.renderer);
        const environment = new RoomEnvironment(this.renderer);
        this.scene.environment = this.pmremGenerator.fromScene(environment, 0.04).texture;
        environment.dispose();
        this.pmremGenerator.dispose();

        // 4. OrbitControls: Xoay 360 độ, zoom mượt mà
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.minDistance = 0.12;
        this.controls.maxDistance = 0.70;
        this.controls.target.set(0, 0, 0);

        // 5. Hệ thống ánh sáng Studio chuyên nghiệp (Key light, Rim light viền vàng, Ambient)
        this.setupLighting();

        if (this.options.phoneSlug) {
            const phoneLoaded = await this.loadPhoneModel(this.options.phoneSlug);

            if (phoneLoaded) {
                this.buildFitted3DCase();
                this.setCaseStyle(this.options.initialCaseCode || 'OL01', {
                    textureUrl: this.options.initialTextureUrl,
                    materialType: this.options.initialMaterialType,
                    modelUrl: this.options.initialCaseModelUrl
                });
                await this.caseModelLoadPromise;
            } else {
                // Khong dung model iPhone de thay the cho dien thoai chua ho tro.
                console.error(`Studio chua co mo hinh 3D cho: ${this.options.phoneSlug}`);
                this.currentCaseStyle = this.options.initialCaseCode || 'OL01';
                this.currentCaseOptions = {
                    textureUrl: this.options.initialTextureUrl,
                    materialType: this.options.initialMaterialType,
                    modelUrl: this.options.initialCaseModelUrl
                };
            }
        } else {
            this.currentCaseStyle = this.options.initialCaseCode || 'OL01';
            this.currentCaseOptions = {
                textureUrl: this.options.initialTextureUrl,
                materialType: this.options.initialMaterialType,
                modelUrl: this.options.initialCaseModelUrl
            };
        }

        window.addEventListener('resize', () => this.onResize());
        this.animate();
    }

    setupLighting() {
        // Ánh sáng môi trường Studio trung tính
        const ambient = new THREE.AmbientLight(0xffffff, 1.5);
        this.scene.add(ambient);

        // Đèn chính (Key Light) từ góc trên bên trái chiếu xuống làm nổi bật chi tiết mặt kính và camera
        const keyLight = new THREE.DirectionalLight(0xffffff, 3.2);
        keyLight.position.set(-1.8, 2.6, 3.2);
        this.scene.add(keyLight);

        // Đèn viền (Rim Light) làm nổi bật viền thép không gỉ sáng bóng như gương
        const rimLight = new THREE.DirectionalLight(0xffffff, 3.6);
        rimLight.position.set(2.4, 0.4, -1.0);
        this.scene.add(rimLight);

        // Đèn viền phụ phản chiếu sắc thái kim loại
        const rimSecondaryLight = new THREE.DirectionalLight(0xeef4ff, 1.8);
        rimSecondaryLight.position.set(-2.5, -1.5, -1.5);
        this.scene.add(rimSecondaryLight);

        // Đèn nền mềm chống góc khuất
        const fillLight = new THREE.DirectionalLight(0xffffff, 1.2);
        fillLight.position.set(0, -2.5, 2.5);
        this.scene.add(fillLight);
    }

    async loadPhoneModel(phoneSlug) {
        phoneSlug = String(phoneSlug || '').trim().toLowerCase();

        const iphoneDimensions = {
            'iphone-15-pro': [0.0706, 0.1466, 0.00825],
            'iphone-15-prm': [0.0767, 0.1599, 0.00825],
            'iphone-16-pro-max': [0.0776, 0.1630, 0.00825],
            'iphone-x': [0.0709, 0.1436, 0.0077]
        };

        // Only declare GLB files that are confirmed to exist.
        const modelPaths = {
            'iphone-x': '/models/phones/iphone-x/iphone_x.glb',
            'iphone-16-pro-max': '/models/phones/iphone-16-pro-max-no-sim-desert-titanium.glb'
        };

        const isIPhone = Object.hasOwn(iphoneDimensions, phoneSlug);
        const isIPhoneXModel = phoneSlug === 'iphone-x';
        const glbPath = modelPaths[phoneSlug];

        this.clearPhoneModel();
        this.phoneModelBaseSize = null;
        this.phoneModelBaseScale = null;
        this.phoneMeshAxisOrder = null;
        this.phoneMeshUsesRotatedAxes = false;

        try {
            if (!glbPath) {
                throw new Error(`Chua co file GLB cho dong may: ${phoneSlug}`);
            }

            const gltf = await this.gltfLoader.loadAsync(glbPath);

            this.phoneMesh = new THREE.Group();
            this.phoneMesh.add(gltf.scene);
            this.options.phoneSlug = phoneSlug;

            if (isIPhoneXModel) {
                gltf.scene.rotation.y = Math.PI;
            } else if (isIPhone) {
                gltf.scene.rotation.y = -Math.PI / 2;
            }

            gltf.scene.updateMatrixWorld(true);

            const innerBounds = new THREE.Box3().setFromObject(gltf.scene);
            const innerCenter = innerBounds.getCenter(new THREE.Vector3());
            const innerSize = innerBounds.getSize(new THREE.Vector3());

            if (innerSize.x <= 0 || innerSize.y <= 0 || innerSize.z <= 0) {
                throw new Error(`Kich thuoc GLB khong hop le: ${glbPath}`);
            }

            gltf.scene.position.sub(innerCenter);

            const dimensions = iphoneDimensions[phoneSlug] || [
                innerSize.x,
                innerSize.y,
                innerSize.z
            ];

            this.phoneDimensions = {
                width: dimensions[0],
                height: dimensions[1],
                depth: dimensions[2],
                radius: Math.min(dimensions[0], dimensions[1]) * 0.12
            };

            this.cameraPlateauInfo = {
                x: -dimensions[0] * (isIPhoneXModel ? 0.29 : 0.20),
                y: dimensions[1] * (isIPhoneXModel ? 0.34 : 0.354),
                width: dimensions[0] * (isIPhoneXModel ? 0.24 : 0.52),
                height: dimensions[1] * (isIPhoneXModel ? 0.24 : 0.26),
                radius: Math.min(dimensions[0], dimensions[1]) *
                    (isIPhoneXModel ? 0.045 : 0.09)
            };

            this.phoneMesh.scale.set(
                dimensions[0] / innerSize.x,
                dimensions[1] / innerSize.y,
                dimensions[2] / innerSize.z
            );

            this.phoneMesh.rotation.set(0, 0, 0);
            this.phoneMesh.position.set(0, 0, 0);
            this.phoneMeshUsesRotatedAxes = false;
            this.isIPhoneX = isIPhoneXModel;
            this.phoneMesh.updateMatrixWorld(true);

            this.phoneModelBaseSize = new THREE.Vector3(...dimensions);
            this.phoneModelBaseScale = this.phoneMesh.scale.clone();

            const maxAnisotropy = Math.min(
                this.renderer.capabilities.getMaxAnisotropy(),
                8
            );

            this.phoneMesh.traverse(object => {
                if (!object.isMesh) return;

                object.castShadow = true;
                object.receiveShadow = true;

                const materials = Array.isArray(object.material)
                    ? object.material
                    : [object.material];

                materials.forEach(material => {
                    if (!material) return;

                    [
                        'map',
                        'emissiveMap',
                        'normalMap',
                        'roughnessMap',
                        'metalnessMap'
                    ].forEach(key => {
                        if (material[key]) {
                            material[key].anisotropy = maxAnisotropy;
                        }
                    });

                    if (isIPhoneXModel) {
                        const materialName = (material.name || '').toLowerCase();

                        if (materialName.includes('metal.frame')) {
                            this.phoneBodyMaterial = material;
                        }

                        if (materialName.includes('white_plastic')) {
                            this.backGlassMaterial = material;
                        }
                    }

                    if ('envMapIntensity' in material) {
                        material.envMapIntensity = 1.2;
                    }
                });
            });

            this.phoneGroup.add(this.phoneMesh);
            console.log(`Da tai mo hinh dien thoai: ${phoneSlug}`);
            return true;
        } catch (error) {
            console.error(`Khong tai duoc mo hinh 3D "${phoneSlug}".`, error);

            if (phoneSlug === 'iphone-x') {
                this.createPhotorealisticIPhoneX();
                return true;
            }

            if (phoneSlug === 'iphone-15-pro' || phoneSlug === 'iphone-15-prm') {
                this.createPhotorealisticIPhone15Pro(phoneSlug);
                return true;
            }

            if (phoneSlug === 'iphone-16-pro-max') {
                this.createPhotorealisticIPhone15Pro(phoneSlug);
                return true;
            }

            throw new Error(`Chua co mo hinh 3D ho tro cho thiet bi: ${phoneSlug}`);
        }
    }

    clearPhoneModel() {
        if (this.phoneMesh) {
            this.phoneGroup.remove(this.phoneMesh);
            this.phoneMesh = null;
        }
        if (this.caseMesh) {
            this.phoneGroup.remove(this.caseMesh);
            this.caseMesh = null;
        }
        this.caseRimMesh = null;
        this.caseLipMesh = null;
        this.caseModelRequestId++;
        this.caseModelRequestUrl = null;
        this.caseModelUrl = null;
        this.options.phoneSlug = '';
        this.phoneDimensions = null;
        this.cameraPlateauInfo = null;
        this.phoneModelBaseSize = null;
        this.phoneModelBaseScale = null;
    }

    applyDetectionPose(pose) {
        if (!pose || !this.phoneMesh) return;

        const baseSize = this.phoneModelBaseSize || new THREE.Vector3(
            this.phoneDimensions.width,
            this.phoneDimensions.height,
            this.phoneDimensions.depth
        );
        const baseScale = this.phoneModelBaseScale || this.phoneMesh.scale.clone();
        const targetScale = pose.scale;

        if (
            Array.isArray(targetScale) &&
            targetScale.length >= 3 &&
            targetScale.slice(0, 3).every(value => Number.isFinite(value) && value > 0) &&
            baseSize.x > 0 && baseSize.y > 0 && baseSize.z > 0
        ) {
            if (this.phoneMeshAxisOrder) {
                const nextScale = baseScale.toArray();
                this.phoneMeshAxisOrder.forEach((sourceAxis, outputAxis) => {
                    nextScale[sourceAxis] *= targetScale[outputAxis] / baseSize.getComponent(outputAxis);
                });
                this.phoneMesh.scale.set(...nextScale);
            } else if (this.phoneMeshUsesRotatedAxes) {
                this.phoneMesh.scale.set(
                    baseScale.x * targetScale[2] / baseSize.z,
                    baseScale.y * targetScale[1] / baseSize.y,
                    baseScale.z * targetScale[0] / baseSize.x
                );
            } else {
                this.phoneMesh.scale.set(
                    baseScale.x * targetScale[0] / baseSize.x,
                    baseScale.y * targetScale[1] / baseSize.y,
                    baseScale.z * targetScale[2] / baseSize.z
                );
            }
            this.phoneDimensions = {
                width: targetScale[0],
                height: targetScale[1],
                depth: targetScale[2],
                radius: Math.min(targetScale[0], targetScale[1]) * 0.12
            };
            this.cameraPlateauInfo = {
                x: -targetScale[0] * (this.options.phoneSlug === 'iphone-x' ? 0.29 : 0.20),
                y: targetScale[1] * (this.options.phoneSlug === 'iphone-x' ? 0.34 : 0.354),
                width: targetScale[0] * (this.options.phoneSlug === 'iphone-x' ? 0.24 : 0.52),
                height: targetScale[1] * (this.options.phoneSlug === 'iphone-x' ? 0.24 : 0.26),
                radius: Math.min(targetScale[0], targetScale[1]) * (this.options.phoneSlug === 'iphone-x' ? 0.045 : 0.09)
            };
            this.phoneModelBaseSize = baseSize.clone();
            this.phoneModelBaseScale = baseScale.clone();
        }

        const rotation = pose.rotation;
        if (Array.isArray(rotation)) {
            const values = Array.isArray(rotation[0]) ? rotation.flat() : rotation;
            if (values.length === 9 && values.every(Number.isFinite)) {
                const matrix = new THREE.Matrix4().set(
                    values[0], values[1], values[2], 0,
                    values[3], values[4], values[5], 0,
                    values[6], values[7], values[8], 0,
                    0, 0, 0, 1
                );
                this.phoneGroup.rotation.setFromRotationMatrix(matrix);
            }
        }

        const translation = pose.translation;
        if (Array.isArray(translation) && translation.length >= 3 && translation.slice(0, 3).every(Number.isFinite)) {
            const nextPosition = new THREE.Vector3(...translation.slice(0, 3));
            const offset = nextPosition.sub(this.phoneGroup.position);
            this.phoneGroup.position.add(offset);
            this.camera.position.add(offset);
            this.controls.target.add(offset);
            this.controls.update();
        }
    }

    // ==================================================================================
    // NÂNG CẤP VẬT LIỆU PBR PHOTOREALISTIC CHO IPHONE X (GIỐNG 100% ẢNH THẬT NGOÀI ĐỜI)
    // ==================================================================================
    enhanceIPhoneXMaterials(phoneGroup, colorHex = '#f4f5f7') {
        const isSpaceGray = (colorHex.toLowerCase().includes('414247') || 
                             colorHex.toLowerCase().includes('26') || 
                             colorHex.toLowerCase().includes('black') || 
                             colorHex.toLowerCase().includes('3c'));

        const frameColor = isSpaceGray ? 0x36383e : 0xf0f2f5;
        const backGlassColor = isSpaceGray ? 0x24252a : 0xf8f9fa;
        const logoColor = isSpaceGray ? 0x1d1e22 : 0xd8dae0;
        const textColor = isSpaceGray ? 0x585a62 : 0x626570;

        // 1. Khung thép không gỉ bóng loáng như gương (Surgical-grade Stainless Steel Mirror Finish)
        const frameMat = new THREE.MeshPhysicalMaterial({
            color: frameColor,
            metalness: 0.98,
            roughness: isSpaceGray ? 0.12 : 0.05,
            clearcoat: 1.0,
            clearcoatRoughness: 0.03,
            reflectivity: 0.98,
            envMapIntensity: 2.4,
            name: "IPhoneX_Stainless_Steel"
        });

        // 2. Mặt lưng kính trắng bóng loáng (Porcelain Glossy Glass) giống hệt ảnh thật ngoài đời
        const backGlassMat = new THREE.MeshPhysicalMaterial({
            color: backGlassColor,
            roughness: 0.04,
            metalness: 0.02,
            clearcoat: 1.0,
            clearcoatRoughness: 0.02,
            reflectivity: 0.95,
            transmission: 0.06,
            ior: 1.52,
            envMapIntensity: 1.8,
            name: "IPhoneX_Back_Glass"
        });

        // 3. Logo Apple gương phản chiếu (Mirror-polished Chrome Apple Logo)
        const appleLogoMat = new THREE.MeshPhysicalMaterial({
            color: logoColor,
            metalness: 0.98,
            roughness: 0.03,
            clearcoat: 1.0,
            clearcoatRoughness: 0.02,
            envMapIntensity: 2.6,
            name: "IPhoneX_Apple_Logo"
        });

        // 4. Chữ "iPhone" kim loại khắc chìm thanh lịch
        const textMat = new THREE.MeshPhysicalMaterial({
            color: textColor,
            metalness: 0.70,
            roughness: 0.15,
            clearcoat: 0.85,
            name: "IPhoneX_Text"
        });

        // 5. Cụm camera kép hình viên thuốc dọc: Viền thép chrome + nền kính đen obsidian + thấu kính sapphire
        const camBumpHousingMat = new THREE.MeshPhysicalMaterial({
            color: 0x08090b,
            metalness: 0.40,
            roughness: 0.06,
            clearcoat: 1.0,
            clearcoatRoughness: 0.04,
            envMapIntensity: 1.6
        });

        const camBezelRingMat = new THREE.MeshPhysicalMaterial({
            color: frameColor,
            metalness: 0.98,
            roughness: 0.06,
            clearcoat: 1.0,
            envMapIntensity: 2.2
        });

        const camLensGlassMat = new THREE.MeshPhysicalMaterial({
            color: 0x070815,
            roughness: 0.02,
            metalness: 0.45,
            transmission: 0.40,
            ior: 1.77,
            clearcoat: 1.0,
            clearcoatRoughness: 0.02,
            envMapIntensity: 2.2
        });

        const flashMat = new THREE.MeshStandardMaterial({
            color: 0xfffbe8,
            roughness: 0.25,
            metalness: 0.20
        });

        // 6. Màn hình Super Retina OLED đen sâu bóng
        const screenMat = new THREE.MeshPhysicalMaterial({
            color: 0x020204,
            roughness: 0.03,
            metalness: 0.92,
            clearcoat: 1.0,
            clearcoatRoughness: 0.02,
            envMapIntensity: 1.5
        });

        // 7. Vạch ăng ten trên khung thép
        const antennaMat = new THREE.MeshStandardMaterial({
            color: isSpaceGray ? 0x202124 : 0xd2d4d8,
            roughness: 0.50,
            metalness: 0.10
        });

        this.phoneBodyMaterial = frameMat;
        this.backGlassMaterial = backGlassMat;

        phoneGroup.traverse(object => {
            if (!object.isMesh) return;
            object.castShadow = true;
            object.receiveShadow = true;

            const name = object.name;
            if (name === 'Object_5') {
                object.material = appleLogoMat;
            } else if (name === 'Object_7') {
                object.material = backGlassMat;
            } else if (name === 'Object_12') {
                object.material = frameMat;
            } else if (name === 'Object_26') {
                object.material = textMat;
            } else if (name === 'Object_11' || name === 'Object_8') {
                object.material = screenMat;
            } else if (name === 'Object_14') {
                object.material = camBezelRingMat;
            } else if (name === 'Object_19' || name === 'Object_20') {
                object.material = camBumpHousingMat;
            } else if (name === 'Object_15' || name === 'Object_16' || name === 'Object_17') {
                object.material = camLensGlassMat;
            } else if (name === 'Object_10') {
                object.material = flashMat;
            } else if (name >= 'Object_28' && name <= 'Object_31') {
                object.material = antennaMat;
            } else if (name >= 'Object_33' && name <= 'Object_51') {
                object.material = frameMat;
            }
        });
    }

    // ==================================================================================
    // TẠO MÔ HÌNH IPHONE X PHOTOREALISTIC 100% CHUẨN XÁC NGOÀI ĐỜI (GIỐNG HỆT ẢNH 3)
    // ==================================================================================
    createPhotorealisticIPhoneX(colorHex = '#f4f5f7') {
        if (this.phoneMesh) {
            this.phoneGroup.remove(this.phoneMesh);
        }

        this.phoneMeshUsesRotatedAxes = false;
        this.isIPhoneX = true;
        this.options.phoneSlug = 'iphone-x';

        const group = new THREE.Group();
        group.name = "Phone_Model_Group_IPhoneX";

        // Kích thước thật CAD iPhone X (70.9mm x 143.6mm x 7.7mm)
        const width = 0.0709;
        const height = 0.1436;
        const depth = 0.0077;
        const radius = 0.0092;

        this.phoneDimensions = { width, height, depth, radius };

        const isSpaceGray = (colorHex.toLowerCase().includes('414247') || 
                             colorHex.toLowerCase().includes('26') || 
                             colorHex.toLowerCase().includes('black') || 
                             colorHex.toLowerCase().includes('2c') ||
                             colorHex.toLowerCase().includes('3c'));

        const frameColor = isSpaceGray ? 0x2e3036 : 0xf2f4f7;
        const backGlassColor = isSpaceGray ? 0x222428 : 0xf9fafc;

        // 1. Khung thép y tế không gỉ bo cong đánh bóng như gương (Surgical-Grade Stainless Steel Mirror Frame)
        const frameShape = this.createRoundedRectShape(width, height, radius);
        const extrudeSettings = {
            depth: depth,
            bevelEnabled: true,
            bevelSegments: 10,
            steps: 1,
            bevelSize: 0.0022,
            bevelThickness: 0.0022
        };
        const frameGeo = new THREE.ExtrudeGeometry(frameShape, extrudeSettings);
        frameGeo.center();

        this.phoneBodyMaterial = new THREE.MeshPhysicalMaterial({
            color: frameColor,
            metalness: 0.99,
            roughness: isSpaceGray ? 0.08 : 0.03,
            clearcoat: 1.0,
            clearcoatRoughness: 0.02,
            reflectivity: 0.99,
            envMapIntensity: 2.6,
            name: "IPhoneX_Stainless_Steel"
        });
        this.frameMesh = new THREE.Mesh(frameGeo, this.phoneBodyMaterial);
        group.add(this.frameMesh);

        // 2. Nút bấm vật lý khung thép (Power bên phải, Volume & Mute bên trái)
        this.addIPhoneXButtons(group, width, height, depth, isSpaceGray);

        // 3. Mặt lưng kính chuẩn 100% tài nguyên người dùng cung cấp
        const backTextureUrl = isSpaceGray 
            ? '/images/iphone-x/back-spacegray.png?v=2'
            : '/images/iphone-x/back-silver.png?v=2';

        const backTex = this.textureLoader.load(backTextureUrl);
        backTex.colorSpace = THREE.SRGBColorSpace;
        backTex.anisotropy = Math.min(this.renderer.capabilities.getMaxAnisotropy(), 8);

        const backGlassGeo = new THREE.PlaneGeometry(width * 0.968, height * 0.968);
        this.backGlassMaterial = new THREE.MeshPhysicalMaterial({
            color: isSpaceGray ? 0x24262b : 0xf8fafc,
            map: backTex,
            roughness: 0.02,
            metalness: 0.04,
            clearcoat: 1.0,
            clearcoatRoughness: 0.01,
            reflectivity: 0.98,
            transmission: 0.02,
            ior: 1.52,
            envMapIntensity: 2.2,
            name: "IPhoneX_Back_Glass"
        });
        const backGlassMesh = new THREE.Mesh(backGlassGeo, this.backGlassMaterial);
        backGlassMesh.position.z = depth / 2 + 0.0020;
        group.add(backGlassMesh);

        // 4. Màn hình phía trước Super Retina HD OLED có Tai thỏ (The Notch) và hình nền chính thức iPhone X
        this.addIPhoneXFrontScreen(group, width, height, depth);

        // 5. Cụm camera kép dạng viên thuốc dọc chuẩn 100% Ảnh 3 (Vertical Dual Pill Camera)
        const bumpW = 0.0112; // 11.2 mm
        const bumpH = 0.0248; // 24.8 mm
        const bumpR = bumpW / 2;
        const bumpX = -width * 0.292;
        const bumpY = height * 0.332;

        this.cameraPlateauInfo = {
            x: bumpX,
            y: bumpY,
            width: bumpW + 0.0016,
            height: bumpH + 0.0016,
            radius: bumpR + 0.0008
        };

        // Gờ nền đen obsidian trong viên thuốc
        const camPillShape = this.createRoundedRectShape(bumpW, bumpH, bumpR);
        const camBumpGeo = new THREE.ExtrudeGeometry(camPillShape, {
            depth: 0.0016,
            bevelEnabled: true,
            bevelSegments: 5,
            bevelSize: 0.0006,
            bevelThickness: 0.0006
        });
        camBumpGeo.center();

        const camBumpMat = new THREE.MeshPhysicalMaterial({
            color: 0x07080a,
            roughness: 0.04,
            metalness: 0.35,
            clearcoat: 1.0,
            clearcoatRoughness: 0.02,
            envMapIntensity: 2.0
        });
        const camBump = new THREE.Mesh(camBumpGeo, camBumpMat);
        camBump.position.set(bumpX, bumpY, depth / 2 + 0.0028);
        group.add(camBump);

        // Viền thép bóng loáng bao quanh viên thuốc (Chrome Pill Bezel)
        const bezelShape = this.createRoundedRectShape(bumpW + 0.0008, bumpH + 0.0008, bumpR + 0.0004);
        const bezelHole = this.createRoundedRectPath(-bumpW/2, -bumpH/2, bumpW, bumpH, bumpR);
        bezelShape.holes.push(bezelHole);
        const bezelGeo = new THREE.ExtrudeGeometry(bezelShape, {
            depth: 0.0018,
            bevelEnabled: true,
            bevelSegments: 3,
            bevelSize: 0.0002,
            bevelThickness: 0.0002
        });
        bezelGeo.center();
        const bezelMesh = new THREE.Mesh(bezelGeo, this.phoneBodyMaterial);
        bezelMesh.position.set(bumpX, bumpY, depth / 2 + 0.0029);
        group.add(bezelMesh);

        // Hai ống kính camera sapphire (Top Wide Lens & Bottom Telephoto Lens)
        const lensCenters = [
            { y: bumpY + bumpH * 0.25 }, // Top 12MP Wide
            { y: bumpY - bumpH * 0.25 }  // Bottom 12MP Telephoto
        ];

        lensCenters.forEach(pos => {
            // Vành chrome bảo vệ ống kính
            const ringGeo = new THREE.CylinderGeometry(0.0040, 0.0040, 0.0008, 32);
            const ringMat = new THREE.MeshStandardMaterial({
                color: isSpaceGray ? 0x484b54 : 0xe2e5ec,
                roughness: 0.06,
                metalness: 0.98
            });
            const ringMesh = new THREE.Mesh(ringGeo, ringMat);
            ringMesh.rotation.x = Math.PI / 2;
            ringMesh.position.set(bumpX, pos.y, depth / 2 + 0.0038);
            group.add(ringMesh);

            // Vòng đen quang học
            const innerRingGeo = new THREE.CylinderGeometry(0.0033, 0.0033, 0.0009, 28);
            const innerRingMat = new THREE.MeshBasicMaterial({ color: 0x050608 });
            const innerMesh = new THREE.Mesh(innerRingGeo, innerRingMat);
            innerMesh.rotation.x = Math.PI / 2;
            innerMesh.position.set(bumpX, pos.y, depth / 2 + 0.0039);
            group.add(innerMesh);

            // Thấu kính sapphire lồi phản chiếu ánh xanh tím
            const lensGeo = new THREE.SphereGeometry(0.0028, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2);
            const lensMat = new THREE.MeshPhysicalMaterial({
                color: 0x0e1022,
                roughness: 0.02,
                metalness: 0.30,
                transmission: 0.35,
                ior: 1.77,
                clearcoat: 1.0,
                clearcoatRoughness: 0.02,
                envMapIntensity: 2.4
            });
            const lensMesh = new THREE.Mesh(lensGeo, lensMat);
            lensMesh.position.set(bumpX, pos.y, depth / 2 + 0.0041);
            group.add(lensMesh);
        });

        // Đèn Quad-LED True Tone Flash ở giữa hai camera
        const flashGeo = new THREE.CylinderGeometry(0.0019, 0.0019, 0.0005, 24);
        const flashMat = new THREE.MeshStandardMaterial({
            color: 0xfff6dc,
            roughness: 0.25,
            metalness: 0.20
        });
        const flashMesh = new THREE.Mesh(flashGeo, flashMat);
        flashMesh.rotation.x = Math.PI / 2;
        flashMesh.position.set(bumpX, bumpY, depth / 2 + 0.0037);
        group.add(flashMesh);

        // Lỗ mic thu âm nhỏ cạnh flash
        const micGeo = new THREE.CylinderGeometry(0.0005, 0.0005, 0.0006, 16);
        const micMat = new THREE.MeshBasicMaterial({ color: 0x020202 });
        const micMesh = new THREE.Mesh(micGeo, micMat);
        micMesh.rotation.x = Math.PI / 2;
        micMesh.position.set(bumpX + 0.0022, bumpY - 0.0038, depth / 2 + 0.0037);
        group.add(micMesh);

        // Giữ vị trí (0, 0, 0) để đồng bộ 100% với ốp lưng và camera
        group.rotation.set(0, 0, 0);
        group.position.set(0, 0, 0);

        this.phoneMesh = group;
        this.phoneGroup.add(this.phoneMesh);
    }

    // Vẽ mặt lưng kính chuẩn xác: Logo Apple chrome phản chiếu + chữ "iPhone" thanh mảnh
    generateIPhoneXBackTexture(baseColorHex, isSpaceGray = false) {
        const canvas = document.createElement('canvas');
        canvas.width = 1024;
        canvas.height = 2048;
        const ctx = canvas.getContext('2d');

        // 1. Nền kính trắng sứ bóng loáng hoặc xám không gian
        const bgHex = typeof baseColorHex === 'number' 
            ? `#${baseColorHex.toString(16).padStart(6, '0')}` 
            : baseColorHex;
        ctx.fillStyle = bgHex;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // 2. Vẽ Logo Apple phản chiếu ánh kim sáng bóng như gương (chuẩn tỉ lệ Ảnh 3)
        ctx.save();
        ctx.translate(512, 720); // Vị trí 1/3 phía trên chuẩn ảnh mẫu
        ctx.scale(1.08, 1.08);

        // Màu gradient ánh kim chrome cho logo Apple
        const appleGrad = ctx.createLinearGradient(-40, -100, 40, 100);
        if (isSpaceGray) {
            appleGrad.addColorStop(0, '#2a2c32');
            appleGrad.addColorStop(0.5, '#444750');
            appleGrad.addColorStop(1, '#1e2025');
        } else {
            appleGrad.addColorStop(0, '#e8ebf0');
            appleGrad.addColorStop(0.3, '#ffffff');
            appleGrad.addColorStop(0.7, '#c6cbd4');
            appleGrad.addColorStop(1, '#b0b6c2');
        }
        ctx.fillStyle = appleGrad;

        // Lá quả táo
        ctx.beginPath();
        ctx.ellipse(8, -130, 22, 38, Math.PI / 4, 0, Math.PI * 2);
        ctx.fill();

        // Thân quả táo
        ctx.beginPath();
        ctx.arc(-42, -20, 68, 0, Math.PI * 2);
        ctx.arc(42, -20, 68, 0, Math.PI * 2);
        ctx.arc(-34, 42, 75, 0, Math.PI * 2);
        ctx.arc(34, 42, 75, 0, Math.PI * 2);
        ctx.fill();

        // Vết cắn khuyết đặc trưng
        ctx.globalCompositeOperation = 'destination-out';
        ctx.beginPath();
        ctx.arc(88, -10, 48, 0, Math.PI * 2);
        ctx.fill();

        // Khuyết trên cuống
        ctx.beginPath();
        ctx.arc(0, -90, 22, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();

        // 3. Chữ "iPhone" thanh lịch in chìm ở phần đáy lưng chuẩn Ảnh 3
        ctx.save();
        ctx.font = '500 46px -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = isSpaceGray ? 'rgba(120, 125, 138, 0.75)' : 'rgba(92, 98, 110, 0.82)';
        ctx.letterSpacing = '2px';
        ctx.fillText('iPhone', 512, 1620);
        ctx.restore();

        const tex = new THREE.CanvasTexture(canvas);
        tex.colorSpace = THREE.SRGBColorSpace;
        tex.flipY = false;
        return tex;
    }

    addIPhoneXButtons(group, w, h, d, isSpaceGray) {
        const btnMat = this.phoneBodyMaterial;

        // Nút Nguồn / Siri (Cạnh phải dài 16mm)
        const powerGeo = new THREE.BoxGeometry(0.0012, 0.0165, 0.0022);
        const powerBtn = new THREE.Mesh(powerGeo, btnMat);
        powerBtn.position.set(w / 2 + 0.0006, h * 0.16, 0);
        group.add(powerBtn);

        // Cần gạt Rung / Chuông Mute switch (Cạnh trái)
        const muteGeo = new THREE.BoxGeometry(0.0012, 0.0055, 0.0018);
        const muteBtn = new THREE.Mesh(muteGeo, btnMat);
        muteBtn.position.set(-w / 2 - 0.0006, h * 0.28, 0);
        group.add(muteBtn);

        // Nút Tăng âm lượng (Cạnh trái)
        const volUpGeo = new THREE.BoxGeometry(0.0012, 0.0105, 0.0022);
        const volUpBtn = new THREE.Mesh(volUpGeo, btnMat);
        volUpBtn.position.set(-w / 2 - 0.0006, h * 0.20, 0);
        group.add(volUpBtn);

        // Nút Giảm âm lượng (Cạnh trái)
        const volDownGeo = new THREE.BoxGeometry(0.0012, 0.0105, 0.0022);
        const volDownBtn = new THREE.Mesh(volDownGeo, btnMat);
        volDownBtn.position.set(-w / 2 - 0.0006, h * 0.10, 0);
        group.add(volDownBtn);

        // Cổng Lightning & dải loa dưới đáy
        const portGeo = new THREE.BoxGeometry(0.0085, 0.0020, 0.0014);
        const portMat = new THREE.MeshBasicMaterial({ color: 0x050608 });
        const port = new THREE.Mesh(portGeo, portMat);
        port.position.set(0, -h / 2 - 0.0006, 0);
        group.add(port);
    }

    addIPhoneXFrontScreen(group, w, h, d) {
        // Màn hình OLED viền mỏng với hình nền chính thức iPhone X
        const screenGeo = new THREE.PlaneGeometry(w * 0.955, h * 0.955);
        const wallpaperTex = this.textureLoader.load('/images/iphone-x/screen-wallpaper.jpg?v=2');
        wallpaperTex.colorSpace = THREE.SRGBColorSpace;
        wallpaperTex.anisotropy = Math.min(this.renderer.capabilities.getMaxAnisotropy(), 8);
        const screenMat = new THREE.MeshStandardMaterial({
            map: wallpaperTex,
            roughness: 0.12,
            metalness: 0.10
        });
        const screenMesh = new THREE.Mesh(screenGeo, screenMat);
        screenMesh.rotation.y = Math.PI;
        screenMesh.position.z = -d / 2 - 0.0020;
        group.add(screenMesh);

        // Tai thỏ đặc trưng iPhone X (The Notch)
        const notchCanvas = document.createElement('canvas');
        notchCanvas.width = 512;
        notchCanvas.height = 140;
        const nctx = notchCanvas.getContext('2d');
        nctx.fillStyle = '#050507';
        nctx.beginPath();
        nctx.moveTo(90, 0);
        nctx.lineTo(422, 0);
        nctx.quadraticCurveTo(422, 70, 380, 70);
        nctx.lineTo(132, 70);
        nctx.quadraticCurveTo(90, 70, 90, 0);
        nctx.fill();

        // Khe loa thoại và camera trước trong tai thỏ
        nctx.fillStyle = '#22242a';
        nctx.fillRect(206, 20, 100, 10);
        nctx.fillStyle = '#080c14';
        nctx.beginPath();
        nctx.arc(170, 25, 7, 0, Math.PI * 2);
        nctx.arc(335, 25, 5, 0, Math.PI * 2);
        nctx.fill();

        const notchTexture = new THREE.CanvasTexture(notchCanvas);
        notchTexture.colorSpace = THREE.SRGBColorSpace;
        const notchGeo = new THREE.PlaneGeometry(w * 0.58, h * 0.048);
        const notchMat = new THREE.MeshBasicMaterial({
            map: notchTexture,
            transparent: true
        });
        const notchMesh = new THREE.Mesh(notchGeo, notchMat);
        notchMesh.rotation.y = Math.PI;
        notchMesh.position.set(0, h * 0.468, -d / 2 - 0.0022);
        group.add(notchMesh);
    }

    // ==================================================================================
    // TẠO MÔ HÌNH IPHONE 15 PRO CHÂN THỰC 100% NHƯ HÌNH ẢNH MẪU CỦA NGƯỜI DÙNG
    // ==================================================================================
   createPhotorealisticIPhone15Pro(phoneSlug) {
    if (this.phoneMesh) {
        this.phoneGroup.remove(this.phoneMesh);
        this.phoneMesh = null;
    }

    this.phoneMeshUsesRotatedAxes = false;
    this.isIPhoneX = false;
    this.options.phoneSlug = phoneSlug;

    const group = new THREE.Group();
    group.name = "Phone_Model_Group";

    const isMax =
        phoneSlug.includes('max') ||
        phoneSlug.includes('prm');

    const width = isMax ? 0.0767 : 0.0706;
    const height = isMax ? 0.1599 : 0.1466;
    const depth = 0.00825;
    const radius = 0.0092;

    this.phoneDimensions = {
        width,
        height,
        depth,
        radius
    };

    // 1. Khung viền kim loại.
    const frameShape = this.createRoundedRectShape(
        width,
        height,
        radius
    );

    const extrudeSettings = {
        depth: depth,
        bevelEnabled: true,
        bevelSegments: 8,
        steps: 1,
        bevelSize: 0.002,
        bevelThickness: 0.002
    };

    const frameGeo = new THREE.ExtrudeGeometry(
        frameShape,
        extrudeSettings
    );

    frameGeo.center();

    this.phoneBodyMaterial = new THREE.MeshPhysicalMaterial({
        color: 0xc5b8a5,
        metalness: 0.90,
        roughness: 0.26,
        clearcoat: 0.35,
        clearcoatRoughness: 0.1,
        name: "Titanium_Frame_Mat"
    });

    this.frameMesh = new THREE.Mesh(
        frameGeo,
        this.phoneBodyMaterial
    );

    group.add(this.frameMesh);

    // 2. Các nút bấm vật lý.
    this.addPhysicalButtons(
        group,
        width,
        height,
        depth
    );

    // 3. Mặt lưng kính.
    const backGlassGeo = new THREE.PlaneGeometry(
        width * 0.965,
        height * 0.965
    );

    const appleLogoTexture = this.generateAppleLogoTexture(
        0xd2c6b4
    );

    this.backGlassMaterial = new THREE.MeshPhysicalMaterial({
        color: 0xd2c6b4,
        map: appleLogoTexture,
        roughness: 0.40,
        metalness: 0.16,
        clearcoat: 0.65,
        clearcoatRoughness: 0.15
    });

    const backGlassMesh = new THREE.Mesh(
        backGlassGeo,
        this.backGlassMaterial
    );

    backGlassMesh.position.z = depth / 2 + 0.0020;
    group.add(backGlassMesh);

    // 4. Màn hình phía trước.
    const screenGeo = new THREE.PlaneGeometry(
        width * 0.96,
        height * 0.96
    );

    const screenMat = new THREE.MeshStandardMaterial({
        color: 0x050505,
        roughness: 0.05,
        metalness: 0.95
    });

    const screenMesh = new THREE.Mesh(
        screenGeo,
        screenMat
    );

    screenMesh.rotation.y = Math.PI;
    screenMesh.position.z = -depth / 2 - 0.0020;

    group.add(screenMesh);

    // 5. Cụm camera.
    const bumpW = width * 0.47;
    const bumpH = height * 0.265;

    const bumpShape = this.createRoundedRectShape(
        bumpW,
        bumpH,
        0.0065
    );

    const bumpGeo = new THREE.ExtrudeGeometry(
        bumpShape,
        {
            depth: 0.0024,
            bevelEnabled: true,
            bevelSegments: 6,
            bevelSize: 0.0014,
            bevelThickness: 0.0014
        }
    );

    bumpGeo.center();

    const camBumpMat = new THREE.MeshPhysicalMaterial({
        color: 0xc8bcab,
        roughness: 0.20,
        metalness: 0.45,
        clearcoat: 0.95,
        clearcoatRoughness: 0.08
    });

    const camBump = new THREE.Mesh(
        bumpGeo,
        camBumpMat
    );

    const bumpX = -width * 0.225;
    const bumpY = height * 0.33;

    camBump.position.set(
        bumpX,
        bumpY,
        depth / 2 + 0.0031
    );

    group.add(camBump);

    // Lưu thông số camera để tạo lỗ khoét trên ốp.
    this.cameraPlateauInfo = {
        x: bumpX,
        y: bumpY,
        width: bumpW + 0.0030,
        height: bumpH + 0.0030,
        radius: 0.007
    };

    // 6. Ba ống kính camera.
    const cameraPositions = [
        {
            x: bumpX - bumpW * 0.22,
            y: bumpY + bumpH * 0.23
        },
        {
            x: bumpX - bumpW * 0.22,
            y: bumpY - bumpH * 0.23
        },
        {
            x: bumpX + bumpW * 0.22,
            y: bumpY
        }
    ];

    cameraPositions.forEach(pos => {
        const ringGeo = new THREE.CylinderGeometry(
            0.0092,
            0.0092,
            0.0028,
            36
        );

        const ringMat = new THREE.MeshStandardMaterial({
            color: 0xd8c8b0,
            roughness: 0.15,
            metalness: 0.95
        });

        const ringMesh = new THREE.Mesh(
            ringGeo,
            ringMat
        );

        ringMesh.rotation.x = Math.PI / 2;
        ringMesh.position.set(
            pos.x,
            pos.y,
            depth / 2 + 0.0048
        );

        group.add(ringMesh);

        const innerBezelGeo = new THREE.CylinderGeometry(
            0.0076,
            0.0076,
            0.0030,
            32
        );

        const innerBezelMat = new THREE.MeshStandardMaterial({
            color: 0x121214,
            roughness: 0.85
        });

        const innerMesh = new THREE.Mesh(
            innerBezelGeo,
            innerBezelMat
        );

        innerMesh.rotation.x = Math.PI / 2;
        innerMesh.position.set(
            pos.x,
            pos.y,
            depth / 2 + 0.0049
        );

        group.add(innerMesh);

        const lensGlassGeo = new THREE.SphereGeometry(
            0.0062,
            32,
            16,
            0,
            Math.PI * 2,
            0,
            Math.PI / 2
        );

        const lensGlassMat = new THREE.MeshPhysicalMaterial({
            color: 0x121426,
            roughness: 0.02,
            metalness: 0.35,
            transmission: 0.25,
            clearcoat: 1.0,
            clearcoatRoughness: 0.05
        });

        const lensGlass = new THREE.Mesh(
            lensGlassGeo,
            lensGlassMat
        );

        lensGlass.position.set(
            pos.x,
            pos.y,
            depth / 2 + 0.0055
        );

        group.add(lensGlass);
    });

    // 7. Đèn Flash.
    const flashGeo = new THREE.CylinderGeometry(
        0.0035,
        0.0035,
        0.0015,
        24
    );

    const flashMat = new THREE.MeshStandardMaterial({
        color: 0xfffae6,
        roughness: 0.2,
        metalness: 0.3
    });

    const flash = new THREE.Mesh(
        flashGeo,
        flashMat
    );

    flash.rotation.x = Math.PI / 2;
    flash.position.set(
        bumpX + bumpW * 0.22,
        bumpY + bumpH * 0.28,
        depth / 2 + 0.0045
    );

    group.add(flash);

    // 8. Cảm biến LiDAR.
    const lidarGeo = new THREE.CylinderGeometry(
        0.0036,
        0.0036,
        0.0015,
        24
    );

    const lidarMat = new THREE.MeshStandardMaterial({
        color: 0x161618,
        roughness: 0.9,
        metalness: 0.1
    });

    const lidar = new THREE.Mesh(
        lidarGeo,
        lidarMat
    );

    lidar.rotation.x = Math.PI / 2;
    lidar.position.set(
        bumpX + bumpW * 0.22,
        bumpY - bumpH * 0.28,
        depth / 2 + 0.0045
    );

    group.add(lidar);

    // 9. Lỗ Micro.
    const micGeo = new THREE.CylinderGeometry(
        0.0009,
        0.0009,
        0.0016,
        16
    );

    const micMat = new THREE.MeshBasicMaterial({
        color: 0x050505
    });

    const mic = new THREE.Mesh(
        micGeo,
        micMat
    );

    mic.rotation.x = Math.PI / 2;
    mic.position.set(
        bumpX,
        bumpY - bumpH * 0.28,
        depth / 2 + 0.0045
    );

    group.add(mic);

    group.rotation.set(0, 0, 0);
    group.position.set(0, 0, 0);

    this.phoneMesh = group;
    this.phoneGroup.add(this.phoneMesh);

    this.phoneModelBaseSize = new THREE.Vector3(
        width,
        height,
        depth
    );

    this.phoneModelBaseScale = this.phoneMesh.scale.clone();

    console.log(`Đã tạo mô hình dự phòng: ${phoneSlug}`);
}
    // Thêm các nút bấm vật lý (Power, Action, Volume) vào thân máy
    addPhysicalButtons(group, w, h, d) {
        const btnMat = this.phoneBodyMaterial;

        // Nút Nguồn (Power button - Cạnh phải)
        const powerGeo = new THREE.BoxGeometry(0.0012, 0.016, 0.0022);
        const powerBtn = new THREE.Mesh(powerGeo, btnMat);
        powerBtn.position.set(w / 2 + 0.0006, h * 0.15, 0);
        group.add(powerBtn);

        // Nút Action Button (Cạnh trái trên)
        const actionGeo = new THREE.BoxGeometry(0.0012, 0.0085, 0.0022);
        const actionBtn = new THREE.Mesh(actionGeo, btnMat);
        actionBtn.position.set(-w / 2 - 0.0006, h * 0.26, 0);
        group.add(actionBtn);

        // Nút Tăng âm lượng (Volume Up - Cạnh trái)
        const volUpGeo = new THREE.BoxGeometry(0.0012, 0.013, 0.0022);
        const volUpBtn = new THREE.Mesh(volUpGeo, btnMat);
        volUpBtn.position.set(-w / 2 - 0.0006, h * 0.16, 0);
        group.add(volUpBtn);

        // Nút Giảm âm lượng (Volume Down - Cạnh trái)
        const volDownGeo = new THREE.BoxGeometry(0.0012, 0.013, 0.0022);
        const volDownBtn = new THREE.Mesh(volDownGeo, btnMat);
        volDownBtn.position.set(-w / 2 - 0.0006, h * 0.06, 0);
        group.add(volDownBtn);
    }

    // ==================================================================================
    // XÂY DỰNG ỐP LƯNG 3D ÔM SÁT VỚI LỖ KHOÉT CAMERA CHUẨN XÁC (KHÔNG BỊ HỘP CARTON!)
    // ==================================================================================
    buildFitted3DCase() {
        this.caseModelRequestId++;
        this.caseModelUrl = null;
        this.caseModelRequestUrl = null;
        if (this.caseMesh) {
            this.phoneGroup.remove(this.caseMesh);
            this.caseMesh.traverse(object => {
                if (object.geometry) object.geometry.dispose();
            });
        }

        const dims = this.phoneDimensions || { width: 0.0706, height: 0.1466, depth: 0.00825, radius: 0.0092 };
        const cam = this.cameraPlateauInfo || { x: -0.016, y: 0.048, width: 0.035, height: 0.040, radius: 0.007 };

        const caseW = dims.width + 0.0008;
        const caseH = dims.height + 0.0008;
        const caseRadius = dims.radius + 0.0004;

        // Keep only a thin clearance around the phone so the case does not look oversized.
        const rimShape = this.createRoundedRectShape(caseW, caseH, caseRadius);
        const innerWidth = dims.width + 0.0002;
        const innerHeight = dims.height + 0.0002;
        rimShape.holes.push(this.createRoundedRectPath(
            -innerWidth / 2,
            -innerHeight / 2,
            innerWidth,
            innerHeight,
            Math.max(0.001, dims.radius - 0.0002)
        ));
        const rimGeo = new THREE.ExtrudeGeometry(rimShape, {
            depth: dims.depth + 0.0004,
            bevelEnabled: false,
            steps: 1
        });
        rimGeo.center();

        // 1. Tạo Shape mặt lưng của ốp có LỖ KHOÉT CAMERA (Camera Cutout Hole)
        const caseBackShape = this.createRoundedRectShape(caseW, caseH, caseRadius);

        // Tạo lỗ khoét camera bo cong góc tương ứng
        const holePath = new THREE.Path();
        const hx = cam.x - cam.width / 2;
        const hy = cam.y - cam.height / 2;
        const hr = cam.radius;
        const hw = cam.width;
        const hh = cam.height;

        holePath.moveTo(hx + hr, hy);
        holePath.lineTo(hx + hw - hr, hy);
        holePath.quadraticCurveTo(hx + hw, hy, hx + hw, hy + hr);
        holePath.lineTo(hx + hw, hy + hh - hr);
        holePath.quadraticCurveTo(hx + hw, hy + hh, hx + hw - hr, hy + hh);
        holePath.lineTo(hx + hr, hy + hh);
        holePath.quadraticCurveTo(hx, hy + hh, hx, hy + hh - hr);
        holePath.lineTo(hx, hy + hr);
        holePath.quadraticCurveTo(hx, hy, hx + hr, hy);

        // Thêm lỗ khoét vào Shape của ốp
        caseBackShape.holes.push(holePath);

        // Extrude mặt lưng ốp
        const caseBackGeo = new THREE.ExtrudeGeometry(caseBackShape, {
            depth: 0.0006,
            bevelEnabled: true,
            bevelSegments: 2,
            steps: 1,
            bevelSize: 0.0001,
            bevelThickness: 0.0001
        });
        caseBackGeo.center();
        const positions = caseBackGeo.attributes.position;
        const uvs = caseBackGeo.attributes.uv;
        for (let i = 0; i < positions.count; i++) {
            uvs.setXY(
                i,
                (positions.getX(i) + caseW / 2) / caseW,
                (positions.getY(i) + caseH / 2) / caseH
            );
        }
        uvs.needsUpdate = true;

        // 2. Vật liệu ốp lưng PBR cao cấp
        this.caseMaterial = new THREE.MeshPhysicalMaterial({
            color: 0xffffff,
            roughness: 0.1,
            metalness: 0.05,
            clearcoat: 1.0,
            clearcoatRoughness: 0.05,
            transparent: true,
            opacity: 0.70,
            transmission: 0.85,
            ior: 1.5,
            map: this.caseTexture,
            polygonOffset: true,
            polygonOffsetFactor: -1.0,
            polygonOffsetUnits: -1.0
        });
        this.caseEdgeMaterial = new THREE.MeshPhysicalMaterial({
            color: 0xe8e5e3,
            roughness: 0.32,
            metalness: 0.02,
            clearcoat: 0.55,
            clearcoatRoughness: 0.18
        });

        const caseGroup = new THREE.Group();
        caseGroup.name = "Custom_3D_Case_Group";

        const rimMesh = new THREE.Mesh(rimGeo, this.caseEdgeMaterial);
        caseGroup.add(rimMesh);

        const backMesh = new THREE.Mesh(caseBackGeo, this.caseMaterial);
        backMesh.position.z = dims.depth / 2 + 0.0026;
        caseGroup.add(backMesh);

        // 3. Gờ bảo vệ cụm camera nhô cao (Raised Camera Bezel Protection Ring)
        const lipWidth = cam.width + 0.0006;
        const lipHeight = cam.height + 0.0006;
        const lipShape = this.createRoundedRectShape(lipWidth, lipHeight, cam.radius + 0.0003);
        const lipHolePath = new THREE.Path();
        const lipHoleX = -cam.width / 2;
        const lipHoleY = -cam.height / 2;
        lipHolePath.moveTo(lipHoleX + hr, lipHoleY);
        lipHolePath.lineTo(lipHoleX + hw - hr, lipHoleY);
        lipHolePath.quadraticCurveTo(lipHoleX + hw, lipHoleY, lipHoleX + hw, lipHoleY + hr);
        lipHolePath.lineTo(lipHoleX + hw, lipHoleY + hh - hr);
        lipHolePath.quadraticCurveTo(lipHoleX + hw, lipHoleY + hh, lipHoleX + hw - hr, lipHoleY + hh);
        lipHolePath.lineTo(lipHoleX + hr, lipHoleY + hh);
        lipHolePath.quadraticCurveTo(lipHoleX, lipHoleY + hh, lipHoleX, lipHoleY + hh - hr);
        lipHolePath.lineTo(lipHoleX, lipHoleY + hr);
        lipHolePath.quadraticCurveTo(lipHoleX, lipHoleY, lipHoleX + hr, lipHoleY);
        lipShape.holes.push(lipHolePath);
        const lipGeo = new THREE.ExtrudeGeometry(lipShape, {
            depth: 0.0008,
            bevelEnabled: true,
            bevelSegments: 2,
            bevelSize: 0.0001,
            bevelThickness: 0.0001
        });
        lipGeo.center();

        const lipMesh = new THREE.Mesh(lipGeo, this.caseEdgeMaterial);
        lipMesh.position.set(
            cam.x,
            cam.y,
            dims.depth / 2 + 0.0034
        );
        caseGroup.add(lipMesh);

        // Giữ vị trí và góc xoay chuẩn xác ôm sát thân máy
        caseGroup.rotation.set(0, 0, 0);
        caseGroup.position.set(0, 0, 0);

        this.caseMesh = caseGroup;
        this.caseRimMesh = rimMesh;
        this.caseLipMesh = lipMesh;
        this.phoneGroup.add(this.caseMesh);
    }

    getDefaultCaseModelUrl(phoneSlug = this.options.phoneSlug) {
        return '';
    }

    async loadCaseModel(modelUrl) {
        if (modelUrl === this.caseModelUrl || modelUrl === this.caseModelRequestUrl) return;
        const requestId = ++this.caseModelRequestId;
        this.caseModelRequestUrl = modelUrl;
        try {
            const gltf = await this.gltfLoader.loadAsync(modelUrl);
            if (requestId !== this.caseModelRequestId) return;

            const dims = this.phoneDimensions;
            const caseDepth = dims.depth + 0.0012;
            const targetSize = new THREE.Vector3(dims.width + 0.0008, dims.height + 0.0008, caseDepth);
            const model = gltf.scene;
            model.updateMatrixWorld(true);
            const sourceBounds = new THREE.Box3().setFromObject(model);
            const sourceSize = sourceBounds.getSize(new THREE.Vector3());
            if (sourceSize.x <= 0 || sourceSize.y <= 0 || sourceSize.z <= 0) {
                throw new Error(`Mô hình ốp "${modelUrl}" không có kích thước hợp lệ.`);
            }

            model.scale.set(
                targetSize.x / sourceSize.x,
                targetSize.y / sourceSize.y,
                targetSize.z / sourceSize.z
            );
            model.updateMatrixWorld(true);
            const scaledBounds = new THREE.Box3().setFromObject(model);
            model.position.sub(scaledBounds.getCenter(new THREE.Vector3()));

            const fittedCase = new THREE.Group();
            fittedCase.name = 'Phone_Case_Model';
            fittedCase.position.z = dims.depth / 2 + caseDepth / 2;
            fittedCase.add(model);
            fittedCase.traverse(object => {
                if (!object.isMesh) return;
                object.castShadow = true;
                object.receiveShadow = true;
            });

            if (this.caseMesh) {
                this.phoneGroup.remove(this.caseMesh);
                this.caseMesh.traverse(object => {
                    if (object.geometry) object.geometry.dispose();
                });
            }
            this.caseMesh = fittedCase;
            this.caseRimMesh = null;
            this.caseLipMesh = null;
            this.caseModelUrl = modelUrl;
            this.phoneGroup.add(this.caseMesh);
        } catch (error) {
            if (requestId === this.caseModelRequestId) {
                console.error(`Không tải được mô hình ốp "${modelUrl}".`, error);
            }
        } finally {
            if (requestId === this.caseModelRequestId) {
                this.caseModelRequestUrl = null;
            }
        }
    }

    // ==================================================================================
    // CÁC KIỂU DÁNG ỐP LƯNG CHUYÊN NGHIỆP (0ms DELAY)
    // ==================================================================================
    setCaseStyle(caseCode, productOptions = null) {
        this.currentCaseStyle = caseCode || 'OL01';
        this.currentCaseOptions = productOptions;
        if (!this.caseMaterial) return;

        const modelUrl = productOptions?.modelUrl || this.getDefaultCaseModelUrl();
        if (modelUrl && modelUrl !== this.caseModelUrl) {
            this.caseModelLoadPromise = this.loadCaseModel(modelUrl);
        } else if (!modelUrl && this.caseModelUrl) {
            this.buildFitted3DCase();
        }

        const ctx = this.caseCtx;
        const cvs = this.caseCanvas;
        ctx.clearRect(0, 0, cvs.width, cvs.height);

        // Sản phẩm do Admin nhập: dùng ảnh thật làm texture trên mặt lưng ốp 3D.
        // Hình dáng ốp vẫn được dựng tự động theo kích thước điện thoại đang tải.
        if (productOptions && productOptions.textureUrl) {
            const material = String(productOptions.materialType || 'Silicone').toLowerCase();
            this.caseMaterial.color.set(0xffffff);
            this.caseMaterial.transparent = material.includes('clear') || material.includes('trong');
            this.caseMaterial.opacity = this.caseMaterial.transparent ? 0.78 : 1.0;
            this.caseMaterial.transmission = this.caseMaterial.transparent ? 0.35 : 0.0;
            this.caseMaterial.roughness = material.includes('silicone') ? 0.72 : (material.includes('leather') || material.includes('da') ? 0.82 : 0.38);
            this.caseMaterial.metalness = 0.02;
            this.caseMaterial.clearcoat = material.includes('silicone') ? 0.18 : 0.55;
            this.caseEdgeMaterial.color.set(
                material.includes('pink') || material.includes('hồng') ? 0xe9b8c5 : 0xe8e5e3
            );
            this.caseEdgeMaterial.transparent = material.includes('clear')
                || material.includes('trong')
                || material.includes('silicone');
            this.caseEdgeMaterial.opacity = this.caseEdgeMaterial.transparent ? 0.62 : 1;
            this.caseEdgeMaterial.transmission = this.caseEdgeMaterial.transparent ? 0.45 : 0;
            this.caseEdgeMaterial.roughness = material.includes('silicone') ? 0.42 : 0.3;
            this.caseEdgeMaterial.needsUpdate = true;

            const image = new Image();
            image.onload = () => {
                // Cắt ảnh theo tỉ lệ dọc của mặt lưng, tránh méo ảnh sản phẩm.
                const sourceRatio = image.width / image.height;
                const targetRatio = cvs.width / cvs.height;
                let sx = 0, sy = 0, sw = image.width, sh = image.height;
                if (sourceRatio > targetRatio) {
                    sw = image.height * targetRatio;
                    sx = (image.width - sw) / 2;
                } else {
                    sh = image.width / targetRatio;
                    sy = (image.height - sh) / 2;
                }
                ctx.clearRect(0, 0, cvs.width, cvs.height);
                ctx.drawImage(image, sx, sy, sw, sh, 0, 0, cvs.width, cvs.height);
                if (this.currentEngraveText) this.renderEngravingText(ctx, cvs.width, cvs.height, this.currentEngraveText);
                this.caseTexture.needsUpdate = true;
            };
            image.onerror = () => console.warn('Không tải được ảnh texture ốp:', productOptions.textureUrl);
            image.src = productOptions.textureUrl;
            this.caseTexture.needsUpdate = true;
            this.caseMaterial.map = this.caseTexture;
            this.caseMaterial.needsUpdate = true;
            return;
        }

        this.caseMaterial.map = this.caseTexture;

        // OL01: ỐP TRONG SUỐT MAGSAFE (CLEAR MAGSAFE CASE)
        if (caseCode === 'OL01' || caseCode.includes('Trong Suốt') || caseCode.includes('MagSafe')) {
            this.caseMaterial.color.set(0xffffff);
            this.caseMaterial.transparent = true;
            this.caseMaterial.opacity = 0.65;
            this.caseMaterial.transmission = 0.88;
            this.caseMaterial.roughness = 0.06;
            this.caseMaterial.metalness = 0.02;
            this.caseMaterial.clearcoat = 1.0;

            // Vẽ vòng nam châm MagSafe màu trắng chuẩn xác
            this.drawMagSafeRing(ctx, cvs.width, cvs.height);
        }
        // OL02: ỐP DA BÒ THUỘC TITAN GOLD (LUXURY LEATHER CASE)
        else if (caseCode === 'OL02' || caseCode.includes('Da')) {
            this.caseMaterial.color.set(0xb38654); // Da bò màu Caramel / Titan Gold
            this.caseMaterial.transparent = false;
            this.caseMaterial.opacity = 1.0;
            this.caseMaterial.transmission = 0.0;
            this.caseMaterial.roughness = 0.78;
            this.caseMaterial.metalness = 0.06;
            this.caseMaterial.clearcoat = 0.25;

            // Vẽ vân da và đường chỉ may thủ công (Saddle Stitching)
            this.drawLeatherPattern(ctx, cvs.width, cvs.height);
        }
        // OL03: ỐP SỢI CARBON SPORT (CARBON FIBER CASE)
        else if (caseCode === 'OL03' || caseCode.includes('Carbon')) {
            this.caseMaterial.color.set(0x222225); // Đen sợi carbon
            this.caseMaterial.transparent = false;
            this.caseMaterial.opacity = 1.0;
            this.caseMaterial.transmission = 0.0;
            this.caseMaterial.roughness = 0.38;
            this.caseMaterial.metalness = 0.32;
            this.caseMaterial.clearcoat = 0.55;

            // Vẽ họa tiết sợi dệt carbon đa giác
            this.drawCarbonFiberPattern(ctx, cvs.width, cvs.height);
        }
        // OL04: ỐP LIQUID SILICONE CAO CẤP (SILICONE CASE)
        else {
            this.caseMaterial.color.set(0x3a4252); // Xanh Navy Titan sang trọng
            this.caseMaterial.transparent = false;
            this.caseMaterial.opacity = 1.0;
            this.caseMaterial.transmission = 0.0;
            this.caseMaterial.roughness = 0.88;
            this.caseMaterial.metalness = 0.02;
            this.caseMaterial.clearcoat = 0.05;

            this.drawSiliconeFinish(ctx, cvs.width, cvs.height);
        }

        // Vẽ lại chữ khắc nếu có
        if (this.currentEngraveText) {
            this.renderEngravingText(ctx, cvs.width, cvs.height, this.currentEngraveText);
        }

        this.caseTexture.needsUpdate = true;
        this.caseMaterial.needsUpdate = true;
    }

    // Vẽ vòng nam châm MagSafe chuẩn xác ở giữa lưng máy
    drawMagSafeRing(ctx, w, h) {
        ctx.save();
        const centerX = w / 2;
        const centerY = h / 2 + 80;
        const ringRadius = 260;

        // Vòng tròn MagSafe chính
        ctx.lineWidth = 26;
        ctx.strokeStyle = "rgba(255, 255, 255, 0.88)";
        ctx.shadowColor = "rgba(0, 0, 0, 0.25)";
        ctx.shadowBlur = 10;
        ctx.beginPath();
        ctx.arc(centerX, centerY, ringRadius, 0, Math.PI * 2);
        ctx.stroke();

        // Thanh căn chỉnh dọc ở dưới vòng tròn (Alignment Bar)
        ctx.fillStyle = "rgba(255, 255, 255, 0.88)";
        ctx.beginPath();
        ctx.roundRect(centerX - 13, centerY + ringRadius + 40, 26, 90, 12);
        ctx.fill();

        ctx.restore();
    }

    // Vẽ vân da và đường chỉ may thủ công (Leather Stitching)
    drawLeatherPattern(ctx, w, h) {
        ctx.save();
        ctx.fillStyle = "#8d643a";
        ctx.fillRect(0, 0, w, h);

        // Hạt vân da vi mô
        for (let i = 0; i < 4000; i++) {
            const rx = Math.random() * w;
            const ry = Math.random() * h;
            ctx.fillStyle = Math.random() > 0.5 ? "rgba(0,0,0,0.06)" : "rgba(255,255,255,0.04)";
            ctx.fillRect(rx, ry, 3, 3);
        }

        // Đường chỉ may viền đứt nét (Saddle Stitching)
        ctx.strokeStyle = "rgba(240, 220, 180, 0.85)";
        ctx.lineWidth = 6;
        ctx.setLineDash([18, 14]);
        ctx.strokeRect(50, 50, w - 100, h - 100);

        ctx.restore();
    }

    // Vẽ sợi dệt Carbon Kevlar đa chiều
    drawCarbonFiberPattern(ctx, w, h) {
        ctx.save();
        ctx.fillStyle = "#161618";
        ctx.fillRect(0, 0, w, h);

        const step = 20;
        for (let y = 0; y < h; y += step) {
            for (let x = 0; x < w; x += step) {
                const isEven = ((x / step) + (y / step)) % 2 === 0;
                ctx.fillStyle = isEven ? "rgba(45, 45, 52, 0.95)" : "rgba(18, 18, 20, 0.95)";
                ctx.fillRect(x, y, step, step);

                // Đường sợi vân chéo
                ctx.strokeStyle = isEven ? "rgba(70, 70, 80, 0.35)" : "rgba(0, 0, 0, 0.4)";
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(x, y);
                ctx.lineTo(x + step, y + step);
                ctx.stroke();
            }
        }
        ctx.restore();
    }

    // Hoàn thiện Liquid Silicone mịn màng
    drawSiliconeFinish(ctx, w, h) {
        ctx.save();
        ctx.fillStyle = "#2c3340";
        ctx.fillRect(0, 0, w, h);

        // Logo Apple chìm tinh tế
        ctx.translate(w / 2, h / 2 + 50);
        ctx.scale(0.8, 0.8);
        ctx.fillStyle = "rgba(0, 0, 0, 0.15)";
        ctx.beginPath();
        ctx.arc(-30, -15, 50, 0, Math.PI * 2);
        ctx.arc(30, -15, 50, 0, Math.PI * 2);
        ctx.arc(-25, 30, 55, 0, Math.PI * 2);
        ctx.arc(25, 30, 55, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
    }

    // Vẽ chữ khắc Laser tùy biến lên ốp
    renderEngravingText(ctx, w, h, text) {
        if (!text || text.trim().length === 0) return;

        ctx.save();
        ctx.fillStyle = this.currentCaseStyle === 'OL01' ? 'rgba(255,255,255,0.95)' : 'rgba(235, 235, 240, 0.9)';
        ctx.shadowColor = 'rgba(0, 0, 0, 0.7)';
        ctx.shadowBlur = 8;
        ctx.font = 'bold 54px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(text, w / 2, h - 350);
        ctx.restore();
    }

    // Bật / tắt hiển thị ốp lưng (Xem máy trần nguyên bản giống y ảnh mẫu)
    toggleCaseVisibility() {
        this.isCaseVisible = !this.isCaseVisible;
        if (this.caseMesh) {
            this.caseMesh.visible = this.isCaseVisible;
        }
        return this.isCaseVisible;
    }

    // Cập nhật chữ khắc
    updateEngraving(text) {
        this.currentEngraveText = text;
        this.setCaseStyle(this.currentCaseStyle, this.currentCaseOptions);
    }

    // Đổi màu vỏ thân máy nguyên bản (Bạc, Xám không gian, Titan Tự Nhiên, Titan Xanh, Đen, Trắng)
    changePhoneColor(hexColor) {
        if (this.phoneBodyMaterial) {
            this.phoneBodyMaterial.color.set(hexColor);
        }
        if (this.backGlassMaterial) {
            const intVal = parseInt(hexColor.replace('#', '0x'), 16);
            this.backGlassMaterial.color.set(hexColor);
            if (!this.isIPhoneX) {
                this.backGlassMaterial.map = this.generateAppleLogoTexture(intVal);
            }
            this.backGlassMaterial.needsUpdate = true;
        }
    }

    // Tách ốp (Exploded / Disassembly View Animation)
    toggleExplodedView() {
        this.isExploded = !this.isExploded;
        this.targetCaseX = this.isExploded ? 0.066 : 0.0;
        return this.isExploded;
    }

    // Tải ảnh Snapshot chất lượng cao về máy
    downloadSnapshot(filename = 'iPhone15Pro_3DTryOn.jpg') {
        this.renderer.render(this.scene, this.camera);
        const dataUrl = this.renderer.domElement.toDataURL("image/jpeg", 0.95);
        const link = document.createElement('a');
        link.download = filename;
        link.href = dataUrl;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // Reset góc nhìn về chuẩn 3/4 mặt lưng giống ảnh mẫu
    resetCameraView() {
        this.camera.position.set(0.065, 0.008, 0.30);
        this.controls.target.set(0, 0, 0);
        this.controls.update();
    }

    // ==================================================================================
    // HELPERS HÌNH HỌC VÀ TEXTURE
    // ==================================================================================
    createRoundedRectShape(w, h, r) {
        const shape = new THREE.Shape();
        const x = -w / 2;
        const y = -h / 2;
        shape.moveTo(x + r, y);
        shape.lineTo(x + w - r, y);
        shape.quadraticCurveTo(x + w, y, x + w, y + r);
        shape.lineTo(x + w, y + h - r);
        shape.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
        shape.lineTo(x + r, y + h);
        shape.quadraticCurveTo(x, y + h, x, y + h - r);
        shape.lineTo(x, y + r);
        shape.quadraticCurveTo(x, y, x + r, y);
        return shape;
    }

    createRoundedRectPath(x, y, w, h, r) {
        const path = new THREE.Path();
        path.moveTo(x + r, y);
        path.lineTo(x + w - r, y);
        path.quadraticCurveTo(x + w, y, x + w, y + r);
        path.lineTo(x + w, y + h - r);
        path.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
        path.lineTo(x + r, y + h);
        path.quadraticCurveTo(x, y + h, x, y + h - r);
        path.lineTo(x, y + r);
        path.quadraticCurveTo(x, y, x + r, y);
        return path;
    }

    // Vẽ Logo Apple ánh kim sắc nét ở trung tâm mặt lưng
    generateAppleLogoTexture(baseColorHex) {
        const canvas = document.createElement('canvas');
        canvas.width = 1024;
        canvas.height = 2048;
        const ctx = canvas.getContext('2d');

        // Nền mặt lưng
        ctx.fillStyle = `#${baseColorHex.toString(16).padStart(6, '0')}`;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Logo Apple ánh kim ở giữa
        ctx.save();
        ctx.translate(512, 1024);
        ctx.scale(1.05, 1.05);

        ctx.fillStyle = "rgba(165, 150, 132, 0.42)";

        // Lá quả táo
        ctx.beginPath();
        ctx.ellipse(8, -130, 24, 40, Math.PI / 4, 0, Math.PI * 2);
        ctx.fill();

        // Thân quả táo
        ctx.beginPath();
        ctx.arc(-44, -20, 70, 0, Math.PI * 2);
        ctx.arc(44, -20, 70, 0, Math.PI * 2);
        ctx.arc(-36, 45, 78, 0, Math.PI * 2);
        ctx.arc(36, 45, 78, 0, Math.PI * 2);
        ctx.fill();

        // Vết cắn khuyết
        ctx.globalCompositeOperation = 'destination-out';
        ctx.beginPath();
        ctx.arc(92, -10, 50, 0, Math.PI * 2);
        ctx.fill();

        // Khuyết trên
        ctx.beginPath();
        ctx.arc(0, -92, 24, 0, Math.PI * 2);
        ctx.fill();

        ctx.restore();

        const tex = new THREE.CanvasTexture(canvas);
        tex.colorSpace = THREE.SRGBColorSpace;
        tex.flipY = false;
        tex.anisotropy = Math.min(this.renderer.capabilities.getMaxAnisotropy(), 8);
        return tex;
    }

    onResize() {
        this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 3));
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        // Hiệu ứng Lerp mượt mà khi tách hoặc lắp ốp
        if (this.caseMesh) {
            this.caseMesh.position.x += (this.targetCaseX - this.caseMesh.position.x) * 0.12;
            const targetCaseZ = Math.tan(this.phoneGroup.rotation.y) * this.targetCaseX;
            this.caseMesh.position.z += (targetCaseZ - this.caseMesh.position.z) * 0.12;
        }

        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }
}
