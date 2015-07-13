


# Standard Library Imports
from PySide import QtCore, QtGui
import pickle

import os

from ht.sohohooks.aovs import models, utils
from ht.sohohooks.aovs.aov import AOV, AOVGroup
from ht.sohohooks.aovs.manager import findOrCreateSessionAOVManager

import ht.sohohooks.aovs.dialogs

class AOVFilterWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(AOVFilterWidget, self).__init__(parent)

        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QtGui.QLabel("Filter"))

        self.field = QtGui.QLineEdit()
        self.field.setToolTip("Filter the list of AOVs by name.")
        layout.addWidget(self.field)

        self.setLayout(layout)


# =============================================================================
# AOV CHOICES
# =============================================================================

class AOVSelectTreeWidget(QtGui.QTreeView):

    selectionChangedSignal = QtCore.Signal()

    def __init__(self, parent=None):

        super(AOVSelectTreeWidget, self).__init__(parent)

        self.root = models.TreeNode()

        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

        manager = findOrCreateSessionAOVManager()

        if manager.groups:
            groups_node = models.FolderNode("Groups", self.root)

            groups = manager.groups

            for group in groups.itervalues():
                group_node = models.AOVGroupNode(group, groups_node)

                for aov in group.aovs:
                    models.AOVNode(aov, group_node)

        if manager.aovs:
            aovs_node = models.FolderNode("AOVs", self.root)

            aovs = manager.aovs

            for aov in aovs:
                models.AOVNode(aov, aovs_node)

        model = models.AOVSelectModel(self.root)
        self.proxy_model = models.LeafFilterProxyModel()
        self.proxy_model.setSourceModel(model)
        self.setModel(self.proxy_model)

        self.setAlternatingRowColors(True)
        self.setHeaderHidden(True)
        self.setDragEnabled(True)

        self.expandAll()


        QtCore.QObject.connect(
            self.selectionModel(),
            QtCore.SIGNAL("selectionChanged(QItemSelection, QItemSelection)"),
            self.selectionChange
        )


        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openMenu)

    def insertAOV(self, aov):
        self.model().sourceModel().insertAOV(aov)

    def insertGroup(self, group):
        self.model().sourceModel().insertGroup(group)

    def selectionChange(self, selected, deselected):
        self.selectionChangedSignal.emit()

    def getSelectedNodes(self):
        nodes = []

        indexes = self.selectionModel().selectedIndexes()

        model = self.model()

        if indexes:
            for index in indexes:
                index = model.mapToSource(index)
                nodes.append(model.sourceModel().getNode(index))

        return nodes

    def openMenu(self, position):
        indices = self.selectedIndexes()

        menu = QtGui.QMenu(self)


        show_expand = False
        show_collapse = False

        for idx in indices:
            src_idx = self.model().mapToSource(idx)
            node = src_idx.internalPointer()

            if isinstance(node, models.AOVGroupNode):
                if self.isExpanded(idx):
                    show_collapse = True
                else:
                    show_expand = True

        if show_collapse:
            menu.addAction(
                "Collapse",
                self.collapseSelected,
                QtGui.QKeySequence(QtCore.Qt.Key_Left)
            )

        if show_expand:
            menu.addAction(
                "Expand",
                self.expandSelected,
                QtGui.QKeySequence(QtCore.Qt.Key_Right)
            )

        menu.addAction(
            "Collapse All",
            self.collapseBelow
        )

        menu.addAction(
            "Expand All",
            self.expandBelow
        )

        menu.addSeparator()

        menu.addAction(
            "Select All",
            self.selectAll,
            QtGui.QKeySequence.SelectAll
        )

        menu.addSeparator()

        menu.addAction(
            "Install",
            self.installSelected,
            QtGui.QKeySequence(QtCore.Qt.Key_I),
        )

        menu.addAction(
            "Uninstall",
            self.uninstallSelected,
            QtGui.QKeySequence(QtCore.Qt.Key_U),
        )

        menu.exec_(self.mapToGlobal(position))

    def collapseSelected(self):
        indexes = self.selectedIndexes()

        for index in reversed(indexes):
            self.collapse(index)

    def expandSelected(self):
        indexes = self.selectedIndexes()

        for index in reversed(indexes):
            self.expand(index)

    def _expandIndex(self, index):
        self.expand(index)

        if self.model().hasChildren(index):
            for i in range(self.model().rowCount(index)):
                idx = self.model().index(i, 0, index)
                self._expandIndex(idx)


    def expandBelow(self):
        indexes = self.selectedIndexes()

        for index in indexes:
            self._expandIndex(index)

    def _collapseIndex(self, index):
        self.collapse(index)

        if self.model().hasChildren(index):
            for i in range(self.model().rowCount(index)):
                idx = self.model().index(i, 0, index)
                self._collapseIndex(idx)

    def collapseBelow(self):
        indexes = self.selectedIndexes()

        for index in indexes:
            self._collapseIndex(index)

    def installSelected(self):
        nodes = self.getSelectedNodes()

        if nodes:
            self.parent().installSignal.emit(nodes)

    def uninstallSelected(self):
        nodes = self.getSelectedNodes()

        if nodes:
            self.parent().removeSignal.emit(nodes)

    def keyPressEvent(self, event):
        key = event.key()

        if key == QtCore.Qt.Key_I:
            self.installSelected()

        elif key == QtCore.Qt.Key_U:
            self.uninstallSelected()

        super(AOVSelectTreeWidget, self).keyPressEvent(event)


class AOVMoveWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(AOVMoveWidget, self).__init__(parent)

        layout = QtGui.QVBoxLayout()
        layout.addStretch(1)

        self.to_right = QtGui.QPushButton("")
        self.to_right.setIcon(
            QtGui.QIcon(
                ":ht/rsc/icons/sohohooks/aovs/move_to_right.png"
            )
        )
        self.to_right.setIconSize(QtCore.QSize(14, 14))
        self.to_right.setMaximumSize(QtCore.QSize(20, 20))
        self.to_right.setToolTip("Add selected to list.")
        self.to_right.setEnabled(False)
        self.to_right.setFlat(True)

        layout.addWidget(self.to_right, alignment=QtCore.Qt.AlignVCenter)


        self.to_left = QtGui.QPushButton("")
        self.to_left.setIcon(
            QtGui.QIcon(
                ":ht/rsc/icons/sohohooks/aovs/move_to_left.png"
            )
        )
        self.to_left.setIconSize(QtCore.QSize(14, 14))
        self.to_left.setMaximumSize(QtCore.QSize(20, 20))
        self.to_left.setToolTip("Remove selected from list.")
        self.to_left.setEnabled(False)
        self.to_left.setFlat(True)

        layout.addWidget(self.to_left, alignment=QtCore.Qt.AlignVCenter)
        layout.addStretch(1)

        layout.setContentsMargins(0,0,0,0)

        self.setLayout(layout)


    def enableHandler(self, contains):
        self.to_left.setEnabled(contains)
        self.to_right.setEnabled(not contains)

    def disableHandler(self):
        self.to_left.setEnabled(False)
        self.to_right.setEnabled(False)


class AvailableAOVsToolBar(QtGui.QToolBar):

    def __init__(self, parent=None):
        super(AvailableAOVsToolBar, self).__init__(parent)

        self.setStyleSheet("QToolBar {border: 0;}")
        self.setIconSize(QtCore.QSize(24, 24))


        new_aov_action = QtGui.QAction(
            QtGui.QIcon(":ht/rsc/icons/sohohooks/aovs/create_aov.png"),
            "Create new AOV.",
            self,
            triggered=self.createNewAOV
        )

        new_aov_button = QtGui.QToolButton(self)
        new_aov_button.setDefaultAction(new_aov_action)
        self.addWidget(new_aov_button)


        new_group_action = QtGui.QAction(
            QtGui.QIcon(":ht/rsc/icons/sohohooks/aovs/create_group.png"),
            "Create a new AOV group.",
            self,
            triggered=self.createNewGroup
        )

        new_group_button = QtGui.QToolButton(self)
        new_group_button.setDefaultAction(new_group_action)
        self.addWidget(new_group_button)


        load_file_action = QtGui.QAction(
            QtGui.QIcon(":ht/rsc/icons/sohohooks/aovs/file.png"),
            "Load AOVs from a .json file.",
            self,
            triggered=self.loadJsonFile
        )

        load_file_button = QtGui.QToolButton(self)
        load_file_button.setDefaultAction(load_file_action)
        self.addWidget(load_file_button)

        self.new_aov_dialog = ht.sohohooks.aovs.dialogs.NewAOVDialog()

    def createNewAOV(self):
        self.new_aov_dialog.show()


    def createNewGroup(self):
        pass

    def loadJsonFile(self):
        import hou
        b = hou.ui.curDesktop().createFloatingPane(
            hou.paneTabType.HelpBrowser
        )

        b.displayHelpPath("pypanel/aov_manager")
