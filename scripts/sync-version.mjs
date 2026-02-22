import fs from "node:fs";

const pkgPath = new URL("../package.json", import.meta.url);
const manifestPath = new URL("../manifest.json", import.meta.url);

const pkg = JSON.parse(fs.readFileSync(pkgPath, "utf8"));
const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));

const ref = process.env.GITHUB_REF_NAME || process.env.npm_package_version || pkg.version;
const normalized = ref.startsWith("v") ? ref.slice(1) : ref;

if (!normalized) {
  throw new Error("Unable to determine version for sync-version script.");
}

pkg.version = normalized;
manifest.version = normalized;

fs.writeFileSync(pkgPath, `${JSON.stringify(pkg, null, 2)}\n`);
fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);

console.log(`Synced package.json and manifest.json to version ${normalized}`);
