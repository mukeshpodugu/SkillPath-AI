const fs = require('fs');
const path = require('path');

const srcDir = path.join(__dirname, 'frontend', 'dist');
const targets = [
  path.join(__dirname, 'dist'),
  path.join(__dirname, 'build')
];

if (fs.existsSync(srcDir)) {
  for (const target of targets) {
    if (!fs.existsSync(target)) {
      fs.mkdirSync(target, { recursive: true });
    }
    fs.cpSync(srcDir, target, { recursive: true });
    console.log(`[Deploy] Synced dist to ${target}`);
  }
} else {
  console.error(`[Deploy] Source directory ${srcDir} does not exist!`);
  process.exit(1);
}