#        manager = findOrCreateSessionAOVManager()

#        path = hou.ui.selectFile()

#        path = os.path.expandvars(path)

#        if os.path.exists(path):
#            manager.load(path)


class AOVSelectWidget(QtGui.QWidget):

    installSignal = QtCore.Signal(models.AOVBaseNode)
    removeSignal = QtCore.Signal(models.AOVBaseNode)

    def __init__(self, parent=None):
        super(AOVSelectWidget, self).__init__(parent)

        layout = QtGui.QHBoxLayout()

        tree_layout = QtGui.QVBoxLayout()

        bold_font = QtGui.QFont()
        bold_font.setBold(True)

        label = QtGui.QLabel("Available AOVs")
        label.setFont(bold_font)
        tree_layout.addWidget(label)


        self.tree = AOVSelectTreeWidget(parent=self)
        tree_layout.addWidget(self.tree)

        self.filter = AOVFilterWidget()
        tree_layout.addWidget(self.filter)

        QtCore.QObject.connect(
            self.filter.field,
            QtCore.SIGNAL("textChanged(QString)"),
            self.tree.proxy_model.setFilterWildcard
        )

        self.toolbar = AvailableAOVsToolBar(parent=self)
        tree_layout.addWidget(self.toolbar)

        layout.addLayout(tree_layout)


        manager = findOrCreateSessionAOVManager()

        self.toolbar.new_aov_dialog.newAOVSignal.connect(
            manager.addAOV
        )

        self.move = AOVMoveWidget()
        layout.addWidget(self.move)

        self.setLayout(layout)


        self.move.to_left.clicked.connect(self.emitRemoveSignal)
        self.move.to_right.clicked.connect(self.emitInstallSignal)

    def getSelectedNodes(self):
        return self.tree.getSelectedNodes()

    def emitInstallSignal(self):
        nodes = self.getSelectedNodes()

        if nodes:# is not None:
            self.installSignal.emit(nodes)

    def emitRemoveSignal(self):
        nodes = self.getSelectedNodes()

        if nodes:# is not None:
            self.removeSignal.emit(nodes)



# =============================================================================
# AOVS TO APPLY
# =============================================================================





class AOVsToAddTreeWidget(QtGui.QTreeView):

    def __init__(self, parent=None):

        super(AOVsToAddTreeWidget, self).__init__(parent)

        self.setAlternatingRowColors(True)
        self.setHeaderHidden(True)

        self.setAcceptDrops(True)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

        self.root = models.TreeNode(None)

        model = models.AOVsToAddModel(self.root)
        self.proxy_model = models.LeafFilterProxyModel()
        self.proxy_model.setSourceModel(model)
        self.setModel(self.proxy_model)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openMenu)

    def dragEnterEvent(self, event):
        if False and event.mimeData().hasFormat("text/csv"):
            event.acceptProposedAction()
        else:
            event.ignore()
#        if event.mimeData().hasFormat("text/csv"):
#            data = pickle.loads(event.mimeData().data("text/csv"))
#            event.acceptProposedAction()

#        else:
#            super(AOVsToAddTreeWidget, self).dragEnterEvent(event)

#    def dragMoveEvent(self, event):
#        if False and event.mimeData().hasFormat("text/csv"):
#            event.accept()
#        else:
#            event.ignore()
#        super(AOVsToAddTreeWidget, self).dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat("text/csv"):
            data = pickle.loads(event.mimeData().data("text/csv"))

            # Flatten any data when moving with Ctrl.
            if event.keyboardModifiers() == QtCore.Qt.ControlModifier:
                data = utils.flattenList(data)

                event.mimeData().setData("text/csv", pickle.dumps(data))

#            self.model().insertRows(data)

#            event.acceptProposedAction()
#            pass

