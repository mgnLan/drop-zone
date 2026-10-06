<script>(function(){ window.dzVKError=window.dzVKError||'';
 window.dzDiag={iw:0,ih:0,cw:0,ch:0,aw:0,ah:0,rr:'-',rr2:'-',ac:'-',pd:'0'};
function dzUp(){try{var c=document.getElementById('canvas');
window.dzDiag.iw=window.innerWidth;
window.dzDiag.ih=window.innerHeight;
window.dzDiag.cw=c?c.width:0;
window.dzDiag.ch=c?c.height:0;
window.dzDiag.aw=window.screen.availWidth;
window.dzDiag.ah=window.screen.availHeight;
}
catch(e){}}setInterval(dzUp,1000);
dzUp();
document.addEventListener('pointerdown',function(){try{if(window.dzDiag.pd==='0'){window.dzDiag.pd='1';
var t=new (window.AudioContext||window.webkitAudioContext)();
if(t.resume){t.resume();
}setTimeout(function(){window.dzDiag.ac=t.state;
try{t.close();
}
catch(e2){}},800);
}}
catch(e){window.dzDiag.ac='ERR';
}},{capture:true});
 function noBridge(){return !window.vkBridge||!window.vkBridge.send;
} if(noBridge()){window.dzVKError='мост ВК не загрузился (vk-bridge)';
} else{try{window.vkBridge.send('VKWebAppInit');
}
catch(e){window.dzVKError='VKWebAppInit: '+e;
}} window.dzRewarded={show:function(){ if(noBridge()){window.dzVKError='реклама: мост ВК недоступен';
return false;
} window.vkBridge.send('VKWebAppShowNativeAds',{ad_format:'reward'}).then(function(res){ if(res&&res.result===true&&window.__dz_ad_reward){window.__dz_ad_reward();
} }).catch(function(e){window.dzVKError='реклама: '+String(e).slice(0,120);
});
 return true;
}};
 var DZ_PACKS=[{n:'Разведчик · 210 монет',p:29},{n:'Штурмовик · 825 монет',p:99},{n:'Снайпер · 1950 монет',p:199},{n:'Легенда · 4800 монет',p:399}];
 var DZ_ITEMS={bp:{n:'Premium Battle Pass · сезон 1',p:399}};
 window.dzOrder=function(pack){ var P=DZ_PACKS[pack];
if(!P){return false;
} if(noBridge()){window.dzVKError='оплата: мост ВК недоступен';
return false;
} window.vkBridge.send('VKWebAppShowOrderBox',{type:'item',item:P.n,price:P.p}).then(function(res){ if(res&&res.order_id&&window.__dz_order){window.__dz_order({status:'paid',pack:pack,order_id:String(res.order_id)});
} }).catch(function(e){window.dzVKError='оплата: '+String(e).slice(0,120);
});
 return true;
};
 window.dzOrderItem=function(id){ var I=DZ_ITEMS[id];
if(!I){return false;
} if(noBridge()){window.dzVKError='оплата: мост ВК недоступен';
return false;
} window.vkBridge.send('VKWebAppShowOrderBox',{type:'item',item:I.n,price:I.p}).then(function(res){ if(res&&res.order_id&&window.__dz_order){window.__dz_order({status:'paid',item:id,order_id:String(res.order_id)});
} }).catch(function(e){window.dzVKError='оплата (предмет): '+String(e).slice(0,120);
});
 return true;
};
 var dzFired=false;
 function dzReady(p){ if(dzFired){return;
} if(!window.__dz_vk_ready){setTimeout(function(){dzReady(p);
},200);
return;
} dzFired=true;
window.__dz_vk_ready(p);
 } if(noBridge()){ dzReady({__error:window.dzVKError});
 }
else{ /* вход не должен зависеть от GetUserInfo: sign уже в URL, имя — не обязательно. */ /* в ВК этот промис может не резолвиться и не реджектиться вовсе — ловить нечего */ setTimeout(function(){window.dzVKError=window.dzVKError||'ВК не ответил на GetUserInfo';
dzReady({name:''});
},2500);
 var initP=null;
 try{initP=window.vkBridge.send('VKWebAppInit');
}
catch(e){window.dzVKError='VKWebAppInit: '+e;
} if(!initP||!initP.then){initP=Promise.resolve(null);
} initP.catch(function(){return null;
}).then(function(){ try{var cp=window.vkBridge.send('VKWebAppGetConfig');
if(cp&&cp.then){cp.then(function(cfg){var vw=(cfg&&cfg.viewport_width)||0;
var vh=(cfg&&cfg.viewport_height)||0;
window.dzDiag.gc=vw+'x'+vh;
}).catch(function(){});
}}
catch(e){} return window.vkBridge.send('VKWebAppGetUserInfo');
 }).then(function(r){ window.dzVK=(r&&r.id)?{id:r.id,name:(r.first_name||'')+' '+(r.last_name||'')}:null;
 dzReady(window.dzVK||{name:''});
 }).catch(function(e){ window.dzVKError='GetUserInfo: '+String(e).slice(0,120);
 dzReady({name:''});
 });
 } })();
</script>