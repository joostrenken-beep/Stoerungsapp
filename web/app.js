'use strict';
/* Kanalbetrieb Osterholz-Scharmbeck – Web-Version.
   Bestandsnetz aus netz.json (fiktive Demo), alles Veränderliche in der gemeinsamen Datenbank (db). */

// ------------------------------------------------------------------ Hilfen
const $ = (s, el = document) => el.querySelector(s);
const esc = t => String(t ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const zahl = (v, n = 2) => v == null || v === '' || isNaN(v) ? '–' : Number(v).toLocaleString('de-DE', {minimumFractionDigits: n, maximumFractionDigits: n});
const datum = iso => { if (!iso) return '–'; const [j, m, t] = iso.slice(0, 10).split('-'); return `${t}.${m}.${j}`; };
const datumZeit = iso => !iso ? '–' : datum(iso) + (iso.length > 10 ? ' ' + iso.slice(11, 16) : '');
const heute = () => new Date().toISOString().slice(0, 10);
const jetztIso = () => { const d = new Date(); d.setMinutes(d.getMinutes() - d.getTimezoneOffset()); return d.toISOString().slice(0, 16); };
const tageBis = iso => Math.round((new Date(iso + 'T00:00') - new Date(heute() + 'T00:00')) / 864e5);
const neueId = p => p + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
function monateAddieren(iso, n) {
  const [j, m, t] = iso.split('-').map(Number); const z = new Date(Date.UTC(j, m - 1 + n, 1));
  const letzter = new Date(Date.UTC(z.getUTCFullYear(), z.getUTCMonth() + 1, 0)).getUTCDate();
  z.setUTCDate(Math.min(t, letzter)); return z.toISOString().slice(0, 10);
}
const num = v => { if (v == null || v === '') return null; const z = parseFloat(String(v).replace(',', '.')); return isNaN(z) ? null : z; };

const ZK = [
  ['sehr starker Mangel', 'sofortiger Handlungsbedarf', 'var(--zk0)'], ['starker Mangel', 'kurzfristiger Handlungsbedarf', 'var(--zk1)'],
  ['mittlerer Mangel', 'mittelfristiger Handlungsbedarf', 'var(--zk2)'], ['leichter Mangel', 'langfristiger Handlungsbedarf', 'var(--zk3)'],
  ['geringfügiger Mangel', 'kein Handlungsbedarf', 'var(--zk4)'], ['kein Mangel', 'kein Handlungsbedarf', 'var(--zk5)']];
const KANAL = {SW: 'Schmutzwasser', RW: 'Regenwasser', MW: 'Mischwasser'};
const PRIOS = ['kritisch', 'hoch', 'mittel', 'niedrig'];
const MELDEWEGE = ['Fernwirktechnik / Alarm', 'Telefon', 'Bürgermeldung', 'Kontrollgang', 'Bereitschaft', 'Sonstiges'];
const WARTUNGSARTEN = ['Wartung', 'Inspektion', 'Reinigung', 'Sichtkontrolle', 'Funktionsprüfung', 'TV-Inspektion', 'Prüfung (DGUV/VDE)', 'Reparatur'];
const ERGEBNISSE = ['in Ordnung', 'Mängel festgestellt', 'nicht in Ordnung'];
const ZIELNAMEN = {haltung: 'Haltung', knoten: 'Schacht/Bauwerk', anlage: 'Anlage', objekt: 'Anlagenobjekt'};
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const zkFarbe = k => k == null ? css('--leise') : css('--zk' + k);

const zkChip = k => k == null ? '<span class="chip" title="nicht bewertet">–</span>' :
  `<span class="chip zk zk${k}" title="${ZK[k][0]} – ${ZK[k][1]}">${k}</span>`;
const artChip = a => a ? `<span class="chip art-${a}">${a}</span>` : '';
const prioChip = p => `<span class="chip prio-${esc(p)}">${esc(p)}</span>`;
const statusChip = s => `<span class="chip st-${esc((s || '').replace(/ /g, '-'))}">${esc(s)}</span>`;

// ------------------------------------------------------------------ Koordinaten (UTM / Gauß-Krüger)
function tmInverse(x, y, a, f, k0, lon0, fe) {
  const e2 = f * (2 - f), ep2 = e2 / (1 - e2), m = y / k0;
  const mu = m / (a * (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256));
  const e1 = (1 - Math.sqrt(1 - e2)) / (1 + Math.sqrt(1 - e2));
  const p1 = mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * Math.sin(2 * mu) + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * Math.sin(4 * mu) +
    (151 * e1 ** 3 / 96) * Math.sin(6 * mu) + (1097 * e1 ** 4 / 512) * Math.sin(8 * mu);
  const n1 = a / Math.sqrt(1 - e2 * Math.sin(p1) ** 2), t1 = Math.tan(p1) ** 2, c1 = ep2 * Math.cos(p1) ** 2;
  const r1 = a * (1 - e2) / (1 - e2 * Math.sin(p1) ** 2) ** 1.5, d = (x - fe) / (n1 * k0);
  const lat = p1 - (n1 * Math.tan(p1) / r1) * (d ** 2 / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * ep2) * d ** 4 / 24 +
    (61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * ep2 - 3 * c1 ** 2) * d ** 6 / 720);
  const lon = lon0 * Math.PI / 180 + (d - (1 + 2 * t1 + c1) * d ** 3 / 6 + (5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * ep2 + 24 * t1 ** 2) * d ** 5 / 120) / Math.cos(p1);
  return [lat * 180 / Math.PI, lon * 180 / Math.PI];
}
function gkNachWgs84(rw, hw) {
  const z = Math.floor(rw / 1e6), [la, lo] = tmInverse(rw, hw, 6377397.155, 1 / 299.1528128, 1, z * 3, z * 1e6 + 5e5);
  const a = 6377397.155, f = 1 / 299.1528128, e2 = f * (2 - f), R = Math.PI / 180;
  const n = a / Math.sqrt(1 - e2 * Math.sin(la * R) ** 2);
  let X = n * Math.cos(la * R) * Math.cos(lo * R), Y = n * Math.cos(la * R) * Math.sin(lo * R), Z = n * (1 - e2) * Math.sin(la * R);
  const s = 1 + 6.7e-6, rx = 0.202 / 3600 * R, ry = 0.045 / 3600 * R, rz = -2.455 / 3600 * R;
  [X, Y, Z] = [598.1 + s * (X - rz * Y + ry * Z), 73.7 + s * (rz * X + Y - rx * Z), 418.2 + s * (-ry * X + rx * Y + Z)];
  const A = 6378137, F = 1 / 298.257223563, E2 = F * (2 - F), p = Math.hypot(X, Y);
  let lat = Math.atan2(Z, p * (1 - E2));
  for (let i = 0; i < 10; i++) { const N2 = A / Math.sqrt(1 - E2 * Math.sin(lat) ** 2); lat = Math.atan2(Z + E2 * N2 * Math.sin(lat), p); }
  return [lat / R, Math.atan2(Y, X) / R];
}
function nachWgs84(rw, hw) {
  if (rw == null || hw == null) return null;
  if (rw >= 1e7 && rw < 1e8) { const z = Math.floor(rw / 1e6); return tmInverse(rw - z * 1e6, hw, 6378137, 1 / 298.257222101, 0.9996, z * 6 - 183, 5e5); }
  if (rw >= 1e5 && rw < 1e6) return tmInverse(rw, hw, 6378137, 1 / 298.257222101, 0.9996, 9, 5e5);
  if (rw >= 1e6 && rw < 6e6) return gkNachWgs84(rw, hw);
  return null;
}
function abstand(a, b) { const m = 111320, c = Math.cos((a[0] + b[0]) / 2 * Math.PI / 180); return Math.hypot((b[0] - a[0]) * m, (b[1] - a[1]) * m * c); }
function punktAufLinie(pts, anteil) {
  if (!pts || !pts.length) return null; if (pts.length === 1) return pts[0];
  anteil = Math.min(Math.max(anteil, 0), 1);
  const l = []; let g = 0; for (let i = 0; i < pts.length - 1; i++) { l.push(abstand(pts[i], pts[i + 1])); g += l[i]; }
  let z = g * anteil;
  for (let i = 0; i < l.length; i++) { if (z <= l[i] || i === l.length - 1) { const t = l[i] ? Math.min(z / l[i], 1) : 0; return [pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t]; } z -= l[i]; }
  return pts[pts.length - 1];
}

// ------------------------------------------------------------------ DWA-M 149
let KATALOG = {};
const basisKode = k => { k = (k || '').toUpperCase(); return k.length === 3 && k[0] === 'D' ? 'B' + k.slice(1) : k; };
function kodeText(k, c1, c2) {
  const i = KATALOG[basisKode(k)]; if (!i) return 'nicht im Katalog';
  const t = [i.text]; if (c1 && i.char1?.[c1]) t.push(i.char1[c1]); if (c2 && i.char2?.[c2]) t.push(i.char2[c2]);
  return t.join(', ') + ((k || '').toUpperCase().startsWith('D') ? ' (Schacht)' : '');
}
const istInfo = k => !!KATALOG[basisKode(k)]?.info;
function prozent(q, g) { if (q == null) return g[g.length - 1][1]; for (const [ab, k] of g) if (q >= ab) return k; return g[g.length - 1][1]; }
function klassenVorschlag(kode, c1, c2, q1) {
  const k = basisKode(kode), c = (c1 || '').toUpperCase(), q = num(q1); let d = null, s = null, b = null;
  switch (k) {
    case 'BAA': s = prozent(q, [[15, 1], [7, 2], [3, 3], [0, 4]]); break;
    case 'BAB': [s, d] = ({A: [4, 4], B: [3, 3], C: [1, 2]})[c] || [3, 3]; break;
    case 'BAC': s = ({A: 1, B: 0, C: 0})[c] ?? 1; d = 1; break;
    case 'BAD': s = ({A: 2, B: 1, C: 1, D: 0})[c] ?? 2; break;
    case 'BAE': s = 3; d = 3; break;
    case 'BAF': s = 'FGHI'.includes(c) && c ? 1 : 'BCDE'.includes(c) && c ? 2 : 'JK'.includes(c) && c ? 3 : 4; break;
    case 'BAG': b = prozent(q, [[50, 1], [25, 2], [0, 3]]); break;
    case 'BAH': d = ({A: 2, B: 3, C: 2, D: 2})[c] ?? 3; if (c === 'E') b = 1; break;
    case 'BAI': b = 2; d = 3; break;
    case 'BAJ': d = c === 'A' ? ((q || 0) >= 40 ? 2 : 3) : c === 'B' ? 2 : 3; break;
    case 'BAK': case 'BAL': case 'BAM': d = 2; break;
    case 'BAN': d = 1; break;
    case 'BAO': s = 1; d = 1; break;
    case 'BAP': s = 0; d = 1; break;
    case 'BBA': b = prozent(q, [[50, 1], [10, 2], [0, 3]]); d = 2; break;
    case 'BBB': case 'BBC': case 'BBE': b = prozent(q, [[50, 1], [25, 2], [10, 3], [0, 4]]); break;
    case 'BBD': s = 1; d = 1; break;
    case 'BBF': d = ({A: 3, B: 2, C: 1, D: 0})[c] ?? 2; break;
    case 'BBG': d = 1; break;
    case 'BBH': b = 3; break;
  }
  return [d, s, b];
}
const minKlasse = (...k) => { const w = k.filter(x => x != null); return w.length ? Math.min(...w) : null; };

// ------------------------------------------------------------------ Zustand
const S = {
  basis: null, db: null, user: null, assets: null, downloads: null, darf: null,
  dyn: {stoerungen: new Map(), wartungsplaene: new Map(), massnahmen: new Map(), schaeden: new Map(), schadenstatus: new Map(), importe: new Map(), importdaten: new Map()},
  geladen: {}, dbStatus: 'verbinde',
  N: null, ansicht: 'uebersicht', filter: {}, seitenGroesse: 50, detail: null, karte: null,
};

