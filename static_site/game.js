/* Mind Meld static engine — faithful port of game/engine.py.
 * No DOM access here; this file is pure game logic so it can be
 * unit-tested under Node and reused by any UI.
 * Requires MM_DATA (data.js) loaded first.
 */
"use strict";

const MM = (() => {
  const YES = 1.0, NO = 0.0, MAYBE = 0.5;
  const ATTRS = MM_DATA.attributes;
  const ATTR_INDEX = {};
  ATTRS.forEach((a, i) => { ATTR_INDEX[a] = i; });
  const ENTITIES = MM_DATA.entities;
  const QUESTIONS = MM_DATA.questions;
  const SYNONYMS = MM_DATA.synonyms;
  const ANSWER_WORDS = {
    yes: new Set(MM_DATA.answer_words.yes),
    no: new Set(MM_DATA.answer_words.no),
    maybe: new Set(MM_DATA.answer_words.maybe),
  };

  const BASE_NAMES = Object.keys(ENTITIES).sort();
  let NAMES = BASE_NAMES.slice();
  let MATRIX = NAMES.map(n => ATTRS.map(a => ENTITIES[n].vec[a]));
  const LEARN_KEY = "mm_learned";

  function loadLearned() {
    try {
      const raw = localStorage.getItem(LEARN_KEY);
      if (!raw) return {};
      const d = JSON.parse(raw);
      return (d && typeof d === "object") ? d : {};
    } catch { return {}; }
  }

  function reload() {
    const learned = loadLearned();
    for (const key of Object.keys(learned)) {
      const e = learned[key];
      if (e && e.vec && !ENTITIES[key]) {
        ENTITIES[key] = { blurb: e.blurb || "learned from a challenger", vec: e.vec, learned: true };
      }
    }
    NAMES = Object.keys(ENTITIES).sort();
    MATRIX = NAMES.map(n => ATTRS.map(a => {
      const v = ENTITIES[n].vec[a];
      return v === undefined ? MAYBE : v;
    }));
  }
  reload();

  const MAX_QUESTIONS = 20;

  function parseAnswer(text) {
    const words = new Set(text.toLowerCase().trim().split(/\s+/));
    for (const [key, set] of Object.entries(ANSWER_WORDS)) {
      for (const w of words) if (set.has(w)) return key === "yes" ? YES : key === "no" ? NO : MAYBE;
    }
    return null;
  }

  function entropy(ws) {
    const total = ws.reduce((a, b) => a + b, 0);
    if (total <= 0) return 0;
    let h = 0;
    for (const w of ws) {
      if (w > 0) { const p = w / total; h -= p * Math.log2(p); }
    }
    return h;
  }

  class MindReader {
    constructor(maxQuestions = MAX_QUESTIONS, boss = false) {
      this.maxQuestions = maxQuestions;
      this.boss = boss;
      this.w = new Array(NAMES.length).fill(1.0);
      this.asked = [];
      this.answers = [];
      this.guessesMade = [];
    }
    nextQuestion() {
      const avail = [];
      for (let a = 0; a < ATTRS.length; a++) if (!this.asked.includes(ATTRS[a])) avail.push(a);
      if (!avail.length || this.asked.length >= this.maxQuestions) return null;
      const total = this.w.reduce((a, b) => a + b, 0);
      const curH = entropy(this.w);
      let bestA = -1, bestGain = -1;
      for (const a of avail) {
        let yw = 0, nw = 0, mw = 0;
        const yl = [], nl = [], ml = [];
        for (let i = 0; i < NAMES.length; i++) {
          const v = MATRIX[i][a], wi = this.w[i];
          if (v === YES) { yw += wi; yl.push(wi); }
          else if (v === NO) { nw += wi; nl.push(wi); }
          else { mw += wi; ml.push(wi); }
        }
        const expH = (yw / total) * entropy(yl) + (nw / total) * entropy(nl) + (mw / total) * entropy(ml);
        const gain = curH - expH;
        if (gain > bestGain) { bestGain = gain; bestA = a; }
      }
      return ATTRS[bestA];
    }
    answer(attr, value) {
      this.asked.push(attr);
      this.answers.push([attr, value]);
      const a = ATTR_INDEX[attr];
      for (let i = 0; i < NAMES.length; i++) {
        const agree = 1.0 - Math.abs(MATRIX[i][a] - value);
        this.w[i] *= 0.05 + 0.95 * agree;
      }
      const s = this.w.reduce((x, y) => x + y, 0);
      if (s > 0) for (let i = 0; i < NAMES.length; i++) this.w[i] /= s;
    }
    ranked() {
      return NAMES.map((n, i) => [n, this.w[i]]).sort((x, y) => y[1] - x[1]);
    }
    bestCandidate() { return this.ranked()[0][0]; }
    topShare() {
      const total = this.w.reduce((a, b) => a + b, 0);
      return total > 0 ? this.w[NAMES.indexOf(this.bestCandidate())] / total : 0;
    }
    topCandidates(n = 3) { return this.ranked().slice(0, n).map(x => x[0]); }
    shouldGuess() {
      const asked = this.asked.length;
      if (asked >= this.maxQuestions) return true;
      const r = this.ranked();
      if (r.length < 2) return true;
      const ratioGate = this.boss ? 1.3 : (this.maxQuestions <= 10 ? 1.6 : 2.0);
      if (asked >= 4 && r[1][1] > 0 && r[0][1] / r[1][1] >= ratioGate) return true;
      if (asked >= 5 && this.topShare() >= 0.30) return true;
      return false;
    }
    guess() {
      const g = this.bestCandidate();
      this.guessesMade.push(g);
      return g;
    }
    confirmGuess(correct) {
      if (correct) return;
      const wrong = this.guessesMade.length ? this.guessesMade[this.guessesMade.length - 1] : this.bestCandidate();
      this.w[NAMES.indexOf(wrong)] *= 0.01;
    }
    questionsLeft() { return this.maxQuestions - this.asked.length; }
  }

  function matchAttribute(text) {
    const t = text.toLowerCase();
    let best = null, bestLen = 0;
    for (const word of Object.keys(SYNONYMS)) {
      if (t.includes(word) && word.length > bestLen) { best = SYNONYMS[word]; bestLen = word.length; }
    }
    return best;
  }

  function resolveEntity(text) {
    let t = text.toLowerCase().trim().replace(/\?$/, "").trim();
    t = t.replace(/^is it /, "").replace(/^(a|an|the) /, "").trim();
    const lookup = {};
    for (const n of NAMES) lookup[n.toLowerCase()] = n;
    if (lookup[t]) return lookup[t];
    for (const n of NAMES) {
      const low = n.toLowerCase();
      if (Math.min(t.length, low.length) >= 4 && (low.includes(t) || t.includes(low))) return n;
    }
    return null;
  }

  function similarity(a, b) {
    let score = 0;
    for (const attr of ATTRS) score += 1.0 - 0.9 * Math.abs(ENTITIES[a].vec[attr] - ENTITIES[b].vec[attr]);
    return score / ATTRS.length;
  }

  function heatLabel(s) {
    if (s >= 0.90) return "🔥 BURNING — almost there";
    if (s >= 0.82) return "🔥 warm — close";
    if (s >= 0.74) return "🌤 coolish — some overlap";
    if (s >= 0.66) return "❄ cold";
    return "🥶 ice cold — wrong kingdom entirely";
  }

  class SecretKeeper {
    constructor(secret, { bluff = true, bluffCount = 1, invertFirstN = 0, rng = Math.random } = {}) {
      this.secret = secret;
      this.bluff = bluff;
      this.invertFirstN = invertFirstN;
      this.questionsAsked = 0;
      this.solved = false;
      this.bluffAttrs = [];
      this.bluffUsed = false;
      if (bluff) {
        const cands = ATTRS.filter(a => ENTITIES[secret].vec[a] !== MAYBE);
        const pool = cands.slice();
        for (let i = 0; i < Math.min(bluffCount, pool.length); i++) {
          const j = Math.floor(rng() * pool.length);
          this.bluffAttrs.push(pool.splice(j, 1)[0]);
        }
      }
    }
    answerQuestion(text) {
      this.questionsAsked++;
      const attr = matchAttribute(text);
      if (!attr) return ["unknown", "The spirits cannot parse that question. Ask about a trait — alive? animal? metal? famous?"];
      let v = ENTITIES[this.secret].vec[attr];
      if (this.bluffAttrs.includes(attr)) { this.bluffUsed = true; v = v === YES ? NO : v === NO ? YES : v; }
      if (this.questionsAsked <= this.invertFirstN) v = v === YES ? NO : v === NO ? YES : v;
      if (v === YES) return ["yes", "Yes."];
      if (v === NO) return ["no", "No."];
      return ["maybe", "Hmm... sometimes, in a manner of speaking."];
    }
    tryGuess(text) {
      let t = text.toLowerCase().trim().replace(/^is it /, "").replace(/\?$/, "").trim();
      t = t.replace(/^(a|an|the) /, "").trim();
      const secret = this.secret.toLowerCase();
      if (t && t.length >= 3 && (t === secret || (t.length >= 4 && (secret.includes(t) || t.includes(secret))))) {
        this.solved = true;
        return [true, null];
      }
      const known = resolveEntity(text);
      if (known !== null) return [false, heatLabel(similarity(this.secret, known))];
      return [false, null];
    }
    bluffDisclosure() {
      if (!this.bluff) return null;
      if (this.bluffUsed && this.bluffAttrs.length) {
        const used = this.bluffAttrs.map(a => QUESTIONS[a][0].replace(/\?$/, "").toLowerCase());
        const n = this.bluffAttrs.length;
        return `(confession: I ${n === 1 ? "lied once" : `lied ${n} times`} — about: ${used.join(", ")})`;
      }
      return null;
    }
  }

  function dateToOrdinal(y, m, d) { return Math.floor(Date.UTC(y, m - 1, d) / 86400000) + 719163; }

  const WEEKDAY_THEMES = {
    1: ["Animal Tuesday", e => e.vec.is_animal === YES],
    4: ["Cinema Friday", e => e.vec.from_screen === YES || e.vec.is_fictional === YES],
    5: ["Feast Saturday", e => e.vec.is_edible === YES],
  };

  function eventForDate(y, m, d, weekday) {
    if (m === 4 && d === 1) return { key: "opposite_day", name: "🃏 Opposite Day",
      intro: "Today is Opposite Day. My first three answers will be exactly backwards. Good luck.", invertFirstN: 3 };
    if (m === 10 && d === 31) return { key: "halloween", name: "🎃 Halloween",
      intro: "Tonight the mist holds only monsters and villains.",
      pool: e => e.vec.is_villain === YES || e.vec.is_dangerous === YES || e.vec.is_mythological === YES };
    if (weekday === 4 && d === 13) return { key: "friday13", name: "🔪 Friday the 13th",
      intro: "Friday the 13th. The genie lies TWICE today.", bluffCount: 2 };
    return null;
  }

  async function sha256Hex(text) {
    const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
    return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("");
  }

  async function dailyInfo(y, m, d) {
    const weekday = weekdayPy(y, m, d);
    const theme = WEEKDAY_THEMES[weekday];
    const event = eventForDate(y, m, d, weekday);
    let pool = BASE_NAMES.slice();
    if (event && event.pool) pool = pool.filter(n => event.pool(ENTITIES[n]));
    else if (theme) pool = pool.filter(n => theme[1](ENTITIES[n]));
    if (!pool.length) pool = BASE_NAMES.slice();
    const hex = await sha256Hex(`mindmeld-${dateToOrdinal(y, m, d)}`);
    const idx = Number(BigInt("0x" + hex) % BigInt(pool.length));
    const secret = pool.slice().sort()[idx];
    return [secret, (event ? event.name : null) || (theme ? theme[0] : null), event];
  }

  function weekdayPy(y, m, d) { return (new Date(Date.UTC(y, m - 1, d)).getUTCDay() + 6) % 7; }

  function shareCard(day, aiQ, aiWon, youQ, youWon, theme, rank) {
    const aiLine = aiWon ? `AI read you in ${aiQ} 🟩` : "AI failed to read you 🟥";
    const youLine = youWon ? `You read the AI in ${youQ} 🟩` : "The AI kept its secret 🟥";
    let verdict;
    if (youWon && (!aiWon || (youQ || 99) <= (aiQ || 99))) verdict = "⚡ YOU WON THE MELD";
    else if (aiWon) verdict = "🧠 THE AI WINS";
    else verdict = "🤝 A RARE DRAW";
    let card = `MIND MELD #${day}${theme ? " · " + theme : ""}\n${aiLine}\n${youLine}\n${verdict}`;
    if (rank) card += `\nrank: ${rank}`;
    return card + "\n🧠 brain: 26M params, trained at home";
  }

  function learnEntity(name, answers) {
    const clean = name.trim().toLowerCase();
    if (!/^[a-z0-9][a-z0-9 '\-]{1,38}[a-z0-9]$/.test(clean)) throw new Error("names: 3-40 chars, letters/numbers/spaces only");
    if (resolveEntity(clean) !== null) throw new Error(`I already know something very close to '${clean}'`);
    const learned = loadLearned();
    if (Object.keys(learned).some(k => k.toLowerCase() === clean)) throw new Error(`'${clean}' is already learned`);
    const vec = {};
    for (const a of ATTRS) vec[a] = MAYBE;
    for (const [attr, val] of answers) if (attr in vec) vec[attr] = val;
    learned[clean] = { blurb: "learned from a challenger", vec };
    const keys = Object.keys(learned);
    while (keys.length > 200) { delete learned[keys.shift()]; }
    localStorage.setItem(LEARN_KEY, JSON.stringify(learned));
    reload();
    return clean;
  }

  return {
    YES, NO, MAYBE, ATTRS, ENTITIES, QUESTIONS, NAMES: () => NAMES, MAX_QUESTIONS,
    MindReader, SecretKeeper, parseAnswer, matchAttribute, resolveEntity,
    similarity, heatLabel, dailyInfo, eventForDate, shareCard, learnEntity,
    dateToOrdinal, weekdayPy, reload,
  };
})();

if (typeof module !== "undefined" && module.exports) module.exports = MM;
