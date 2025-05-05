#!/usr/bin/env bash

# Set default values
WIDTH=${1:-1920}
HEIGHT=${2:-2160}
X_POS=${3:-0}
Y_POS=${4:-0}

# Get QGIS window ID
json=$(gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell/Extensions/Windows --method org.gnome.Shell.Extensions.Windows.List)
# Clean JSON: remove surrounding (' and '),) and ensure valid JSON
echo "$json"
clean_json="${json:2:-3}"
echo "$clean_json" | jq .

# Validate JSON and extract QGIS window ID
wid=$(echo "$clean_json" | jq -c '.[] | select(.wm_class and (.wm_class | test("QGIS3"; "i"))) | .id' 2>/dev/null || echo "Error: No QGIS window found")
# Check if wid is valid
if [[ "$wid" == "Error: No QGIS window found" ]]; then
    echo "$wid"
    exit 1
fi
# Print window ID
echo "QGIS Window ID: $wid"
# Resize to 1920x2160
gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell/Extensions/Windows --method org.gnome.Shell.Extensions.Windows.Resize ${wid} $WIDTH $HEIGHT
# Move to (0,0)
gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell/Extensions/Windows --method org.gnome.Shell.Extensions.Windows.Move ${wid} $X_POS $Y_POS
