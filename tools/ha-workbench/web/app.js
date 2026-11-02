"use strict";

const $ = selector => document.querySelector(selector);
const fields = Object.fromEntries(["profile","notice","preview","firmware","validate","screen","empty","screen-wrap","capture-tabs","freshness","job-badge","job-summary","job-detail","job-error","log","log-size","log-details","git-state","git-branch","git-commit","source-hash","result-hash","artifacts","artifacts-card","editor","builder"].map(id=>[id,$(`#${id}`)]));
const actions = ["preview","firmware","validate"];
let selected = "", state = null, captures = [], activeCapture = "", submitting = false, requestNumber = 0, timer;
const kindLabels = {preview:"Предпросмотр",firmware:"Сборка прошивки",validate:"Проверка конфигурации"};

export function isBusy(job) { return ["running","queued","pending"].includes(job?.status); }
export function captureLabel(name) {
  if (/(?:^|[-_])off$/i.test(name)) return "Свет выключен";
  if (/(?:^|[-_])on$/i.test(name)) return "Свет включён";
  if (/common|secondary|shared/i.test(name)) return "Общая страница";
  return name.replace(/[-_]/g," ");
}
export function relativeResource(url) {
  if (typeof url!=="string" || !url.startsWith("files/") || url.includes("..") || /[\\?#]/.test(url)) return null;
  return url;
}
export function profileLabel(data,id) { return data?.profiles?.find(profile=>profile.id===id)?.label || id || "Профиль"; }
export function jobSummary(job,data) {
  if (!job?.kind || job.status==="idle") return "Готово к работе";
  const operation=kindLabels[job.kind]||"Задача", label=profileLabel(data,job.profile);
  return `${operation} · ${label}`;
}

function notice(message="") { fields.notice.textContent=message;fields.notice.hidden=!message; }
function setButtons() { actions.forEach(kind=>{fields[kind].disabled=!selected||submitting||isBusy(state?.job);}); }
function clearCaptures() {
  captures=[];activeCapture="";fields.screen.hidden=true;fields.screen.removeAttribute("src");fields.empty.hidden=false;
  fields.empty.querySelector("strong").textContent="Первый кадр ещё не собран";fields.empty.querySelector("p").textContent="Выберите профиль и обновите предпросмотр.";
  fields["capture-tabs"].replaceChildren();fields["capture-tabs"].hidden=true;fields["artifacts-card"].hidden=true;
  fields.freshness.textContent="Снимки из общей конфигурации экрана";fields.freshness.classList.remove("stale");
}
function showCapture(name) {
  const capture=captures.find(item=>item.name===name),url=relativeResource(capture?.url);
  if(!url)return;
  activeCapture=name;fields.screen.alt=`${profileLabel(state,selected)} · ${captureLabel(name)}`;
  if(fields.screen.getAttribute("src")!==url)fields.screen.src=url;
  fields.screen.hidden=false;fields.empty.hidden=true;
  for(const button of fields["capture-tabs"].children)button.setAttribute("aria-pressed",String(button.dataset.capture===name));
}
function renderCaptures(data) {
  const incoming=(data.captures||[]).filter(capture=>relativeResource(capture.url));
  const signature=items=>items.map(item=>`${item.name}:${item.url}`).join("|");
  if(signature(captures)!==signature(incoming)) {
    captures=incoming;fields["capture-tabs"].replaceChildren();
    for(const capture of captures) {
      const button=document.createElement("button");button.type="button";button.dataset.capture=capture.name;button.textContent=captureLabel(capture.name);
      button.addEventListener("click",()=>showCapture(capture.name));fields["capture-tabs"].append(button);
    }
    fields["capture-tabs"].hidden=captures.length<2;
  }
  if(captures.length)showCapture(captures.some(item=>item.name===activeCapture)?activeCapture:captures.find(item=>/(?:^|[-_])on$/i.test(item.name))?.name||captures[0].name);
  else {fields.screen.hidden=true;fields.empty.hidden=false;}
  fields.freshness.classList.toggle("stale",Boolean(data.captures_stale));
  fields.freshness.textContent=data.captures_stale?"Изменения ещё не собраны":captures.length?"Снимок соответствует текущим исходникам":"Снимки из общей конфигурации экрана";
  fields["result-hash"].textContent=data.result_fingerprint||"Снимков пока нет";
}
function renderArtifacts(data) {
  fields.artifacts.replaceChildren();
  const artifacts=(data.artifacts||[]).filter(item=>relativeResource(item.url));
  fields["artifacts-card"].hidden=!artifacts.length;
  for(const artifact of artifacts) {
    const link=document.createElement("a");link.className="artifact";link.href=relativeResource(artifact.url);link.setAttribute("download",artifact.name);
    const name=document.createElement("strong");name.textContent=artifact.name;
    const size=document.createElement("span");size.textContent=Number.isFinite(artifact.bytes)?`${(artifact.bytes/1024/1024).toFixed(2)} МБ ↓`:"Скачать ↓";
    link.append(name,size);fields.artifacts.append(link);
  }
}
function renderJob(data) {
  const job=data.job||{},badge=fields["job-badge"],busy=isBusy(job);
  badge.className=`job-badge ${busy?"running":job.status||"idle"}`;
  badge.textContent=busy?"Выполняется":job.status==="complete"?"Готово":job.status==="failed"?"Ошибка":"Ожидание";
  fields["job-summary"].textContent=jobSummary(job,data);
  let detail="Измените файлы в редакторе и запустите нужное действие.";
  if(job.started_at) {
    const time=new Date(job.started_at*1000).toLocaleTimeString("ru-RU",{hour:"2-digit",minute:"2-digit"});
    detail=busy?`Начато в ${time}. Журнал обновляется автоматически.`:job.status==="complete"?`Завершено. Начало в ${time}.`:`Начало в ${time}. Подробности в журнале.`;
  }
  fields["job-detail"].textContent=detail;fields["job-error"].textContent=job.error||"";fields["job-error"].hidden=!job.error;
  const log=job.log||"Журнал появится после запуска.";
  if(fields.log.textContent!==log){const nearEnd=fields.log.scrollTop+fields.log.clientHeight>=fields.log.scrollHeight-36;fields.log.textContent=log;if(nearEnd)fields.log.scrollTop=fields.log.scrollHeight;}
  fields["log-size"].textContent=job.log?`${job.log.split("\n").length} строк`:"";
}
function render(data) {
  state=data;
  if(!selected)selected=data.profile||data.profiles?.[0]?.id||"";
  if(!data.profiles?.some(profile=>profile.id===selected))selected=data.profiles?.[0]?.id||"";
  const existing=Array.from(fields.profile.options).map(option=>`${option.value}:${option.textContent}`).join("|");
  const available=(data.profiles||[]).map(profile=>`${profile.id}:${profile.label}`).join("|");
  if(existing!==available){fields.profile.replaceChildren();for(const profile of data.profiles||[]){const option=document.createElement("option");option.value=profile.id;option.textContent=profile.label;fields.profile.append(option);}}
  fields.profile.value=selected;fields.profile.disabled=!selected;
  for(const name of ["editor","builder"]){const link=data.links?.[name];if(typeof link==="string"&&link.startsWith("/")&&!link.startsWith("//"))fields[name].href=link;}
  fields["git-branch"].textContent=data.git?.branch||"Без ветки";fields["git-commit"].textContent=data.git?.commit||"Нет коммитов";
  fields["git-state"].textContent=data.git?.dirty?"Есть изменения":"Без изменений";fields["git-state"].classList.toggle("dirty",Boolean(data.git?.dirty));
  fields["source-hash"].textContent=data.source_fingerprint||"—";
  renderCaptures(data);renderArtifacts(data);renderJob(data);setButtons();
}
async function refresh() {
  clearTimeout(timer);const request=++requestNumber,profile=selected;
  try {
    const response=await fetch(`api/state?profile=${encodeURIComponent(profile)}`,{cache:"no-store"});
    if(!response.ok)throw new Error("state");const data=await response.json();
    if(request!==requestNumber||profile!==selected)return;
    notice();render(data);
  } catch {
    if(request===requestNumber){notice("Не удалось обновить состояние. Проверяем подключение…");actions.forEach(kind=>fields[kind].disabled=true);}
  } finally {if(request===requestNumber)timer=setTimeout(refresh,isBusy(state?.job)?2000:5000);}
}
async function start(kind) {
  if(submitting||isBusy(state?.job)||!selected)return;
  submitting=true;setButtons();notice();const profile=selected;
  try {
    const response=await fetch("api/jobs",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({kind,profile})});
    if(response.status===409){notice("Уже выполняется другая сборка. Дождитесь её завершения.");return;}
    if(!response.ok)throw new Error("start");
    const result=await response.json();if(state){state={...state,job:result.job};renderJob(state);}
    fields["log-details"].open=true;
  } catch {notice("Не удалось запустить задачу. Проверьте подключение и повторите.");}
  finally {submitting=false;setButtons();await refresh();}
}

fields.profile.addEventListener("change",()=>{selected=fields.profile.value;requestNumber++;clearCaptures();setButtons();refresh();});
for(const kind of actions)fields[kind].addEventListener("click",()=>start(kind));
fields.screen.addEventListener("error",()=>{fields.screen.hidden=true;fields.empty.hidden=false;fields.empty.querySelector("strong").textContent="Не удалось загрузить кадр";fields.empty.querySelector("p").textContent="Обновите предпросмотр или дождитесь восстановления подключения.";});
document.addEventListener("visibilitychange",()=>{if(!document.hidden)refresh();});
refresh();
