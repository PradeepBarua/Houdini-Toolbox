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

        self.manager = manager.findOrCreateSessionAOVManager()

        layout = QtGui.QVBoxLayout()

#        blayout = QtGui.QHBoxLayout()
#        blayout.addStretch()
#        blayout.setContentsMargins(0, 0, 4, 0)

#        button = QtGui.QPushButton(
#            QtGui.QIcon(":ht/rsc/icons/sohohooks/aovs/help.png"),
#            ""
#        )

#        button.setToolTip("Show help")

#        button.setIconSize(QtCore.QSize(16, 16))
#        button.setMaximumSize(QtCore.QSize(25, 25))
#        button.setFlat(True)

#        button.clicked.connect(self.displayHelp)

#        blayout.addWidget(button)

#        layout.addLayout(blayout)

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
        self.selectedAOVContainedSignal.connect(self.select_widget.move.enableHandler)
        self.invalidAOVSelectedSignal.connect(self.select_widget.move.disableHandler)


        self.manager.initInterface()

        self.manager.interface.aovAddedSignal.connect(
            self.select_widget.tree.insertAOV
        )

        self.manager.interface.groupAddedSignal.connect(
            self.select_widget.tree.insertGroup
        )

    @property
    def interface_name(self):
        return self._interface_name

    @interface_name.setter
    def interface_name(self, name):
        self._interface_name = name


    # TODO: Dim out added nodes...
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


    def displayHelp(self):
        if self.interface_name is not None:
            desktop = hou.ui.curDesktop()
            browser = desktop.createFloatingPaneTab(hou.paneTabType.HelpBrowser)
            browser.displayHelpPyPanel(self.interface_name)



class AOVViewerInterface(QtCore.QObject):

    aovAddedSignal = QtCore.Signal(aov.AOV)
    groupAddedSignal = QtCore.Signal(aov.AOVGroup)

    def __init__(self, parent=None):
        super(AOVViewerInterface, self).__init__(parent)


