"""This module builds provides an interace for AOV management.
"""

# =============================================================================
# IMPORTS
# =============================================================================

# Python Imports
from PySide import QtCore, QtGui

# Houdini Toolbox Imports
from ht.sohohooks.aovs import aov, manager
from ht.ui.aovs import models, widgets
import ht.ui.icons

# Houdini Imports
import hou

# =============================================================================
# CLASSES
# =============================================================================

class AOVViewer(QtGui.QWidget):
    """Widget to view and perform actions with AOVs."""

    invalidAOVSelectedSignal = QtCore.Signal()
    selectedAOVContainedSignal = QtCore.Signal(bool)

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    def __init__(self, parent=None):
        super(AOVViewer, self).__init__(parent)

        self._interface_name = None

        self.initUI()

        # Left/right button action signals.
        self.select_widget.installSignal.connect(self.to_add_widget.installListener)
        self.select_widget.uninstallSignal.connect(self.to_add_widget.uninstallListener)

        # Update left/right buttons after data changed.
        self.select_widget.aov_tree.selectionChangedSignal.connect(self.checkNodeAdded)
        self.to_add_widget.updateEnabledSignal.connect(self.checkNodeAdded)

        # Left/right button enabling/disabling.
        self.selectedAOVContainedSignal.connect(self.select_widget.install_bar.enableHandler)
        self.invalidAOVSelectedSignal.connect(self.select_widget.install_bar.disableHandler)

        # Really need a signal?  Maybe just refresh everything?
        manager.MANAGER.initInterface()
        manager.MANAGER.interface.aovAddedSignal.connect(self.select_widget.aov_tree.insertAOV)
        manager.MANAGER.interface.groupAddedSignal.connect(self.select_widget.aov_tree.insertGroup)
        #dialogs.AOVGroupDialog.groupUpdatedSignal.connect(self.select_widget.aov_tree.updateGroup)

        self.to_add_widget.tree.model().sourceModel().insertedItemsSignal.connect(
            self.select_widget.markItemsInstalled
        )

        self.to_add_widget.tree.model().sourceModel().removedItemsSignal.connect(
            self.select_widget.markItemsUninstalled
        )

        self.to_add_widget.displayHelpSignal.connect(self.displayHelp)

    # =========================================================================
    # PROPERTIES
    # =========================================================================

    @property
    def interface_name(self):
        """Houdini interface name."""
        return self._interface_name

    @interface_name.setter
    def interface_name(self, name):
        self._interface_name = name

    # =========================================================================
    # METHODS
    # =========================================================================

    def checkNodeAdded(self):
        """This function detects whether selected tree nodes are currently
        in the 'AOVs to Apply' tree.

        """
        # Get selected nodes in the 'AOVs and Groups' tree.
        nodes = self.select_widget.getSelectedNodes()

        if nodes:
            # Are any contained.
            contains = False

            for node in nodes:
                # See if the node corresponds to an index in the target view.
                if self.to_add_widget.tree.nodeIndexInModel(node) is not None:
                    contains = True
                    break

            # Notify the move to left/right buttons on the status.
            self.selectedAOVContainedSignal.emit(contains)

        else:
            self.invalidAOVSelectedSignal.emit()

    def displayHelp(self):
        """Display help for the AOV Viewer."""
        browser = None

        for pane_tab in hou.ui.paneTabs():
            if isinstance(pane_tab, hou.HelpBrowser):
                if pane_tab.isFloating():
                    browser = pane_tab
                    break

        if browser is None:
            desktop = hou.ui.curDesktop()
            browser = desktop.createFloatingPaneTab(hou.paneTabType.HelpBrowser)

        browser.displayHelpPyPanel(self.interface_name)

    def initUI(self):
        """Initliaze the UI."""
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        layout.setContentsMargins(0, 0, 0, 0)

        # =====================================================================

        splitter = QtGui.QSplitter()
        layout.addWidget(splitter)

        self.select_widget = widgets.AOVSelectWidget()
        splitter.addWidget(self.select_widget)

        # =====================================================================

        self.to_add_widget = widgets.AOVsToAddWidget()
        splitter.addWidget(self.to_add_widget)


class AOVViewerInterface(QtCore.QObject):
    """This class acts as an interface between viewer related UI elements
    and the AOVManager.

    """

    # Signals for when AOVs are created or changed.
    aovAddedSignal = QtCore.Signal(aov.AOV)
    aovUpdatedSignal = QtCore.Signal(aov.AOV)

    # Signals for when AOVGroups are created or changed.
    groupAddedSignal = QtCore.Signal(aov.AOVGroup)
    groupUpdatedSignal = QtCore.Signal(aov.AOVGroup)

    def __init__(self, parent=None):
        super(AOVViewerInterface, self).__init__(parent)
