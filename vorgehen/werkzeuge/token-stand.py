#!/usr/bin/env python3
"""Live-Token-Stand eines laufenden Claude-Code-Laufs.

Liest das Transcript (.jsonl), das Claude Code waehrend des Laufs mitschreibt —
runde-N.json kommt erst am Ende, das hier geht sofort.
  python3 token-stand.py <laufordner>
"""
import json, sys, os, glob, time

lauf = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
slug = os.path.abspath(lauf).replace('/', '-').replace('_', '-')
kandidaten = glob.glob(os.path.expanduser(f'~/.claude/projects/{slug}/*.jsonl'))
if not kandidaten:
    print(f'Kein Transcript fuer {lauf}'); sys.exit(1)
pfad = max(kandidaten, key=os.path.getmtime)

# WICHTIG: Bei Streaming schreibt das Transcript pro Nachricht MEHRFACH eine
# usage — kumulativ. Alle zu addieren zaehlt vier- bis fuenffach (nachgewiesen
# 02.09.2026: 1,2 Mio statt 350k). Deshalb je message.id nur den LETZTEN Stand.
je_nachricht = {}
werkzeuge = 0
modelle = set()
with open(pfad, encoding='utf-8', errors='replace') as f:
    for zeile in f:
        try: d = json.loads(zeile)
        except Exception: continue
        m = d.get('message') or {}
        u = m.get('usage') or {}
        if u:
            kennung = m.get('id') or d.get('uuid')
            je_nachricht[kennung] = u          # letzter Stand gewinnt
            if m.get('model'): modelle.add(m['model'])
        for teil in (m.get('content') or []) if isinstance(m.get('content'), list) else []:
            if teil.get('type') == 'tool_use': werkzeuge += 1

ein = sum(u.get('input_tokens', 0) or 0 for u in je_nachricht.values())
aus = sum(u.get('output_tokens', 0) or 0 for u in je_nachricht.values())
cache_neu = sum(u.get('cache_creation_input_tokens', 0) or 0 for u in je_nachricht.values())
cache_gelesen = sum(u.get('cache_read_input_tokens', 0) or 0 for u in je_nachricht.values())
antworten = len(je_nachricht)
denk = 0

dauer = (time.time() - os.path.getctime(lauf)) / 60
print(f"Modell:            {', '.join(sorted(modelle)) or '?'}")
print(f"Laufzeit:          {dauer:.0f} min")
print(f"Antworten:         {antworten}")
print(f"Werkzeugaufrufe:   {werkzeuge}")
print()
print(f"Ausgabe-Token:     {aus:>12,}".replace(',', '.'))
print(f"Eingabe-Token:     {ein:>12,}".replace(',', '.'))
print(f"Cache geschrieben: {cache_neu:>12,}".replace(',', '.'))
print(f"Cache gelesen:     {cache_gelesen:>12,}".replace(',', '.'))
print(f"Denk-Zeichen:      {denk:>12,}".replace(',', '.'))
print()
gesamt_ein = ein + cache_neu + cache_gelesen
print(f"Eingabe gesamt:    {gesamt_ein:>12,}".replace(',', '.'))
if dauer > 0:
    print(f"Ausgabe/min:       {aus/dauer:>12,.0f}".replace(',', '.'))
# Kostenschaetzung nach Anthropic-Listenpreis fuer Fable 5 (ZU VERIFIZIEREN)
print()
print("Kosten: erst aus runde-N.json (total_cost_usd) — das ist die belastbare Zahl.")
