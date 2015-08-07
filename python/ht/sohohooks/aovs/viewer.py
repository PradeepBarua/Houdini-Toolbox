"""This module builds a dialog for displaying render plane information.

Synopsis
--------

"""

# =============================================================================
# IMPORTS
# =============================================================================

# Standard Library Imports
from PySide import QtCore, QtGui

# Houdini Toolbox Imports
from ht.sohohooks.aovs import aov, manager, models, widgets

import ht.ui.icons

import hou

# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
]

# =============================================================================
# CLASSES
# =============================================================================

class AOVViewer(QtGui.QWidget):

    invalidAOVSelectedSignal = QtCore.Signal()
    selectedAOVContainedSignal = QtCore.Signal(bool)

    def __init__(self, parent=None):
        super(AOVViewer, self).__init__(parent)

        self._interface_name = None

        layout = QtGui.QVBoxLayout()

        splitter = QtGui.QSplitter()

        self.select_widget = widgets.AOVSelectWidget()
        splitter.addWidget(self.select_widget)

        self.to_add_widget = widgets.AOVsToAddWidget()
        splitter.addWidget(self.to_add_widget)

        layout.addWidget(splitter)

        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)


        # Signals

        # Left/right button actions.
        self.select_widget.installSignal.connect(self.to_add_widget.installListener)
        self.select_widget.removeSignal.connect(self.to_add_widget.removeListener)

        # Update left/right buttons after data changed.
        self.select_widget.tree.selectionChangedSignal.connect(self.checkNodeAdded)
        self.to_add_widget.updateEnabledSignal.connect(self.checkNodeAdded)

        # Left/right button enabling/disabling.
        self.selectedAOVContainedSignal.connect(self.select_widget.install_bar.enableHandler)
        self.invalidAOVSelectedSignal.connect(self.select_widget.install_bar.disableHandler)



        # Really need a signal?  Maybe just refresh everything?
        manager.MANAGER.initInterface()
        manager.MANAGER.interface.aovAddedSignal.connect(self.select_widget.tree.insertAOV)
        manager.MANAGER.interface.groupAddedSignal.connect(self.select_widget.tree.insertGroup)
        #dialogs.AOVGroupDialog.groupUpdatedSignal.connect(self.select_widget.tree.updateGroup)


        self.to_add_widget.tree.model().sourceModel().insertedItemsSignal.connect(
            self.select_widget.markItemsInstalled
        )
        self.to_add_widget.tree.model().sourceModel().removedItemsSignal.connect(
            self.select_widget.markItemsUninstalled
        )


    @property
    def interface_name(self):
        return self._interface_name

    @interface_name.setter
    def interface_name(self, name):
        self._interface_name = name

    def checkNodeAdded(self):
        nodes = self.select_widget.getSelectedNodes()

        if nodes:
            contains = False

            for node in nodes:
                if self.to_add_widget.nodeIndexInModel(node) is not None:
                    contains = True
                    break

            self.selectedAOVContainedSignal.emit(contains)

        else:
            self.invalidAOVSelectedSignal.emit()

class AOVViewerInterface(QtCore.QObject):

    aovAddedSignal = QtCore.Signal(aov.AOV)
    aovUpdatedSignal = QtCore.Signal(aov.AOV)

    groupAddedSignal = QtCore.Signal(aov.AOVGroup)
    groupUpdatedSignal = QtCore.Signal(aov.AOVGroup)

    def __init__(self, parent=None):
        super(AOVViewerInterface, self).__init__(parent)
