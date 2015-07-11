"""This module builds a dialog for displaying render plane information.

Synopsis
--------

"""

# =============================================================================
# IMPORTS
# =============================================================================

# Standard Library Imports
from PySide import QtCore, QtGui

import pickle

# Houdini Toolbox Imports
#from ht.sohohooks.planes import buildPlaneGroups, RenderPlane, RenderPlaneGroup
#from ht.sohohooks.planes import flattenList, applyToNodeAsParms, listAsString
import ht.sohohooks.aovs.models
from ht.sohohooks.aovs import widgets, aov, manager

import ht.ui.icons
from ht.ui.pyside import findOrCreateEventLoop

# TODO: Don't need Houdini to run.
import hou

# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
]

# =============================================================================
# CONSTANTS
# =============================================================================


# =============================================================================
# CLASSES
# =============================================================================

class AOVViewer(QtGui.QWidget):

    def __init__(self, parent=None):
        super(AOVViewer, self).__init__(parent)

        manager.findOrCreateSessionAOVManager()

        tabs = QtGui.QTabWidget()

        self.setter = ApplyAOVTabWidget()
        icon = QtGui.QIcon(hou.findFile("help/icons/large/DESKTOP/ifd.png"))

        tabs.addTab(self.setter, icon, "Set")

        self.groups = widgets.GroupTabWidget()
        icon = QtGui.QIcon(hou.findFile("help/icons/large/DATATYPES/bundle.png"))
        tabs.addTab(self.groups, icon, "Groups")

        self.aovs = widgets.AOVTabWidget()
        icon = QtGui.QIcon(hou.findFile("help/icons/large/PANETYPES/viewer_cop.png"))
        tabs.addTab(self.aovs, icon, "AOVs")

        layout = QtGui.QVBoxLayout()

        layout.addWidget(tabs)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)


class ApplyAOVTabWidget(QtGui.QWidget):

    def __init__(self):

        super(ApplyAOVTabWidget, self).__init__()

        # Get all the plane sets.
