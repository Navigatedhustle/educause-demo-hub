let demos={}, lastState=null, menuRequested=false, retryDemo=null;
const $=id=>document.getElementById(id);
async function action(path,data={}) {
  menuRequested=false;
  try {
    const response=await fetch('/api/'+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    if(!response.ok) throw new Error((await response.json()).error);
    render(await response.json());
  } catch(error) { $('status').textContent=error.message; }
}
function render(state) {
  if(lastState&&state.generation!==lastState.generation) menuRequested=false;
  lastState=state;
  const running=state.phase==='running'&&!menuRequested;
  const loading=['starting','stopping','error'].includes(state.phase);
  $('menu').hidden=running||loading; $('view').hidden=!running; $('loading').hidden=!loading;
  $('status').textContent='Status: '+state.message;
  if(running) {
    const url=demos[state.demo][2];
    const external=demos[state.demo][4]==='external';
    $('external-view').hidden=!external;
    $('demo-frame').hidden=external;
    if(external) {
      $('demo-frame').removeAttribute('src');
      $('external-title').textContent=demos[state.demo][0]+' is ready';
      $('external-link').href=url;
      $('external-link').textContent='Open '+demos[state.demo][0];
    } else if($('demo-frame').getAttribute('src')!==url) $('demo-frame').src=url;
    $('view-title').textContent=demos[state.demo][0];
  } else if($('demo-frame').hasAttribute('src')) $('demo-frame').removeAttribute('src');
  if(loading) {
    retryDemo=state.demo;
    $('loading-title').textContent=state.demo?demos[state.demo][0]:'Stop current demo';
    $('loading-message').textContent=state.message+' · '+state.available_gib.toFixed(1)+' GiB available';
    $('elapsed').textContent=state.elapsed.toFixed(1)+' seconds elapsed';
    $('stages').replaceChildren(...Object.entries(state.stages).map(([name,ready])=>{
      const li=document.createElement('li');li.textContent=(ready?'✓ ':'○ ')+name+(ready?' — ready':' — waiting');li.dataset.ready=String(ready);return li;
    }));
    $('retry').hidden=state.phase!=='error'||!state.demo;
    $('log').hidden=!state.log_tail; $('log').textContent=state.log_tail;
  }
}
document.querySelectorAll('[data-stop]').forEach(button=>button.onclick=()=>action('stop'));
$('retry').onclick=()=>action('start',{demo:retryDemo});
$('back').onclick=()=>{menuRequested=true;render(lastState);};
async function init() {
  demos=await (await fetch('/api/demos')).json();
  for(const [id,[title,description]] of Object.entries(demos)) {
    const button=document.createElement('button');button.className='demo';button.dataset.demo=id;
    if(id==='atlas') {const img=document.createElement('img');img.src='/atlas.png';img.alt='Atlas running on this Nano';button.append(img);}
    const copy=document.createElement('span');copy.className='copy';const name=document.createElement('strong');name.textContent=title;const desc=document.createElement('small');desc.textContent=description;copy.append(name,desc);button.append(copy);
    button.onclick=()=>action('start',{demo:id});$('demos').append(button);
  }
  async function poll(){try{render(await(await fetch('/api/status')).json());}catch(error){$('status').textContent='Hub connection lost. Retrying...';}setTimeout(poll,500);}
  poll();
}
init();
