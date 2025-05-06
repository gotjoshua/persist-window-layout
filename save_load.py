import os
import json
import subprocess
from qgis.utils import iface
from qgis.core import Qgis, QgsProject
from qgis.gui import QgsLayoutDesignerInterface
from PyQt5.QtWidgets import QMainWindow, QDockWidget, QApplication, QSplitter
from PyQt5.QtCore import Qt, QRect, QByteArray, QTimer

# File to store layout settings
CONFIG_FILE = os.path.expanduser("~/.qgis_layout_config.json")

def save_layout():
    """Save QGIS window, layout, visible panel settings, and splitter sizes to a file."""
    main_window = iface.mainWindow()
    settings = {
        "window": {
            "size": [main_window.width(), main_window.height()],
            "position": [main_window.x(), main_window.y()],
            "maximized": main_window.isMaximized(),
            "state": main_window.saveState().toHex().data().decode()
        },
        "panels": {},
        "tab_groups": [],
        "splitter_sizes": {}
    }
    
    # Get true window geometry including decorations
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(plugin_dir, 'qgis-window.sh')
    if os.path.isfile(script_path):
        try:
            result = subprocess.run(
                [script_path, "0", "0", "0", "0", "get"],
                check=True,
                capture_output=True,
                text=True
            )
            geometry = json.loads(result.stdout)
            settings["window"]["size"] = [geometry["width"], geometry["height"]]
            settings["window"]["position"] = [geometry["x"], geometry["y"]]
            print("True window geometry saved:", json.dumps(geometry, indent=2))
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            print(f"Failed to get window geometry: {str(e)}")
            iface.messageBar().pushMessage("Warning", "Using QGIS internal geometry (may exclude decorations)", level=Qgis.Warning)

    # Save visible dock widget states and tab order
    processed_docks = set()
    for dock in main_window.findChildren(QDockWidget):
        if not dock.isVisible():
            continue
        dock_name = dock.objectName()
        settings["panels"][dock_name] = {
            "visible": True,
            "floating": dock.isFloating(),
            "geometry": [dock.x(), dock.y(), dock.width(), dock.height()] if dock.isFloating() else None,
            "area": int(main_window.dockWidgetArea(dock)) if not dock.isFloating() else None
        }
        if dock_name not in processed_docks:
            tabbed_docks = main_window.tabifiedDockWidgets(dock)
            if tabbed_docks:
                tab_group = [dock_name] + [d.objectName() for d in tabbed_docks if d.isVisible()]
                if tab_group:
                    settings["tab_groups"].append(tab_group)
                    processed_docks.update(tab_group)
    print("Panel settings saved:", json.dumps(settings["panels"], indent=2))
    print("Tab groups saved:", json.dumps(settings["tab_groups"], indent=2))

    # Save splitter sizes with hierarchy-based identification
    for splitter in main_window.findChildren(QSplitter):
        parent_name = splitter.parent().objectName() if splitter.parent() and splitter.parent().objectName() else "root"
        splitter_name = f"splitter_{splitter.orientation()}_{parent_name}_{splitter.count()}"
        settings["splitter_sizes"][splitter_name] = splitter.sizes()
        print(f"Saved splitter {splitter_name}: {splitter.sizes()}")
    print("Splitter sizes saved:", json.dumps(settings["splitter_sizes"], indent=2))

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

    print("Full saved layout settings:", json.dumps(settings, indent=2))

def load_layout():
    """Load and apply QGIS window, layout, panel settings, and splitter sizes from file."""
    if not os.path.exists(CONFIG_FILE):
        iface.messageBar().pushMessage("Error", "No layout config file found.")
        return

    main_window = iface.mainWindow()

    def apply_splitter_sizes():
        """Apply splitter sizes after layout is settled."""
        for splitter in main_window.findChildren(QSplitter):
            parent_name = splitter.parent().objectName() if splitter.parent() and splitter.parent().objectName() else "root"
            splitter_name = f"splitter_{splitter.orientation()}_{parent_name}_{splitter.count()}"
            sizes = settings.get("splitter_sizes", {}).get(splitter_name)
            if sizes and len(sizes) == len(splitter.sizes()):
                # Reverse sizes for lower panel set splitters
                if "lower" in parent_name.lower():
                    sizes = sizes[::-1]
                splitter.setSizes(sizes)
                print(f"Applied sizes {sizes} to {splitter_name}")

    try:
        with open(CONFIG_FILE, 'r') as f:
            settings = json.load(f)

        print("Full loaded layout settings:", json.dumps(settings, indent=2))

        # Restore window size, position, and state
        window = settings.get("window", {})
        print("Loading window settings:", json.dumps(window, indent=2))
        if window.get("maximized"):
            main_window.showMaximized()
        else:
            size = window.get("size", [800, 600])
            pos = window.get("position", [0, 0])
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(plugin_dir, 'qgis-window.sh')
            
            if not os.path.isfile(script_path):
                iface.messageBar().pushMessage("Error", f"Script not found: {script_path}", level=Qgis.Critical)
                return
                
            os.chmod(script_path, 0o755)
            
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

        # Restore window state (docks and splitters)
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

        # Restore tab groups with explicit left-to-right order
        print("Loading tab groups:", json.dumps(settings.get("tab_groups", []), indent=2))
        for tab_group in settings.get("tab_groups", []):
            if len(tab_group) > 1:
                first_dock = dock_widgets.get(tab_group[0])
                if first_dock:
                    # Clear existing tab relationships
                    for dock_name in tab_group:
                        dock = dock_widgets.get(dock_name)
                        if dock and not dock.isFloating():
                            main_window.addDockWidget(Qt.DockWidgetArea(settings["panels"][dock_name]["area"]), dock)
                    # Rebuild tab group in saved order
                    for i, other_dock_name in enumerate(tab_group[1:], 1):
                        other_dock = dock_widgets.get(other_dock_name)
                        if other_dock:
                            main_window.tabifyDockWidget(first_dock, other_dock)
                            other_dock.show()
                            other_dock.raise_()
                            print(f"Tab {i}: {other_dock_name}")

        # Force window resize and process events to settle layout
        main_window.resize(settings["window"]["size"][0], settings["window"]["size"][1])
        QApplication.processEvents()

        # Apply splitter sizes after a short delay to avoid race condition
        QTimer.singleShot(100, apply_splitter_sizes)

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