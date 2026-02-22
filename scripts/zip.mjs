import { execSync } from "node:child_process";
import fs from "node:fs";

const output = "medlog-oneclick.zip";
for (const file of ["main.js", "manifest.json", "styles.css"]) {
  if (!fs.existsSync(file)) {
    throw new Error(`Missing required file for zip: ${file}`);
  }
}

if (fs.existsSync(output)) {
  fs.unlinkSync(output);
}

execSync(`zip -j ${output} main.js manifest.json styles.css`, { stdio: "inherit" });
console.log(`Created ${output}`);
