# บริบทสำหรับเปิด CloudLifeOS ต่อ

สถานะเอกสาร: operational handoff ของโครงการ ไม่ใช่ Canon หรือทะเบียน capability ใหม่

## แหล่งที่ใช้จริง

Core Brain: `sangkeat/LifeOS-Foundry`, branch `main` ตรวจผ่าน Git ปัจจุบันในรอบงาน 2026-10-11 ได้ revision `6034f92b76138e6ccf8c23f0522c4c2a9ff3edc2` ต้องตรวจใหม่เมื่อเปิดงานต่อ ไม่ถือว่า SHA นี้ยังล่าสุด

คำสั่ง `#Lifeos`, `#LifeosDeepPlan`, `#LifeosSmartRun` resolve จาก `protocols/lifeos-command-registry.md` และนิยามใน `skills/lifeos-work-flow/SKILL.md` ของ revision นี้ DeepPlan วางแผนเท่านั้น SmartRun ใช้ขอบเขตการลงมือที่เจ้าของอนุญาตไว้ในภารกิจ การใช้คำสั่งไม่ได้ให้สิทธิ์เพิ่ม

ชุดบริบทที่จำเป็น: `A00_SYSTEM_INDEX.md`, gate ที่เกี่ยวข้องใน `A01_RUNTIME_GATES.md`, `A03_CONTEXT_ROUTER.md`, `AGENTS.md`, `A02_OPERATING_CONTEXT.md`, command registry/workflow, `protocols/holographic-memory.md`, `protocols/cloud-portable-active-recall.md` และเอกสาร Monitor ที่เกี่ยวข้อง ห้ามอ่านสมองกลางทุกไฟล์ซ้ำโดยไม่มีเหตุผล

## ข้อเท็จจริงที่ตรวจแล้ว

- CloudLifeOS เดิมเป็น checkout ที่ยังไม่มี commit หรือ remote branch; ไม่พบไฟล์ฐานใน workspace
- อ่าน Foundry main ผ่าน HTTPS Git ได้ ไม่ต้องขอ token เพิ่ม
- Source tree ของ Foundry ไม่มีไฟล์ v0.8 และ handoff ตามชื่อที่เจ้าของระบุ มี `tools/agent-process-monitor/dashboard.html`, `owner-status.js`, `server.py` และ `workflow.json` อยู่แล้ว
- Goal Registry ใน source revision นี้ระบุ `G2-OWNER-DASHBOARD` ว่า `completed` ข้อเท็จจริงนี้เป็นสถานะทะเบียน ไม่ใช่หลักฐาน runtime ปัจจุบัน ห้ามเริ่มเป้าหมายเดิมซ้ำ
- ภารกิจใหม่ที่ได้รับอนุญาตคือเตรียม CloudLifeOS เป็น Owner Cockpit ในพื้นที่โครงการ ตอนนี้ทำเฉพาะทางเชื่อมแบบอ่านอย่างเดียวระหว่างรอฐาน v0.8
- Local monitor บนเครื่องพัฒนามีสถานะบทบาทเฉพาะรอบงานนี้ผ่าน writer เดิมใน `.local/status` ไม่ได้ส่งไปยัง Monitor ของ PiDzPC หรือแช็ตอื่น

## ยังไม่ตรวจได้

- ที่อยู่และเนื้อหาไฟล์ฐาน Owner Workspace v0.8 รวมถึง QA handoff
- Operator ของ PiDzPC: เจ้าของระบุให้ใช้ แต่ไม่มี schema ที่เรียกได้ในรายการเครื่องมือเซสชันนี้ จึงไม่มีการเรียกจริงหรือเข้าถึงไฟล์เครื่องเจ้าของ
- ปลั๊กอิน GitHub: ขอการติดตั้งแล้ว ผลไม่ได้ยืนยันว่าเสร็จ และยังไม่มีคำสั่ง connector ให้เรียก; ใช้ Git ที่ตรวจแล้วเป็นเส้นทางสำรอง
- Drive และ LifeOsWiki: ไม่มี adapter ที่เรียกได้ในงานนี้ จึงไม่สรุปว่าคลังความรู้ไม่มีข้อมูลหรือระบบล่ม
- quota/billing ของบริการภายนอก: ไม่ทราบ ใช้เครื่องพัฒนาและเครื่องมือเดิมแบบจำกัด ไม่มีบริการใหม่หรือค่าใช้จ่ายเพิ่มที่เริ่มโดยงานนี้
- private hosted URL, การเปิดจากเครื่องเจ้าของจริง และ fresh-session readback ยังไม่ทดสอบ

## ขอบเขตการทำงานและอำนาจ

System Authority คือ Core Brain ที่ตรวจจาก GitHub; Primary Work Bucket คือ Codex Cloud สำหรับ coding/testing; Auditor เป็น agent ตรวจแยกในเครื่องเดียวกัน ไม่มีการอ้างว่า quota หรือ provider แยกกัน

อนุญาตเฉพาะไฟล์โครงการ `/workspace/CloudLifeOS`, `.local` ที่งานนี้ดูแล, loopback server และชุดทดสอบ ไม่เปลี่ยน Foundry Canon, สิทธิ์ LocalAgent, credential, billing หรือ production ไม่ merge เข้า main

Resource Steward gate เดิมให้ `USE_BOUNDED_WITH_OBSERVATION` จาก resource แบบ Observed/Yellow และ quota ที่ไม่ทราบ ทำงานจำกัดในเครื่องเดิม ไม่เปิด worker หรือบริการภายนอกเพิ่ม Mission Control helper ให้ `DISPATCH_BOUNDED` สำหรับขอบเขตทางเชื่อมใหม่ที่ไม่ซ้ำเป้าหมายเก่า

## ขั้นต่อไปที่ปลอดภัย

1. เมื่อ Operator schema พร้อมจริง ใช้ bounded inventory/workspace list ใน root ที่อนุญาต แล้วค้นสองไฟล์ v0.8 เฉพาะตำแหน่งโครงการที่เกี่ยวข้อง ห้ามขยาย root หรือเปิด credential
2. ตรวจ revision/ความสดของไฟล์และเอกสารส่งต่อก่อนยอมรับเป็นฐาน เก็บ hash และ source pointer
3. เปรียบเทียบ v0.8 กับ Monitor/Cloud adapter ให้รักษาข้อมูลและฟังก์ชันเดิม แล้วทำ Owner Cockpit ในขอบเขตใหม่ที่อนุญาต
4. ทดสอบ desktop/mobile, การนำทาง, stale/offline, privacy, same-resource update และเปิดงานต่ออีกเซสชันก่อนรับมอบทั้งภารกิจ

สิ่งที่ถูกกันออกจาก working truth: ภาพสถานะเก่าของ LocalAgent, ข้ออ้างว่าปลั๊กอินใช้ได้เพราะมีชื่อ, synthetic GitHub publishing experiment และการถือ shared-chat URL เป็น hosted Site งานทดลองเก่าที่ปิดแล้วไม่ถูกเริ่มใหม่
