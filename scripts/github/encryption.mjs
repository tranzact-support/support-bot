import {pbkdf2Sync,randomBytes,createCipheriv,createDecipheriv} from 'node:crypto';
import {gzipSync,gunzipSync} from 'node:zlib';
export const AAD=Buffer.from('tranzact-support-v1');
export function derive(password,salt,iterations=210000){return pbkdf2Sync(password,Buffer.from(salt,'base64'),iterations,32,'sha256')}
export function seal(value,key){const iv=randomBytes(12);const cipher=createCipheriv('aes-256-gcm',key,iv);cipher.setAAD(AAD);const encrypted=Buffer.concat([cipher.update(gzipSync(Buffer.from(JSON.stringify(value)))),cipher.final(),cipher.getAuthTag()]);return {iv:iv.toString('base64'),ciphertext:encrypted.toString('base64')}}
export function unseal(value,key){const b=Buffer.from(value.ciphertext,'base64');const decipher=createDecipheriv('aes-256-gcm',key,Buffer.from(value.iv,'base64'));decipher.setAAD(AAD);decipher.setAuthTag(b.subarray(-16));return JSON.parse(gunzipSync(Buffer.concat([decipher.update(b.subarray(0,-16)),decipher.final()])).toString())}