// Datenmodell aus Bestand + Importen + manuellen Schäden aufbauen
function aufbauen() {
  const B = S.basis, N = {knoten: new Map(), haltungen: new Map(), insp: new Map(), schaeden: new Map(), anlagen: new Map(), objekte: new Map(), inspNachObjekt: new Map()};
  for (const k of B.knoten) N.knoten.set(k[0], {bez: k[0], art: k[1], kanalart: k[2], ortsteil: k[3], strasse: k[4], lat: k[5], lon: k[6], deckel: k[7], sohle: k[8], baujahr: k[9], material: k[10], anlage: k[11], quelle: 'Bestand (Demo)'});
  for (const h of B.haltungen) {
    const g = []; for (let i = 0; i < h[13].length; i += 2) g.push([h[13][i], h[13][i + 1]]);
    N.haltungen.set(h[0], {bez: h[0], von: h[1], bis: h[2], kanalart: h[3], funktion: h[4], ortsteil: h[5], strasse: h[6], laenge: h[7], dn: h[8], material: h[9], baujahr: h[10], sz: h[11], sa: h[12], geo: g, quelle: 'Bestand (Demo)'});
  }
  for (const i of B.inspektionen) N.insp.set('b' + i[0], {id: 'b' + i[0], typ: i[1] === 'h' ? 'haltung' : 'knoten', objekt: i[2], datum: i[3], firma: i[4], untersucher: i[5], gegen: !!i[6], laenge: i[7], quelle: 'Bestand (Demo)', schaeden: []});
  for (const s of B.schaeden) {
    const insp = N.insp.get('b' + s[1]);
    const o = {id: 'b' + s[0], insp: insp.id, typ: insp.typ, objekt: insp.objekt, datum: insp.datum, kode: s[2], c1: s[3], c2: s[4], q1: s[5], station: s[6], stationBis: s[7], uhr: s[8], verbindung: !!s[9], kd: s[10], ks: s[11], kb: s[12], foto: s[13]};
    N.schaeden.set(o.id, o); insp.schaeden.push(o);
  }
  for (const a of B.anlagen) N.anlagen.set(a.bez, {...a, objekte: []});
  for (const o of B.objekte) { const ob = {...o, key: o.anlage + '/' + o.bez}; N.objekte.set(ob.key, ob); N.anlagen.get(o.anlage)?.objekte.push(ob); }

  // Importe in zeitlicher Reihenfolge anwenden
  const importe = [...S.dyn.importe.values()].sort((a, b) => (a.zeitpunkt || '').localeCompare(b.zeitpunkt || ''));
  for (const imp of importe) {
    const teile = [...S.dyn.importdaten.values()].filter(t => t.import_id === imp._id).sort((a, b) => a.teil - b.teil);
    for (const t of teile) {
      for (const k of t.knoten || []) N.knoten.set(k.bez, {...N.knoten.get(k.bez), ...k, quelle: imp.datei});
      for (const h of t.haltungen || []) { const alt = N.haltungen.get(h.bez); N.haltungen.set(h.bez, {...alt, ...h, geo: h.geo && h.geo.length >= 2 ? h.geo : (alt?.geo || []), quelle: imp.datei}); }
      for (const a of t.anlagen || []) N.anlagen.set(a.bez, {...(N.anlagen.get(a.bez) || {objekte: []}), ...a});
      for (const [n, i] of (t.inspektionen || []).entries()) {
        for (const [id, alt] of N.insp) if (alt.typ === i.typ && alt.objekt === i.objekt && alt.datum === i.datum) { N.insp.delete(id); alt.schaeden.forEach(s => N.schaeden.delete(s.id)); }
        const id = `i:${imp._id}:${t.teil}:${n}`, insp = {...i, id, quelle: imp.datei, schaeden: []};
        i.schaeden.forEach((s, j) => { const o = {...s, id: id + ':' + j, insp: id, typ: i.typ, objekt: i.objekt, datum: i.datum}; N.schaeden.set(o.id, o); insp.schaeden.push(o); });
        N.insp.set(id, insp);
      }
    }
  }
  for (const [docId, m] of S.dyn.schaeden) { const o = {...m, id: 'm:' + docId, manuell: true}; N.schaeden.set(o.id, o); }
  for (const i of N.insp.values()) { const k = i.typ + ':' + i.objekt; if (!N.inspNachObjekt.has(k)) N.inspNachObjekt.set(k, []); N.inspNachObjekt.get(k).push(i); }
  for (const l of N.inspNachObjekt.values()) l.sort((a, b) => b.datum.localeCompare(a.datum));
  S.N = N;
  for (const h of N.haltungen.values()) zustandSetzen('haltung', h);
  for (const k of N.knoten.values()) zustandSetzen('knoten', k);
}
function schadenStatus(s) { if (s.manuell) return s.status || 'offen'; return S.dyn.schadenstatus.get(s.id.replace(/:/g, '~'))?.status || 'offen'; }
const schadenKlasse = s => minKlasse(s.kd, s.ks, s.kb);
function aktuelleSchaeden(typ, bez) {
  const letzte = S.N.inspNachObjekt.get(typ + ':' + bez)?.[0];
  const liste = letzte ? [...letzte.schaeden] : [];
  for (const s of S.N.schaeden.values()) if (s.manuell && s.typ === typ && s.objekt === bez) liste.push(s);
  return {letzte, liste};
}
function zustandSetzen(typ, o) {
  const {letzte, liste} = aktuelleSchaeden(typ, o.bez);
  const k = liste.filter(s => schadenStatus(s) !== 'saniert').map(schadenKlasse).filter(x => x != null);
  o.zk = k.length ? Math.min(...k) : letzte ? 5 : null; o.letzteInsp = letzte?.datum || null;
}
function zielObjekt(typ, bez) {
  const N = S.N; return typ === 'haltung' ? N.haltungen.get(bez) : typ === 'knoten' ? N.knoten.get(bez) : typ === 'anlage' ? N.anlagen.get(bez) : typ === 'objekt' ? N.objekte.get(bez) : null;
}
function zielName(typ, bez) {
  if (!typ || !bez) return '–';
  const o = zielObjekt(typ, bez);
  if (typ === 'anlage') return o ? `${o.typ} ${o.name || o.bez}` : bez;
  if (typ === 'objekt') { if (!o) return bez; const a = S.N.anlagen.get(o.anlage); return `${o.typ} ${o.bez} (${a?.name || o.anlage})`; }
  if (typ === 'knoten') return `${o?.art || 'Schacht'} ${bez}`;
  return `Haltung ${bez}`;
}
function haltungGeo(h) {
  if (h.geo && h.geo.length >= 2) return h.geo;
  const a = S.N.knoten.get(h.von), b = S.N.knoten.get(h.bis);
  return a?.lat != null && b?.lat != null ? [[a.lat, a.lon], [b.lat, b.lon]] : [];
}
function zielPosition(typ, bez) {
  const o = zielObjekt(typ, bez); if (!o) return null;
  if (typ === 'haltung') return punktAufLinie(haltungGeo(o), 0.5);
  if (typ === 'objekt') { const a = S.N.anlagen.get(o.anlage); return a?.lat != null ? [a.lat, a.lon] : null; }
  return o.lat != null ? [o.lat, o.lon] : null;
}
function schadenPosition(s) {
  if (s.lat != null) return [s.lat, s.lon];
  if (s.typ === 'haltung') {
    const h = S.N.haltungen.get(s.objekt); if (!h) return null;
    let a = h.laenge ? (s.station || 0) / h.laenge : 0.5; if (S.N.insp.get(s.insp)?.gegen) a = 1 - a;
    return punktAufLinie(haltungGeo(h), a);
  }
  return zielPosition(s.typ, s.objekt);
}
function stoerungPosition(s) { return s.lat != null ? [s.lat, s.lon] : zielPosition(s.ziel_typ, s.ziel); }

// ------------------------------------------------------------------ Datenbank
async function speichern(coll, id, daten) {
  if (!S.db) throw new Error('Keine Verbindung zur gemeinsamen Datenbank.');
  try { await S.db.collection(coll).doc(id).set(daten); }
  catch (e) {
    if (e?.code === 'invalid_argument') { S.darf = false; render(); throw new Error('Sie haben keine Schreibrechte für diese Seite.'); }
    if (e?.code === 'quota_exceeded') throw new Error('Der Speicher der Seite ist voll. Bitte alte Importe löschen.');
    throw new Error('Speichern fehlgeschlagen (' + (e?.code || e?.message || e) + '). Bitte erneut versuchen.');
  }
}
async function loeschen(coll, id) { try { await S.db.collection(coll).doc(id).delete(); } catch (e) { meldung('Löschen fehlgeschlagen: ' + (e?.code || e), 'fehler'); } }
let neuAufbauen = true, renderTimer = null;
function geaendert(struktur) { if (struktur) neuAufbauen = true; clearTimeout(renderTimer); renderTimer = setTimeout(() => { if (neuAufbauen && S.basis) { aufbauen(); neuAufbauen = false; karteAktualisieren(true); } else karteAktualisieren(false); render(); }, 60); }
async function verbinden() {
  const [db, user, assets, downloads] = await Promise.all(['db', 'user', 'assets', 'downloads'].map(n => window.claude?.use ? window.claude.use(n).catch(() => null) : Promise.resolve(null)));
  S.db = db; S.user = user; S.assets = assets; S.downloads = downloads;
  if (user) { S.darf = await user.can('data.write'); S.ich = await user.id(); }
  if (!db) { S.dbStatus = 'ohne'; render(); return; }
  S.dbStatus = 'ok';
  const struktur = new Set(['schaeden', 'schadenstatus', 'importe', 'importdaten']);
  for (const coll of Object.keys(S.dyn)) {
    db.collection(coll).onSnapshot(snap => {
      const m = new Map(); snap.docs.forEach(d => m.set(d.id, {...d.data(), _id: d.id})); S.dyn[coll] = m; S.geladen[coll] = true;
      geaendert(struktur.has(coll));
    }, e => { console.warn(coll, e); S.dbStatus = 'fehler'; render(); });
  }
}
async function namen(ids) {
  ids = [...new Set(ids.filter(Boolean))]; if (!S.user || !ids.length) return {};
  try { return await S.user.profiles(ids); } catch { return {}; }
}

// ------------------------------------------------------------------ Meldungen und Dialoge
function meldung(text, art = 'ok') {
  const el = document.createElement('div'); el.className = 'toast ' + art; el.textContent = text; $('#toasts').appendChild(el);
  setTimeout(() => el.remove(), art === 'fehler' ? 7000 : 3500);
}
function dialogOeffnen(titel, html, beiAbsenden, nachOeffnen) {
  const d = $('#dialog'); d.innerHTML = `<div class="dlg-karte" role="dialog" aria-modal="true" aria-labelledby="dlg-titel"><div class="dlg-kopf"><h2 id="dlg-titel">${esc(titel)}</h2><button class="knopf zweit klein" data-akt="dialog-zu" aria-label="Schließen">Schließen</button></div><form id="dlg-form" novalidate>${html}<div class="dlg-fehler" id="dlg-fehler" hidden></div><div class="aktionen"><button class="knopf" type="submit">Speichern</button><button class="knopf zweit" type="button" data-akt="dialog-zu">Abbrechen</button></div></form></div>`;
  d.hidden = false; document.body.classList.add('modal-offen');
  const f = $('#dlg-form');
  f.addEventListener('submit', async e => {
    e.preventDefault(); const fehler = $('#dlg-fehler'); fehler.hidden = true;
    const knopf = f.querySelector('[type=submit]'); knopf.disabled = true; knopf.textContent = 'Speichert …';
    try { await beiAbsenden(new FormData(f), f); dialogZu(); }
    catch (err) { fehler.textContent = err.message || String(err); fehler.hidden = false; knopf.disabled = false; knopf.textContent = 'Speichern'; }
  });
  nachOeffnen?.(f); setTimeout(() => f.querySelector('input:not([type=hidden]),select,textarea')?.focus(), 50);
}
function dialogZu() { $('#dialog').hidden = true; $('#dialog').innerHTML = ''; document.body.classList.remove('modal-offen'); if (S.pickerKarte) { S.pickerKarte.remove(); S.pickerKarte = null; } }
const feld = (name, label, inhalt, breit) => `<div class="feld${breit ? ' breit' : ''}"><label for="f-${name}">${esc(label)}</label>${inhalt}</div>`;
const eingabe = (name, label, wert, attr = '', breit) => feld(name, label, `<input id="f-${name}" name="${name}" value="${esc(wert ?? '')}" ${attr}>`, breit);
const textfeld = (name, label, wert) => feld(name, label, `<textarea id="f-${name}" name="${name}" rows="3">${esc(wert ?? '')}</textarea>`, true);
const auswahl = (name, label, optionen, wert, leer) => feld(name, label, `<select id="f-${name}" name="${name}">${leer ? '<option value="">–</option>' : ''}${optionen.map(o => { const [v, t] = Array.isArray(o) ? o : [o, o]; return `<option value="${esc(v)}" ${String(wert ?? '') === String(v) ? 'selected' : ''}>${esc(t)}</option>`; }).join('')}</select>`);
function zielFelder(typ, bez) {
  return `<div class="feld"><label for="f-ziel_typ">Betrifft</label><select id="f-ziel_typ" name="ziel_typ">${Object.entries(ZIELNAMEN).map(([v, t]) => `<option value="${v}" ${typ === v ? 'selected' : ''}>${t}</option>`).join('')}<option value="" ${!typ ? 'selected' : ''}>nur Ort (kein Objekt)</option></select></div>
  <div class="feld"><label for="f-ziel">Objekt (Bezeichnung)</label><input id="f-ziel" name="ziel" value="${esc(bez || '')}" list="dl-ziel" autocomplete="off" placeholder="z. B. OHZ-S0042 oder Anlage wählen"><datalist id="dl-ziel"></datalist></div>`;
}
function zielDatalist(f) {
  const typSel = f.querySelector('#f-ziel_typ'), dl = f.querySelector('#dl-ziel'); if (!typSel) return;
  const quellen = {
    anlage: [...S.N.anlagen.values()].map(a => [a.bez, `${a.name || a.bez} (${a.typ})`]),
    objekt: [...S.N.objekte.values()].map(o => [o.key, `${o.typ} ${o.bez} – ${S.N.anlagen.get(o.anlage)?.name || o.anlage}`]),
  };
  const fuellen = () => {
    const t = typSel.value; let opts = [];
    if (t === 'anlage' || t === 'objekt') opts = quellen[t];
    else if (t === 'haltung') opts = [...S.N.haltungen.keys()].map(k => [k, S.N.haltungen.get(k).strasse || '']);
    else if (t === 'knoten') opts = [...S.N.knoten.keys()].map(k => [k, S.N.knoten.get(k).strasse || '']);
    dl.innerHTML = opts.map(([v, l]) => `<option value="${esc(v)}">${esc(l)}</option>`).join('');
  };
  typSel.addEventListener('change', () => { f.querySelector('#f-ziel').value = ''; fuellen(); }); fuellen();
}
function zielPruefen(fd) {
  const typ = fd.get('ziel_typ') || null, bez = (fd.get('ziel') || '').trim() || null;
  if (typ && !bez) throw new Error('Bitte das betroffene Objekt angeben.');
  if (typ && !zielObjekt(typ, bez)) throw new Error(`${ZIELNAMEN[typ]} „${bez}“ gibt es nicht. Bitte aus der Vorschlagsliste wählen.`);
  return [typ, bez];
}
function darfSchreiben() { return S.db && S.darf !== false; }

