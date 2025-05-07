#!/usr/bin/env bash

# Set default values
WIDTH=${1:-1920}
HEIGHT=${2:-2160}
X_POS=0        #${3:-0} #ignoring these options cuz i only want top corner alignment
Y_POS=0        #${4:-0}
MODE=${5:-set} # Default mode is 'set', can be 'get' for geometry

# Get QGIS window ID using gdbus
json=$(gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell/Extensions/Windows --method org.gnome.Shell.Extensions.Windows.List 2>/dev/null)
# Clean up gdbus output: strip outer ('...'), unescape quotes
clean_json="${json:2:-3}"
# shellcheck disable=SC2001
clean_json=$(echo "$clean_json" | sed 's/\\"/"/g')
# echo "$clean_json" | jq . # only for debugging otherwise breaks the return val
# Validate JSON and extract QGIS window ID
wid=$(echo "$clean_json" | jq -c '.[] | select(.wm_class and (.wm_class | test("QGIS3"; "i"))) | .id' 2>/dev/null || echo "Error: No QGIS window found")
if [[ "$wid" == "Error: No QGIS window found" ]]; then
    echo "$wid"
    exit 1
fi

if [[ "$MODE" == "get" ]]; then
    # Get window geometry using xwininfo
    xwininfo_output=$(xwininfo -id "$(xdotool search --class qgis | tail -n1)" 2>/dev/null)
    if [[ $? -ne 0 ]]; then
        echo "Error: Failed to get window geometry for $wid"
        exit 1
    fi
    # Extract geometry
    x=$(echo "$xwininfo_output" | grep "Absolute upper-left X" | awk '{print $4}')
    y=$(($(echo "$xwininfo_output" | grep "Absolute upper-left Y" | awk '{print $4}') - 37))
    width=$(echo "$xwininfo_output" | grep "Width" | awk '{print $2}')
    height=$(($(echo "$xwininfo_output" | grep "Height" | awk '{print $2}') + 37)) # add 37 for the title bar here
    # Output JSON
    echo "{\"width\": $width, \"height\": $height, \"x\": $x, \"y\": $y}"
    exit 0
fi

# Set mode: Resize and move window
gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell/Extensions/Windows --method org.gnome.Shell.Extensions.Windows.Resize "${wid}" "$WIDTH" "$HEIGHT"
gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell/Extensions/Windows --method org.gnome.Shell.Extensions.Windows.Move "${wid}" "$X_POS" "$Y_POS"
