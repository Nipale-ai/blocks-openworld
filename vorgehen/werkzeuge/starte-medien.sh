#!/bin/bash
# Musik + Video fuer das Spiel. Laeuft in phase2-medien/, fasst den Spielcode nicht an.
# Die System-A-Sperre nimmt der LAUF SELBST, gezielt fuer die GPU-Phasen —
# nicht das Skript fuer die ganze Laufzeit. Sonst blockieren wir die andere
# Session unnoetig, waehrend das Modell nur nachdenkt oder Dateien schreibt.
set -u
HIER="$(cd "$(dirname "$0")" && pwd)"
ORDNER="${1:?phase2-medien-Ordner fehlt}"
SPEC="$HOME/Desktop/BENCH/PROMPTS/phase2-medien.txt"
MAX="${2:-2}"
cd "$ORDNER" || exit 1
export CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000
export API_TIMEOUT_MS="3000000"
export PATH="$HOME/bin:$PATH"     # systema-belegen/-frei muessen im PATH sein

for runde in $(seq 1 "$MAX"); do
  echo "=== MEDIEN-RUNDE $runde/$MAX ($(date +%H:%M:%S)) ==="
  JSON="medien-runde-$runde.json"
  ARGS=(--model fable --dangerously-skip-permissions
        --add-dir "$HOME/pyriq" --add-dir "$HOME/Desktop/BENCH" --add-dir "$HOME/bin"
        --output-format json --effort "${EFFORT:-xhigh}"
        --strict-mcp-config --mcp-config '{"mcpServers":{}}')
  if [ "$runde" -eq 1 ]; then
    claude -p "$(cat "$SPEC")" "${ARGS[@]}" > "$JSON" 2>> medien-lauf.log
  else
    claude -p -c "Continue: finish what is missing against the same brief, verify it, and update NOTES-medien.md. Do not ask questions." \
      "${ARGS[@]}" > "$JSON" 2>> medien-lauf.log
  fi
  python3 - "$JSON" "$runde" >> medien-kosten.md 2>/dev/null <<'PY'
import json, sys
try: d = json.load(open(sys.argv[1]))
except Exception as f:
    print(f"| m{sys.argv[2]} | JSON unlesbar: {f} |"); sys.exit()
mu = (d.get("modelUsage") or {}).get("claude-fable-5-1", {})
print(f"| m{sys.argv[2]} | {d.get('total_cost_usd','–')} | {d.get('duration_ms','–')} | "
      f"out {mu.get('outputTokens','–')} / denk {mu.get('thinkingTokens','–')} | turns {d.get('num_turns','–')} |")
PY
  # fertig, wenn Audio UND Doku da sind
  if ls out/*.ogg out/*.mp3 >/dev/null 2>&1 && [ -s NOTES-medien.md ]; then
    echo "=== MEDIEN FERTIG in Runde $runde ==="; ls -la out/ ; break
  fi
  echo "--- noch nicht vollstaendig, naechste Runde"
done
# Sicherheitsnetz: falls der Lauf die Sperre haelt und abgebrochen ist
~/bin/systema-wer 2>/dev/null | grep -q "model-research" && ~/bin/systema-frei "model-research" 2>/dev/null
echo "=== Ende $(date +%H:%M:%S) ==="
