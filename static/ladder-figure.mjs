// Figure 1 — a real measured ladder (WSI-Bench report task), drawn coarsest first so it reads bottom-up like a ladder.
// Shared by the ladder page and the product page. Values enter the DOM as text only.
import {ladderView} from './ladder-view.mjs?v=ladder-6';

function el(tag,attrs={},...children){
 const node=document.createElement(tag);
 for(const [k,v] of Object.entries(attrs)){if(k==='class')node.className=v;else if(v!==null&&v!==undefined&&v!==false)node.setAttribute(k,v)}
 for(const child of children.flat(Infinity))if(child!==null&&child!==undefined&&child!==false)node.append(child instanceof Node?child:document.createTextNode(String(child)));
 return node;
}

export function plural(name,n){return n===1?name:({patient:'patients',site:'sites',slide:'slides',recording:'recordings',subject:'subjects',person:'people',case:'cases',ecg:'ECGs',clip:'clips'}[name]||(/(s|x)$/.test(name)?name:name+'s'))}

function rung(row,level){
 const bar=el('span');if(row.percent!==null)bar.style.width=`${Math.min(100,Math.max(row.percent,row.percent>0?2:0))}%`;
 const count=level.status==='measured'?level.shared:null;
 return el('li',{class:`rung row-${row.tone}${row.isClaim?' is-claim':''}`},
  el('div',{class:'rung-name'},row.name,el('small',{},row.isClaim?'the claim':row.kind)),
  el('div',{class:'rung-measure'},
   el('div',{class:'rung-value'},el('span',{class:'rung-count'},count===null?'—':count.toLocaleString('en-US')),
    el('span',{class:'rung-of'},count===null?row.detail:`of ${level.test_units.toLocaleString('en-US')} test ${plural(row.name,level.test_units)} also in training`)),
   el('div',{class:'rung-bar','aria-hidden':'true'},bar)),
  el('span',{class:`tone-chip tone-${row.tone}`},row.state));
}

export async function heroFigure(list,source='/static/ladders/wsibench-report.json'){
 if(!list)return;
 try{
  const r=await fetch(source);if(!r.ok)throw new Error();const result=await r.json();
  const view=ladderView(result),levels=Object.fromEntries(result.levels.map(l=>[l.name,l]));
  list.replaceChildren(...view.rows.filter(x=>x.kind!=='attribute').reverse().map(x=>rung(x,levels[x.name])));
 }catch{list.replaceChildren(el('li',{class:'figure-loading'},'The measured ladder could not be loaded.'))}
}

const auto=document.querySelector('[data-ladder-figure]');
if(auto)heroFigure(auto);
