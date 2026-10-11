# CloudLifeOS

ทางเชื่อมคลาวด์แบบอ่านอย่างเดียวสำหรับ LifeOS ที่ใช้ Core Brain และ Monitor เดิมจาก [LifeOS-Foundry](https://github.com/sangkeat/LifeOS-Foundry)

**สถานะ: ส่วนทางเชื่อมทดลองผ่านการตรวจแล้ว; Owner Cockpit ทั้งภารกิจยังไม่เสร็จ**

ยังไม่พบ `LifeOS_Dashboard_Local_Owner_Workspace_v0.8.html` และ `LifeOS_Owner_Workspace_v0.8_QA_And_Handoff.md` ในแหล่งที่เข้าถึงได้ เครื่องมือ PiDzPC Operator ยังไม่ปรากฏเป็นคำสั่งที่เรียกได้ในเซสชันนี้ จึงยังไม่อ้างว่ารักษาฟังก์ชัน v0.8 ครบหรือเชื่อม LocalAgent แล้ว

## สิ่งที่ทำได้

- อ่านและยืนยัน `main` ปัจจุบันผ่าน Git โดยใช้ authentication ที่แพลตฟอร์มให้
- แสดง Cloud / GitHub / LocalAgent / Google Drive / LifeOsWiki พร้อมหลักฐานและขอบเขตการตรวจ
- แยกการเชื่อมต่อ การยืนยันตัวตน การอนุญาตในขอบเขต และการทดสอบใช้งานผ่าน
- ลดสถานะเมื่อหลักฐานหมดอายุ อ่าน server ไม่ได้ หรือแหล่งข้อมูลเปลี่ยนหลังเริ่ม process
- เปิด Monitor เดิมจาก Foundry โดยไม่แก้ต้นฉบับ และระบุว่าข้อมูลเป้าหมาย/ภารกิจเป็น snapshot
- แสดงหน้าทางเชื่อมเป็นภาษาไทย พร้อมรายละเอียดที่กดเปิดได้ และขนาดหน้าจอคอมพิวเตอร์/มือถือ

หน้านี้เป็นเครื่องมือตรวจสอบทางเชื่อม ไม่ใช่ไฟล์ Owner Workspace v0.8 ที่สร้างทดแทน ไม่มีคำสั่งควบคุมเครื่องเจ้าของหรือเปลี่ยน Canon

## เตรียมและเปิด

ใช้ Python 3.12+, Git, Node.js 18+ สำหรับชุดทดสอบ และ Chromium ที่ `/usr/bin/chromium` หรือระบุเส้นทางผ่าน `LIFEOS_CHROMIUM` ในการทดสอบเบราว์เซอร์ ตัว server ใช้ Python standard library ไม่ต้องติดตั้ง dependency สำหรับ runtime

จาก `/workspace/CloudLifeOS`:

```bash
bash scripts/install.sh
python3 -m cloudlifeos.server
```

Server รับคำขอเฉพาะ loopback port 8765 เพื่อทดลองในเครื่องพัฒนา ไม่ใช่เว็บที่เผยแพร่หรือ URL preview ภายนอก ตรวจการทำงานด้วยคำขอในเครื่อง:

```bash
curl --fail --silent http://127.0.0.1:8765/api/health
```

ตรวจ `source.repository`, `source.revision`, `source_changed_since_start` และข้อมูลขอบเขตของแต่ละช่องทาง ไม่ใช้การมี process หรือ port เปิดเป็นหลักฐานว่า connector ทั้งระบบพร้อม

เปิดงานต่อด้วย checkout เดิม ไม่สร้าง Git worktree เพิ่ม เว้นแต่เจ้าของร้องขอ หยุด/เริ่มใหม่เฉพาะ process ที่งานนี้เป็นผู้เริ่ม หาก port มีผู้ใช้เดิม ให้ตรวจว่าเป็น server ของโครงการนี้ก่อน หรือใช้ `--port` อื่น

หลัง bootstrap เปลี่ยน `.local/source.json` หรือ Core Brain ต้องเริ่ม server ใหม่ source เก่าจะไม่ถูกรายงานว่า process รับไปใช้แล้วโดยอัตโนมัติ bootstrap จะรักษา checkout ที่มี local changes และหยุดแทนการล้างไฟล์

## การตรวจ

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
npm --cache /workspace/CloudLifeOS/.local/npm-cache run test:browser
python3 -B -m unittest discover -s .local/core-brain/tests -p 'test_dashboard_owner_view.py'
```

ชุด browser เปิด server ของตัวเองที่ loopback port 8876 และปิดเมื่อจบ ไม่ควรมี server อื่นใช้ port นี้ รายละเอียดผลที่ตรวจจริงอยู่ใน [QA_AND_HANDOFF.md](docs/QA_AND_HANDOFF.md)

## แหล่งข้อมูลและการเก็บ

กฎระบบอยู่ใน Foundry บน `main` ต้นฉบับที่ดึงมาและ snapshot อยู่ใน `.local/` ซึ่ง Git ไม่ติดตาม manifest เก็บ revision และ SHA-256 ของไฟล์ที่ใช้ ห้ามใส่ credential ลงในไฟล์ setup หรือโครงการ

การอ่าน Git สำเร็จพิสูจน์เฉพาะการอ่าน repository นั้น ไม่พิสูจน์ปลั๊กอิน GitHub, GitHub API, push หรือสิทธิ์ที่ repository อื่น การ fetch ใหม่ไม่เปลี่ยนวันที่บันทึกของข้อมูล runtime เก่า

ดูขอบเขตกฎและงานต่อใน [LIFEOS_CONTEXT.md](docs/LIFEOS_CONTEXT.md) ไม่มีการเพิ่มบริการเสียเงิน เปลี่ยนสิทธิ์ เผยแพร่ production หรือ merge เข้า main
