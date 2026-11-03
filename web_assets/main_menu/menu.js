(function(){
"use strict";
var root=null;
var profile={name:"Боец",coins:0,shards:0,stamina:100,wins:0,slots:2,max_level:1,vip:0,rating:1000,reaper_days:0,missions:[]};
var markup=`
<main class="dz" aria-label="Главное меню Drop Zone">
<header class="top">
<div class="brand-mini">СЕЗОН // 01</div><div class="online">Боевой контур активен</div><div class="spacer"></div>
<span class="profile-chip" id="dz-menu-name">Боец</span>
<div class="resources"><span class="res" title="Монеты"><b id="dz-menu-coins">0</b> монет</span><span class="res" title="Осколки"><b id="dz-menu-shards">0</b> осколков</span></div>
<button type="button" class="top-btn fullscreen-btn" id="dz-menu-fullscreen" title="Во весь экран" aria-label="Во весь экран"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 3H3v5M16 3h5v5M3 16v5h5M21 16v5h-5"/></svg></button>
<button type="button" class="top-btn" id="dz-menu-more" aria-expanded="false">Ещё</button>
<button type="button" class="top-btn" data-action="settings">Настройки</button>
</header>
<section class="hero"><div class="hero-kicker">ТВОЯ АРЕНА. ТВОИ ПРАВИЛА.</div><h1 class="logo"><span>ТОЧКА</span> СБРОСА</h1><div class="subtitle">КОРОЛЕВСКАЯ БИТВА</div><div class="hero-line"></div></section>
<div class="layout">
<section><div class="section-head"><div><small>БОЕВАЯ ГОТОВНОСТЬ</small><h2>Выбери режим</h2></div><div class="spacer"></div><button type="button" class="rating-btn" data-action="rating" id="dz-menu-rating">Против игроков →</button></div>
<div class="modes">
<button type="button" class="mode primary" data-action="mode:1"><span class="tag">ОСНОВНОЙ РЕЖИМ</span><strong>Дуэль 1 × 1</strong><p>Свободный вход · быстрый бой · награда за победу</p><i class="arrow">→</i></button>
<button type="button" class="mode" data-action="mode:2"><span class="tag">КОМАНДНЫЙ БОЙ</span><strong>Пара 2 × 2</strong><p>Держите строй и накрывайте с двух сторон</p><i class="arrow">→</i></button>
<button type="button" class="mode" data-action="mode:3" data-mode="3"><span class="tag">35 УРОВЕНЬ</span><strong>Тройка 3 × 3</strong><p>Третий слот отряда ещё закрыт</p><i class="arrow">—</i></button>
<button type="button" class="mode" data-action="mode:4" data-mode="4"><span class="tag">ПОЛНЫЙ ОТРЯД</span><strong>Отряд 4 × 4</strong><p>Максимум огня. Максимум награды</p><i class="arrow">→</i></button>
<button type="button" class="mode" data-action="mode:5" data-mode="5"><span class="tag">СОБЫТИЕ</span><strong>Арена лидеров</strong><p>Испытание для бойцов 25 уровня</p><i class="arrow">—</i></button>
</div>
<button type="button" class="mode reaper" data-action="mode:6" data-mode="6"><span class="tag">РЕЙД-БОСС</span><strong>Жнец</strong><p>Фазы, карты и особый трофей</p><i class="arrow">→</i></button>
</section>
<aside class="side"><div class="panel"><div class="panel-title" id="dz-missions-title">МИССИИ ДНЯ</div><div id="dz-missions"></div></div>
<button type="button" class="panel pass" data-action="bp"><div class="panel-title">СЕЗОН 01 · СКОРО</div><strong>Первый сброс</strong><p>Эксклюзивная косметика и награды</p><b>→</b></button></aside>
</div>
<nav class="nav" aria-label="Разделы игры"><button type="button" class="active" data-action="main"><span>01</span>Бой</button><button type="button" data-action="squad"><span>02</span>Отряд</button><button type="button" data-action="heroes"><span>03</span>Герои</button><button type="button" data-action="shop"><span>04</span>Магазин</button><button type="button" data-action="showbiz"><span>05</span>Касса шоу</button><button type="button" data-action="bp"><span>06</span>Battle Pass</button></nav>
<div class="menu-foot"><span id="dz-squad-status">ОТРЯД · 2/4</span><span id="dz-player-stats">ЭНЕРГИЯ 100 · ПОБЕД 0</span></div>
<div class="more-panel" id="dz-more-panel" hidden>
<button type="button" data-action="deck">Шоу-карты</button><button type="button" data-action="chests">Сундуки</button>
<button type="button" data-action="progress">Прогрессия</button><button type="button" data-action="med">Медцентр</button>
<button type="button" data-action="profile">Личные данные</button><button type="button" data-action="rating">Рейтинг и дуэли</button>
</div>
</main>`;
function num(v){return Math.max(0,Number(v)||0).toLocaleString("ru-RU");}
function text(id,value){var el=document.getElementById(id);if(el)el.textContent=String(value);}
function setMode(id,locked,desc,tag){var b=root.querySelector('[data-mode="'+id+'"]');if(!b)return;b.disabled=!!locked;b.classList.toggle("locked",!!locked);b.setAttribute("aria-disabled",locked?"true":"false");b.querySelector("p").textContent=desc;if(tag)b.querySelector(".tag").textContent=tag;b.querySelector(".arrow").textContent=locked?"—":"→";}
function renderMissions(list){var host=document.getElementById("dz-missions");if(!host)return;host.textContent="";var left=0;(list||[]).forEach(function(q){var target=Math.max(1,Number(q.target)||1);var value=Math.min(target,Math.max(0,Number(q.value)||0));var done=!!q.done||value>=target;if(!done)left++;var box=document.createElement("div");box.className="mission"+(done?" done":"");var row=document.createElement("div");row.className="mission-row";var name=document.createElement("span");name.textContent=q.name||"Миссия";var count=document.createElement("span");count.textContent=done?"Готово":num(value)+" / "+num(target);row.append(name,count);var track=document.createElement("div");track.className="track";var fill=document.createElement("i");fill.style.width=Math.round(value/target*100)+"%";track.appendChild(fill);var reward=document.createElement("small");reward.textContent=done?"Награда получена":"Награда · "+(q.reward||"сезонный опыт");box.append(row,track,reward);host.appendChild(box);});text("dz-missions-title","МИССИИ ДНЯ · "+left+" АКТИВНЫ");}
function apply(data){if(!data||typeof data!=="object")return;profile=Object.assign({},profile,data);text("dz-menu-name",profile.name||"Боец");text("dz-menu-coins",num(profile.coins));text("dz-menu-shards",num(profile.shards));text("dz-menu-rating","Против игроков · "+num(profile.rating)+" →");text("dz-squad-status","ОТРЯД · "+num(profile.slots)+"/4");text("dz-player-stats","ЭНЕРГИЯ "+num(profile.stamina)+" · ПОБЕД "+num(profile.wins));var slots=Number(profile.slots)||2;var lvl=Number(profile.max_level)||1;var vip=Number(profile.vip)||0;var days=Number(profile.reaper_days)||0;setMode(3,slots<3,slots<3?"Третий слот отряда ещё закрыт":"Трое против троих · командный бой",slots<3?"35 УРОВЕНЬ":"КОМАНДНЫЙ БОЙ");setMode(4,slots<4,slots<4?(vip?"Сначала открой третий слот":"Доступно по ВИП-подписке"):"Максимум огня. Максимум награды",slots<4?"ВИП · ПОЛНЫЙ ОТРЯД":"ПОЛНЫЙ ОТРЯД");setMode(5,lvl<25,lvl<25?"Нужен 25 уровень · сейчас "+lvl:"16 врагов · повышенные награды");setMode(6,days>0,days>0?"Жнец вернётся через "+days+" дн.":"Фазы, карты и особый трофей");renderMissions(profile.missions);}
function closeMore(){if(!root)return;var panel=document.getElementById("dz-more-panel");var btn=document.getElementById("dz-menu-more");panel.hidden=true;btn.setAttribute("aria-expanded","false");}
function toggleFullscreen(){var entering=!document.fullscreenElement;window.dzFs=entering;var p=entering?(document.documentElement.requestFullscreen&&document.documentElement.requestFullscreen()):(document.exitFullscreen&&document.exitFullscreen());if(p&&p.catch)p.catch(function(){window.dzFs=!!document.fullscreenElement;});try{if(window.vkBridge)window.vkBridge.send("VKWebAppResizeWindow",{width:entering?window.screen.width:1000,height:entering?window.screen.height:720});}catch(e){}}
function send(action){closeMore();if(action==="main"){root.scrollTo({top:0,behavior:"smooth"});return;}window.dzMenuLastAction=action;if(typeof window.__dz_menu_action==="function"){window.__dz_menu_action(action);}}
function init(){
if(root)return;
root=document.createElement("div");root.id="dz-main-menu";root.hidden=true;root.setAttribute("aria-label","Игровое лобби");root.innerHTML=markup;document.body.appendChild(root);
root.addEventListener("click",function(ev){var b=ev.target.closest("button[data-action]");if(b&&!b.disabled){ev.preventDefault();send(b.dataset.action);}});
document.getElementById("dz-menu-fullscreen").addEventListener("click",function(ev){ev.preventDefault();ev.stopPropagation();toggleFullscreen();});
document.addEventListener("fullscreenchange",function(){window.dzFs=!!document.fullscreenElement;var b=document.getElementById("dz-menu-fullscreen");if(b)b.classList.toggle("active",window.dzFs);});
document.getElementById("dz-menu-more").addEventListener("click",function(ev){ev.stopPropagation();var panel=document.getElementById("dz-more-panel");panel.hidden=!panel.hidden;this.setAttribute("aria-expanded",panel.hidden?"false":"true");});
document.addEventListener("keydown",function(ev){if(ev.key==="Escape")closeMore();});
document.addEventListener("pointerdown",function(ev){if(root&&!root.hidden&&!ev.target.closest("#dz-more-panel")&&!ev.target.closest("#dz-menu-more"))closeMore();});
apply(profile);
}
window.dzMenuProfile=function(data){if(!root)init();apply(data);};
window.dzMainMenu=function(show){if(!root)init();root.hidden=!show;document.body.classList.toggle("dz-html-menu-open",!!show);if(show){closeMore();root.scrollTop=0;}};
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();
})();
