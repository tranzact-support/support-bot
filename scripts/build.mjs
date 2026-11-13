import {build} from 'esbuild';
import {mkdir,copyFile,readFile} from 'node:fs/promises';
await mkdir('dist/server',{recursive:true});await mkdir('dist/.openai',{recursive:true});
await build({entryPoints:['worker/index.js'],bundle:true,format:'esm',target:'es2022',platform:'browser',outfile:'dist/server/index.js',loader:{'.html':'text'}});
await copyFile('.openai/hosting.json','dist/.openai/hosting.json');
console.log('Worker built; server secrets and transcript files are excluded.');