// ------------------------------------------------------------------ Formulare
function stoerungFormular(id, vorgabe = {}) {
  const s = id ? S.dyn.stoerungen.get(id) : {status: 'offen', prioritaet: 'mittel', meldeweg: 'Kontrollgang', gemeldet_am: jetztIso(), ...vorgabe};
  dialogOeffnen(id ? 'Störmeldung bearbeiten' : 'Neue Störmeldung', `<div class="formular">
    ${eingabe('titel', 'Kurzbeschreibung *', s.titel, 'required maxlength="200"', true)}
    ${zielFelder(s.ziel_typ, s.ziel)}
    ${auswahl('prioritaet', 'Priorität', PRIOS, s.prioritaet)}${auswahl('status', 'Status', ['offen', 'in Bearbeitung', 'behoben'], s.status)}
    ${auswahl('meldeweg', 'Meldeweg', MELDEWEGE, s.meldeweg)}${eingabe('gemeldet_am', 'Gemeldet am', s.gemeldet_am, 'type="datetime-local"')}
    ${eingabe('gemeldet_von', 'Gemeldet von', s.gemeldet_von)}${eingabe('bearbeiter', 'Bearbeiter', s.bearbeiter)}
    ${textfeld('beschreibung', 'Beschreibung', s.beschreibung)}${textfeld('ursache', 'Ursache', s.ursache)}${textfeld('massnahme', 'Maßnahme', s.massnahme)}
    ${eingabe('behoben_am', 'Behoben am', s.behoben_am, 'type="datetime-local"')}${eingabe('ausfallzeit_h', 'Ausfallzeit [h]', s.ausfallzeit_h, 'inputmode="decimal"')}
    <div class="feld breit"><label>Ort auf der Karte (antippen, optional)</label><div id="picker" class="picker"></div>
      <div class="klein leise" id="picker-info">${s.lat != null ? `Gesetzt: ${zahl(s.lat, 5)}, ${zahl(s.lon, 5)}` : 'Kein eigener Ort – es gilt die Lage des Objekts.'}</div>
      <input type="hidden" name="lat" id="f-lat" value="${s.lat ?? ''}"><input type="hidden" name="lon" id="f-lon" value="${s.lon ?? ''}"></div>
    ${S.assets ? `<div class="feld breit"><label for="f-fotos">Fotos anhängen</label><input type="file" id="f-fotos" name="fotos" accept="image/*" capture="environment" multiple></div>` : ''}
  </div>`, async (fd) => {
    const [ziel_typ, ziel] = zielPruefen(fd);
    const titel = (fd.get('titel') || '').trim(); if (!titel) throw new Error('Bitte eine Kurzbeschreibung eingeben.');
    const daten = {...(id ? S.dyn.stoerungen.get(id) : {}), titel, ziel_typ, ziel,
      prioritaet: fd.get('prioritaet'), status: fd.get('status'), meldeweg: fd.get('meldeweg'), gemeldet_am: fd.get('gemeldet_am') || jetztIso(),
      gemeldet_von: fd.get('gemeldet_von') || null, bearbeiter: fd.get('bearbeiter') || null, beschreibung: fd.get('beschreibung') || null,
      ursache: fd.get('ursache') || null, massnahme: fd.get('massnahme') || null, behoben_am: fd.get('behoben_am') || null,
      ausfallzeit_h: num(fd.get('ausfallzeit_h')), lat: num(fd.get('lat')), lon: num(fd.get('lon'))};
    delete daten._id;
    if (!id) daten.erfasst_von = S.ich || null;
    if (daten.status === 'behoben' && !daten.behoben_am) daten.behoben_am = jetztIso();
    if (daten.status === 'behoben' && daten.ausfallzeit_h == null) daten.ausfallzeit_h = Math.round((new Date(daten.behoben_am) - new Date(daten.gemeldet_am)) / 36e5 * 10) / 10;
    daten.fotos = [...(daten.fotos || []), ...await fotosHochladen(fd.getAll('fotos'))];
    const neu = id || neueId('st'); await speichern('stoerungen', neu, daten);
    meldung('Störmeldung gespeichert.'); detailOeffnen('stoerung', neu);
  }, f => { zielDatalist(f); pickerAnlegen(s.lat != null ? [s.lat, s.lon] : stoerungPosition(s)); });
}
async function fotosHochladen(dateien) {
  const ids = [];
  for (const d of dateien) { if (!d || !d.size) continue; if (!S.assets) break;
    try { ids.push((await S.assets.upload(d)).id); } catch (e) { throw new Error(`Foto „${d.name}“ konnte nicht hochgeladen werden (${e?.code || e}).`); } }
  return ids;
}
function pickerAnlegen(pos) {
  if (!window.L) { $('#picker').innerHTML = '<p class="leise klein">Karte nicht verfügbar.</p>'; return; }
  const k = L.map('picker', {preferCanvas: true, attributionControl: false}); S.pickerKarte = k;
  const linien = []; for (const h of S.N.haltungen.values()) { const g = haltungGeo(h); if (g.length > 1) linien.push(g); }
  L.polyline(linien, {color: css('--leise'), weight: 2, opacity: .7, interactive: false}).addTo(k);
  let m = null; const setzen = ll => { if (m) m.remove(); m = L.circleMarker(ll, {radius: 9, color: css('--flaeche'), weight: 3, fillColor: css('--gefahr'), fillOpacity: 1}).addTo(k); };
  if (pos) { k.setView(pos, 17); if ($('#f-lat').value) setzen(pos); } else k.setView([53.2265, 8.795], 13);
  k.on('click', e => { setzen(e.latlng); $('#f-lat').value = e.latlng.lat.toFixed(6); $('#f-lon').value = e.latlng.lng.toFixed(6); $('#picker-info').textContent = `Gesetzt: ${zahl(e.latlng.lat, 5)}, ${zahl(e.latlng.lng, 5)}`; });
  setTimeout(() => k.invalidateSize(), 80);
}
function schadenFormular(typ, bez, id) {
  const s = id ? S.dyn.schaeden.get(id) : {typ, objekt: bez, datum: heute(), status: 'offen'};
  const kodes = Object.entries(KATALOG).filter(([, i]) => !i.info);
  dialogOeffnen(id ? 'Schaden bearbeiten' : `Schaden erfassen – ${zielName(typ || s.typ, bez || s.objekt)}`, `<div class="formular">
    ${eingabe('kode', 'Hauptkode (DWA-M 149-2) *', s.kode, 'required list="dl-kodes" autocomplete="off" style="text-transform:uppercase"')}<datalist id="dl-kodes">${kodes.map(([k, i]) => `<option value="${k}">${esc(i.text)}</option>`).join('')}</datalist>
    <div class="feld"><span class="klein leise" id="kode-text"></span></div>
    ${eingabe('c1', 'Charakterisierung 1', s.c1, 'list="dl-c1" autocomplete="off"')}<datalist id="dl-c1"></datalist>
    ${eingabe('c2', 'Charakterisierung 2', s.c2, 'list="dl-c2" autocomplete="off"')}<datalist id="dl-c2"></datalist>
    ${eingabe('q1', 'Quantifizierung', s.q1)}${eingabe('station', 'Station [m]', s.station, 'inputmode="decimal"')}
    ${eingabe('stationBis', 'Station bis [m] (Streckenschaden)', s.stationBis, 'inputmode="decimal"')}${eingabe('uhr', 'Lage [Uhr]', s.uhr, 'inputmode="numeric"')}
    ${auswahl('kd', 'Klasse Dichtheit (D)', [0, 1, 2, 3, 4, 5], s.kd, true)}${auswahl('ks', 'Klasse Standsicherheit (S)', [0, 1, 2, 3, 4, 5], s.ks, true)}
    ${auswahl('kb', 'Klasse Betriebssicherheit (B)', [0, 1, 2, 3, 4, 5], s.kb, true)}${eingabe('datum', 'Festgestellt am', s.datum, 'type="date"')}
    ${auswahl('status', 'Status', ['offen', 'Sanierung geplant', 'saniert'], s.status)}${textfeld('bemerkung', 'Bemerkung', s.bemerkung)}
    <p class="klein leise breit">Ohne Klassen trägt die Seite einen vereinfachten Vorschlag nach DWA-M 149-3 ein. Er ersetzt keine fachliche Bewertung.</p>
  </div>`, async fd => {
    const kode = (fd.get('kode') || '').trim().toUpperCase(); if (!/^[A-Z]{3}$/.test(kode)) throw new Error('Bitte einen dreistelligen Hauptkode eingeben, z. B. BAB.');
    const d = {typ: typ || s.typ, objekt: bez || s.objekt, kode, c1: (fd.get('c1') || '').toUpperCase() || null, c2: (fd.get('c2') || '').toUpperCase() || null,
      q1: fd.get('q1') || null, station: num(fd.get('station')), stationBis: num(fd.get('stationBis')), uhr: num(fd.get('uhr')),
      kd: num(fd.get('kd')), ks: num(fd.get('ks')), kb: num(fd.get('kb')), datum: fd.get('datum') || heute(), status: fd.get('status'), bemerkung: fd.get('bemerkung') || null,
      erfasst_von: s.erfasst_von || S.ich || null};
    if (d.kd == null && d.ks == null && d.kb == null) { [d.kd, d.ks, d.kb] = klassenVorschlag(d.kode, d.c1, d.c2, d.q1); meldung('Klassen vorgeschlagen – bitte prüfen.', 'info'); }
    const neu = id || neueId('sm'); await speichern('schaeden', neu, d); meldung('Schaden gespeichert.');
  }, f => {
    const k = f.querySelector('#f-kode');
    const upd = () => { const i = KATALOG[basisKode(k.value)]; $('#kode-text').textContent = i ? i.text + (i.quant1 ? ' · Quantifizierung: ' + i.quant1 : '') : (k.value ? 'nicht im Katalog' : '');
      for (const n of ['char1', 'char2']) $('#dl-' + n.replace('char', 'c')).innerHTML = Object.entries(i?.[n] || {}).map(([v, t]) => `<option value="${v}">${esc(t)}</option>`).join(''); };
    k.addEventListener('input', upd); upd();
  });
}
function planFormular(typ, bez, id) {
  const p = id ? S.dyn.wartungsplaene.get(id) : {ziel_typ: typ, ziel: bez, art: 'Wartung', intervall: 12, aktiv: true};
  dialogOeffnen((id ? 'Wartungsplan bearbeiten – ' : 'Neuer Wartungsplan – ') + zielName(p.ziel_typ, p.ziel), `<div class="formular">
    ${eingabe('bezeichnung', 'Tätigkeit *', p.bezeichnung, 'required', true)}${auswahl('art', 'Art', WARTUNGSARTEN, p.art)}
    ${eingabe('intervall', 'Intervall [Monate] *', p.intervall, 'required inputmode="numeric"')}${eingabe('letzte', 'Zuletzt durchgeführt', p.letzte, 'type="date"')}
    ${eingabe('naechste', 'Nächste Fälligkeit', p.naechste, 'type="date"')}${eingabe('zustaendig', 'Zuständig', p.zustaendig)}
    ${auswahl('aktiv', 'Aktiv', [['1', 'ja'], ['0', 'nein']], p.aktiv === false ? '0' : '1')}${textfeld('beschreibung', 'Tätigkeiten / Checkliste', p.beschreibung)}
  </div>`, async fd => {
    const bezeichnung = (fd.get('bezeichnung') || '').trim(), intervall = Math.round(num(fd.get('intervall')) || 0);
    if (!bezeichnung) throw new Error('Bitte die Tätigkeit angeben.'); if (intervall < 1) throw new Error('Das Intervall muss mindestens 1 Monat sein.');
    const d = {ziel_typ: p.ziel_typ, ziel: p.ziel, bezeichnung, art: fd.get('art'), intervall, letzte: fd.get('letzte') || null,
      naechste: fd.get('naechste') || null, zustaendig: fd.get('zustaendig') || null, aktiv: fd.get('aktiv') === '1', beschreibung: fd.get('beschreibung') || null};
    if (!d.naechste && d.letzte) d.naechste = monateAddieren(d.letzte, intervall);
    await speichern('wartungsplaene', id || neueId('p'), d); meldung('Wartungsplan gespeichert.');
  });
}
function massnahmeFormular(typ, bez, planId, id) {
  const plan = planId ? S.dyn.wartungsplaene.get(planId) : null;
  const m = id ? S.dyn.massnahmen.get(id) : {ziel_typ: typ, ziel: bez, plan: planId || null, art: plan?.art || 'Wartung', datum: heute(), ergebnis: 'in Ordnung', beschreibung: plan?.beschreibung};
  dialogOeffnen((plan ? plan.bezeichnung + ' – ' : 'Maßnahme – ') + zielName(m.ziel_typ, m.ziel), `<div class="formular">
    ${auswahl('art', 'Art', WARTUNGSARTEN, m.art)}${eingabe('datum', 'Datum *', m.datum, 'type="date" required')}
    ${eingabe('durch', 'Durchgeführt von', m.durch)}${auswahl('ergebnis', 'Ergebnis', ERGEBNISSE, m.ergebnis)}
    ${eingabe('dauer', 'Dauer [h]', m.dauer, 'inputmode="decimal"')}${textfeld('beschreibung', 'Tätigkeit', m.beschreibung)}${textfeld('befund', 'Befund / Mängel', m.befund)}
  </div>`, async fd => {
    const d = {ziel_typ: m.ziel_typ, ziel: m.ziel, plan: m.plan, art: fd.get('art'), datum: fd.get('datum'), durch: fd.get('durch') || null,
      ergebnis: fd.get('ergebnis'), dauer: num(fd.get('dauer')), beschreibung: fd.get('beschreibung') || null, befund: fd.get('befund') || null, erfasst_von: m.erfasst_von || S.ich || null};
    if (!d.datum) throw new Error('Bitte das Datum angeben.');
    await speichern('massnahmen', id || neueId('m'), d);
    const p = d.plan ? S.dyn.wartungsplaene.get(d.plan) : null;
    if (p && (!p.letzte || d.datum >= p.letzte)) {
      const neu = {...p, letzte: d.datum, naechste: monateAddieren(d.datum, p.intervall)}; delete neu._id;
      await speichern('wartungsplaene', d.plan, neu); meldung(`Erledigt. Nächste Fälligkeit: ${datum(neu.naechste)}`);
    } else meldung('Maßnahme dokumentiert.');
  });
}
async function stoerungStatus(id, status) {
  const s = {...S.dyn.stoerungen.get(id)}; delete s._id; s.status = status;
  if (status === 'in Bearbeitung' && !s.bearbeiter) { const me = S.user ? await S.user.me() : null; s.bearbeiter = me?.name || 'Kanalbetrieb'; }
  if (status === 'behoben') { s.behoben_am = s.behoben_am || jetztIso(); if (s.ausfallzeit_h == null) s.ausfallzeit_h = Math.round((new Date(s.behoben_am) - new Date(s.gemeldet_am)) / 36e5 * 10) / 10; }
  try { await speichern('stoerungen', id, s); meldung('Status: ' + status); } catch (e) { meldung(e.message, 'fehler'); }
}
async function schadenStatusSetzen(sid, status) {
  try {
    if (sid.startsWith('m:')) { const d = {...S.dyn.schaeden.get(sid.slice(2)), status}; delete d._id; await speichern('schaeden', sid.slice(2), d); }
    else await speichern('schadenstatus', sid.replace(/:/g, '~'), {status, datum: heute()});
    meldung('Schaden: ' + status);
  } catch (e) { meldung(e.message, 'fehler'); }
}

