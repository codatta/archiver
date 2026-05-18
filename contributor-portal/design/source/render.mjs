/**
 * Render all SVG wireframes in this directory to PNG.
 * Uses sharp (via webapp node_modules) with librsvg at 2x density.
 *
 * Run from repo root:
 *   NODE_PATH=packages/webapp/node_modules node design/source/render.mjs
 */

import { createRequire } from 'module';
import { readFileSync, readdirSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const require = createRequire(import.meta.url);
const sharp = require('sharp');

const __dir  = dirname(fileURLToPath(import.meta.url));
const outDir = join(__dir, '..', 'exports');

mkdirSync(outDir, { recursive: true });

const svgFiles = readdirSync(__dir)
  .filter(f => f.endsWith('.svg'))
  .sort();

console.log(`Rendering ${svgFiles.length} SVG file(s) → ui-designs/pencil-png/\n`);

for (const file of svgFiles) {
  const svgPath = join(__dir, file);
  const pngName = file.replace('.svg', '.png');
  const pngPath = join(outDir, pngName);

  const svgBuf = readFileSync(svgPath);
  const info = await sharp(svgBuf, { density: 144 })
    .png()
    .toFile(pngPath);

  console.log(`✓  ${file.padEnd(32)} →  ${pngName}  (${info.width}×${info.height})`);
}

console.log('\nDone.');
