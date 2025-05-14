import os
import json
import subprocess
from qgis.utils import iface
from qgis.core import Qgis, QgsProject
from qgis.gui import QgsLayoutDesignerInterface
from PyQt5.QtWidgets import QMainWindow, QDockWidget, QApplication, QSplitter
from PyQt5.QtCore import Qt, QRect, QByteArray, QTimer

# File to store layout
# settings
CONFIG_FILE = os.path.expanduser("~/.qgis_layout_config.json")


def get_plugin_script_path():
    """Get the path to qgis-window.sh in the plugin directory."""
    try:
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(plugin_dir, "qgis-window.sh")
        if not os.path.isfile(script_path):
            raise FileNotFoundError(f"Script not found: {script_path}")
        return script_path
    except Exception as e:
        iface.messageBar().pushMessage("Error", str(e), level=Qgis.Critical)
        raise


def get_window_geometry(script_path):
    """Get true window geometry using qgis-window.sh."""
    try:
        result = subprocess.run(
            [script_path, "0", "0", "0", "0", "get"],
            check=True,
            capture_output=True,
            text=True,
        )
        geometry = json.loads(result.stdout)
        return geometry
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Failed to get window geometry: {str(e)}")
        iface.messageBar().pushMessage(
            "Warning",
            "Using QGIS internal geometry (may exclude decorations)",
            level=Qgis.Warning,
        )
        return None


def save_window_settings(main_window):
    """Save window size, position, maximized state, and state."""
    try:
        settings = {
            "size": [main_window.width(), main_window.height()],
            "position": [main_window.x(), main_window.y()],
            "maximized": main_window.isMaximized(),
            "state": main_window.saveState().toHex().data().decode(),
        }
        script_path = get_plugin_script_path()
        geometry = get_window_geometry(script_path)
        if geometry:
            settings["size"] = [geometry["width"], geometry["height"]]
            settings["position"] = [geometry["x"], geometry["y"]]
            print("True window geometry saved:", json.dumps(geometry, indent=2))
        return settings
    except Exception as e:
        print(f"Failed to save window settings: {str(e)}")
        return {"size": [800, 600], "position": [0, 0], "maximized": False, "state": ""}


def save_dock_settings(main_window):
    """Save visible dock widget states and tab groups."""
    try:
        panels = {}
        tab_groups = []
        processed_docks = set()
        for dock in main_window.findChildren(QDockWidget):
            if not dock.isVisible():
                continue
            dock_name = dock.objectName()
            panels[dock_name] = {
                "visible": True,
                "floating": dock.isFloating(),
                "geometry": (
                    [dock.x(), dock.y(), dock.width(), dock.height()]
                    if dock.isFloating()
                    else None
                ),
                "area": (
                    int(main_window.dockWidgetArea(dock))
                    if not dock.isFloating()
                    else None
                ),
            }
            if dock_name not in processed_docks:
                tabbed_docks = main_window.tabifiedDockWidgets(dock)
                if tabbed_docks:
                    tab_group = [dock_name] + [
                        d.objectName() for d in tabbed_docks if d.isVisible()
                    ]
                    if tab_group:
                        tab_groups.append(tab_group)
                        processed_docks.update(tab_group)
        print("Panel settings saved:", json.dumps(panels, indent=2))
        print("Tab groups saved:", json.dumps(tab_groups, indent=2))
        return panels, tab_groups
    except Exception as e:
        print(f"Failed to save dock settings: {str(e)}")
        return {}, []


def save_splitter_settings(main_window):
    """Save splitter sizes with hierarchy-based identification."""
    try:
        splitter_sizes = {}
        for splitter in main_window.findChildren(QSplitter):
            parent_name = (
                splitter.parent().objectName()
                if splitter.parent() and splitter.parent().objectName()
                else "root"
            )
            splitter_name = (
                f"splitter_{splitter.orientation()}_{parent_name}_{splitter.count()}"
            )
            splitter_sizes[splitter_name] = splitter.sizes()
            print(f"Saved splitter {splitter_name}: {splitter.sizes()}")
        print("Splitter sizes saved:", json.dumps(splitter_sizes, indent=2))
        return splitter_sizes
    except Exception as e:
        print(f"Failed to save splitter settings: {str(e)}")
        return {}


def save_active_layout(main_window):
    """Save the active layout if open."""
    try:
        layout_manager = QgsProject.instance().layoutManager()
        for designer in main_window.findChildren(QgsLayoutDesignerInterface):
            if designer.isVisible():
                current_layout = designer.layout().name()
                print("Active layout saved:", current_layout)
                return current_layout
        return None
    except Exception as e:
        print(f"Failed to save active layout: {str(e)}")
        return None


