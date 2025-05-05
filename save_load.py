import os
import json
import subprocess
from qgis.utils import iface
from qgis.core import Qgis, QgsProject
from qgis.gui import QgsLayoutDesignerInterface
from PyQt5.QtWidgets import QMainWindow, QDockWidget, QApplication
from PyQt5.QtCore import Qt, QRect, QByteArray

# File to store layout settings
CONFIG_FILE = os.path.expanduser("~/.qgis_layout_config.json")

def save_layout():
    """Save QGIS window, layout, and panel settings to a file."""
    main_window = iface.mainWindow()
    settings = {
        "window": {
            "size": [main_window.width(), main_window.height()],
            "position": [main_window.x(), main_window.y()],
            "maximized": main_window.isMaximized(),
            "state": main_window.saveState().toHex().data().decode()  # Save splitter and dock state
        },
        "panels": {},
        "tab_groups": []
    }
    print("Window settings saved:", json.dumps(settings["window"], indent=2))

    # Save dock widget states
    processed_docks = set()
    for dock in main_window.findChildren(QDockWidget):
        dock_name = dock.objectName()
        settings["panels"][dock_name] = {
            "visible": dock.isVisible(),
            "floating": dock.isFloating(),
            "geometry": [dock.x(), dock.y(), dock.width(), dock.height()] if dock.isFloating() else None,
            "area": int(main_window.dockWidgetArea(dock)) if not dock.isFloating() else None
        }
        # Save tabified relationships only if not processed
        if dock_name not in processed_docks:
            tabbed_docks = main_window.tabifiedDockWidgets(dock)
            if tabbed_docks:
                tab_group = [dock_name] + [d.objectName() for d in tabbed_docks]
                settings["tab_groups"].append(tab_group)
                processed_docks.update(tab_group)
    print("Panel settings saved:", json.dumps(settings["panels"], indent=2))
    print("Tab groups saved:", json.dumps(settings["tab_groups"], indent=2))

    # Save current layout if open
    layout_manager = QgsProject.instance().layoutManager()
    current_layout = None
    for designer in main_window.findChildren(QgsLayoutDesignerInterface):
        if designer.isVisible():
            current_layout = designer.layout().name()
            break

    if current_layout:
        settings["active_layout"] = current_layout
        print("Active layout saved:", current_layout)

    # Write to file
    with open(CONFIG_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

    # Output full settings JSON
    print("Full saved layout settings:", json.dumps(settings, indent=2))

def load_layout():
    """Load and apply QGIS window, layout, and panel settings from file."""
    if not os.path.exists(CONFIG_FILE):
        iface.messageBar().pushMessage("Error", "No layout config file found.")
        return

    main_window = iface.mainWindow()

    try:
        with open(CONFIG_FILE, 'r') as f:
            settings = json.load(f)

        # Output full loaded settings
        print("Full loaded layout settings:", json.dumps(settings, indent=2))

        # Restore window size, position, and state
        window = settings.get("window", {})
        print("Loading window settings:", json.dumps(window, indent=2))
        if window.get("maximized"):
            main_window.showMaximized()
        else:
            size = window.get("size", [800, 600])
            pos = window.get("position", [0, 0])
            # Get plugin directory and path to bash script
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(plugin_dir, 'qgis-window.sh')
            
            # Verify script exists
            if not os.path.isfile(script_path):
                iface.messageBar().pushMessage("Error", f"Script not found: {script_path}", level=Qgis.Critical)
                return
                
            # Make script executable
            os.chmod(script_path, 0o755)
            
            # Run script with parameters (example: size and position)
            try:
                result = subprocess.run(
                    [script_path, str(size[0]), str(size[1]), str(pos[0]), str(pos[1])],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print("Script output:", result.stdout)
            except subprocess.CalledProcessError as e:
                iface.messageBar().pushMessage("Error", f"Failed to run script: {str(e)}", level=Qgis.Critical)
                return
        # Restore splitter and dock state
        if "state" in window:
            main_window.restoreState(QByteArray.fromHex(window["state"].encode()))

        # Restore panels
        print("Loading panel settings:", json.dumps(settings.get("panels", {}), indent=2))
        dock_widgets = {dock.objectName(): dock for dock in main_window.findChildren(QDockWidget)}
        for dock_name, panel_settings in settings.get("panels", {}).items():
            dock = dock_widgets.get(dock_name)
            if dock:
                dock.setVisible(panel_settings.get("visible", True))
                if panel_settings.get("floating"):
                    geom = panel_settings.get("geometry")
                    if geom:
                        dock.setFloating(True)
                        dock.setGeometry(QRect(geom[0], geom[1], geom[2], geom[3]))
                else:
                    area = panel_settings.get("area")
                    if area is not None:
                        main_window.addDockWidget(Qt.DockWidgetArea(area), dock)

        # Restore tab groups
        print("Loading tab groups:", json.dumps(settings.get("tab_groups", []), indent=2))
        for tab_group in settings.get("tab_groups", []):
            if len(tab_group) > 1:
                first_dock = dock_widgets.get(tab_group[0])
                if first_dock:
                    for other_dock_name in tab_group[1:]:
                        other_dock = dock_widgets.get(other_dock_name)
                        if other_dock:
                            main_window.tabifyDockWidget(first_dock, other_dock)

        # Restore active layout
        active_layout = settings.get("active_layout")
        if active_layout:
            print("Loading active layout:", active_layout)
            layout_manager = QgsProject.instance().layoutManager()
            layout = layout_manager.layoutByName(active_layout)
            if layout:
                iface.openLayoutDesigner(layout)

    except Exception as e:
        iface.messageBar().pushMessage("Error", f"Failed to load layout: {str(e)}", level=Qgis.Critical)

# Commented out to prevent saving on script run
# save_layout()

# To load layout on startup, add this script to QGIS startup
# In QGIS: Settings -> User Profiles -> Open Active Profile Folder
# Place this script in python/ folder and add to python/qgis_user.py:
# from qgis_layout_manager import load_layout
# load_layout()