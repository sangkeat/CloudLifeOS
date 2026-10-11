const {test,expect} = require('@playwright/test');
for(const viewport of [{width:1440,height:1000},{width:390,height:844}]) {
  test(`อ่านและนำทาง ${viewport.width}px`,async({page})=>{
    await page.setViewportSize(viewport);
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto('/');
    await expect(page.locator('[data-channel]')).toHaveCount(5);
    await expect(page.locator('[data-channel="cloud"] .badge')).toHaveText('ผ่านเฉพาะขอบเขตที่ระบุ');
    for(const id of ['localagent','drive','wiki']) {
      await expect(page.locator(`[data-channel="${id}"] .yes`)).toHaveCount(0);
    }
    await page.locator('[data-channel="github"] summary').click();
    await expect(page.locator('[data-channel="github"] details')).toHaveAttribute('open','');
    await page.locator('#source-panel summary').click();
    await expect(page.locator('#source')).toContainText('revision ที่โหลด');
    await page.locator('#monitor-panel summary').click();
    const legacy=page.frameLocator('#monitor');
    await expect(legacy.locator('#connectionPanel summary')).toBeVisible();
    await legacy.locator('#connectionPanel summary').click();
    await expect(legacy.locator('#connections')).toContainText('ยังไม่ทราบ');
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
    expect(errors).toEqual([]);
    await page.screenshot({path:`.local/adapter-${viewport.width}.png`,fullPage:true});
  });
}
test('หลักฐานหมดอายุและ server หยุดต้องไม่ค้างสีพร้อมใช้งาน',async({page})=>{
  await page.goto('/');
  await expect(page.locator('[data-channel="cloud"] .yes')).toHaveCount(3);
  await page.locator('#monitor-panel summary').click();
  await expect(page.locator('#monitor')).toHaveAttribute('src','/monitor');
  await page.clock.install();
  await page.clock.setSystemTime(new Date(Date.now()+600000));
  await page.clock.runFor(1100);
  await expect(page.locator('[data-channel="github"] .yes')).toHaveCount(0);
  await expect(page.locator('[data-channel="cloud"] .yes')).toHaveCount(0);
  await page.route('**/api/**',route=>route.abort());
  await page.locator('#refresh').click();
  await expect(page.locator('#notice')).toContainText('อ่านสถานะไม่ได้');
  await expect(page.locator('.yes')).toHaveCount(0);
  await expect(page.locator('#monitor')).toBeHidden();
  await expect(page.locator('#monitor')).not.toHaveAttribute('src','/monitor');
});
test('ข้อความจากแหล่งข้อมูลไม่กลายเป็น HTML ที่รันสคริปต์ได้',async({page})=>{
  await page.route('**/api/health',async route=>{
    const response=await route.fetch();const data=await response.json();
    data.channels[0].label='<img src=x onerror="window.compromised=true">';
    data.channels[0].limitation='<script>window.compromised=true</script>';
    await route.fulfill({json:data});
  });
  await page.goto('/');
  await expect(page.locator('[data-channel="cloud"] h3')).toContainText('<img');
  expect(await page.evaluate(()=>window.compromised)).toBeUndefined();
  await expect(page.locator('[data-channel="cloud"] img')).toHaveCount(0);
});