#        planeGroups = buildPlaneGroups()
#        manager = ht.sohohooks.aovs.manager.AOVManager()
#        planeGroups = manager.groups

        # The base layout.
        layout = QtGui.QVBoxLayout()

        add_widget = QtGui.QWidget()
        add_layout = QtGui.QVBoxLayout()

        bold_font = QtGui.QFont()
	bold_font.setBold(True)

        label = QtGui.QLabel("Add AOVs")
        label.setFont(bold_font)

        add_layout.addWidget(label)




        self.to_add_tabs = QtGui.QTabWidget()


        # =====================================================================
        # By Group
        # =====================================================================

        group_widget = QtGui.QWidget()
        group_layout = QtGui.QVBoxLayout()

        self.groupList = QtGui.QListView()
        self.groupList.setStyleSheet("alternate-background-color: rgb(46, 46 ,46);")
        self.groupList.setAlternatingRowColors(True)

        m = ht.sohohooks.aovs.models.AOVGroupListModel()
        self.groupProxyModel = QtGui.QSortFilterProxyModel()
        self.groupProxyModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.groupProxyModel.setSourceModel(m)
        self.groupList.setModel(self.groupProxyModel)
        self.groupProxyModel.sort(0)

        self.groupList.setDragEnabled(True)


        groupFilterLayout = QtGui.QHBoxLayout()
        groupFilterLayout.setContentsMargins(0, 0, 0, 0)

        groupFilterLayout.addWidget(QtGui.QLabel("Filter"))


        # Construct the filter text field.
        self.groupFilterField = QtGui.QLineEdit()
        self.groupFilterField.setToolTip(
            "Filter the list of groups by name."
        )

        groupFilterLayout.addWidget(self.groupFilterField)


        QtCore.QObject.connect(
            self.groupFilterField,
            QtCore.SIGNAL("textChanged(QString)"),
            self.groupProxyModel.setFilterRegExp
        )

        group_layout.addWidget(self.groupList)
        group_layout.addLayout(groupFilterLayout)

        group_widget.setLayout(group_layout)

        self.to_add_tabs.addTab(group_widget, "By Group")

        QtCore.QObject.connect(
            self.groupList.selectionModel(),
            QtCore.SIGNAL("currentChanged(QModelIndex, QModelIndex)"),
            self.handleGroupSelectChange
        )

        # =====================================================================
        # By Name
        # =====================================================================

        plane_widget = QtGui.QWidget()
        plane_layout = QtGui.QVBoxLayout()

        self.planeList = QtGui.QListView()
        m = ht.sohohooks.aovs.models.AOVChoiceListModel()
        self.planeList.setDragEnabled(True)
        self.planeList.setStyleSheet("alternate-background-color: rgb(46, 46 ,46);")
        self.planeList.setAlternatingRowColors(True)


        self.planeProxyModel = QtGui.QSortFilterProxyModel()
        self.planeProxyModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.planeProxyModel.setSourceModel(m)
        self.planeList.setModel(self.planeProxyModel)
        self.planeProxyModel.sort(0)

        plane_layout.addWidget(self.planeList)


        aovFilterLayout = QtGui.QHBoxLayout()
        aovFilterLayout.setContentsMargins(0, 0, 0, 0)

        aovFilterLayout.addWidget(QtGui.QLabel("Filter"))


        # Construct the filter text field.
        self.aovFilterField = QtGui.QLineEdit()
        self.aovFilterField.setToolTip(
            "Filter the list of AOVs by name."
        )

        aovFilterLayout.addWidget(self.aovFilterField)

        plane_layout.addLayout(aovFilterLayout)


        QtCore.QObject.connect(
            self.aovFilterField,
            QtCore.SIGNAL("textChanged(QString)"),
            self.planeProxyModel.setFilterRegExp
        )





        plane_widget.setLayout(plane_layout)

        self.to_add_tabs.addTab(plane_widget, "By Name")

        QtCore.QObject.connect(
            self.planeList.selectionModel(),
            QtCore.SIGNAL("currentChanged(QModelIndex, QModelIndex)"),
            self.handleAOVSelectChange
        )



        split_layout = QtGui.QSplitter()





        add_layout.addWidget(self.to_add_tabs)


        self.to_add_tabs.currentChanged.connect(self.addTabChanged)



        # =====================================================================
        # Move buttons
        # =====================================================================

        blah = QtGui.QHBoxLayout()

        blah.addLayout(add_layout)

        move_layout = QtGui.QVBoxLayout()
        move_layout.addStretch(1)

        self.to_right = QtGui.QPushButton("")
        self.to_right.setIcon(
            QtGui.QIcon(hou.findFile("help/icons/large/BUTTONS/move_to_right.png"))
        )
#        self.to_right.setFlat(True)
        self.to_right.setIconSize(QtCore.QSize(16, 16))
        self.to_right.setMaximumSize(QtCore.QSize(24, 24))
        self.to_right.clicked.connect(self.moveRight)

        move_layout.addWidget(self.to_right, alignment=QtCore.Qt.AlignVCenter)


        self.to_left = QtGui.QPushButton("")
        self.to_left.setIcon(
            QtGui.QIcon(hou.findFile("help/icons/large/BUTTONS/move_to_left.png"))
        )
        self.to_left.setIconSize(QtCore.QSize(16, 16))
        self.to_left.setMaximumSize(QtCore.QSize(24, 24))
        self.to_left.clicked.connect(self.moveLeft)

        self.to_left.setEnabled(False)

        move_layout.addWidget(self.to_left, alignment=QtCore.Qt.AlignVCenter)
        move_layout.addStretch(1)

        blah.addLayout(move_layout)

        # =====================================================================


        add_widget.setLayout(blah)


        split_layout.addWidget(add_widget)

#        self.chosen_aovs = ChosenAOVWidget()
        self.to_add_widget = widgets.AOVsToAddWidget()

        split_layout.addWidget(self.to_add_widget)


#        self.tree = widgets.AOVsToAddWidget()#widgets.AOVTreeWidget()
#        split_layout.addWidget(self.tree)




        layout.addWidget(split_layout)

        self.setLayout(layout)

        self._current_selected = None

    def handleGroupSelectChange(self, selected, deselected):
        model = self.groupProxyModel.sourceModel()

        idx = self.groupList.model().mapToSource(selected)

        element = model.groups[idx.row()]

        if self.to_add_widget.treeContainsItem(element):
