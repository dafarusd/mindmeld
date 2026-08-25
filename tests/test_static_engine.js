/* Parity tests: the JS port must behave identically to the Python engine.
 * Run with: node tests/test_static_engine.js   (from repo root)
 * Exits non-zero on failure.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const ROOT = path.join(__dirname, "..");
global.localStorage = { getItem: () => null, setItem: () => {} };
eval(fs.readFileSync(path.join(ROOT, "static_site", "data.js"), "utf8"));
const MM = require(path.join(ROOT, "static_site", "game.js"));

let failures = 0;
function check(name, cond, extra = "") {
  if (cond) console.log(`  ok  ${name}`);
  else { failures++; console.log(`FAIL  ${name} ${extra}`); }
}

function simulate(target, maxQ = 20, boss = false) {
  const mr = new MM.MindReader(maxQ, boss);
  while (true) {
    const attr = mr.nextQuestion();
    if (attr === null) return [mr.bestCandidate() === target, mr.asked.length];
    mr.answer(attr, MM.ENTITIES[target].vec[attr]);
    if (mr.shouldGuess()) {
      if (mr.guess() === target) return [true, mr.asked.length];
      mr.confirmGuess(false);
      if (mr.guessesMade.length >= 3) return [false, mr.asked.length];
    }
  }
}

async function main() {
  console.log("== self-play parity (JS engine, all entities) ==");
  let wins = 0;
  const qcounts = [];
  const names = MM.NAMES();
  for (const t of names) {
    const [ok, nq] = simulate(t);
    qcounts.push(nq);
    if (ok) wins++;
  }
  qcounts.sort((a, b) => a - b);
  const rate = wins / names.length;
  const median = qcounts[Math.floor(qcounts.length / 2)];
  console.log(`  JS: ${wins}/${names.length} = ${(rate * 100).toFixed(1)}%, median ${median}q`);
  check("self-play >= 90%", rate >= 0.90, `(got ${(rate * 100).toFixed(1)}%)`);
  check("median <= 14", median <= 14);

  console.log("== daily secret parity with Python engine ==");
  const pyScript = `
from game.engine import daily_info
import sys
for d in [$(DAYS)]:
    s, label = daily_info(d)
    print(f"{d}|{s}|{label or ''}")
`;
  const testDays = [739900, 739901, 739902, 739903, 739904, 739905, 739906, 740013, 740046];
  const pyOut = execFileSync("python3", ["-c", pyScript.replace("$(DAYS)", testDays.join(","))], { cwd: ROOT }).toString().trim().split("\n");
  const epoch1970 = new Date(Date.UTC(1970, 0, 1));
  for (const line of pyOut) {
    const [ordS, pySecret, pyLabel] = line.split("|");
    const ord = parseInt(ordS);
    const epochDays = ord - 719163;
    const dt = new Date(epoch1970.getTime() + epochDays * 86400000);
    const [jsSecret, jsLabel] = await MM.dailyInfo(dt.getUTCFullYear(), dt.getUTCMonth() + 1, dt.getUTCDate());
    check(`day ${ord}: secret`, jsSecret === pySecret, `(js=${jsSecret} py=${pySecret})`);
    check(`day ${ord}: label`, (jsLabel || "") === pyLabel, `(js=${jsLabel} py=${pyLabel})`);
  }

  console.log("== engine details ==");
  const k = new MM.SecretKeeper("dog", { bluff: false });
  check("ground truth yes", k.answerQuestion("is it an animal?")[1] === "Yes.");
  check("ground truth no", k.answerQuestion("can it fly?")[1] === "No.");
  const [c1, h1] = new MM.SecretKeeper("dog", { bluff: false }).tryGuess("cat");
  check("known wrong guess gives heat", !c1 && h1 !== null);
  const [c2, h2] = new MM.SecretKeeper("dog", { bluff: false }).tryGuess("zzzunknown");
  check("unknown guess gives no heat", !c2 && h2 === null);
  const k2 = new MM.SecretKeeper("dog", { bluff: false, invertFirstN: 3 });
  check("opposite day inverts", k2.answerQuestion("is it an animal?")[1] === "No.");
  check("parseAnswer", MM.parseAnswer("yep") === 1.0 && MM.parseAnswer("nope") === 0.0 && MM.parseAnswer("zzz") === null);
  check("resolveEntity", MM.resolveEntity("is it Darth Vader?") === "Darth Vader");
  check("similarity ordering", MM.similarity("dog", "cat") > MM.similarity("dog", "pizza"));
  const card = MM.shareCard(42, 11, true, 9, true, "Cinema Friday", "Mistwalker");
  check("share card", card.includes("MIND MELD #42") && card.includes("Cinema Friday") && card.includes("⚡ YOU WON THE MELD"));

  console.log(failures === 0 ? "\nALL PASS" : `\n${failures} FAILURES`);
  process.exit(failures === 0 ? 0 : 1);
}

main().catch(e => { console.error(e); process.exit(1); });
