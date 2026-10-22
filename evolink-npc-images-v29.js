/* EvoLink NPC image presentation — progressive enhancement; non-destructive. */
(()=>{
 'use strict';
 const formats=['image/png','image/jpeg','image/webp'];
 const MAX=5*1024*1024;
 function enhance(root=document){
   const inputs=[...root.querySelectorAll('input[type="file"]')].filter(x=>{
     const context=(x.closest('label')?.textContent||x.parentElement?.textContent||'').toLowerCase();
     return /foto de perfil|foto de corpo inteiro|miniatura.*npc|ficha.*npc/.test(context);
   });
   inputs.forEach(input=>{
     if(input.dataset.evoNpcV29)return;
     input.dataset.evoNpcV29='1';
     input.accept='image/png,image/jpeg,image/webp';
     const preview=document.createElement('div');
     preview.className='evolink-npc-image-preview';
     preview.setAttribute('aria-live','polite');
     input.insertAdjacentElement('afterend',preview);
     let objectUrl=null;
     input.addEventListener('change',()=>{
       if(objectUrl){URL.revokeObjectURL(objectUrl);objectUrl=null;}
       preview.replaceChildren();
       const file=input.files?.[0];if(!file)return;
       if(!formats.includes(file.type)||file.size>MAX){
         input.value='';preview.textContent='Selecione PNG, JPG ou WEBP com até 5 MB.';return;
       }
       objectUrl=URL.createObjectURL(file);
       const image=document.createElement('img');image.src=objectUrl;
       image.alt='Prévia da imagem selecionada';image.loading='lazy';
       image.style.cssText='display:block;max-width:180px;max-height:240px;object-fit:contain;border-radius:12px;margin-top:12px';
       preview.appendChild(image);
     });
   });
 }
 let pending=false;
 const observer=new MutationObserver(()=>{if(!pending){pending=true;queueMicrotask(()=>{pending=false;enhance();});}});
 const start=()=>{enhance();observer.observe(document.body,{childList:true,subtree:true});};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