// ------------------------------------------------------------------ Import (ISYBAU / DWA-M 150 / CSV)
const lok = el => el.localName;
const kind = (el, ...n) => el ? [...el.children].find(c => n.includes(lok(c))) || null : null;
const kinder = (el, ...n) => el ? [...el.children].filter(c => n.includes(lok(c))) : [];
const alle = (el, ...n) => el ? [...el.getElementsByTagName('*')].filter(c => n.includes(lok(c))) : [];
function pfad(el, weg) { for (const t of weg.split('/')) { el = kind(el, ...t.split('|')); if (!el) return null; } return el; }
const txt = (el, weg) => { const e = weg ? pfad(el, weg) : el; const t = e?.textContent?.trim(); return t || null; };
const ART = {KS: 'SW', KR: 'RW', KM: 'MW', S: 'SW', R: 'RW', M: 'MW', SW: 'SW', RW: 'RW', MW: 'MW'};
function isybauLesen(xmlText) {
  const doc = new DOMParser().parseFromString(xmlText, 'application/xml');
  if (doc.getElementsByTagName('parsererror').length) throw new Error('Die Datei ist kein gültiges XML.');
  const root = doc.documentElement, knoten = [], haltungen = [], inspektionen = [], hinweise = [];
  for (const anl of alle(root, 'AbwassertechnischeAnlage')) {
    const bez = txt(anl, 'Objektbezeichnung'); if (!bez) continue;
    const ke = kind(anl, 'Kante'), kn = kind(anl, 'Knoten'), oa = txt(anl, 'Objektart');
    const istKante = oa === '1' || (oa == null && ke);
    const basis = {bez, kanalart: ART[(txt(anl, 'Entwaesserungsart') || txt(anl, 'Kanalart') || '').toUpperCase()] || null,
      strasse: txt(anl, 'Lage/Strassenname'), ortsteil: txt(anl, 'Lage/Ortsteilname'), baujahr: num(txt(anl, 'Baujahr'))};
    const geoEl = pfad(anl, 'Geometrie/Geometriedaten') || kind(anl, 'Geometrie');
    const punkte = alle(geoEl, 'Punkt', 'Start', 'Ende').map(p => ({rw: num(txt(p, 'Rechtswert')), hw: num(txt(p, 'Hochwert')), h: num(txt(p, 'Punkthoehe')), a: (txt(p, 'PunktattributAbwasser') || '').toUpperCase()})).filter(p => p.rw != null && p.hw != null);
    for (const k of Object.keys(basis)) if (basis[k] == null) delete basis[k];
    if (istKante) {
      const profil = kind(ke, 'Profil'), geo = [];
      for (const p of punkte) { const ll = nachWgs84(p.rw, p.hw); if (ll) { const q = [+ll[0].toFixed(7), +ll[1].toFixed(7)]; const l = geo[geo.length - 1]; if (!l || l[0] !== q[0] || l[1] !== q[1]) geo.push(q); } }
      const h = {...basis, von: txt(ke, 'KnotenZulauf'), bis: txt(ke, 'KnotenAblauf'), sz: num(txt(ke, 'SohlhoeheZulauf')), sa: num(txt(ke, 'SohlhoeheAblauf')),
        laenge: num(txt(ke, 'Laenge')) ?? num(txt(ke, 'Haltung/DMPLaenge')), material: txt(ke, 'Material'),
        dn: num(txt(profil, 'Profilhoehe')) ?? num(txt(profil, 'Profilbreite')), funktion: /druck/i.test((txt(anl, 'Kommentar') || '') + (txt(ke, 'Funktion') || '')) ? 'Druckleitung' : 'Freispiegel', geo};
      for (const k of Object.keys(h)) if (h[k] == null) delete h[k];
      haltungen.push(h);
    } else {
      const typ = txt(kn, 'KnotenTyp'), bw = txt(kn, 'Bauwerk/Bauwerkstyp') || '';
      const dmp = punkte.find(p => p.a === 'DMP'), smp = punkte.find(p => ['SMP', 'SBW', 'GOK'].includes(p.a)), lage = dmp || smp || punkte[0];
      const ll = lage ? nachWgs84(lage.rw, lage.hw) : null;
      const k = {...basis, art: /auslauf/i.test(bw) ? 'Auslaufbauwerk' : ({0: 'Schacht', 1: 'Anschlusspunkt', 2: 'Bauwerk'})[typ] || 'Schacht',
        lat: ll ? +ll[0].toFixed(7) : null, lon: ll ? +ll[1].toFixed(7) : null, deckel: dmp?.h ?? null, sohle: smp?.h ?? num(txt(kn, 'Schacht/Sohlhoehe')), material: txt(kn, 'Schacht/Material') || txt(kn, 'Material')};
      if (!ll) hinweise.push(`Schacht ${bez}: keine Koordinaten`);
      for (const x of Object.keys(k)) if (k[x] == null) delete k[x];
      knoten.push(k);
    }
  }
  for (const anl of alle(root, 'InspizierteAbwassertechnischeAnlage')) {
    const bez = txt(anl, 'Objektbezeichnung'); if (!bez) continue;
    for (const insp of kinder(anl, 'OptischeInspektion')) {
      const rohr = kind(insp, 'Rohrleitung'), kn = kind(insp, 'Knoten'), istK = txt(anl, 'Anlagentyp') === '2' || (!rohr && kn);
      const cont = istK ? kn : rohr, schaeden = [], offen = {};
      for (const z of alle(cont, 'RZustand', 'KZustand', 'Zustand')) {
        const kode = (txt(z, 'InspektionsKode') || txt(z, 'Hauptkode') || '').toUpperCase(); if (!kode) continue;
        const station = num(txt(z, istK ? 'VertikaleLage|Vertikale_Lage|Station' : 'Station')), strecke = (txt(z, 'Streckenschaden') || '').toUpperCase();
        if (strecke.startsWith('B') && offen[strecke.slice(1)]) { offen[strecke.slice(1)].stationBis = station; delete offen[strecke.slice(1)]; continue; }
        if (istInfo(kode)) continue;
        const c1 = txt(z, 'Charakterisierung1'), c2 = txt(z, 'Charakterisierung2'), q1 = txt(z, 'Quantifizierung1Numerisch|Quantifizierung1|Quantifizierung1Text');
        const kl = kind(z, 'Klassifizierung', 'Zustandsklassifizierung');
        let [kd, ks, kb] = kl ? [num(txt(kl, 'Dichtheit|KlasseDichtheit|KlasseD')), num(txt(kl, 'Standsicherheit|KlasseStandsicherheit|KlasseS')), num(txt(kl, 'Betriebssicherheit|KlasseBetriebssicherheit|KlasseB'))] : [null, null, null];
        if (kd == null && ks == null && kb == null) [kd, ks, kb] = klassenVorschlag(kode, c1, c2, q1);
        const s = {kode, c1, c2, q1, station, stationBis: null, uhr: num(txt(z, 'PositionVon')), verbindung: /^(ja|j|1|true)$/i.test(txt(z, 'Verbindung') || ''), kd, ks, kb, foto: txt(z, 'Fotobezeichnung|Fotodatei')};
        if (strecke.startsWith('A')) offen[strecke.slice(1)] = s;
        schaeden.push(s);
      }
      inspektionen.push({typ: istK ? 'knoten' : 'haltung', objekt: bez, datum: (txt(insp, 'Inspektionsdatum') || heute()).slice(0, 10).replace(/^(\d\d)\.(\d\d)\.(\d{4})$/, '$3-$2-$1'),
        untersucher: txt(insp, 'NameUntersucher|Untersucher'), firma: txt(insp, 'Auftragnehmer|Firma|Inspektionsfirma'),
        gegen: rohr ? ['U', 'G'].includes((txt(rohr, 'Inspektionsrichtung') || 'O').toUpperCase()) : false, laenge: rohr ? num(txt(rohr, 'Inspektionslaenge')) : null, schaeden});
    }
  }
  const version = txt(root, 'Version');
  return {knoten, haltungen, inspektionen, anlagen: [], hinweise, format: (/150|dwa/i.test(root.tagName) ? 'DWA-M 150' : 'ISYBAU') + (version ? ` (${version})` : '')};
}
function csvLesen(text) {
  const zeile1 = text.split(/\r?\n/, 1)[0], tr = (zeile1.match(/;/g) || []).length >= (zeile1.match(/,/g) || []).length ? ';' : ',';
  const zeilen = []; let feld = '', reihe = [], q = false;
  for (let i = 0; i < text.length; i++) { const c = text[i];
    if (q) { if (c === '"') { if (text[i + 1] === '"') { feld += '"'; i++; } else q = false; } else feld += c; }
    else if (c === '"') q = true; else if (c === tr) { reihe.push(feld); feld = ''; }
    else if (c === '\n' || c === '\r') { if (c === '\r' && text[i + 1] === '\n') i++; reihe.push(feld); zeilen.push(reihe); reihe = []; feld = ''; } else feld += c; }
  if (feld || reihe.length) { reihe.push(feld); zeilen.push(reihe); }
  const kopf = (zeilen.shift() || []).map(h => h.trim().toLowerCase().replace(/^\ufeff/, ''));
  const daten = zeilen.filter(z => z.some(v => v.trim())).map(z => Object.fromEntries(kopf.map((h, i) => [h, (z[i] || '').trim() || null])));
  const ks = new Set(kopf), erg = {knoten: [], haltungen: [], inspektionen: [], anlagen: [], hinweise: []};
  const ll = z => { let lat = num(z.lat), lon = num(z.lon); if (lat == null && z.rechtswert) { const p = nachWgs84(num(z.rechtswert), num(z.hochwert)); if (p) [lat, lon] = p; } return [lat, lon]; };
  if (ks.has('von') && ks.has('bis')) { erg.format = 'Tabelle (Haltungen)'; erg.haltungen = daten.map(z => ({bez: z.bezeichnung, von: z.von, bis: z.bis, kanalart: z.kanalart, funktion: z.funktion || 'Freispiegel', ortsteil: z.ortsteil, strasse: z.strasse, laenge: num(z.laenge), dn: num(z.dn), material: z.material, baujahr: num(z.baujahr), sz: num(z.sohle_zulauf), sa: num(z.sohle_ablauf), geo: []})); }
  else if (ks.has('kode') && ks.has('objekt')) {
    erg.format = 'Tabelle (Schäden)'; const g = new Map();
    for (const z of daten) { const typ = /^(k|s)/i.test(z.objektart || '') ? 'knoten' : 'haltung', dat = (z.datum || heute()).replace(/^(\d\d)\.(\d\d)\.(\d{4})$/, '$3-$2-$1'), key = typ + z.objekt + dat;
      if (!g.has(key)) g.set(key, {typ, objekt: z.objekt, datum: dat, untersucher: z.untersucher, firma: z.firma, gegen: /gegen/i.test(z.richtung || ''), schaeden: []});
      const kode = z.kode.toUpperCase(); let kd = num(z.klasse_d), ksx = num(z.klasse_s), kb = num(z.klasse_b);
      if (kd == null && ksx == null && kb == null) [kd, ksx, kb] = klassenVorschlag(kode, z.char1, z.char2, z.quant1);
      g.get(key).schaeden.push({kode, c1: z.char1, c2: z.char2, q1: z.quant1, station: num(z.station), stationBis: num(z.station_bis), uhr: num(z.uhr_von), kd, ks: ksx, kb, bemerkung: z.bemerkung}); }
    erg.inspektionen = [...g.values()];
  } else if (ks.has('anlagentyp')) { erg.format = 'Tabelle (Anlagen)'; erg.anlagen = daten.map(z => { const [lat, lon] = ll(z); return {bez: z.bezeichnung, name: z.name, typ: z.anlagentyp, kanalart: z.kanalart, ortsteil: z.ortsteil, adresse: z.adresse, lat, lon, baujahr: num(z.baujahr), volumen: num(z.volumen_m3), vorfluter: z.vorfluter, bemerkung: z.bemerkung}; }); }
  else if (ks.has('bezeichnung')) { erg.format = 'Tabelle (Schächte)'; erg.knoten = daten.map(z => { const [lat, lon] = ll(z); return {bez: z.bezeichnung, art: z.knotenart || 'Schacht', kanalart: z.kanalart, ortsteil: z.ortsteil, strasse: z.strasse, lat, lon, deckel: num(z.deckelhoehe), sohle: num(z.sohlhoehe), material: z.material, baujahr: num(z.baujahr)}; }); }
  else throw new Error('Spalten nicht erkannt. Erwartet z. B. „bezeichnung“, „von/bis“, „objekt/kode“ oder „anlagentyp“.');
  for (const l of ['knoten', 'haltungen', 'anlagen']) erg[l] = erg[l].filter(x => x.bez).map(x => Object.fromEntries(Object.entries(x).filter(([, v]) => v != null)));
  return erg;
}
async function importieren(dateien) {
  const ergebnisse = [];
  for (const datei of dateien) {
    const text = await datei.text(), name = datei.name;
    let d; try { d = /\.xml$/i.test(name) ? isybauLesen(text) : /\.csv$/i.test(name) ? csvLesen(text) : (() => { throw new Error('Nur .xml oder .csv möglich (Excel bitte als CSV speichern).'); })(); }
    catch (e) { ergebnisse.push(`${name}: ${e.message}`); continue; }
    // Objekte von Inspektionen müssen bekannt sein (im Bestand oder in derselben Datei)
    const bekannt = new Set([...S.N.haltungen.keys(), ...S.N.knoten.keys(), ...d.haltungen.map(h => h.bez), ...d.knoten.map(k => k.bez)]);
    const ohne = d.inspektionen.filter(i => !bekannt.has(i.objekt)); d.inspektionen = d.inspektionen.filter(i => bekannt.has(i.objekt));
    ohne.forEach(i => d.hinweise.push(`Inspektion: ${i.objekt} unbekannt – übersprungen`));
    const id = neueId('imp'), teile = []; let teil = {knoten: [], haltungen: [], inspektionen: [], anlagen: []}, groesse = 0;
    for (const l of ['knoten', 'haltungen', 'anlagen', 'inspektionen']) for (const x of d[l]) { const g = JSON.stringify(x).length; if (groesse + g > 180000) { teile.push(teil); teil = {knoten: [], haltungen: [], inspektionen: [], anlagen: []}; groesse = 0; } teil[l].push(x); groesse += g; }
    teile.push(teil);
    const anzahl = {knoten: d.knoten.length, haltungen: d.haltungen.length, inspektionen: d.inspektionen.length, schaeden: d.inspektionen.reduce((n, i) => n + i.schaeden.length, 0), anlagen: d.anlagen.length};
    try {
      for (const [n, t] of teile.entries()) await speichern('importdaten', `${id}_${n}`, {import_id: id, teil: n, ...t});
      await speichern('importe', id, {datei: name, format: d.format, zeitpunkt: new Date().toISOString(), von: S.ich || null, teile: teile.length, anzahl, hinweise: d.hinweise.slice(0, 100)});
      ergebnisse.push(`${name}: ${anzahl.knoten} Schächte, ${anzahl.haltungen} Haltungen, ${anzahl.inspektionen} Inspektionen, ${anzahl.schaeden} Schäden, ${anzahl.anlagen} Anlagen übernommen.`);
    } catch (e) { ergebnisse.push(`${name}: ${e.message}`); }
  }
  return ergebnisse;
}