#        else:

        return super(AOVsToAddTreeWidget, self).dropEvent(event)

    def keyPressEvent(self, event):
        key = event.key()

        if key == QtCore.Qt.Key_Delete:
            self.removeSelected()

        elif key == QtCore.Qt.Key_E:
            self.extractSelected()

        super(AOVsToAddTreeWidget, self).keyPressEvent(event)


    def extractSelected(self, plane_groups=None):
        indexes = self.selectedIndexes()

        for index in reversed(indexes):
            row = index.row()

            idx = self.model().mapToSource(index)

            node = idx.internalPointer()

            if isinstance(node, models.AOVNode):
                continue

            group = node.group

            aovs = reversed(group.aovs)

            self.model().removeRows(index)
            self.model().sourceModel().insertRows(aovs, row)


    def removeSelected(self):
        indexes = self.selectedIndexes()

        for idx in reversed(indexes):
            self.model().removeRows(idx)


    def collapseSelected(self):
        indexes = self.selectedIndexes()

        for index in indexes:
            self.collapse(index)

    def expandSelected(self):
        indexes = self.selectedIndexes()

        for index in indexes:
            self.expand(index)


    def openMenu(self, position):
        indices = self.selectedIndexes()

        menu = QtGui.QMenu(self)

        # Expand/collapse

        show_expand = False
        show_collapse = False

        for idx in indices:
            src_idx = self.model().mapToSource(idx)
            node = src_idx.internalPointer()

            if isinstance(node, models.AOVGroupNode):
                if self.isExpanded(idx):
                    show_collapse = True
                else:
                    show_expand = True

        if show_collapse:
            menu.addAction(
                "Collapse",
                self.collapseSelected,
                QtGui.QKeySequence(QtCore.Qt.Key_Left)
            )

        if show_expand:
            menu.addAction(
                "Expand",
                self.expandSelected,
                QtGui.QKeySequence(QtCore.Qt.Key_Right)
            )

        if show_collapse or show_expand:
            menu.addAction(
                "Collapse All",
                self.collapseAll
            )

            menu.addAction(
                "Expand All",
                self.expandAll
            )

            menu.addSeparator()

        menu.addAction(
            "Select All",
            self.selectAll,
            QtGui.QKeySequence.SelectAll
        )

        menu.addAction(
            "Delete",
            self.removeSelected,
            QtGui.QKeySequence.Delete,
        )

        menu.addSeparator()

        show_extract = False

        for idx in indices:
            idx = self.model().mapToSource(idx)
            node = idx.internalPointer()

            if isinstance(node, models.AOVGroupNode):
                show_extract = True
                break

        if show_extract:
            extract_action = menu.addAction(
                "Extract AOVs from group",
                self.extractSelected,
                QtGui.QKeySequence(QtCore.Qt.Key_E),
            )


        menu.exec_(self.mapToGlobal(position))



