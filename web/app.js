/* This view projects evidence only; it never repairs or dispatches connectors. */
const byId = id => document.getElementById(id);
let records = [];
let latestSource = null;
let failed = true;
function monitorAvailability(available) {
  const frame = byId('monitor');
  if (!available) {
    frame.removeAttribute('src');frame.hidden = true;
  } else {
    frame.hidden = false;
    if (byId('monitor-panel').open && !frame.getAttribute('src')) frame.src='/monitor';
  }
}
function node(tag, text, cls) {
  const result = document.createElement(tag);
  if (text !== undefined) result.textContent = text;
  if (cls) result.className = cls;
  return result;
}
function moment(value) {
  const d = new Date(value);
  return value && Number.isFinite(d.getTime()) ? d.toLocaleString('th-TH', {timeZone:'Asia/Bangkok',dateStyle:'medium',timeStyle:'medium'}) + ' (เวลาไทย)' : 'ยังไม่มีหลักฐาน';
}
function effective(record) {
  const time = Date.parse(record.observed_at);
  const age = (Date.now() - time) / 1000;
  const fresh = !failed && Number.isFinite(time) && Number.isFinite(record.ttl_seconds) && record.ttl_seconds > 0 && age >= -5 && age <= record.ttl_seconds;
  return fresh && record.mode === 'live' && record.freshness === 'current' ? record.effective : {};
}
function render() {
  const root = byId('channels');
  root.replaceChildren();
  for (const record of records) {
    const flags = effective(record);
    const article = node('article', undefined, 'channel');
    article.dataset.channel = record.id;
    article.append(node('h3', record.label));
    const ready = flags.connected === true && flags.admitted === true && flags.verified_working === true;
    article.append(node('span', ready ? 'ผ่านเฉพาะขอบเขตที่ระบุ' : failed ? 'อ่านสถานะไม่ได้' : record.observed_at ? 'ต้องตรวจใหม่ / หลักฐานเก่า' : 'ยังไม่ยืนยัน', 'badge ' + (ready ? 'current' : 'stale')));
    const list = node('dl', undefined, 'flags');
    for (const [key, label] of [['connected','เชื่อมต่อ'],['authenticated','ยืนยันตัวตน'],['admitted','อนุญาตในขอบเขต'],['verified_working','ทดสอบใช้งานผ่าน']]) {
      const value = flags[key];
      list.append(node('dt', label),node('dd',value === true ? 'ยืนยันแล้ว' : value === false ? 'ไม่ผ่าน' : 'ยังไม่ทราบ',value === true ? 'yes' : value === false ? 'no' : 'unknown'));
    }
    article.append(list,node('p', record.scope, 'muted'));
    const details = node('details', undefined, 'detail');
    details.append(node('summary', 'หลักฐานและข้อจำกัด'));
    for (const text of ['ตรวจล่าสุด: '+moment(record.observed_at), 'อายุความเชื่อมั่น: '+record.ttl_seconds+' วินาที', 'แหล่งที่มา: '+record.source, 'ข้อจำกัด: '+record.limitation, 'ทางกู้คืน: '+(record.recovery || 'ยังไม่มีทางเชื่อมที่ได้รับอนุญาตใน adapter นี้')]) details.append(node('p', text));
    article.append(details);root.append(article);
  }
}
async function readJson(path) {
  const response = await fetch(path,{cache:'no-store',signal:AbortSignal.timeout(6000)});
  if (!response.ok) throw new Error('read failed');
  return response.json();
}
async function refresh() {
  byId('refresh').disabled = true;
  try {
    const [data, snapshots] = await Promise.all([readJson('/api/health'),readJson('/api/source-summary')]);
    if (!Array.isArray(data.channels) || !data.source?.revision) throw new Error('invalid source');
    records = data.channels;failed = false;latestSource = data.source;
    monitorAvailability(!data.source_changed_since_start);
    byId('notice').textContent = 'คำขอเครื่องพัฒนาตอบแล้ว • '+data.snapshot_notice;
    byId('next-action').textContent = 'ขั้นถัดไป: '+data.mission.next_action;
    const source = byId('source');source.replaceChildren();
    source.append(node('p','Core Brain: '+data.source.repository+' / '+data.source.branch),node('p','revision ที่โหลด: '+data.source.revision),node('p','ตรวจ main ล่าสุด: '+moment(data.source.observed_at)));
    if(data.source_changed_since_start) source.append(node('p','แหล่งข้อมูลเปลี่ยนหลังเริ่ม process ต้องเริ่ม server ใหม่'));
    const links = node('p');
    for(const [label,path] of [['ดัชนีระบบ','A00_SYSTEM_INDEX.md'],['คำสั่ง LifeOS','protocols/lifeos-command-registry.md'],['DeepPlan / SmartRun','skills/lifeos-work-flow/SKILL.md']]) {
      const link = node('a',label);link.href='https://github.com/sangkeat/LifeOS-Foundry/blob/'+data.source.revision+'/'+path;link.target='_blank';link.rel='noopener noreferrer';links.append(link,node('span',' · '));
    }
    source.append(links);
    const target=byId('snapshots');target.replaceChildren();
    for(const [name,record] of Object.entries(snapshots)) target.append(node('p',name+' — ข้อมูล snapshot; วันที่บันทึกเดิม: '+moment(record.record_updated_at)));
  } catch {
    failed = true;
    monitorAvailability(false);
    byId('notice').textContent = 'อ่านสถานะไม่ได้ — ยกเลิกการแสดงผลพร้อมใช้งานทั้งหมด กรุณาเริ่ม server ของโครงการแล้วอ่านใหม่';
    // Keep historical timestamps, but never leave old green flags on screen.
    if (!latestSource) byId('source').textContent='ยังไม่มีแหล่งข้อมูลที่อ่านสำเร็จ';
  } finally {
    render();byId('refresh').disabled=false;
  }
}
byId('refresh').addEventListener('click',refresh);
byId('monitor-panel').addEventListener('toggle',() => {
  if (!failed && byId('monitor-panel').open && !byId('monitor').hidden && !byId('monitor').getAttribute('src')) byId('monitor').src='/monitor';
});
setInterval(render,1000);
setInterval(refresh,10000);
refresh();
