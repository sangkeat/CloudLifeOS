const {defineConfig} = require('@playwright/test');
module.exports = defineConfig({
  testDir: './tests/browser',
  workers: 1,
  reporter: [['list'], ['json', {outputFile:'.local/browser-results.json'}]],
  use: {
    baseURL:'http://127.0.0.1:8876',
    launchOptions:{executablePath:process.env.LIFEOS_CHROMIUM || '/usr/bin/chromium'},
    screenshot:'only-on-failure',
  },
  webServer: {
    command:'python3 -m cloudlifeos.server --port 8876',
    url:'http://127.0.0.1:8876/api/health',
    reuseExistingServer:false,
  },
});
