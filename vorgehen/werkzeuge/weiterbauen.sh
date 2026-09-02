#!/bin/bash
# ============================================================
# Weiterbauen an einem bestehenden Lauf.
#   bash weiterbauen.sh <laufordner> <spec-datei> [runden]
#
# Anders als duell-cloud.sh: kein neuer Ordner, kein neuer Anfang.
# Fable liest den vorhandenen src/-Baum und arbeitet daran weiter.
# Vorher wird gesichert — eine funktionierende Fassung geht nie verloren.
#
# ⛔ System A wird NICHT angefasst (die Maschine ist belegt).
# ============================================================
set -u
HIER="$(cd "$(dirname "$0")" && pwd)"
ORDNER="${1:?Laufordner fehlt}"
SPEC="${2:?Spec fehlt}"
MAX="${3:-3}"
GATE="${GATE_SKRIPT:-$HIER/pruefe_openworld.mjs}"
EFFORT="${EFFORT:-xhigh}"

[ -d "$ORDNER/src" ] || { echo "ABBRUCH: kein src/ in $ORDNER"; exit 1; }
[ -s "$SPEC" ]       || { echo "ABBRUCH: Spec fehlt: $SPEC"; exit 1; }

# Sicherung der abgenommenen Fassung, bevor irgendetwas angefasst wird
STAND="$ORDNER/stand-$(date +%Y%m%d-%H%M)"
mkdir -p "$STAND"
cp -R "$ORDNER/src" "$STAND/" 2>/dev/null
cp "$ORDNER/game.html" "$ORDNER/NOTES.md" "$STAND/" 2>/dev/null
echo "→ Sicherung: $STAND"

cd "$ORDNER" || exit 1
export CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000
export API_TIMEOUT_MS="3000000"

RUNDE_DATEI() { echo "weiter-$(date +%Y%m%d-%H%M)-runde-$1.json"; }

gate() {
  [ -s game.html ] || { echo "ROT: game.html fehlt"; return 1; }
  node "$GATE" "$ORDNER/game.html"
}

START=$(date +%s)
for runde in $(seq 1 "$MAX"); do
  echo "=== WEITERBAU-RUNDE $runde/$MAX ($(date +%H:%M:%S)) ==="
  JSON="$(RUNDE_DATEI "$runde")"
  ARGS=(--model fable --dangerously-skip-permissions
        --add-dir "$HOME/pyriq" --add-dir "$HOME/Desktop/BENCH"
        --output-format json --effort "$EFFORT"
        --strict-mcp-config --mcp-config '{"mcpServers":{}}')

  if [ "$runde" -eq 1 ]; then
    claude -p "$(cat "$SPEC")" "${ARGS[@]}" > "$JSON" 2>> lauf.log
  else
    claude -p -c "GOAL CHECK FAILED. The automated gate reports:
$(cat gate.log)
Fix these findings and re-verify against the brief you were given.
Do not ask questions." "${ARGS[@]}" > "$JSON" 2>> lauf.log
  fi

  python3 - "$JSON" "$runde" >> kosten.md 2>/dev/null <<'PY'
import json, sys
try: d = json.load(open(sys.argv[1]))
except Exception as f:
    print(f"| w{sys.argv[2]} | – | – | JSON unlesbar: {f} |"); sys.exit()
mu = (d.get("modelUsage") or {}).get("claude-fable-5-1", {})
print(f"| w{sys.argv[2]} | {d.get('total_cost_usd','–')} | {d.get('duration_ms','–')} | "
      f"out {mu.get('outputTokens','–')} / denk {mu.get('thinkingTokens','–')} | "
      f"turns {d.get('num_turns','–')} |")
PY

  if gate > gate.log 2>&1; then
    echo "=== ZIEL ERREICHT in Runde $runde ($(( ($(date +%s)-START)/60 )) min) ==="
    cat gate.log; exit 0
  fi
  echo "--- Gate rot:"; cat gate.log
done
echo "=== DECKEL ERREICHT, Ziel nicht erreicht ==="; exit 1
