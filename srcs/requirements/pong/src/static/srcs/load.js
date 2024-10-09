import * as THREE from '../js/three.module.js';
import { GLTFLoader } from '../js/GLTFLoader.js';
import { STLLoader } from '../js/STLLoader.js';

const host = window.location.hostname;
const port = window.location.port;

function loadModelGLT(url) {
    return new Promise((resolve, reject) => {
        const loader = new GLTFLoader();
        
        loader.load(`http://${host}:${port}/api/pong/static/pong/models/` + url, function (gltf) {
            resolve(gltf);
        }, undefined, function (error) {
            reject(error);
        });
    });
}

function loadModelSTL(url) {
    return new Promise((resolve, reject) => {
        const loader = new STLLoader();
        loader.load(`http://${host}:${port}/api/pong/static/pong/models/` + url, resolve, undefined, reject);
    });
};

function loadTexture(url) {
    
    return new Promise((resolve, reject) => {
        const loader = new THREE.TextureLoader();
        
        loader.load(`http://${host}:${port}/api/pong/static/pong/texture/` + url, function (texture) {
            resolve(texture);
        }, undefined, function (error) {
            reject(error);
        });
    });
}

export { loadModelGLT, loadModelSTL, loadTexture };