def save_layout():
    """Save QGIS window, layout, visible panel settings, and splitter sizes to a file."""
    try:
        main_window = iface.mainWindow()
        panels, tab_groups = save_dock_settings(main_window)
        settings = {
            "window": save_window_settings(main_window),
            "panels": panels,
            "tab_groups": tab_groups,
            "splitter_sizes": save_splitter_settings(main_window),
            "active_layout": save_active_layout(main_window),
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(settings, f, indent=2)
        print("Full saved layout settings:", json.dumps(settings, indent=2))
    except Exception as e:
        iface.messageBar().pushMessage(
            "Error", f"Failed to save layout: {str(e)}", level=Qgis.Critical
        )


def load_config_file():
    """Load the configuration file."""
    try:
        if not os.path.exists(CONFIG_FILE):
            raise FileNotFoundError("No layout config file found")
        with open(CONFIG_FILE, "r") as f:
            settings = json.load(f)
        print("Full loaded layout settings:", json.dumps(settings, indent=2))
        return settings
    except Exception as e:
        iface.messageBar().pushMessage("Error", str(e), level=Qgis.Critical)
        raise


def restore_window(main_window, window_settings, script_path):
    """Restore window size, position, and state."""
    try:
        print("Loading window settings:", json.dumps(window_settings, indent=2))
        if window_settings.get("maximized"):
            main_window.showMaximized()
        else:
            size = window_settings.get("size", [800, 600])
            pos = window_settings.get("position", [0, 0])
            os.chmod(script_path, 0o755)
            result = subprocess.run(
                [script_path, str(size[0]), str(size[1]), str(pos[0]), str(pos[1])],
                check=True,
                capture_output=True,
                text=True,
            )
            print("Script output:", result.stdout)
        if "state" in window_settings:
            main_window.restoreState(
                QByteArray.fromHex(window_settings["state"].encode())
            )
    except subprocess.CalledProcessError as e:
        iface.messageBar().pushMessage(
            "Error", f"Failed to run script: {str(e)}", level=Qgis.Critical
        )
    except Exception as e:
        print(f"Failed to restore window: {str(e)}")


def restore_panels(main_window, panels):
    """Restore dock widget states."""
    try:
        print("Loading panel settings:", json.dumps(panels, indent=2))
        dock_widgets = {
            dock.objectName(): dock for dock in main_window.findChildren(QDockWidget)
        }
        for dock_name, panel_settings in panels.items():
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
    except Exception as e:
        print(f"Failed to restore panels: {str(e)}")


def restore_tab_groups(main_window, tab_groups, panels):
    """Restore tab groups with explicit left-to-right order."""
    try:
        print("Loading tab groups:", json.dumps(tab_groups, indent=2))
        dock_widgets = {
            dock.objectName(): dock for dock in main_window.findChildren(QDockWidget)
        }
        for tab_group in tab_groups:
            if len(tab_group) > 1:
                first_dock = dock_widgets.get(tab_group[0])
                if first_dock:
                    for dock_name in tab_group:
                        dock = dock_widgets.get(dock_name)
                        if dock and not dock.isFloating():
                            main_window.addDockWidget(
                                Qt.DockWidgetArea(panels[dock_name]["area"]), dock
                            )
                    for i, other_dock_name in enumerate(tab_group[1:], 1):
                        other_dock = dock_widgets.get(other_dock_name)
                        if other_dock:
                            main_window.tabifyDockWidget(first_dock, other_dock)
                            other_dock.show()
                            other_dock.raise_()
                            print(f"Tab {i}: {other_dock_name}")
    except Exception as e:
        print(f"Failed to restore tab groups: {str(e)}")


def apply_splitter_sizes(main_window, splitter_sizes):
    """Apply splitter sizes after layout is settled."""
    try:
        print("Loading splitter sizes:", json.dumps(splitter_sizes, indent=2))
        for splitter in main_window.findChildren(QSplitter):
            parent_name = (
                splitter.parent().objectName()
                if splitter.parent() and splitter.parent().objectName()
                else "root"
            )
            splitter_name = (
                f"splitter_{splitter.orientation()}_{parent_name}_{splitter.count()}"
            )
            sizes = splitter_sizes.get(splitter_name)
            if sizes and len(sizes) == len(splitter.sizes()):
                if "lower" in parent_name.lower():
                    sizes = sizes[::-1]
                splitter.setSizes(sizes)
                print(f"Applied sizes {sizes} to {splitter_name}")
    except Exception as e:
        print(f"Failed to apply splitter sizes: {str(e)}")


def restore_active_layout(main_window, active_layout):
    """Restore the active layout if specified."""
    try:
        if active_layout:
            print("Loading active layout:", active_layout)
            layout_manager = QgsProject.instance().layoutManager()
            layout = layout_manager.layoutByName(active_layout)
            if layout:
                iface.openLayoutDesigner(layout)
    except Exception as e:
        print(f"Failed to restore active layout: {str(e)}")


def load_layout():
    """Load and apply QGIS window, layout, panel settings, and splitter sizes from file."""
    try:
        main_window = iface.mainWindow()
        settings = load_config_file()
        script_path = get_plugin_script_path()

        QTimer.singleShot(
            100,
            lambda: restore_window(
                main_window, settings.get("window", {}), script_path
            ),
        )
        QTimer.singleShot(
            100, lambda: restore_panels(main_window, settings.get("panels", {}))
        )
        QTimer.singleShot(
            100,
            lambda: restore_tab_groups(
                main_window, settings.get("tab_groups", []), settings.get("panels", {})
            ),
        )

        QTimer.singleShot(
            100,
            lambda: main_window.resize(
                settings["window"]["size"][0], settings["window"]["size"][1]
            ),
        )
        QApplication.processEvents()

        QTimer.singleShot(
            100,
            lambda: apply_splitter_sizes(
                main_window, settings.get("splitter_sizes", {})
            ),
        )

        # restore_active_layout(main_window, settings.get("active_layout"))
    except Exception as e:
        iface.messageBar().pushMessage(
            "Error", f"Failed to load layout: {str(e)}", level=Qgis.Critical
        )
