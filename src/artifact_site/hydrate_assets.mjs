// Rebuild static output from the committed pages and hash-pinned artifact sources.
// A local cache is optional; without it the same original bytes come from GitHub.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
const cwd=process.cwd();
const cacheFlag=process.argv.indexOf('--cache');
const cache=cacheFlag<0?null:path.resolve(process.argv[cacheFlag+1]);
const assets=JSON.parse(await fs.readFile('assets.json','utf8'));
const digest=buffer=>createHash('sha256').update(buffer).digest('hex');
const dest=path.join(cwd,'dist');
await fs.rm(dest,{recursive:true,force:true});
await fs.cp('web',dest,{recursive:true});
let cursor=0,verified=0;
async function worker(){
 while(cursor<assets.length){
  const asset=assets[cursor++];
  if(asset.path.startsWith('/')||asset.path.split('/').includes('..'))throw Error('Invalid artifact path');
  let bytes;
  if(cache){try{const b=await fs.readFile(path.join(cache,asset.path));if(digest(b)===asset.sha256)bytes=b;}catch{}}
  if(!bytes){
   const response=await fetch(asset.source_url,{signal:AbortSignal.timeout(120000)});
   if(!response.ok)throw Error(`Artifact fetch failed (${response.status}): ${asset.path}`);
   bytes=Buffer.from(await response.arrayBuffer());
  }
  if(bytes.length!==asset.bytes||digest(bytes)!==asset.sha256)throw Error('Artifact checksum mismatch: '+asset.path);
  const file=path.join(dest,asset.path);await fs.mkdir(path.dirname(file),{recursive:true});await fs.writeFile(file,bytes);verified++;
 }
}
await Promise.all(Array.from({length:4},worker));
console.log(JSON.stringify({verified_original_artifacts:verified,source:'committed hash-pinned assets.json',output:'dist'}));
