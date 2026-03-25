#!/bin/bash
#
# Inflation Dashboard — One-command update
#
# Usage:
#   ./update.sh cpi          # Update CPI data for one or more countries
#   ./update.sh forecast     # Open cb_forecasts.json for editing, then commit
#   ./update.sh imf          # Open imf_forecasts.json for editing, then commit
#   ./update.sh status       # Show current data status
#
set -e
cd "$(dirname "$0")"

EDITOR="${EDITOR:-code}"  # default to VS Code; change to nano/vim if preferred

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

show_status() {
    echo -e "${CYAN}=== Current CPI Data ===${NC}"
    python3 update_cpi.py --show-all
    echo ""
    echo -e "${CYAN}=== CB Forecast Dates ===${NC}"
    python3 -c "
import json
with open('docs/data/cb_forecasts.json') as f:
    cb = json.load(f)
for code in cb.get('display_order', []):
    fc = cb['forecasts'].get(code, {})
    rate = fc.get('policy_rate', {}).get('rate', '?')
    date = fc.get('publication_date', '?')
    print(f'  {code:4s} rate={rate:>12s}  forecast={date}')
"
    echo ""
    echo -e "${CYAN}=== IMF Version ===${NC}"
    python3 -c "
import json
with open('docs/data/imf_forecasts.json') as f:
    print('  ' + json.load(f).get('version', '?'))
"
}

update_cpi() {
    echo -e "${CYAN}=== CPI Update ===${NC}"
    echo ""
    show_status
    echo ""
    echo -e "${YELLOW}Enter updates (one per line). Format: COUNTRY DATE VALUE${NC}"
    echo -e "${YELLOW}Example: US 2026-03 2.8${NC}"
    echo -e "${YELLOW}Type 'done' when finished.${NC}"
    echo ""

    updates=()
    while true; do
        read -p "> " input
        [ "$input" = "done" ] && break
        [ -z "$input" ] && continue

        country=$(echo "$input" | awk '{print $1}')
        date=$(echo "$input" | awk '{print $2}')
        value=$(echo "$input" | awk '{print $3}')

        if [ -z "$country" ] || [ -z "$date" ] || [ -z "$value" ]; then
            echo "  Invalid format. Use: COUNTRY DATE VALUE (e.g. US 2026-03 2.8)"
            continue
        fi

        echo -e "  Updating ${GREEN}$country${NC} $date = ${GREEN}$value%${NC}"
        python3 update_cpi.py -c "$country" -d "$date" -v "$value"
        updates+=("$country $date")
    done

    if [ ${#updates[@]} -eq 0 ]; then
        echo "No updates made."
        return
    fi

    # Build commit message
    countries=$(printf '%s\n' "${updates[@]}" | awk '{print $1}' | sort -u | tr '\n' ', ' | sed 's/,$//')
    dates=$(printf '%s\n' "${updates[@]}" | awk '{print $2}' | sort -u | tr '\n' ', ' | sed 's/,$//')
    msg="Update CPI data: $countries ($dates)"

    echo ""
    echo -e "${GREEN}Committing: $msg${NC}"
    git add docs/data/historical_cpi.json
    git commit -m "$msg"
    git push origin main
    echo -e "${GREEN}Pushed. Newsletter draft workflow will trigger automatically.${NC}"
}

update_forecast() {
    echo -e "${CYAN}=== CB Forecast Update ===${NC}"
    echo "Opening cb_forecasts.json in $EDITOR..."
    echo "Edit the forecasts, save, and close. Then return here."
    echo ""
    $EDITOR docs/data/cb_forecasts.json

    read -p "Commit and push? (y/n) " confirm
    if [ "$confirm" = "y" ]; then
        read -p "Which bank(s) updated? (e.g. 'Fed Mar 2026 FOMC'): " desc
        git add docs/data/cb_forecasts.json
        git commit -m "Update CB forecast: $desc"
        git push origin main
        echo -e "${GREEN}Pushed.${NC}"
    else
        echo "Skipped. Changes are still in your working directory."
    fi
}

update_imf() {
    echo -e "${CYAN}=== IMF WEO Update ===${NC}"
    echo "Opening imf_forecasts.json in $EDITOR..."
    echo "Update version, retrieved date, and all country forecasts."
    echo ""
    $EDITOR docs/data/imf_forecasts.json

    read -p "Commit and push? (y/n) " confirm
    if [ "$confirm" = "y" ]; then
        read -p "Which WEO edition? (e.g. 'April 2026'): " edition
        git add docs/data/imf_forecasts.json
        git commit -m "Update IMF WEO forecasts ($edition)"
        git push origin main
        echo -e "${GREEN}Pushed.${NC}"
    else
        echo "Skipped. Changes are still in your working directory."
    fi
}

# Main
case "${1:-}" in
    cpi)
        update_cpi
        ;;
    forecast|cb)
        update_forecast
        ;;
    imf)
        update_imf
        ;;
    status|s)
        show_status
        ;;
    *)
        echo "Inflation Dashboard — Update Tool"
        echo ""
        echo "Usage:"
        echo "  ./update.sh cpi        Update CPI data (interactive)"
        echo "  ./update.sh forecast   Edit CB forecasts, commit & push"
        echo "  ./update.sh imf        Edit IMF forecasts, commit & push"
        echo "  ./update.sh status     Show current data status"
        echo ""
        echo "After CPI updates, the newsletter draft workflow triggers automatically."
        ;;
esac
