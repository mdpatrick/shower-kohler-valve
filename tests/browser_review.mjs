// Local UI test with an isolated browser context; never uses the user's browser data.
import {writeFile, readFile, mkdir} from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=process.cwd();
const modulePath=process.env.PROJECT_PLAYWRIGHT || '/Users/mdpatrick/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
const {chromium}=await import(modulePath);
const browser=await chromium.launch({channel:'chrome',headless:true});
const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
const page=await context.newPage();const errors=[];const failed=[];
page.on('pageerror',e=>errors.push(e.message));page.on('requestfailed',r=>failed.push(r.url()));
try {
  await page.goto(process.env.PROJECT_REVIEW_URL||'http://127.0.0.1:8765/review/index.html');
  await page.waitForFunction(()=>window.reviewFormReady&&window.reviewModelLoaded,{},{timeout:45000});
  const nodes=await page.evaluate(()=>window.reviewModelNodes);
  assert(nodes.includes('CUSTOM-01'));assert(nodes.includes('PLATE-INNER'));assert(nodes.includes('DIVERTER-TRIM'));assert(nodes.some(n=>n.startsWith('WALL')));
  const cadParts=JSON.parse(await readFile(path.join(root,'deliverables/current/cad/cad_manifest.json'),'utf8')).parts;
  await page.locator('[data-state="factory"]').click();
  assert(await page.locator('#fit-warning').isVisible());
  assert((await page.locator('#fit-warning').textContent()).includes('FAIL'));
  let display=await page.evaluate(()=>window.reviewDisplay);
  assert.equal(display.state,'factory');assert(!display.parts['CUSTOM-01'].visible);assert(!display.parts['NEW-SEAL-PATH'].visible);assert(display.parts['DIVERTER-TRIM'].visible);
  for(const p of cadParts.filter(p=>p.factory_location_mm))for(let axis=0;axis<3;axis++)assert(Math.abs(display.parts[p.id].position_m[axis]*1000-p.factory_location_mm[axis])<.001);
  assert(await page.locator('[data-layer="custom"]').isDisabled());
  await page.locator('[data-state="proposed"]').click();await page.locator('[data-view="oblique"]').click();
  display=await page.evaluate(()=>window.reviewDisplay);
  assert(display.parts['CUSTOM-01'].visible);assert(!(await page.locator('[data-layer="custom"]').isDisabled()));
  for(const p of cadParts)for(let axis=0;axis<3;axis++)assert(Math.abs(display.parts[p.id].position_m[axis]*1000-p.location_mm[axis])<.001);
  await page.locator('#explode').fill('0.35');await page.locator('#section').check();await page.locator('#section').uncheck();
  await page.locator('#explode').fill('0');await page.locator('[data-view="front"]').click();
  await mkdir(path.join(root,'build/browser-qa'),{recursive:true});
  await page.locator('[data-depth-case="factory"]').click();
  assert((await page.locator('#depth-image').getAttribute('src')).endsWith('depth_factory.svg'));
  await page.locator('[data-depth-case="proposed"]').click();
  assert((await page.locator('#depth-image').getAttribute('src')).endsWith('depth_proposed.svg'));
  await page.locator('#depth-image').screenshot({path:path.join(root,'build/browser-qa/depth-diagram.png')});
  await page.locator('#show-depth-3d').click();
  assert(await page.locator('#section').isChecked());
  display=await page.evaluate(()=>window.reviewDisplay);
  assert(display.parts['STUD-NE'].visible&&display.parts['STUD-SW'].visible);
  await page.locator('[data-view="front"]').click();
  assert(!(await page.locator('#section').isChecked()));
  await page.locator('[data-state="observed"]').click();
  assert(!(await page.locator('#fit-warning').isVisible()));
  await page.locator('[data-state="proposed"]').click();
  await page.locator('#model').screenshot({path:path.join(root,'build/browser-qa/model-desktop.png')});
  await page.locator('#measurement-date').fill('2026-10-14');
  const first=page.locator('[data-measurement="M01-O"]');
  await first.locator('.raw').fill('4');await first.locator('.units').selectOption('in');await first.locator('.repeat').fill('4.01, 4');
  await page.locator('#current-state').fill('TEST ONLY — no real observations submitted');
  let packet=JSON.parse(await page.locator('#response').inputValue());
  assert.equal(packet.observations.length,1);assert.equal(packet.observations[0].unit,'in');assert.deepEqual(packet.observations[0].raw_readings,[4,4.01,4]);
  const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#export-json').click()]);
  const downloaded=JSON.parse(await readFile(await download.path(),'utf8'));assert.deepEqual(downloaded,packet);
  await page.reload();await page.waitForFunction(()=>window.reviewFormReady);
  assert.equal(await first.locator('.raw').inputValue(),'4');
  await page.setViewportSize({width:390,height:844});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Horizontal page overflow');
  await page.locator('#depth').screenshot({path:path.join(root,'build/browser-qa/depth-mobile.png')});
  await page.locator('#measurements').screenshot({path:path.join(root,'build/browser-qa/worksheet-mobile.png')});
  await page.setViewportSize({width:1440,height:1000});
  const assets=await page.evaluate(()=>[...new Set([...document.querySelectorAll('img[src],a[href]')].map(el=>el.src||el.href).filter(u=>u.startsWith(location.origin)&&!u.includes('#')))]);
  for(const url of assets){const response=await page.request.get(url);assert(response.ok(),`${response.status()} ${url}`);}
  const coordinate=await page.evaluate(async()=>{
    const THREE=await import('three');const {GLTFLoader}=await import('three/addons/loaders/GLTFLoader.js');
    const load=url=>new Promise((resolve,reject)=>new GLTFLoader().load(url,g=>resolve(g.scene),undefined,reject));
    const test=await load('../analysis/coordinate_test.glb');test.updateMatrixWorld(true);
    const box=new THREE.Box3().setFromObject(test),size=box.getSize(new THREE.Vector3());let pts=[];
    test.traverse(o=>{if(o.isMesh){const a=o.geometry.attributes.position;for(let i=0;i<a.count;i++)pts.push(new THREE.Vector3().fromBufferAttribute(a,i).applyMatrix4(o.matrixWorld));}});
    const marker=pts.some(v=>v.distanceTo(new THREE.Vector3(.1,.05,0))<1e-6)&&pts.some(v=>v.distanceTo(new THREE.Vector3(.09,.06,0))<1e-6);
    const ring=pts.filter(v=>Math.abs(Math.hypot(v.x-.02,v.y-.015)-.005)<1e-6).length;
    const assembly=await load('installation_DRAFT.glb');assembly.updateMatrixWorld(true);const custom=assembly.getObjectByName('CUSTOM-01');
    const bounds=new THREE.Box3().setFromObject(custom);
    return {dims_m:size.toArray(),marker,hole_ring_vertices:ring,custom_bounds_m:[bounds.min.toArray(),bounds.max.toArray()]};
  });
  [0.1,0.06,0.004].forEach((v,i)=>assert(Math.abs(coordinate.dims_m[i]-v)<1e-6));assert(coordinate.marker);assert(coordinate.hole_ring_vertices>40);
  const resolved=JSON.parse(await readFile(path.join(root,'deliverables/current/analysis/resolved.json'),'utf8'));
  const cad=JSON.parse(await readFile(path.join(root,'deliverables/current/cad/cad_manifest.json'),'utf8')).parts.find(p=>p.id==='CUSTOM-01');
  for(let side=0;side<2;side++)for(let axis=0;axis<3;axis++)assert(Math.abs(coordinate.custom_bounds_m[side][axis]*1000-(cad.bounds_local_mm[side][axis]+cad.location_mm[axis]))<.05);
  assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
  const report={status:'PASS',revision:resolved.revision,desktop:[1440,1000],mobile:[390,844],model_nodes:nodes,
    checks:['GLB loading','original-wall/added-plate per-part positions, visibility and round-trip restoration','fit warnings and visible unchanged studs','depth diagram switching and stud-section navigation','local controls','responsive page','JSON download and persistence','linked asset HTTP success','known-size asymmetric part + hole in browser','CAD-to-browser custom placement/bounds'],coordinate,errors,failed,
    note:'Isolated synthetic browser values were never imported. No physical measurements or fit established.'};
  await writeFile(path.join(root,'docs/validation/browser_check.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
}catch(e){
  console.error(JSON.stringify({errors,failed,status:await page.locator('#model-status').textContent().catch(()=>null)}));throw e;
}finally{await context.close();await browser.close();}