class AOVsToAddToolBar(QtGui.QToolBar):

    applySignal = QtCore.Signal(bool)
    installSignal = QtCore.Signal(list)

    def __init__(self, parent=None):
        super(AOVsToAddToolBar, self).__init__(parent)

        self._apply_as_parms = False

        self.setStyleSheet("QToolBar {border: 0;}")
        self.setIconSize(QtCore.QSize(24, 24))

        # Apply action and button
        apply_action = QtGui.QAction(
            QtGui.QIcon(":ht/rsc/icons/sohohooks/aovs/apply.png"),
            "Apply",
            self,
            triggered=self.applyToNodes
        )

        apply_action.setToolTip("Apply AOVs to selected nodes.")


        apply_button = QtGui.QToolButton(self)
        apply_button.setDefaultAction(apply_action)

        self.addWidget(apply_button)

        # Does this need to be attached to self?
        self.apply_menu = QtGui.QMenu(self)

        action_group = QtGui.QActionGroup(self.apply_menu, exclusive=True)

        action1 = QtGui.QAction(
            "At rendertime",
            action_group,
            checkable=True,
            triggered=self.setAtRendertime
        )

        action_group.addAction(action1)

        action2 = QtGui.QAction(
            "As parameters",
            action_group,
            checkable=True,
            triggered=self.setAsParameters
        )

        action_group.addAction(action2)

        action1.setChecked(True)


        self.apply_menu.addAction(action1)
        self.apply_menu.addAction(action2)

        apply_button.setMenu(self.apply_menu)



        load_action = QtGui.QAction(
            QtGui.QIcon(":ht/rsc/icons/sohohooks/aovs/from_node.png"),
            "Load AOVs from a node",
            self,
            triggered=self.loadFromNode
        )

        load_button = QtGui.QToolButton(self)
        load_button.setDefaultAction(load_action)
        self.addWidget(load_button)


        new_group_action = QtGui.QAction(
            QtGui.QIcon(":ht/rsc/icons/sohohooks/aovs/create_group.png"),
            "Create a new group from chosen AOVs.",
            self,
            triggered=self.createNewGroup
        )

        new_group_button = QtGui.QToolButton(self)
        new_group_button.setDefaultAction(new_group_action)
        self.addWidget(new_group_button)


    def loadFromNode(self):
        nodes = _findSelectedMantraNodes()

        if not nodes:
            return

        mantra = nodes[0]

        manager = findOrCreateSessionAOVManager()

        items = []

        if mantra.parm("auto_aovs") is not None:
            value = mantra.evalParm("auto_aovs")
            items.extend(manager.getAOVsFromString(value))

        self.installSignal.emit(items)

    def createNewGroup(self):
        pass

    def setAsParameters(self):
        self._apply_as_parms = True

    def setAtRendertime(self):
        self._apply_as_parms = False

    def applyToNodes(self):
        self.applySignal.emit(self._apply_as_parms)


class AOVsToAddWidget(QtGui.QWidget):

    updateEnabledSignal = QtCore.Signal()

    def __init__(self, parent=None):
        super(AOVsToAddWidget, self).__init__(parent)

        layout = QtGui.QVBoxLayout()

        bold_font = QtGui.QFont()
        bold_font.setBold(True)

        label = QtGui.QLabel("AOVs to Add")
        label.setFont(bold_font)
        layout.addWidget(label)

        # Tree View

        self.tree = AOVsToAddTreeWidget()
        layout.addWidget(self.tree)

        self.filter = AOVFilterWidget()
        layout.addWidget(self.filter)

        QtCore.QObject.connect(
            self.filter.field,
            QtCore.SIGNAL("textChanged(QString)"),
            self.tree.proxy_model.setFilterWildcard
        )

        # Tool bar
        self.toolbar = AOVsToAddToolBar(parent=self)
        layout.addWidget(self.toolbar)

        self.setLayout(layout)

        self.toolbar.applySignal.connect(self.applyToNodes)
        self.toolbar.installSignal.connect(self.installItems)

        self.tree.model().sourceModel().rowsInserted.connect(self.dataUpdated)
        self.tree.model().sourceModel().rowsRemoved.connect(self.dataUpdated)




    def dataUpdated(self, index, start, end):
        self.updateEnabledSignal.emit()


    def applyToNodes(self, apply_as_parms):
        nodes = _findSelectedMantraNodes()

        if not nodes:
            return

        elements = self.tree.model().sourceModel().items

        if apply_as_parms:
            utils.applyElementsAsParms(elements, nodes)

        else:
            utils.applyElementsAsString(elements, nodes)


    def installItems(self, items):
        self.tree.model().insertRows(items)

    def installListener(self, nodes):
        items = []

        for node in nodes:
            if isinstance(node, models.FolderNode):
                items.extend(node.items)

            else:
                items.append(node.item)

        self.installItems(items)

    def removeListener(self, nodes):
        for node in nodes:
            index = self.nodeIndexInModel(node)

            if index is not None:
                self.tree.model().removeRows(index)

    def nodeIndexInModel(self, node):
        model = self.tree.model()

        root = QtCore.QModelIndex()

        if model.hasChildren(root):
            for i in range(model.rowCount(root)):
                index = model.index(i, 0, root)
                item = model.mapToSource(index).internalPointer()

                if item == node:
                    return index

        return None

def _findSelectedMantraNodes():
    import hou

    nodes = hou.selectedNodes()

    mantra_type = hou.nodeType("Driver/ifd")

    nodes = [node for node in nodes if node.type() == mantra_type]

    if not nodes:
        hou.ui.displayMessage(
            "No mantra nodes selected.",
            severity=hou.severityType.Error
        )

    return tuple(nodes)

