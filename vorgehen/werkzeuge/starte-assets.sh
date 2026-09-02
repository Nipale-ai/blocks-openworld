#!/bin/bash
# Asset-Lauf auf System A: Blender-Modelle + PBR-Texturen.
# Laeuft in phase2-assets/ und fasst den Spielcode NICHT an —
# dort arbeitet parallel der Beleuchtungs-Lauf.
set -u
HIER="$(cd "$(dirname "$0")" && pwd)"
ORDNER="${1:?phase2-assets-Ordner fehlt}"
SPEC="$HOME/Desktop/BENCH/PROMPTS/phase2-assets-blender.txt"
MAX="${2:-3}"
EFFORT="${EFFORT:-xhigh}"

[ -d "$ORDNER" ] || { echo "ABBRUCH: $ORDNER fehlt"; exit 1; }
echo "→ System A pruefen"
ssh -o ConnectTimeout=8 systema 'true' || { echo "ABBRUCH: System A nicht erreichbar"; exit 1; }
ssh systema 'touch ~/.systema-keep-awake' 2>/dev/null
ssh systema 'nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader'

cd "$ORDNER" || exit 1
export CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000
export API_TIMEOUT_MS="3000000"

START=$(date +%s)
for runde in $(seq 1 "$MAX"); do
  echo "=== ASSET-RUNDE $runde/$MAX ($(date +%H:%M:%S)) ==="
  JSON="assets-runde-$runde.json"
  ARGS=(--model fable --dangerously-skip-permissions
        --add-dir "$HOME/pyriq" --add-dir "$HOME/Desktop/BENCH"
        --output-format json --effort "$EFFORT"
        --strict-mcp-config --mcp-config '{"mcpServers":{}}')
  if [ "$runde" -eq 1 ]; then
    claude -p "$(cat "$SPEC")" "${ARGS[@]}" > "$JSON" 2>> assets-lauf.log
  else
    claude -p -c "GOAL CHECK FAILED:
$(cat assets-gate.log)
Fix these and continue against the same brief. Do not ask questions." \
      "${ARGS[@]}" > "$JSON" 2>> assets-lauf.log
  fi
  python3 - "$JSON" "$runde" >> assets-kosten.md 2>/dev/null <<'PY'
import json, sys
try: d = json.load(open(sys.argv[1]))
except Exception as f:
    print(f"| a{sys.argv[2]} | JSON unlesbar: {f} |"); sys.exit()
mu = (d.get("modelUsage") or {}).get("claude-fable-5-1", {})
print(f"| a{sys.argv[2]} | {d.get('total_cost_usd','–')} | {d.get('duration_ms','–')} | "
      f"out {mu.get('outputTokens','–')} / denk {mu.get('thinkingTokens','–')} | turns {d.get('num_turns','–')} |")
PY
  if node "$HIER/pruefe_assets.mjs" "$ORDNER" > assets-gate.log 2>&1; then
    echo "=== ASSETS FERTIG in Runde $runde ($(( ($(date +%s)-START)/60 )) min) ==="
    cat assets-gate.log; exit 0
  fi
  echo "--- Gate rot:"; cat assets-gate.log
done
echo "=== DECKEL ERREICHT ==="; exit 1