// ------------------------------------------------------------------ Export
async function csvExport(name, kopf, zeilen) {
  const text = '\ufeff' + [kopf, ...zeilen].map(z => z.map(v => { v = v == null ? '' : typeof v === 'number' ? String(v).replace('.', ',') : String(v); return /[;"\n]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v; }).join(';')).join('\r\n');
  if (!S.downloads) { meldung('Download ist in dieser Ansicht nicht verfügbar.', 'fehler'); return; }
  try { await S.downloads.save({filename: name, data: text}); } catch (e) { if (e?.code !== 'declined') meldung('Export nicht möglich: ' + (e?.code || e), 'fehler'); }
}

// ------------------------------------------------------------------ Ansichten
const TABS = [['uebersicht', 'Übersicht'], ['karte', 'Karte'], ['kanalnetz', 'Kanalnetz'], ['anlagen', 'Anlagen'], ['wartung', 'Wartung'], ['schaeden', 'Schäden'], ['stoerungen', 'Störungen'], ['import', 'Import']];
function navRender() {
  const offen = [...S.dyn.stoerungen.values()].filter(s => s.status !== 'behoben').length;
  $('#nav').innerHTML = TABS.map(([k, t]) => `<a href="#${k}" class="${S.ansicht === k ? 'aktiv' : ''}" ${S.ansicht === k ? 'aria-current="page"' : ''}>${t}${k === 'stoerungen' && offen ? `<span class="zaehler">${offen}</span>` : ''}</a>`).join('');
  const st = {verbinde: ['Verbinde …', ''], ok: [darfSchreiben() ? 'Gemeinsame Daten · bearbeiten' : 'Gemeinsame Daten · nur lesen', 'ok'], ohne: ['Nur Ansicht – gemeinsame Daten in dieser Ansicht nicht verfügbar', 'warn'], fehler: ['Verbindung gestört', 'warn']}[S.dbStatus];
  $('#dbstatus').textContent = st[0]; $('#dbstatus').className = 'dbstatus ' + st[1];
}
function render() {
  navRender();
  const app = $('#app'), karte = $('#kartenansicht');
  if (!S.N) { app.innerHTML = '<div class="laden">Kanalnetz wird geladen …</div>'; return; }
  karte.hidden = S.ansicht !== 'karte'; app.hidden = S.ansicht === 'karte';
  if (S.ansicht === 'karte') { karteZeigen(); }
  else { const y = window.scrollY; app.innerHTML = (ANSICHTEN[S.ansicht] || ANSICHTEN.uebersicht)(); if (S.zuletzt === S.ansicht) window.scrollTo(0, y); S.zuletzt = S.ansicht; nachRender(); }
  if (S.detail) detailRender();
}
function nachRender() {
  document.querySelectorAll('[data-filter]').forEach(el => el.addEventListener(el.tagName === 'INPUT' ? 'input' : 'change', () => {
    S.filter[el.dataset.filter] = el.value; S.seiten = 1; clearTimeout(S.ft); S.ft = setTimeout(() => { const pos = el.selectionStart; render(); const neu = document.querySelector(`[data-filter="${el.dataset.filter}"]`); if (neu && el.tagName === 'INPUT') { neu.focus(); try { neu.setSelectionRange(pos, pos); } catch {} } }, el.tagName === 'INPUT' ? 250 : 0);
  }));
  namenAufloesen();
}
async function namenAufloesen() {
  const els = [...document.querySelectorAll('[data-person]')]; if (!els.length) return;
  const p = await namen(els.map(e => e.dataset.person)); els.forEach(e => { e.textContent = p[e.dataset.person]?.name || e.dataset.fallback || 'Teammitglied'; });
}
const f = k => S.filter[k] || '';
const sel = (k, opts, alleText) => `<select data-filter="${k}" aria-label="${esc(alleText)}"><option value="">${esc(alleText)}</option>${opts.map(o => { const [v, t] = Array.isArray(o) ? o : [o, o]; return `<option value="${esc(v)}" ${f(k) === String(v) ? 'selected' : ''}>${esc(t)}</option>`; }).join('')}</select>`;
const ortsteile = () => [...new Set([...S.N.haltungen.values()].map(h => h.ortsteil).filter(Boolean))].sort();
const kopf = (titel, unter, aktionen = '') => `<div class="seitenkopf"><div><h1>${titel}</h1>${unter ? `<p class="leise">${unter}</p>` : ''}</div><div class="aktionen">${aktionen}</div></div>`;
const neuKnopf = (text, akt, extra = '') => darfSchreiben() ? `<button class="knopf" data-akt="${akt}" ${extra}>${text}</button>` : '';
const mehr = (n, gezeigt) => n > gezeigt ? `<div class="mehr"><span class="leise">${gezeigt} von ${n} angezeigt</span><button class="knopf zweit klein" data-akt="mehr">Weitere ${Math.min(S.seitenGroesse, n - gezeigt)} anzeigen</button></div>` : `<p class="leise klein">${n} Einträge</p>`;
const limit = () => S.seitenGroesse * (S.seiten || 1);
const faellig = p => { if (!p.naechste) return '<span class="leise">ohne Termin</span>'; const t = tageBis(p.naechste); return t < 0 ? `<span class="ueber">${datum(p.naechste)} · ${-t} Tage überfällig</span>` : t <= 30 ? `<span class="bald">${datum(p.naechste)} · in ${t} Tagen</span>` : datum(p.naechste); };
const zielLink = (typ, bez) => typ && bez ? `<a href="#" data-detail="${typ}" data-id="${esc(bez)}">${esc(zielName(typ, bez))}</a>` : '<span class="leise">ohne Objekt</span>';
const alleMassnahmen = () => [...(S.basis?.massnahmen_alt || []).map((m, i) => ({...m, _id: 'alt' + i, alt: true})), ...S.dyn.massnahmen.values()];
const prioRang = p => PRIOS.indexOf(p) < 0 ? 9 : PRIOS.indexOf(p);

const ANSICHTEN = {
  uebersicht() {
    const N = S.N, hs = [...N.haltungen.values()], km = hs.reduce((s, h) => s + (h.laenge || 0), 0) / 1000;
    const offen = [...S.dyn.stoerungen.values()].filter(s => s.status !== 'behoben').sort((a, b) => prioRang(a.prioritaet) - prioRang(b.prioritaet) || (a.gemeldet_am || '').localeCompare(b.gemeldet_am || ''));
    const plaene = [...S.dyn.wartungsplaene.values()].filter(p => p.aktiv !== false && p.naechste && tageBis(p.naechste) <= 30).sort((a, b) => a.naechste.localeCompare(b.naechste));
    const zk = {}; hs.forEach(h => { const k = h.zk ?? 'x'; zk[k] = (zk[k] || 0) + 1; }); const max = Math.max(...Object.values(zk), 1);
    const schaedenOffen = [...N.schaeden.values()].filter(s => schadenStatus(s) !== 'saniert').length;
    const laengen = {}; hs.forEach(h => { laengen[h.kanalart] = (laengen[h.kanalart] || 0) + (h.laenge || 0); });
    const ueberfaellig = plaene.filter(p => tageBis(p.naechste) < 0).length;
    return `${kopf('Übersicht', `Fiktives Beispielnetz Osterholz-Scharmbeck · Schmutzwasser zur Kläranlage Lintel, Regenwasser dezentral in die Gewässer`, neuKnopf('Störung melden', 'neu-stoerung') + '<a class="knopf zweit" href="#karte">Karte öffnen</a>')}
    ${S.dbStatus === 'ohne' ? '<div class="hinweis">Diese Ansicht kann die gemeinsamen Daten nicht laden (zum Beispiel ohne Anmeldung). Netz, Schäden und Anlagen sind sichtbar, Störmeldungen und Wartung nicht.</div>' : ''}
    <div class="kennzahlen">
      <div class="kennzahl"><b>${zahl(km, 1)} km</b><span>Kanalnetz · ${hs.length} Haltungen</span></div>
      <div class="kennzahl"><b>${N.knoten.size}</b><span>Schächte und Bauwerke</span></div>
      <div class="kennzahl"><b>${N.anlagen.size}</b><span>Anlagen · ${N.objekte.size} Objekte</span></div>
      <div class="kennzahl ${offen.length ? 'warn' : ''}"><b>${offen.length}</b><span>offene Störungen</span></div>
      <div class="kennzahl ${ueberfaellig ? 'warn' : ''}"><b>${ueberfaellig}</b><span>Wartungen überfällig</span></div>
      <div class="kennzahl"><b>${schaedenOffen}</b><span>offene Schäden</span></div>
    </div>
    <div class="raster">
      <section class="tafel"><div class="tafel-kopf"><h2>Offene Störmeldungen</h2><a href="#stoerungen">alle</a></div>
        ${offen.length ? `<ul class="liste">${offen.slice(0, 8).map(s => `<li><a href="#" data-detail="stoerung" data-id="${s._id}"><span class="zeile1">${prioChip(s.prioritaet)} <strong>${esc(s.titel)}</strong></span><span class="zeile2">${esc(zielName(s.ziel_typ, s.ziel))} · ${datumZeit(s.gemeldet_am)} · ${esc(s.status)}</span></a></li>`).join('')}</ul>` : `<p class="leise">${S.geladen.stoerungen ? 'Keine offenen Störungen.' : 'Wird geladen …'}</p>`}
      </section>
      <section class="tafel"><div class="tafel-kopf"><h2>Fällige Wartungen (30 Tage)</h2><a href="#wartung">alle</a></div>
        ${plaene.length ? `<ul class="liste">${plaene.slice(0, 8).map(p => `<li><a href="#" data-detail="${p.ziel_typ}" data-id="${esc(p.ziel)}"><span class="zeile1"><strong>${esc(p.bezeichnung)}</strong></span><span class="zeile2">${esc(zielName(p.ziel_typ, p.ziel))} · ${faellig(p)}</span></a></li>`).join('')}</ul>` : `<p class="leise">${S.geladen.wartungsplaene ? 'Nichts fällig.' : 'Wird geladen …'}</p>`}
      </section>
      <section class="tafel"><h2>Zustand der Haltungen</h2><p class="leise klein">Zustandsklassen nach DWA-M 149-3</p>
        <div class="balken">${[0, 1, 2, 3, 4, 5, 'x'].map(k => `<span>${k === 'x' ? zkChip(null) + ' nicht inspiziert' : zkChip(k) + ' ' + ZK[k][0]}</span><div class="spur"><div style="width:${((zk[k] || 0) / max * 100).toFixed(1)}%;background:${k === 'x' ? 'var(--leise)' : ZK[k][2]}"></div></div><span class="zahl">${zk[k] || 0}</span>`).join('')}</div>
        <p class="klein leise">${Object.entries(laengen).map(([a, l]) => `${artChip(a)} ${zahl(l / 1000, 1)} km`).join(' &nbsp; ')}</p>
      </section>
    </div>`;
  },
  kanalnetz() {
    const typ = f('netztyp') || 'haltung', q = f('q').toLowerCase();
    let liste = typ === 'haltung' ? [...S.N.haltungen.values()] : [...S.N.knoten.values()];
    liste = liste.filter(o => (!q || o.bez.toLowerCase().includes(q) || (o.strasse || '').toLowerCase().includes(q)) && (!f('ortsteil') || o.ortsteil === f('ortsteil')) && (!f('kanalart') || o.kanalart === f('kanalart')) && (!f('zk') || (f('zk') === 'x' ? o.zk == null : String(o.zk) === f('zk'))));
    liste.sort((a, b) => (a.ortsteil || '').localeCompare(b.ortsteil || '') || (a.strasse || '').localeCompare(b.strasse || '') || a.bez.localeCompare(b.bez));
    const zeilen = liste.slice(0, limit()).map(o => typ === 'haltung'
      ? `<tr data-detail="haltung" data-id="${esc(o.bez)}" tabindex="0"><td><a href="#" data-detail="haltung" data-id="${esc(o.bez)}">${esc(o.bez)}</a>${o.funktion === 'Druckleitung' ? ' <span class="chip">DL</span>' : ''}</td><td>${artChip(o.kanalart)}</td><td class="mobil-aus">${esc(o.strasse || '')}<br><span class="leise klein">${esc(o.ortsteil || '')}</span></td><td class="zahl">${zahl(o.laenge, 1)} m</td><td class="zahl mobil-aus">${o.dn || ''}</td><td class="mobil-aus">${esc(o.material || '')}</td><td class="mobil-aus">${o.baujahr || ''}</td><td>${zkChip(o.zk)}</td></tr>`
      : `<tr data-detail="knoten" data-id="${esc(o.bez)}" tabindex="0"><td><a href="#" data-detail="knoten" data-id="${esc(o.bez)}">${esc(o.bez)}</a>${o.art !== 'Schacht' ? ` <span class="chip">${esc(o.art)}</span>` : ''}</td><td>${artChip(o.kanalart)}</td><td class="mobil-aus">${esc(o.strasse || '')}<br><span class="leise klein">${esc(o.ortsteil || '')}</span></td><td class="zahl">${zahl(o.deckel)}</td><td class="zahl">${zahl(o.sohle)}</td><td class="zahl mobil-aus">${o.deckel != null && o.sohle != null ? zahl(o.deckel - o.sohle) : '–'}</td><td>${zkChip(o.zk)}</td></tr>`).join('');
    return `${kopf('Kanalnetz', 'Haltungen, Schächte und Bauwerke', `<button class="knopf zweit" data-akt="export-netz">CSV-Export</button>`)}
    <div class="filter">${sel('netztyp', [['haltung', 'Haltungen'], ['knoten', 'Schächte & Bauwerke']], 'Haltungen').replace('<option value="">Haltungen</option>', '')}
      <input data-filter="q" value="${esc(f('q'))}" placeholder="Bezeichnung oder Straße" aria-label="Suche" type="search">
      ${sel('ortsteil', ortsteile(), 'Alle Ortsteile')}${sel('kanalart', Object.entries(KANAL), 'Alle Kanalarten')}${sel('zk', [...[0, 1, 2, 3, 4, 5].map(k => [String(k), `ZK ${k} – ${ZK[k][0]}`]), ['x', 'nicht bewertet']], 'Alle Zustandsklassen')}</div>
    <section class="tafel"><div class="tabelle"><table><thead>${typ === 'haltung' ? '<tr><th>Haltung</th><th>Art</th><th class="mobil-aus">Straße</th><th class="zahl">Länge</th><th class="zahl mobil-aus">DN</th><th class="mobil-aus">Material</th><th class="mobil-aus">Baujahr</th><th>ZK</th></tr>' : '<tr><th>Schacht</th><th>Art</th><th class="mobil-aus">Straße</th><th class="zahl">Deckel</th><th class="zahl">Sohle</th><th class="zahl mobil-aus">Tiefe</th><th>ZK</th></tr>'}</thead><tbody>${zeilen}</tbody></table></div>${mehr(liste.length, Math.min(liste.length, limit()))}</section>`;
  },
  anlagen() {
    const liste = [...S.N.anlagen.values()].filter(a => (!f('atyp') || a.typ === f('atyp')) && (!f('aort') || a.ortsteil === f('aort'))).sort((a, b) => a.typ.localeCompare(b.typ) || (a.name || a.bez).localeCompare(b.name || b.bez));
    const offen = {}; for (const s of S.dyn.stoerungen.values()) if (s.status !== 'behoben') { const a = s.ziel_typ === 'anlage' ? s.ziel : s.ziel_typ === 'objekt' ? s.ziel.split('/')[0] : null; if (a) offen[a] = (offen[a] || 0) + 1; }
    return `${kopf('Anlagen', 'Pumpwerke, Regenrückhaltebecken, Auslaufbauwerke und Kläranlage')}
    <div class="filter">${sel('atyp', [...new Set([...S.N.anlagen.values()].map(a => a.typ))].sort(), 'Alle Anlagentypen')}${sel('aort', [...new Set([...S.N.anlagen.values()].map(a => a.ortsteil).filter(Boolean))].sort(), 'Alle Ortsteile')}</div>
    <div class="karten">${liste.map(a => `<a href="#" class="anlage-karte" data-detail="anlage" data-id="${esc(a.bez)}"><span class="typ">${esc(a.typ)} ${artChip(a.kanalart)}</span><strong>${esc(a.name || a.bez)}</strong><span class="leise klein">${esc(a.ortsteil || '')}${a.vorfluter ? ' · ' + esc(a.vorfluter) : ''}</span><span class="fuss">${a.objekte.length} Objekte${a.volumen ? ` · ${zahl(a.volumen, 0)} m³` : ''}${offen[a.bez] ? ` <span class="chip prio-hoch">${offen[a.bez]} offen</span>` : ''}</span></a>`).join('')}</div>`;
  },
  wartung() {
    const tage = +(f('tage') || 60);
    const plaene = [...S.dyn.wartungsplaene.values()].filter(p => p.aktiv !== false && p.naechste && tageBis(p.naechste) <= tage).sort((a, b) => a.naechste.localeCompare(b.naechste));
    const letzte = alleMassnahmen().sort((a, b) => b.datum.localeCompare(a.datum)).slice(0, 15);
    return `${kopf('Wartung & Inspektion', 'Fällige Termine aus den Wartungsplänen. „Erledigt“ dokumentiert die Maßnahme und setzt den nächsten Termin.')}
    <div class="filter"><label class="klein" for="f-tage">Fällig innerhalb</label><select id="f-tage" data-filter="tage">${[14, 30, 60, 90, 180, 365].map(t => `<option value="${t}" ${tage === t ? 'selected' : ''}>${t} Tagen</option>`).join('')}</select></div>
    <div class="raster zwei">
      <section class="tafel"><h2>Fällig und überfällig</h2>${plaene.length ? `<div class="tabelle"><table><thead><tr><th>Fällig</th><th>Tätigkeit</th><th>Objekt</th><th></th></tr></thead><tbody>${plaene.map(p => `<tr><td>${faellig(p)}</td><td>${esc(p.bezeichnung)}<br><span class="leise klein">${esc(p.art)} · alle ${p.intervall} Monate · ${esc(p.zustaendig || '')}</span></td><td>${zielLink(p.ziel_typ, p.ziel)}</td><td>${darfSchreiben() ? `<button class="knopf klein" data-akt="erledigt" data-plan="${p._id}">Erledigt</button>` : ''}</td></tr>`).join('')}</tbody></table></div>` : `<p class="leise">${S.geladen.wartungsplaene ? 'Nichts fällig im gewählten Zeitraum.' : S.db ? 'Wird geladen …' : 'Nur mit gemeinsamen Daten verfügbar.'}</p>`}</section>
      <section class="tafel"><h2>Zuletzt dokumentiert</h2><ul class="liste">${letzte.map(m => `<li><a href="#" data-detail="${m.ziel_typ}" data-id="${esc(m.ziel)}"><span class="zeile1">${datum(m.datum)} · <strong>${esc(m.art)}</strong> · ${esc(m.ergebnis || '')}</span><span class="zeile2">${esc(zielName(m.ziel_typ, m.ziel))}</span></a></li>`).join('')}</ul></section>
    </div>`;
  },
  schaeden() {
    let liste = [...S.N.schaeden.values()].map(s => ({...s, _st: schadenStatus(s), _kl: schadenKlasse(s)}));
    const st = f('sstatus') || 'offen+';
    liste = liste.filter(s => (st === 'alle' || (st === 'offen+' ? s._st !== 'saniert' : s._st === st)) && (!f('kode') || s.kode.startsWith(f('kode').toUpperCase())) && (!f('kl') || (s._kl != null && s._kl <= +f('kl'))) && (!f('styp') || s.typ === f('styp')));
    liste.sort((a, b) => (a._kl ?? 9) - (b._kl ?? 9) || (b.datum || '').localeCompare(a.datum || ''));
    return `${kopf('Einzelschäden', 'Kodierung nach DWA-M 149-2, Klassen D/S/B und Schadensklasse nach DWA-M 149-3', `<button class="knopf zweit" data-akt="katalog">Kodekatalog</button><button class="knopf zweit" data-akt="export-schaeden">CSV-Export</button>`)}
    <div class="filter"><input data-filter="kode" value="${esc(f('kode'))}" placeholder="Kode, z. B. BAB" aria-label="Kode" style="text-transform:uppercase">
      ${sel('kl', [0, 1, 2, 3, 4, 5].map(k => [String(k), 'Klasse ≤ ' + k]), 'Alle Klassen')}
      <select data-filter="sstatus" aria-label="Status">${[['offen+', 'offen und geplant'], ['offen', 'offen'], ['Sanierung geplant', 'Sanierung geplant'], ['saniert', 'saniert'], ['alle', 'alle']].map(([v, t]) => `<option value="${v}" ${st === v ? 'selected' : ''}>${t}</option>`).join('')}</select>
      ${sel('styp', [['haltung', 'Haltungen'], ['knoten', 'Schächte']], 'Alle Objekte')}</div>
    <section class="tafel">${schadenTabelle(liste.slice(0, limit()), true)}${mehr(liste.length, Math.min(liste.length, limit()))}</section>`;
  },
  stoerungen() {
    const st = f('stst') || 'aktiv', q = f('sq').toLowerCase();
    let liste = [...S.dyn.stoerungen.values()].filter(s => (st === 'alle' || (st === 'aktiv' ? s.status !== 'behoben' : s.status === st)) && (!f('sprio') || s.prioritaet === f('sprio')) && (!q || (s.titel || '').toLowerCase().includes(q) || (s.ziel || '').toLowerCase().includes(q)));
    liste.sort((a, b) => (b.gemeldet_am || '').localeCompare(a.gemeldet_am || ''));
    return `${kopf('Störmeldungen', '', neuKnopf('Neue Störung', 'neu-stoerung') + '<button class="knopf zweit" data-akt="export-stoerungen">CSV-Export</button>')}
    <div class="filter"><input data-filter="sq" value="${esc(f('sq'))}" placeholder="Suchbegriff oder Objekt" aria-label="Suche" type="search">
      <select data-filter="stst" aria-label="Status">${[['aktiv', 'offen und in Bearbeitung'], ['offen', 'offen'], ['in Bearbeitung', 'in Bearbeitung'], ['behoben', 'behoben'], ['alle', 'alle']].map(([v, t]) => `<option value="${v}" ${st === v ? 'selected' : ''}>${t}</option>`).join('')}</select>
      ${sel('sprio', PRIOS, 'Alle Prioritäten')}</div>
    <section class="tafel">${!S.db ? '<p class="leise">Störmeldungen sind nur mit gemeinsamen Daten verfügbar.</p>' : liste.length ? `<ul class="liste">${liste.slice(0, limit()).map(s => `<li><a href="#" data-detail="stoerung" data-id="${s._id}"><span class="zeile1">${prioChip(s.prioritaet)} ${statusChip(s.status)} <strong>${esc(s.titel)}</strong></span><span class="zeile2">${esc(zielName(s.ziel_typ, s.ziel))} · gemeldet ${datumZeit(s.gemeldet_am)}${s.bearbeiter ? ' · ' + esc(s.bearbeiter) : ''}</span></a></li>`).join('')}</ul>${mehr(liste.length, Math.min(liste.length, limit()))}` : `<p class="leise">${S.geladen.stoerungen ? 'Keine Störmeldungen für diesen Filter.' : 'Wird geladen …'}</p>`}</section>`;
  },
  import() {
    const importe = [...S.dyn.importe.values()].sort((a, b) => (b.zeitpunkt || '').localeCompare(a.zeitpunkt || ''));
    return `${kopf('Datenimport', 'ISYBAU-XML (Stamm- und Zustandsdaten), DWA-M 150-XML und CSV-Tabellen')}
    <div class="raster zwei">
      <section class="tafel"><h2>Datei einlesen</h2>
        ${darfSchreiben() ? `<form id="importform" class="stapel"><input type="file" id="importdatei" name="datei" accept=".xml,.csv" multiple required><button class="knopf" type="submit">Importieren</button></form><div id="importergebnis" class="stapel">${(S.importErgebnis || []).map(t => `<div class="hinweis">${esc(t)}</div>`).join('')}</div>` : '<p class="leise">Importieren können nur Personen mit Schreibrechten.</p>'}
        <p class="klein leise">Erst Stammdaten, dann Inspektionen einlesen. Schächte, Haltungen und Anlagen werden über die Bezeichnung aktualisiert, eine Inspektion desselben Objekts am selben Tag wird ersetzt. Koordinaten in UTM 32 (mit oder ohne Zonenpräfix) und Gauß-Krüger werden erkannt.</p>
        <details><summary>Spalten für CSV-Tabellen</summary><ul class="klein"><li><b>Schächte:</b> bezeichnung, knotenart, kanalart, ortsteil, strasse, rechtswert, hochwert oder lat, lon, deckelhoehe, sohlhoehe, material, baujahr</li><li><b>Haltungen:</b> bezeichnung, von, bis, kanalart, laenge, dn, material, baujahr, sohle_zulauf, sohle_ablauf, strasse, ortsteil</li><li><b>Schäden:</b> objekt, objektart (haltung/schacht), datum, kode, char1, char2, quant1, station, station_bis, uhr_von, klasse_d, klasse_s, klasse_b, bemerkung</li><li><b>Anlagen:</b> bezeichnung, name, anlagentyp, kanalart, ortsteil, adresse, lat, lon, baujahr, volumen_m3, vorfluter</li></ul></details>
      </section>
      <section class="tafel"><h2>Importprotokoll</h2>${importe.length ? `<ul class="liste">${importe.map(i => `<li><div class="eintrag"><span class="zeile1"><strong>${esc(i.datei)}</strong> · ${esc(i.format || '')}</span><span class="zeile2">${datumZeit(i.zeitpunkt?.slice(0, 16))} · <span data-person="${esc(i.von || '')}" data-fallback="unbekannt">…</span> · ${i.anzahl?.knoten || 0} Schächte, ${i.anzahl?.haltungen || 0} Haltungen, ${i.anzahl?.inspektionen || 0} Inspektionen, ${i.anzahl?.schaeden || 0} Schäden, ${i.anzahl?.anlagen || 0} Anlagen</span>${i.hinweise?.length ? `<details class="klein"><summary>${i.hinweise.length} Hinweise</summary>${i.hinweise.map(esc).join('<br>')}</details>` : ''}${darfSchreiben() ? `<button class="knopf zweit klein" data-akt="import-loeschen" data-id="${i._id}">Import zurücknehmen</button>` : ''}</div></li>`).join('')}</ul>` : '<p class="leise">Noch keine Importe. Das Beispielnetz ist fest hinterlegt.</p>'}</section>
    </div>`;
  },
  karte() { return ''; },
};
function schadenTabelle(liste, mitObjekt) {
  if (!liste.length) return '<p class="leise">Keine Schäden.</p>';
  return `<div class="tabelle"><table><thead><tr>${mitObjekt ? '<th>Objekt</th>' : ''}<th class="zahl">Station</th><th>Kode</th><th>Beschreibung</th><th class="mobil-aus">D/S/B</th><th>Kl.</th><th>Status</th></tr></thead><tbody>${liste.map(s => {
    const kl = schadenKlasse(s), st = schadenStatus(s);
    return `<tr data-detail="schaden" data-id="${esc(s.id)}" tabindex="0">${mitObjekt ? `<td><a href="#" data-detail="${s.typ}" data-id="${esc(s.objekt)}">${esc(s.objekt)}</a></td>` : ''}<td class="zahl">${s.station != null ? zahl(s.station, 1) : '–'}${s.stationBis != null ? '–' + zahl(s.stationBis, 1) : ''}</td><td><a href="#" data-detail="schaden" data-id="${esc(s.id)}" class="kode">${esc(s.kode)}${esc(s.c1 || '')}${esc(s.c2 || '')}</a></td><td>${esc(kodeText(s.kode, s.c1, s.c2))}${s.q1 ? ' · ' + esc(s.q1) : ''}${s.uhr ? ' · ' + s.uhr + ' Uhr' : ''}</td><td class="mobil-aus klein">${s.kd ?? '·'}/${s.ks ?? '·'}/${s.kb ?? '·'}</td><td>${zkChip(kl)}</td><td>${statusChip(st)}</td></tr>`; }).join('')}</tbody></table></div>`;
}

// ------------------------------------------------------------------ Detailansichten
function detailOeffnen(typ, id) { S.detail = {typ, id}; detailRender(); $('#detail').hidden = false; document.body.classList.add('detail-offen'); $('#detail').scrollTop = 0; }
function detailZu() { S.detail = null; $('#detail').hidden = true; document.body.classList.remove('detail-offen'); if (S.detailKarte) { S.detailKarte.remove(); S.detailKarte = null; } }
function dl(paare) { return `<dl class="daten">${paare.filter(p => p).map(([k, v]) => `<dt>${k}</dt><dd>${v == null || v === '' ? '–' : v}</dd>`).join('')}</dl>`; }
function betrieb(typ, bez, optionen = {}) {
  const plaene = [...S.dyn.wartungsplaene.values()].filter(p => p.ziel_typ === typ && p.ziel === bez).sort((a, b) => (a.naechste || '9').localeCompare(b.naechste || '9'));
  const mass = alleMassnahmen().filter(m => m.ziel_typ === typ && m.ziel === bez).sort((a, b) => b.datum.localeCompare(a.datum));
  const stoer = [...S.dyn.stoerungen.values()].filter(s => s.ziel_typ === typ && s.ziel === bez).sort((a, b) => (b.gemeldet_am || '').localeCompare(a.gemeldet_am || ''));
  const w = darfSchreiben(), a = `data-typ="${typ}" data-id="${esc(bez)}"`;
  return `<section class="abschnitt"><div class="tafel-kopf"><h3>Störmeldungen</h3>${w ? `<button class="knopf klein" data-akt="neu-stoerung" ${a}>Störung melden</button>` : ''}</div>
    ${stoer.length ? `<ul class="liste">${stoer.map(s => `<li><a href="#" data-detail="stoerung" data-id="${s._id}"><span class="zeile1">${prioChip(s.prioritaet)} ${statusChip(s.status)} ${esc(s.titel)}</span><span class="zeile2">${datumZeit(s.gemeldet_am)}</span></a></li>`).join('')}</ul>` : '<p class="leise">Keine Störmeldungen.</p>'}</section>
  <section class="abschnitt"><div class="tafel-kopf"><h3>Wartungspläne</h3>${w ? `<button class="knopf zweit klein" data-akt="neu-plan" ${a}>Plan anlegen</button>` : ''}</div>
    ${plaene.length ? `<ul class="liste">${plaene.map(p => `<li><div class="eintrag"><span class="zeile1"><strong>${esc(p.bezeichnung)}</strong>${p.aktiv === false ? ' <span class="chip">inaktiv</span>' : ''}</span><span class="zeile2">${esc(p.art)} · alle ${p.intervall} Monate · fällig ${faellig(p)}</span>${w ? `<span class="aktionen"><button class="knopf klein" data-akt="erledigt" data-plan="${p._id}">Erledigt</button><button class="knopf zweit klein" data-akt="plan-bearbeiten" data-plan="${p._id}">Bearbeiten</button></span>` : ''}</div></li>`).join('')}</ul>` : '<p class="leise">Keine Wartungspläne.</p>'}</section>
  <section class="abschnitt"><div class="tafel-kopf"><h3>Durchgeführte Maßnahmen</h3>${w ? `<button class="knopf zweit klein" data-akt="neu-massnahme" ${a}>Maßnahme</button>` : ''}</div>
    ${mass.length ? `<ul class="liste">${mass.slice(0, 20).map(m => `<li><div class="eintrag"><span class="zeile1">${datum(m.datum)} · <strong>${esc(m.art)}</strong> · ${esc(m.ergebnis || '')}</span><span class="zeile2">${esc(m.durch || '')}${m.befund ? ' · ' + esc(m.befund) : ''}</span></div></li>`).join('')}</ul>` : '<p class="leise">Noch nichts dokumentiert.</p>'}</section>
  ${optionen.schaeden === false ? '' : `<section class="abschnitt"><div class="tafel-kopf"><h3>Manuell erfasste Schäden</h3>${w ? `<button class="knopf zweit klein" data-akt="neu-schaden" ${a}>Schaden erfassen</button>` : ''}</div>${schadenTabelle([...S.N.schaeden.values()].filter(s => s.manuell && s.typ === typ && s.objekt === bez))}</section>`}`;
}
function haltungsband(h, schaeden, gegen) {
  const L = h.laenge || 1, x = st => 40 + 920 * Math.min(Math.max(gegen ? L - st : st, 0), L) / L, schritt = L > 60 ? 10 : 5;
  let s = `<svg class="band" viewBox="0 0 1000 140" role="img" aria-label="Lage der Schäden entlang der Haltung"><text x="20" y="18">${esc(h.von || 'Anfang')}</text><text x="980" y="18" text-anchor="end">${esc(h.bis || 'Ende')}</text><text x="500" y="18" text-anchor="middle">Fließrichtung → · ${zahl(h.laenge, 1)} m${gegen ? ' · Stationierung gegen Fließrichtung' : ''}</text>
    <rect x="40" y="62" width="920" height="26" rx="13" class="rohr"/><rect x="28" y="52" width="12" height="46" class="schacht"/><rect x="960" y="52" width="12" height="46" class="schacht"/>`;
  for (let m = 0; m <= L; m += schritt) s += `<line x1="${x(gegen ? L - m : m)}" y1="88" x2="${x(gegen ? L - m : m)}" y2="94" class="tick"/><text x="${x(gegen ? L - m : m)}" y="108" text-anchor="middle">${m}</text>`;
  schaeden.filter(d => d.station != null).forEach((d, i) => {
    const kl = schadenKlasse(d), farbe = zkFarbe(kl), xa = x(d.station);
    s += `<g class="punkt" data-detail="schaden" data-id="${esc(d.id)}">${d.stationBis != null ? `<rect x="${Math.min(xa, x(d.stationBis))}" y="62" width="${Math.max(Math.abs(x(d.stationBis) - xa), 2)}" height="26" fill="${farbe}" opacity=".6"/>` : `<circle cx="${xa}" cy="75" r="8" fill="${farbe}" class="rand"/>`}<text x="${xa}" y="${46 - (i % 2) * 12}" text-anchor="middle" font-weight="600">${esc(d.kode)}</text><title>${esc(d.kode + (d.c1 || '') + (d.c2 || ''))} – ${esc(kodeText(d.kode, d.c1, d.c2))} – Station ${d.station} m</title></g>`;
  });
  return s + `<g transform="translate(40,128)">${[0, 1, 2, 3, 4, 5].map(k => `<circle cx="${k * 74 + 6}" cy="0" r="6" fill="${ZK[k][2]}"/><text x="${k * 74 + 16}" y="4">Klasse ${k}</text>`).join('')}</g></svg>`;
}
function detailHTML() {
  const {typ, id} = S.detail, N = S.N, w = darfSchreiben();
  if (typ === 'haltung' || typ === 'knoten') {
    const o = typ === 'haltung' ? N.haltungen.get(id) : N.knoten.get(id); if (!o) return '<p>Objekt nicht gefunden.</p>';
    const {letzte, liste} = aktuelleSchaeden(typ, id), inspAlle = N.inspNachObjekt.get(typ + ':' + id) || [];
    const zu = typ === 'knoten' ? [...N.haltungen.values()].filter(h => h.bis === id) : [], ab = typ === 'knoten' ? [...N.haltungen.values()].filter(h => h.von === id) : [];
    const gefaelle = o.sz != null && o.sa != null && o.laenge ? (o.sz - o.sa) / o.laenge * 1000 : null;
    return `<div class="detail-kopf"><p class="eyebrow">${typ === 'haltung' ? 'Haltung' : esc(o.art)} · ${esc(o.ortsteil || '')}</p><h2>${esc(id)} ${artChip(o.kanalart)} ${zkChip(o.zk)}</h2><p class="leise">${esc(o.strasse || '')}${o.funktion === 'Druckleitung' ? ' · Druckleitung' : ''}</p>
      <div class="aktionen"><button class="knopf zweit klein" data-akt="auf-karte" data-typ="${typ}" data-id="${esc(id)}">Auf der Karte</button>${w ? `<button class="knopf klein" data-akt="neu-stoerung" data-typ="${typ}" data-id="${esc(id)}">Störung melden</button>` : ''}</div></div>
      ${typ === 'haltung' ? `<section class="abschnitt"><h3>Schadensbild ${letzte ? `<span class="leise klein">Inspektion ${datum(letzte.datum)}</span>` : ''}</h3>${liste.length ? haltungsband(o, liste, letzte?.gegen) + schadenTabelle(liste) : `<p class="leise">${letzte ? 'Bei der letzten Inspektion keine Schäden.' : 'Noch nicht inspiziert.'}</p>`}</section>` : `<section class="abschnitt"><h3>Schäden ${letzte ? `<span class="leise klein">Inspektion ${datum(letzte.datum)}</span>` : ''}</h3>${schadenTabelle(liste)}</section>`}
      <section class="abschnitt"><h3>Stammdaten</h3>${dl(typ === 'haltung' ? [
        ['Von Schacht', o.von ? `<a href="#" data-detail="knoten" data-id="${esc(o.von)}">${esc(o.von)}</a>` : '–'], ['Bis Schacht', o.bis ? `<a href="#" data-detail="knoten" data-id="${esc(o.bis)}">${esc(o.bis)}</a>` : '–'],
        ['Kanalart', KANAL[o.kanalart]], ['Länge', zahl(o.laenge) + ' m'], ['Profil', `DN ${o.dn || '–'}`], ['Material', esc(o.material)], ['Baujahr', o.baujahr],
        ['Sohle Zulauf', zahl(o.sz) + ' m'], ['Sohle Ablauf', zahl(o.sa) + ' m'], ['Gefälle', zahl(gefaelle, 1) + ' ‰'],
        ['Zustandsklasse', o.zk != null ? `${zkChip(o.zk)} ${ZK[o.zk][0]} – ${ZK[o.zk][1]}` : 'nicht bewertet'], ['Datenquelle', esc(o.quelle)]] : [
        ['Knotenart', esc(o.art)], ['Kanalart', KANAL[o.kanalart]], ['Deckelhöhe', zahl(o.deckel) + ' m ü. NHN'], ['Sohlhöhe', zahl(o.sohle) + ' m ü. NHN'],
        ['Schachttiefe', o.deckel != null && o.sohle != null ? zahl(o.deckel - o.sohle) + ' m' : '–'], ['Material', esc(o.material)], ['Baujahr', o.baujahr],
        ['Koordinaten', o.lat != null ? `${zahl(o.lat, 6)}, ${zahl(o.lon, 6)}` : '–'], o.anlage ? ['Anlage', `<a href="#" data-detail="anlage" data-id="${esc(o.anlage)}">${esc(zielName('anlage', o.anlage))}</a>`] : null,
        ['Zulauf', zu.map(h => `<a href="#" data-detail="haltung" data-id="${esc(h.bez)}">${esc(h.bez)}</a>`).join(', ') || '–'], ['Ablauf', ab.map(h => `<a href="#" data-detail="haltung" data-id="${esc(h.bez)}">${esc(h.bez)}</a>`).join(', ') || '–'],
        ['Datenquelle', esc(o.quelle)]])}</section>
      <section class="abschnitt"><h3>Inspektionen</h3>${inspAlle.length ? `<ul class="liste">${inspAlle.map(i => `<li><div class="eintrag"><span class="zeile1">${datum(i.datum)} · ${i.schaeden.length} Schäden</span><span class="zeile2">${esc(i.firma || '')} · ${esc(i.untersucher || '')} · ${i.gegen ? 'gegen' : 'in'} Fließrichtung · ${esc(i.quelle)}</span></div></li>`).join('')}</ul>` : '<p class="leise">Keine.</p>'}</section>
      ${betrieb(typ, id)}`;
  }
  if (typ === 'anlage') {
    const a = N.anlagen.get(id); if (!a) return '<p>Anlage nicht gefunden.</p>';
    return `<div class="detail-kopf"><p class="eyebrow">${esc(a.typ)} · ${esc(a.ortsteil || '')}</p><h2>${esc(a.name || a.bez)} ${artChip(a.kanalart)}</h2><p class="leise">${esc(a.adresse || '')}</p>
      <div class="aktionen"><button class="knopf zweit klein" data-akt="auf-karte" data-typ="anlage" data-id="${esc(id)}">Auf der Karte</button>${w ? `<button class="knopf klein" data-akt="neu-stoerung" data-typ="anlage" data-id="${esc(id)}">Störung melden</button>` : ''}</div></div>
      <section class="abschnitt"><h3>Anlagenobjekte</h3>${a.objekte.length ? `<div class="tabelle"><table><thead><tr><th>Objekt</th><th>Typ</th><th class="mobil-aus">Hersteller / Modell</th><th class="zahl">Leistung</th></tr></thead><tbody>${a.objekte.map(o => `<tr data-detail="objekt" data-id="${esc(o.key)}" tabindex="0"><td><a href="#" data-detail="objekt" data-id="${esc(o.key)}">${esc(o.bez)}</a></td><td>${esc(o.typ)}</td><td class="mobil-aus">${esc([o.hersteller, o.modell].filter(Boolean).join(' '))}</td><td class="zahl">${o.kw ? zahl(o.kw, 1) + ' kW' : ''}</td></tr>`).join('')}</tbody></table></div>` : '<p class="leise">Keine Objekte.</p>'}</section>
      <section class="abschnitt"><h3>Stammdaten</h3>${dl([['Kennung', esc(a.bez)], ['Typ', esc(a.typ)], ['Kanalart', KANAL[a.kanalart]], ['Baujahr', a.baujahr], ['Volumen', a.volumen ? zahl(a.volumen, 0) + ' m³' : '–'], ['Vorfluter', esc(a.vorfluter)], ['Bemerkung', esc(a.bemerkung)]])}</section>
      ${betrieb('anlage', id)}`;
  }
  if (typ === 'objekt') {
    const o = N.objekte.get(id); if (!o) return '<p>Objekt nicht gefunden.</p>';
    return `<div class="detail-kopf"><p class="eyebrow">${esc(o.typ)} · <a href="#" data-detail="anlage" data-id="${esc(o.anlage)}">${esc(zielName('anlage', o.anlage))}</a></p><h2>${esc(o.typ)} ${esc(o.bez)}</h2>
      <div class="aktionen">${w ? `<button class="knopf klein" data-akt="neu-stoerung" data-typ="objekt" data-id="${esc(id)}">Störung melden</button>` : ''}</div></div>
      <section class="abschnitt"><h3>Stammdaten</h3>${dl([['Hersteller', esc(o.hersteller)], ['Typ / Modell', esc(o.modell)], ['Seriennummer', esc(o.sn)], ['Baujahr', o.baujahr], ['Leistung', o.kw ? zahl(o.kw, 1) + ' kW' : '–'], ['Förderstrom', o.ls ? zahl(o.ls, 1) + ' l/s' : '–'], ['Förderhöhe', o.m ? zahl(o.m, 1) + ' m' : '–'], ['Betriebsstunden', o.bh ? zahl(o.bh, 0) : '–']])}</section>
      ${betrieb('objekt', id, {schaeden: false})}`;
  }
  if (typ === 'stoerung') {
    const s = S.dyn.stoerungen.get(id); if (!s) return '<p>Störmeldung nicht gefunden.</p>';
    return `<div class="detail-kopf"><p class="eyebrow">Störmeldung · gemeldet ${datumZeit(s.gemeldet_am)}</p><h2>${esc(s.titel)}</h2><p>${prioChip(s.prioritaet)} ${statusChip(s.status)} ${zielLink(s.ziel_typ, s.ziel)}</p>
      <div class="aktionen">${w ? `${s.status === 'offen' ? `<button class="knopf zweit klein" data-akt="st-status" data-id="${id}" data-status="in Bearbeitung">Übernehmen</button>` : ''}${s.status !== 'behoben' ? `<button class="knopf klein" data-akt="st-status" data-id="${id}" data-status="behoben">Als behoben melden</button>` : `<button class="knopf zweit klein" data-akt="st-status" data-id="${id}" data-status="offen">Wieder öffnen</button>`}<button class="knopf zweit klein" data-akt="st-bearbeiten" data-id="${id}">Bearbeiten</button>` : ''}</div></div>
      <section class="abschnitt">${dl([['Beschreibung', esc(s.beschreibung)], ['Gemeldet von', esc(s.gemeldet_von)], ['Meldeweg', esc(s.meldeweg)], ['Erfasst von', s.erfasst_von ? `<span data-person="${esc(s.erfasst_von)}">…</span>` : (s.demo ? 'Demodaten' : '–')], ['Bearbeiter', esc(s.bearbeiter)], ['Ursache', esc(s.ursache)], ['Maßnahme', esc(s.massnahme)], ['Behoben', datumZeit(s.behoben_am)], ['Ausfallzeit', s.ausfallzeit_h != null ? zahl(s.ausfallzeit_h, 1) + ' h' : '–']])}</section>
      ${s.fotos?.length ? `<section class="abschnitt"><h3>Fotos</h3><div class="fotos">${s.fotos.map(f => `<a href="/_blob/${esc(f)}" target="_blank" rel="noopener"><img src="/_blob/${esc(f)}" alt="Foto zur Störung" loading="lazy"></a>`).join('')}</div></section>` : ''}
      <section class="abschnitt"><h3>Ort</h3><div id="detailkarte" class="minikarte"></div></section>`;
  }
  if (typ === 'schaden') {
    const s = N.schaeden.get(id); if (!s) return '<p>Schaden nicht gefunden.</p>';
    const kl = schadenKlasse(s), st = schadenStatus(s), i = KATALOG[basisKode(s.kode)];
    return `<div class="detail-kopf"><p class="eyebrow">Einzelschaden · ${s.manuell ? 'manuell erfasst' : 'aus Inspektion ' + datum(s.datum)}</p><h2><span class="kode">${esc(s.kode + (s.c1 || '') + (s.c2 || ''))}</span> ${zkChip(kl)}</h2><p>${esc(kodeText(s.kode, s.c1, s.c2))}</p><p>${zielLink(s.typ, s.objekt)}</p>
      <div class="aktionen"><button class="knopf zweit klein" data-akt="schaden-karte" data-id="${esc(id)}">Auf der Karte</button>${w ? ['offen', 'Sanierung geplant', 'saniert'].filter(x => x !== st).map(x => `<button class="knopf ${x === 'saniert' ? '' : 'zweit'} klein" data-akt="schaden-status" data-id="${esc(id)}" data-status="${x}">${x === 'saniert' ? 'Als saniert melden' : x === 'offen' ? 'Wieder öffnen' : 'Sanierung geplant'}</button>`).join('') + (s.manuell ? `<button class="knopf zweit klein" data-akt="schaden-bearbeiten" data-id="${esc(id)}">Bearbeiten</button>` : '') : ''}</div></div>
      <section class="abschnitt">${dl([['Hauptkode', `<strong>${esc(s.kode)}</strong> ${esc(i?.text || 'nicht im Katalog')}`], ['Charakterisierung', `${esc(s.c1 || '–')} / ${esc(s.c2 || '–')}`], ['Quantifizierung', esc(s.q1) + (i?.quant1 ? ` <span class="leise klein">(${esc(i.quant1)})</span>` : '')],
        ['Station', s.station != null ? zahl(s.station) + ' m' + (s.stationBis != null ? ' bis ' + zahl(s.stationBis) + ' m (Streckenschaden)' : '') : '–'], ['Lage', s.uhr ? s.uhr + ' Uhr' : '–'], ['an Verbindung', s.verbindung ? 'ja' : 'nein'],
        ['Klassen D / S / B', `${zkChip(s.kd)} ${zkChip(s.ks)} ${zkChip(s.kb)}`], ['Schadensklasse', kl != null ? `${zkChip(kl)} ${ZK[kl][0]} – ${ZK[kl][1]}` : '–'], ['Status', statusChip(st)], ['Foto', esc(s.foto)], ['Bemerkung', esc(s.bemerkung)]])}
      <p class="klein leise">D = Dichtheit, S = Standsicherheit, B = Betriebssicherheit. Die Schadensklasse ist die schlechteste der drei.</p></section>`;
  }
  return '';
}
function detailRender() {
  if (!S.N || !S.detail) return;
  const d = $('#detail-inhalt'); d.innerHTML = detailHTML(); namenAufloesen();
  if (S.detailKarte) { S.detailKarte.remove(); S.detailKarte = null; }
  const kEl = $('#detailkarte'); const s = S.detail.typ === 'stoerung' ? S.dyn.stoerungen.get(S.detail.id) : null;
  if (kEl && s && window.L) { const pos = stoerungPosition(s); if (!pos) { kEl.outerHTML = '<p class="leise">Kein Ort bekannt.</p>'; return; }
    const k = L.map(kEl, {preferCanvas: true, attributionControl: false, zoomControl: false}).setView(pos, 17); S.detailKarte = k;
    const linien = []; for (const h of S.N.haltungen.values()) { const g = haltungGeo(h); if (g.length > 1 && abstand(g[0], pos) < 800) linien.push([g, h.kanalart]); }
    linien.forEach(([g, a]) => L.polyline(g, {color: css(a === 'RW' ? '--rw' : '--sw'), weight: 3, interactive: false}).addTo(k));
    L.circleMarker(pos, {radius: 9, color: css('--flaeche'), weight: 3, fillColor: css('--gefahr'), fillOpacity: 1}).addTo(k); setTimeout(() => k.invalidateSize(), 60); }
}

// ------------------------------------------------------------------ Karte
const K = {};
function karteZeigen() {
  if (!window.L) { $('#karte').innerHTML = '<p class="laden">Die Kartenbibliothek konnte nicht geladen werden.</p>'; return; }
  if (!S.karte) {
    const k = L.map('karte', {preferCanvas: true, zoomSnap: 0.5}); S.karte = k; L.control.scale({imperial: false}).addTo(k);
    k.attributionControl.setPrefix('Leaflet').addAttribution('Fiktives Netz · ohne Hintergrundkarte');
    K.haltungen = L.layerGroup().addTo(k); K.knoten = L.layerGroup(); K.anlagen = L.layerGroup().addTo(k); K.schaeden = L.layerGroup(); K.stoerungen = L.layerGroup().addTo(k); K.namen = L.layerGroup().addTo(k);
    k.on('moveend zoomend', knotenZeichnen);
    document.querySelectorAll('#kartenleiste [data-ebene]').forEach(cb => cb.addEventListener('change', () => { const e = K[cb.dataset.ebene]; cb.checked ? k.addLayer(e) : k.removeLayer(e); if (cb.dataset.ebene === 'knoten') knotenZeichnen(); }));
    $('#farbe').addEventListener('change', () => { haltungenZeichnen(); knotenZeichnen(); legende(); });
    $('#kartenort').innerHTML = '<option value="">Ganzes Netz</option>' + ortsteile().map(o => `<option>${esc(o)}</option>`).join('');
    $('#kartenort').addEventListener('change', e => { const o = e.target.value; const pts = [...S.N.knoten.values()].filter(x => x.lat != null && (!o || x.ortsteil === o)).map(x => [x.lat, x.lon]); if (pts.length) k.fitBounds(pts, {padding: [30, 30]}); });
    karteAktualisieren(true); legende();
    const pts = [...S.N.knoten.values()].filter(x => x.lat != null).map(x => [x.lat, x.lon]); k.fitBounds(pts, {padding: [20, 20]});
  }
  setTimeout(() => S.karte.invalidateSize(), 30);
}
function farbeHaltung(h) { return $('#farbe').value === 'zk' ? zkFarbe(h.zk) : css(h.kanalart === 'RW' ? '--rw' : h.kanalart === 'MW' ? '--mw' : '--sw'); }
function haltungenZeichnen() {
  if (!S.karte) return; K.haltungen.clearLayers();
  for (const h of S.N.haltungen.values()) { const g = haltungGeo(h); if (g.length < 2) continue;
    L.polyline(g, {color: farbeHaltung(h), weight: h.funktion === 'Druckleitung' ? 2.5 : h.dn >= 500 ? 5 : 3.5, dashArray: h.funktion === 'Druckleitung' ? '6 6' : null})
      .on('click', () => detailOeffnen('haltung', h.bez)).bindTooltip(esc(`${h.bez} · DN ${h.dn || '–'} · ZK ${h.zk ?? '–'}`), {sticky: true}).addTo(K.haltungen); }
}
function knotenZeichnen() {
  if (!S.karte) return; K.knoten.clearLayers(); if (!S.karte.hasLayer(K.knoten) || S.karte.getZoom() < 16) return;
  const b = S.karte.getBounds().pad(0.2), zk = $('#farbe').value === 'zk';
  for (const k of S.N.knoten.values()) if (k.lat != null && b.contains([k.lat, k.lon]))
    L.circleMarker([k.lat, k.lon], {radius: k.art === 'Schacht' ? 4.5 : 7, color: css('--flaeche'), weight: 1.5, fillOpacity: 1, fillColor: zk && k.zk != null ? zkFarbe(k.zk) : css(k.kanalart === 'RW' ? '--rw' : '--sw')})
      .on('click', () => detailOeffnen('knoten', k.bez)).bindTooltip(esc(`${k.art} ${k.bez}`)).addTo(K.knoten);
}
function karteAktualisieren(alles) {
  if (!S.karte || !S.N) return;
  if (alles) { haltungenZeichnen(); knotenZeichnen();
    K.namen.clearLayers(); const ot = {}; for (const k of S.N.knoten.values()) if (k.lat != null && k.ortsteil) { (ot[k.ortsteil] ||= []).push([k.lat, k.lon]); }
    for (const [n, p] of Object.entries(ot)) { const c = [p.reduce((s, x) => s + x[0], 0) / p.length, p.reduce((s, x) => s + x[1], 0) / p.length]; L.marker(c, {interactive: false, icon: L.divIcon({className: 'ortsname', html: esc(n), iconSize: null})}).addTo(K.namen); }
    K.schaeden.clearLayers();
    for (const s of S.N.schaeden.values()) { if (schadenStatus(s) === 'saniert') continue; const p = schadenPosition(s); if (!p) continue; const kl = schadenKlasse(s);
      L.circleMarker(p, {radius: 5.5, color: css('--flaeche'), weight: 1.5, fillOpacity: 1, fillColor: zkFarbe(kl)}).on('click', () => detailOeffnen('schaden', s.id)).bindTooltip(esc(`${s.kode}${s.c1 || ''} · Klasse ${kl ?? '–'}`)).addTo(K.schaeden); }
  }
  K.anlagen.clearLayers();
  const offen = {}; for (const s of S.dyn.stoerungen.values()) if (s.status !== 'behoben') { const a = s.ziel_typ === 'anlage' ? s.ziel : s.ziel_typ === 'objekt' ? s.ziel.split('/')[0] : null; if (a) offen[a] = 1; }
  for (const a of S.N.anlagen.values()) { if (a.lat == null) continue; const sym = {'Pumpwerk': 'P', 'Regenrückhaltebecken': 'R', 'Auslaufbauwerk': 'A', 'Kläranlage': 'KA'}[a.typ] || '•';
    L.marker([a.lat, a.lon], {icon: L.divIcon({className: '', iconSize: [28, 28], iconAnchor: [14, 14], html: `<div class="anlagen-symbol ${offen[a.bez] ? 'stoer' : a.kanalart === 'RW' ? 'rw' : ''}">${sym}</div>`}), keyboard: true, title: a.name || a.bez})
      .on('click', () => detailOeffnen('anlage', a.bez)).addTo(K.anlagen); }
  K.stoerungen.clearLayers();
  for (const s of S.dyn.stoerungen.values()) { if (s.status === 'behoben') continue; const p = stoerungPosition(s); if (!p) continue;
    L.circleMarker(p, {radius: 9, color: css('--gefahr'), weight: 3, fill: false}).on('click', () => detailOeffnen('stoerung', s._id)).bindTooltip(esc(s.titel)).addTo(K.stoerungen); }
}
function legende() {
  const zk = $('#farbe').value === 'zk';
  $('#legende').innerHTML = (zk ? [0, 1, 2, 3, 4, 5].map(k => `<span><i style="background:${ZK[k][2]}"></i>ZK ${k}</span>`).join('') + '<span><i style="background:var(--leise)"></i>nicht bewertet</span>'
    : '<span><i style="background:var(--sw)"></i>Schmutzwasser</span><span><i class="gestrichelt"></i>Druckleitung</span><span><i style="background:var(--rw)"></i>Regenwasser</span>') + '<span><b class="anlagen-symbol mini">P</b>Anlage</span><span><b class="ring"></b>offene Störung</span>';
}

// ------------------------------------------------------------------ Ereignisse
function navigieren() { const h = location.hash.slice(1); S.ansicht = TABS.some(t => t[0] === h) ? h : 'uebersicht'; S.seiten = 1; detailZu(); render(); window.scrollTo(0, 0); }
window.addEventListener('hashchange', navigieren);
document.addEventListener('click', async e => {
  const det = e.target.closest('[data-detail]');
  const akt = e.target.closest('[data-akt]');
  if (akt) {
    e.preventDefault(); const d = akt.dataset;
    switch (d.akt) {
      case 'dialog-zu': dialogZu(); break;
      case 'detail-zu': detailZu(); break;
      case 'mehr': S.seiten = (S.seiten || 1) + 1; render(); break;
      case 'neu-stoerung': stoerungFormular(null, d.typ ? {ziel_typ: d.typ, ziel: d.id} : {}); break;
      case 'st-bearbeiten': stoerungFormular(d.id); break;
      case 'st-status': stoerungStatus(d.id, d.status); break;
      case 'neu-plan': planFormular(d.typ, d.id); break;
      case 'plan-bearbeiten': planFormular(null, null, d.plan); break;
      case 'erledigt': { const p = S.dyn.wartungsplaene.get(d.plan); massnahmeFormular(p.ziel_typ, p.ziel, d.plan); break; }
      case 'neu-massnahme': massnahmeFormular(d.typ, d.id); break;
      case 'neu-schaden': schadenFormular(d.typ, d.id); break;
      case 'schaden-bearbeiten': schadenFormular(null, null, d.id.slice(2)); break;
      case 'schaden-status': schadenStatusSetzen(d.id, d.status); break;
      case 'auf-karte': { const p = zielPosition(d.typ, d.id); location.hash = 'karte'; setTimeout(() => { if (p && S.karte) { S.karte.setView(p, 18); } }, 120); break; }
      case 'schaden-karte': { const s = S.N.schaeden.get(d.id), p = s && schadenPosition(s); location.hash = 'karte'; setTimeout(() => { if (!S.karte) return; $('[data-ebene="schaeden"]').checked = true; S.karte.addLayer(K.schaeden); if (p) S.karte.setView(p, 19); }, 120); break; }
      case 'katalog': dialogOeffnen('Schadenskodes nach DWA-M 149-2', `<p class="klein leise">Hauptkodes für Haltungen (B..). Für Schächte gilt die D-Gruppe, z. B. DAB = Rissbildung im Schacht.</p>${[...new Set(Object.values(KATALOG).map(i => i.gruppe))].map(g => `<h3>${esc(g)}</h3><div class="tabelle"><table><tbody>${Object.entries(KATALOG).filter(([, i]) => i.gruppe === g).map(([k, i]) => `<tr><td class="kode"><b>${k}</b></td><td>${esc(i.text)}${i.char1 ? `<br><span class="klein leise">${Object.entries(i.char1).map(([c, t]) => `${c} = ${esc(t)}`).join(' · ')}</span>` : ''}</td></tr>`).join('')}</tbody></table></div>`).join('')}`, async () => {}); $('#dlg-form [type=submit]').hidden = true; break;
      case 'import-loeschen': { const id = d.id; if (akt.dataset.sicher !== '1') { akt.dataset.sicher = '1'; akt.textContent = 'Wirklich zurücknehmen?'; akt.classList.add('gefahr'); return; }
        for (const t of [...S.dyn.importdaten.values()].filter(t => t.import_id === id)) await loeschen('importdaten', t._id); await loeschen('importe', id); meldung('Import zurückgenommen.'); break; }
      case 'export-netz': { const typ = f('netztyp') || 'haltung';
        if (typ === 'haltung') csvExport('haltungen.csv', ['bezeichnung', 'von', 'bis', 'kanalart', 'funktion', 'ortsteil', 'strasse', 'laenge', 'dn', 'material', 'baujahr', 'sohle_zulauf', 'sohle_ablauf', 'zustandsklasse', 'letzte_inspektion'], [...S.N.haltungen.values()].map(h => [h.bez, h.von, h.bis, h.kanalart, h.funktion, h.ortsteil, h.strasse, h.laenge, h.dn, h.material, h.baujahr, h.sz, h.sa, h.zk, h.letzteInsp]));
        else csvExport('schaechte.csv', ['bezeichnung', 'knotenart', 'kanalart', 'ortsteil', 'strasse', 'lat', 'lon', 'deckelhoehe', 'sohlhoehe', 'material', 'baujahr', 'zustandsklasse'], [...S.N.knoten.values()].map(k => [k.bez, k.art, k.kanalart, k.ortsteil, k.strasse, k.lat, k.lon, k.deckel, k.sohle, k.material, k.baujahr, k.zk])); break; }
      case 'export-schaeden': csvExport('schaeden.csv', ['objektart', 'objekt', 'datum', 'kode', 'char1', 'char2', 'quant1', 'station', 'station_bis', 'uhr_von', 'klasse_d', 'klasse_s', 'klasse_b', 'schadensklasse', 'status'], [...S.N.schaeden.values()].map(s => [s.typ, s.objekt, s.datum, s.kode, s.c1, s.c2, s.q1, s.station, s.stationBis, s.uhr, s.kd, s.ks, s.kb, schadenKlasse(s), schadenStatus(s)])); break;
      case 'export-stoerungen': csvExport('stoerungen.csv', ['gemeldet_am', 'titel', 'objektart', 'objekt', 'prioritaet', 'status', 'meldeweg', 'gemeldet_von', 'bearbeiter', 'ursache', 'massnahme', 'behoben_am', 'ausfallzeit_h'], [...S.dyn.stoerungen.values()].map(s => [s.gemeldet_am, s.titel, s.ziel_typ, s.ziel, s.prioritaet, s.status, s.meldeweg, s.gemeldet_von, s.bearbeiter, s.ursache, s.massnahme, s.behoben_am, s.ausfallzeit_h])); break;
    }
    return;
  }
  if (det) { e.preventDefault(); detailOeffnen(det.dataset.detail, det.dataset.id); }
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') { if (!$('#dialog').hidden) dialogZu(); else if (S.detail) detailZu(); }
  if (e.key === 'Enter' && e.target.matches('tr[data-detail]')) detailOeffnen(e.target.dataset.detail, e.target.dataset.id);
});
document.addEventListener('submit', async e => {
  if (e.target.id !== 'importform') return; e.preventDefault();
  const dateien = [...$('#importdatei').files]; if (!dateien.length) return;
  const knopf = e.target.querySelector('button'); knopf.disabled = true; knopf.textContent = 'Wird importiert …';
  const erg = await importieren(dateien);
  S.importErgebnis = erg; render(); meldung('Import abgeschlossen.');
});

// ------------------------------------------------------------------ Start
(async function start() {
  S.ansicht = TABS.some(t => t[0] === location.hash.slice(1)) ? location.hash.slice(1) : 'uebersicht';
  render(); verbinden();
  try {
    const r = await fetch('netz.json'); S.basis = await r.json(); KATALOG = S.basis.katalog || {};
    aufbauen(); neuAufbauen = false; render();
  } catch (e) { $('#app').innerHTML = `<div class="hinweis">Das Kanalnetz konnte nicht geladen werden (${esc(e.message)}). Bitte Seite neu laden.</div>`; }
})();
