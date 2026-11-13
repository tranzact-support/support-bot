import {readFile,writeFile,copyFile,mkdir} from 'node:fs/promises';
await mkdir('docs',{recursive:true});
for(const [source,target] of [['worker/page.html','docs/index.html'],['worker/tester.html','docs/test.html']]){let s=await readFile(source,'utf8');s=s.replace(/async function api\(path,body\)\{.*?return d;?\}/s,"async function api(path,body){await window.supportReady;return window.supportAPI(path,body||{});}");s=s.replace("location.href='/test'","location.href='test.html'").replace('href="/"','href="./"').replace('Private workspace','Protected knowledge').replace('support examples','support examples');s=s.replace('<script>','<script src="client-loader.js"></script>\n<script>');await writeFile(target,s)}
await copyFile('worker/knowledge.js','docs/knowledge-tools.js');
console.log('Built standalone GitHub Pages interface.');
