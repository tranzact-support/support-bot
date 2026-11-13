import {readFile,writeFile} from 'node:fs/promises';import {makeIndex} from '../worker/knowledge.js';
const dir=new URL('../data/seed/',import.meta.url);const m=JSON.parse(await readFile(new URL('manifest.json',dir),'utf8'));const indices={};
for(const part of m.parts){const records=JSON.parse(await readFile(new URL(part.key+'.json',dir),'utf8'));indices[part.month]??=[];indices[part.month].push(...makeIndex(records,part.key));}
for(const [month,rows]of Object.entries(indices))await writeFile(new URL('index-'+month+'.json',dir),JSON.stringify(rows));
console.log('Prepared '+m.parts.length+' evidence objects and '+Object.keys(indices).length+' search indexes.');
