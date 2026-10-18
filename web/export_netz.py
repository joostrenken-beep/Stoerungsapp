import json, os, sys
from datetime import date
os.environ["KANALDB_DATA_DIR"] = sys.argv[1]
out = sys.argv[2]; seed = sys.argv[3]
from kanaldb import create_app
from kanaldb.models import *
from kanaldb.dwa149 import katalog
app = create_app({"TESTING": True, "AUTO_IMPORT": False})
r = lambda v, n=2: None if v is None else round(v, n)
with app.app_context():
    kb = {k.id: k.bezeichnung for k in Knoten.query}
    netz = {"meta": {"stand": date.today().isoformat(), "hinweis": "Fiktives Beispielnetz Osterholz-Scharmbeck"}}
    netz["knoten"] = [[k.bezeichnung, k.knotenart, k.kanalart, k.ortsteil, k.strasse, r(k.lat, 6), r(k.lon, 6),
                       r(k.deckelhoehe), r(k.sohlhoehe), k.baujahr, k.material, k.anlage.bezeichnung if k.anlage else None]
                      for k in Knoten.query.order_by(Knoten.bezeichnung)]
    hs = []
    for h in Haltung.query.order_by(Haltung.bezeichnung):
        g = [round(c, 6) for p in json.loads(h.geometrie or "[]") for c in p]
        hs.append([h.bezeichnung, kb.get(h.von_knoten_id), kb.get(h.bis_knoten_id), h.kanalart, h.funktion, h.ortsteil,
                   h.strasse, r(h.laenge), h.dn, h.material, h.baujahr, r(h.sohle_zulauf), r(h.sohle_ablauf), g])
    netz["haltungen"] = hs
    ins, sch = [], []
    for i in Inspektion.query.order_by(Inspektion.id):
        z = i.ziel
        ins.append([i.id, "h" if i.ziel_typ == "haltung" else "k", z.bezeichnung, i.datum.isoformat(), i.firma, i.untersucher,
                    1 if i.gegen_fliessrichtung else 0, r(i.inspektionslaenge)])
        for s in i.schaeden:
            sch.append([s.id, i.id, s.kode, s.char1, s.char2, s.quant1, r(s.station, 1), r(s.station_bis, 1), s.uhr_von,
                        1 if s.verbindung else 0, s.klasse_d, s.klasse_s, s.klasse_b, s.foto])
    netz["inspektionen"], netz["schaeden"] = ins, sch
    netz["anlagen"] = [dict(bez=a.bezeichnung, name=a.name, typ=a.anlagentyp, kanalart=a.kanalart, ortsteil=a.ortsteil,
                            adresse=a.adresse, lat=r(a.lat, 6), lon=r(a.lon, 6), baujahr=a.baujahr, volumen=a.volumen_m3,
                            vorfluter=a.vorfluter, bemerkung=a.bemerkung) for a in Anlage.query.order_by(Anlage.bezeichnung)]
    netz["objekte"] = [dict(anlage=o.anlage.bezeichnung, bez=o.bezeichnung, typ=o.objekttyp, hersteller=o.hersteller,
                            modell=o.typ, sn=o.seriennummer, baujahr=o.baujahr, kw=o.leistung_kw, ls=o.foerderstrom_ls,
                            m=o.foerderhoehe_m, bh=o.betriebsstunden) for o in Anlagenobjekt.query.order_by(Anlagenobjekt.id)]
    netz["katalog"] = katalog()

    def ziel(typ, zid):
        z = ziel_laden(typ, zid)
        if typ == "objekt":
            return f"{z.anlage.bezeichnung}/{z.bezeichnung}"
        return z.bezeichnung
    plan_ids = {}
    writes = []
    for n, p in enumerate(Wartungsplan.query.order_by(Wartungsplan.id), 1):
        pid = f"p{n:03d}"; plan_ids[p.id] = pid
        writes.append({"op": "set", "collection": "wartungsplaene", "doc_id": pid, "data": dict(
            ziel_typ=p.ziel_typ, ziel=ziel(p.ziel_typ, p.ziel_id), bezeichnung=p.bezeichnung, art=p.art,
            intervall=p.intervall_monate, letzte=p.letzte_durchfuehrung.isoformat() if p.letzte_durchfuehrung else None,
            naechste=p.naechste_faelligkeit.isoformat() if p.naechste_faelligkeit else None, zustaendig=p.zustaendig,
            aktiv=p.aktiv, beschreibung=p.beschreibung)})
    netz["massnahmen_alt"] = [dict(ziel_typ=m.ziel_typ, ziel=ziel(m.ziel_typ, m.ziel_id), plan=plan_ids.get(m.wartungsplan_id),
                                   art=m.art, datum=m.datum.isoformat(), durch=m.durchgefuehrt_von, ergebnis=m.ergebnis,
                                   beschreibung=m.beschreibung, befund=m.befund, dauer=m.dauer_h)
                              for m in Massnahme.query.order_by(Massnahme.datum.desc())]
    for n, s in enumerate(Stoermeldung.query.order_by(Stoermeldung.gemeldet_am), 1):
        writes.append({"op": "set", "collection": "stoerungen", "doc_id": f"st{n:03d}", "data": dict(
            ziel_typ=s.ziel_typ, ziel=ziel(s.ziel_typ, s.ziel_id), titel=s.titel, beschreibung=s.beschreibung,
            gemeldet_am=s.gemeldet_am.isoformat(timespec="minutes"), gemeldet_von=s.gemeldet_von, meldeweg=s.meldeweg,
            prioritaet=s.prioritaet, status=s.status, bearbeiter=s.bearbeiter, ursache=s.ursache, massnahme=s.massnahme,
            behoben_am=s.behoben_am.isoformat(timespec="minutes") if s.behoben_am else None, ausfallzeit_h=s.ausfallzeit_h,
            lat=None, lon=None, fotos=[], demo=True)})
    json.dump(netz, open(out, "w"), ensure_ascii=False, separators=(",", ":"))
    for i in range(0, len(writes), 50):
        json.dump(writes[i:i + 50], open(f"{seed}/batch{i // 50 + 1}.json", "w"), ensure_ascii=False)
    print(len(writes), "seed writes")