#        if element in self.to_add_widget.choice_model.items:
            self.to_right.setEnabled(False)
            self.to_left.setEnabled(True)

        else:
            self.to_left.setEnabled(False)
            self.to_right.setEnabled(True)

        self._current_selected = element

    def handleAOVSelectChange(self, selected, deselected):
        model = self.planeProxyModel.sourceModel()

        idx = self.planeList.model().mapToSource(selected)

        element = model.aovs[idx.row()]

        if self.to_add_widget.treeContainsItem(element):
            self.to_right.setEnabled(False)
            self.to_left.setEnabled(True)

        else:
            self.to_left.setEnabled(False)
            self.to_right.setEnabled(True)

        self._current_selected = element


    def addTabChanged(self, idx):
        self.refreshMoveButtons()


    def moveRight(self):
        element = self._findSelectedElementToAdd()

        if element is not None:
            self.to_add_widget.addItemToTree(element)

    def moveLeft(self):
        self.to_add_widget.removeItemFromTree(self._current_selected)

    def refreshMoveButtons(self):
        tab_idx = self.to_add_tabs.currentIndex()

        if tab_idx == 0:
            pass
        else:
            pass


    def _findSelectedElementToAdd(self):
        tab_idx = self.to_add_tabs.currentIndex()

        element = None

        if tab_idx == 0:
            widget = self.groupList

            indices = widget.selectionModel().selectedIndexes()

            if indices:
                model = widget.model().sourceModel()

                idx = widget.model().mapToSource(indices[0])

                element = model.groups[idx.row()]

        else:
            widget = self.planeList

            indices = widget.selectionModel().selectedIndexes()

            if indices:
                model = widget.model().sourceModel()

                idx = widget.model().mapToSource(indices[0])

                element = model.aovs[idx.row()]

        return element

class ChosenAOVWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(ChosenAOVWidget, self).__init__(parent)

        self._as_parms = False

        added_layout = QtGui.QVBoxLayout()

        top_layout = QtGui.QHBoxLayout()

        bold_font = QtGui.QFont()
	bold_font.setBold(True)

        label = QtGui.QLabel("AOVs to Add")
        label.setFont(bold_font)
        top_layout.addWidget(label)

        added_layout.addLayout(top_layout)


        self.listWidget = LayerListWidget()

        self.choice_model = ht.sohohooks.aovs.models.AOVApplyModel()

        self.listWidget.setModel(self.choice_model)



        added_layout.addWidget(self.listWidget)


        toolbar = QtGui.QToolBar(self)

        toolbar.setIconSize(QtCore.QSize(24, 24))

        apply_action = QtGui.QAction(
            QtGui.QIcon(hou.findFile("help/icons/large/DATATYPES/boolean.png")),
            "Apply",
            self,
            triggered=self.applyToNodes
        )

        apply_action.setToolTip("Apply AOVs to selected nodes.")

        b = QtGui.QToolButton(toolbar)
        b.setDefaultAction(apply_action)

        toolbar.addWidget(b)

        self.menu = QtGui.QMenu(self)

        ag = QtGui.QActionGroup(self.menu, exclusive=True)

        a1 = QtGui.QAction(
            "At rendertime",
            ag,
            checkable=True,
            triggered=self.setAtRendertime
        )

        ag.addAction(a1)

        a2 = QtGui.QAction(
            "As parameters",
            ag,
            checkable=True,
            triggered=self.setAsParameters
        )

        ag.addAction(a2)

        a1.setChecked(True)

        self.menu.addAction(a1)
        self.menu.addAction(a2)

        b.setMenu(self.menu)



        load_action = QtGui.QAction(
            QtGui.QIcon(hou.findFile("help/icons/large/COMMON/file.png")),
            "Load from",
            self,
            triggered=self.applyToNodes
        )


        load_menu = QtGui.QMenu(toolbar)
        load_menu.addAction("From node")
        load_menu.addAction("From file")

        load_action.setToolTip("Load AOVs from a file or node.")

        c = QtGui.QToolButton(toolbar)
        c.setDefaultAction(load_action)

        toolbar.addWidget(c)
        load_action.setMenu(load_menu)

        toolbar.setStyleSheet("QToolBar {border: 0;}")

        added_layout.addWidget(toolbar)

        self.setLayout(added_layout)


    def setAsParameters(self):
        self._as_parms = True

    def setAtRendertime(self):
        self._as_parms = False


    def applyToNodes(self):
        nodes = self._getSelectedNodes()

        if self._as_parms:
            self._applyAsParms(nodes)

        else:
            self._applyAsString(nodes)



    def _applyAsString(self, nodes):
        elements = self.listWidget.getAddedPlanes()

