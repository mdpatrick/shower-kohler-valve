import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
const host=document.querySelector('#viewport'),status=document.querySelector('#model-status');
try {
  const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setSize(host.clientWidth,host.clientHeight);renderer.localClippingEnabled=true;host.append(renderer.domElement);
  const scene=new THREE.Scene();scene.background=new THREE.Color('#e5e9eb');
  const camera=new THREE.PerspectiveCamera(42,host.clientWidth/host.clientHeight,.001,10);camera.position.set(0,.04,.68);
  const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(0,.04,0);controls.enableDamping=true;
  scene.add(new THREE.HemisphereLight(0xffffff,0x75808b,2));const light=new THREE.DirectionalLight(0xffffff,2);light.position.set(1,2,3);scene.add(light);
  let model,measure=false,points=[],targets=[];
  const category=n=>n.startsWith('WALL')?'wall':n.startsWith('GASKET')?'gasket':n.startsWith('PLATE')||n.endsWith('NUT')?'inner':n.startsWith('TRIM')||n.startsWith('HANDLE')?'outer':n.startsWith('CUSTOM')?'custom':n.startsWith('NEW-SEAL')?'seal':'hardware';
  function apply(){if(!model)return;const explode=Number(document.querySelector('#explode').value);model.children.forEach(o=>{const g=category(o.name);o.visible=document.querySelector(`[data-layer="${g}"]`)?.checked??false;o.position.copy(o.userData.original);o.position.z+=explode*({custom:.03,seal:.025,gasket:.065,inner:.10,outer:.18,hardware:0,wall:0}[g]);});}
  new GLTFLoader().load('installation_DRAFT.glb',g=>{model=g.scene;scene.add(model);model.children.forEach(o=>{o.userData.original=o.position.clone();o.traverse(n=>{if(n.isMesh)targets.push(n);});});apply();status.textContent='Local model loaded. Drag to orbit; scroll to zoom. Scale remains provisional.';window.reviewModelLoaded=true;window.reviewModelNodes=model.children.map(o=>o.name);},undefined,e=>{status.textContent='3D unavailable. All annotated and section views below remain usable.';console.error(e);});
  document.querySelectorAll('[data-layer]').forEach(el=>el.onchange=apply);document.querySelector('#explode').oninput=apply;
  document.querySelectorAll('[data-state]').forEach(b=>b.onclick=()=>{document.querySelectorAll('[data-layer]').forEach(el=>el.checked=b.dataset.state==='observed'?el.dataset.layer==='wall':el.dataset.layer!=='hardware');document.querySelector('#explode').value=0;apply();});
  document.querySelector('[data-view="front"]').onclick=()=>{camera.position.set(0,.04,.68);controls.target.set(0,.04,0);controls.update();};
  document.querySelector('[data-view="oblique"]').onclick=()=>{camera.position.set(.36,.24,.5);controls.target.set(0,.04,0);controls.update();};
  document.querySelector('#section').onchange=e=>renderer.clippingPlanes=e.target.checked?[new THREE.Plane(new THREE.Vector3(-1,0,0),.0008)]:[];
  const ray=new THREE.Raycaster();document.querySelector('#measure-mesh').onclick=()=>{measure=!measure;points=[];status.textContent=measure?'Click two visible mesh points. Result is approximate, not a CAD or physical measurement.':'Mesh measurement off.';};
  renderer.domElement.addEventListener('click',e=>{if(!measure||!model)return;const r=renderer.domElement.getBoundingClientRect();ray.setFromCamera(new THREE.Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),camera);const visible=o=>{while(o){if(!o.visible)return false;o=o.parent;}return true;};const hit=ray.intersectObjects(targets).find(h=>visible(h.object));if(!hit)return;points.push(hit.point.clone());if(points.length===2){status.textContent=`Approximate display-mesh distance: ${(points[0].distanceTo(points[1])*1000).toFixed(1)} mm. Provisional scale; proxy, point-picking and exploded offsets affect this result.`;points=[];}else status.textContent='First point selected. Click the second point.';});
  new ResizeObserver(()=>{renderer.setSize(host.clientWidth,host.clientHeight);camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();}).observe(host);
  function frame(){requestAnimationFrame(frame);controls.update();renderer.render(scene,camera);}frame();
}catch(e){status.textContent='WebGL unavailable. Use the static project views below.';console.error(e);}
