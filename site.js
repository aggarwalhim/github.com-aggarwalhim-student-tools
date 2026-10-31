/* Shared behaviour for every page: highlight the current page in the menu,
   open the tab named in the link (e.g. pdf.html#cmp), and run the tool finder on the home page. */
(function(){
  var file=(location.pathname.split('/').pop()||'index.html').toLowerCase();
  if(file==='')file='index.html';
  document.querySelectorAll('nav a').forEach(function(a){
    if((a.getAttribute('href')||'').toLowerCase()===file)a.classList.add('on');
  });

  function openTabFromHash(scroll){
    var id=decodeURIComponent((location.hash||'').slice(1));
    if(!id)return;
    var t=document.querySelector('.tab[data-tab="'+id.replace(/"/g,'')+'"]');
    if(!t)return;
    t.click();
    if(scroll){
      var tabs=document.querySelector('.tabs');
      if(tabs)tabs.scrollIntoView({block:'start'});
    }
  }
  openTabFromHash(true);
  window.addEventListener('hashchange',function(){openTabFromHash(true);});

  // ----- tool finder (home page only) -----
  var q=document.getElementById('finder-q');
  if(!q)return;
  var items=Array.prototype.slice.call(document.querySelectorAll('.toc li'));
  var groups=Array.prototype.slice.call(document.querySelectorAll('.toc-group'));
  var hint=document.getElementById('finder-hint'),empty=document.getElementById('toc-empty');
  var total=items.length;
  function norm(s){return (s||'').toLowerCase().replace(/[^a-z0-9ऀ-ॿ\s]/g,' ');}
  function run(){
    var terms=norm(q.value).split(/\s+/).filter(Boolean),shown=0;
    items.forEach(function(li){
      var hay=norm(li.getAttribute('data-k')),ok=terms.every(function(t){return hay.indexOf(t)>-1;});
      li.hidden=!ok;if(ok)shown++;
    });
    groups.forEach(function(g){g.hidden=!g.querySelector('li:not([hidden])');});
    empty.hidden=shown>0;
    hint.textContent=terms.length?(shown?shown+' of '+total+' tools match.':'Nothing matches. Try a shorter word, like pdf, photo or resume.'):'Type a word, or scroll the list. '+total+' tools, all free.';
  }
  q.addEventListener('input',run);
  q.addEventListener('keydown',function(e){
    if(e.key==='Enter'){var first=document.querySelector('.toc li:not([hidden]) a');if(first)location.href=first.href;}
  });
  run();
})();