#        value = listAsString(elements)

#        for node in nodes:
#            if not node.parm("auto_planes"):
#                parm_template = hou.StringParmTemplate(
#                    "auto_planes",
#                    "Automatic AOVs",
#                    1,
#                )

#                node.addSpareParmTuple(parm_template)

#            parm = node.parm("auto_planes")
#            parm.set(value)


    def _applyAsParms(self, nodes):
        elements = self.listWidget.getAddedPlanes()
#        aovs = flattenList(elements)

#        for node in nodes:
#            applyToNodeAsParms(node, aovs)



    def _getSelectedNodes(self):
        nodes = hou.selectedNodes()

        mantra_type = hou.nodeType("Driver/ifd")

        nodes = [node for node in nodes if node.type() == mantra_type]

        if not nodes:
            hou.ui.displayMessage(
                "No mantra nodes selected.",
                severity=hou.severityType.Error
            )

        return tuple(nodes)

class LayerListWidget(QtGui.QListView):


    def __init__(self, parent=None):
        super(LayerListWidget, self).__init__(parent)

        self.setStyleSheet("alternate-background-color: rgb(46, 46 ,46);")

        self.setAcceptDrops(True)
        self.setAlternatingRowColors(True)

        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openMenu)


    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("text/csv"):
            data = pickle.loads(event.mimeData().data("text/csv"))

            if data in self.model().items:
                event.ignore()
                return

            event.acceptProposedAction()

        else:
            super(LayerListWidget, self).dragEnterEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat("text/csv"):
            data = pickle.loads(event.mimeData().data("text/csv"))

            if event.keyboardModifiers() == QtCore.Qt.ControlModifier and isinstance(data, RenderPlaneGroup):
                self._extractFromGroup([data])

            else:
                if data in self.model().items:
                    event.ignore()
                    return

                self.model().insertRows(data)

            event.acceptProposedAction()

        else:
            super(LayerListWidget, self).dropEvent(event)

    def keyPressEvent(self, event):
        key = event.key()

        if key == QtCore.Qt.Key_Delete:
            self._del_item()

        if key == QtCore.Qt.Key_E:
            self._extractFromGroup()

        elif key == QtCore.Qt.Key_Up:
            pass

        elif key == QtCore.Qt.Key_Down:
            pass

        elif key == QtCore.Qt.Key_A:
            if event.modifiers() == QtCore.Qt.ControlModifier:
                self.selectAll()


    def _del_item(self):
        indices = self.selectedIndexes()

        for idx in reversed(indices):
            self.model().removeRows(idx)


    def _extractFromGroup(self, plane_groups=None):
        if plane_groups is None:
            plane_groups = self._getSelectedPlaneGroups()

            self._del_item()

        planes = flattenList(plane_groups)

        for plane in planes:
            self.model().insertRows(plane)

    def getAddedPlanes(self):
        return self.model().items


    def _getSelectedPlaneGroups(self):
        plane_groups = []

        indices = self.selectedIndexes()

        items = self.model().items

        for idx in indices:
            item = items[idx.row()]

            if isinstance(item, RenderPlaneGroup):
                plane_groups.append(item)


        return plane_groups

    def openMenu(self, position):
        indices = self.selectedIndexes()

        menu = QtGui.QMenu(self)

        menu.addAction(
            "Select All",
            self.selectAll,
            QtGui.QKeySequence.SelectAll
        )

        menu.addAction(
            "Delete",
            self._del_item,
            QtGui.QKeySequence.Delete,
        )

        extract_action = menu.addAction(
            "Extract planes from group",
            self._extractFromGroup,
            QtGui.QKeySequence(QtCore.Qt.Key_E),
        )
        extract_action.setDisabled(True)

        items = self.model().items

        for idx in indices:
            item = items[idx.row()]

            if isinstance(item, RenderPlaneGroup):
                extract_action.setDisabled(False)
                break


        menu.exec_(self.mapToGlobal(position))



