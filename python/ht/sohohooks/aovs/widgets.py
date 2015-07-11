


# Standard Library Imports
from PySide import QtCore, QtGui
import pickle

import ht.sohohooks.models

from ht.sohohooks.aovs import AOV, AOVGroup
from ht.sohohooks.planes import RenderPlane, RenderPlaneGroup, buildPlaneGroups
from ht.sohohooks.planes import applyToNodeAsParms, flattenList, listAsString

# REMOVE THIS ONCE ICONS STORED
import hou

class DescriptionTitleWidget(QtGui.QWidget):

    def __init__(self, title, parent=None):
	super(DescriptionTitleWidget, self).__init__(parent)

	layout = QtGui.QVBoxLayout()

	layout.addWidget(QtGui.QLabel(title))

	name_layout = QtGui.QHBoxLayout()

	self.icon_label = QtGui.QLabel()
	name_layout.addWidget(self.icon_label)

	f = QtGui.QFont()
	f.setBold(True)

	self.name_label = QtGui.QLabel()
	self.name_label.setFont(f)
	name_layout.addWidget(self.name_label)

	name_layout.setAlignment(QtCore.Qt.AlignLeft)

	layout.addLayout(name_layout)

	self.file_path = QtGui.QLabel()
	layout.addWidget(self.file_path)

	self.setLayout(layout)

    def setFromElement(self, element):
	if isinstance(element, AOV):
	    self.name_label.setText(element.variable)

	    pm = QtGui.QPixmap(
		    ":houdini/planeviewer/rsc/icons/{0}.png".format(element.vextype)
	    )

	else:
	    self.name_label.setText(element.name)

	    pm = QtGui.QPixmap(
		    ":houdini/planeviewer/rsc/icons/plane.png"
	    )

	pm = pm.scaled(36, 36)

	self.icon_label.setPixmap(pm)

#	self.file_path.setText(element.filePath)
	self.file_path.setText("some path")






class AOVTabWidget(QtGui.QWidget):

    def __init__(self, parent=None):
	super(AOVTabWidget, self).__init__(parent)

        self.splitter = QtGui.QSplitter()


	aov_list_widget = QtGui.QWidget()
        aov_list_layout = QtGui.QVBoxLayout()

	self.aov_view = QtGui.QListView()

	self.aov_view.setAlternatingRowColors(True)
	self.aov_view.setStyleSheet("alternate-background-color: rgb(46, 46 ,46);")

	model = ht.sohohooks.models.AOVListModel()

	self.proxy_model = QtGui.QSortFilterProxyModel()
        self.proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy_model.setSourceModel(model)

        self.aov_view.setModel(self.proxy_model)
        self.proxy_model.sort(0)


	filter_layout = QtGui.QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.addWidget(QtGui.QLabel("Filter"))


        # Construct the filter text field.
        self.filter_field = QtGui.QLineEdit()
        self.filter_field.setToolTip(
            "Filter the list of groups by name."
        )

        filter_layout.addWidget(self.filter_field)


        QtCore.QObject.connect(
            self.filter_field,
            QtCore.SIGNAL("textChanged(QString)"),
            self.proxy_model.setFilterRegExp
        )


	aov_list_layout.addWidget(QtGui.QLabel("Available AOVs"))
        aov_list_layout.addWidget(self.aov_view)
        aov_list_layout.addLayout(filter_layout)

        aov_list_widget.setLayout(aov_list_layout)

	self.splitter.addWidget(aov_list_widget)


	self.title_widget = DescriptionTitleWidget(
	    "AOV Description"
	)

	description_layout = QtGui.QVBoxLayout()
	description_layout.addWidget(self.title_widget)

	self.table = QtGui.QTableView()

	self.table.verticalHeader().hide()


	idx = self.proxy_model.index(0,0)
	current = self.proxy_model.mapToSource(idx)
	row = current.row()
	aov = self.proxy_model.sourceModel().aovs[row]

	self.table.setModel(ht.sohohooks.models.AOVDisplayTableModel(aov))


	self.table.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)


	description_layout.addWidget(self.table)

	description_widget = QtGui.QWidget()
	description_widget.setLayout(description_layout)

	self.splitter.addWidget(description_widget)


	layout = QtGui.QHBoxLayout()
	layout.addWidget(self.splitter)

	self.setLayout(layout)

	QtCore.QObject.connect(
	    self.aov_view.selectionModel(),
	    QtCore.SIGNAL("currentChanged(QModelIndex, QModelIndex)"),
	    self.setSelection
	)

	self.setTitleFromAOV(aov)

    def setSelection(self, current, old):
	current = self.proxy_model.mapToSource(current)

	row = current.row()
	aov = self.proxy_model.sourceModel().aovs[row]

	model = self.table.model()

	model.layoutAboutToBeChanged.emit()
	model.plane = aov
	model.layoutChanged.emit()

	self.setTitleFromAOV(aov)

    def setTitleFromAOV(self, aov):
	self.title_widget.setFromElement(aov)


class GroupTabWidget(QtGui.QWidget):

    def __init__(self, parent=None):
	super(GroupTabWidget, self).__init__(parent)

        self.splitter = QtGui.QSplitter()


	group_list_widget = QtGui.QWidget()
        group_list_layout = QtGui.QVBoxLayout()

	self.group_view = QtGui.QListView()

	self.group_view.setAlternatingRowColors(True)
	self.group_view.setStyleSheet("alternate-background-color: rgb(46, 46 ,46);")

	model = ht.sohohooks.models.AOVGroupListModel()

	self.proxy_model = QtGui.QSortFilterProxyModel()
        self.proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy_model.setSourceModel(model)

        self.group_view.setModel(self.proxy_model)
        self.proxy_model.sort(0)


	filter_layout = QtGui.QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.addWidget(QtGui.QLabel("Filter"))


        # Construct the filter text field.
        self.filter_field = QtGui.QLineEdit()
        self.filter_field.setToolTip(
            "Filter the list of groups by name."
        )

        filter_layout.addWidget(self.filter_field)


        QtCore.QObject.connect(
            self.filter_field,
            QtCore.SIGNAL("textChanged(QString)"),
            self.proxy_model.setFilterRegExp
        )


	group_list_layout.addWidget(QtGui.QLabel("Available Groups"))
        group_list_layout.addWidget(self.group_view)
        group_list_layout.addLayout(filter_layout)

        group_list_widget.setLayout(group_list_layout)

	self.splitter.addWidget(group_list_widget)

	description_layout = QtGui.QVBoxLayout()

	self.title_widget = DescriptionTitleWidget(
	    "Group Members"
	)

	description_layout.addWidget(self.title_widget)

	idx = self.proxy_model.index(0,0)
	current = self.proxy_model.mapToSource(idx)
	row = current.row()
	group = self.proxy_model.sourceModel().groups[row]

	self.members = QtGui.QListView()
	self.members.setModel(ht.sohohooks.models.GroupMemberModel(group))

	self.members.setAlternatingRowColors(True)
	self.members.setStyleSheet("alternate-background-color: rgb(46, 46 ,46);")

	description_layout.addWidget(self.members)

	description_widget = QtGui.QWidget()
	description_widget.setLayout(description_layout)

	self.splitter.addWidget(description_widget)

	layout = QtGui.QHBoxLayout()
	layout.addWidget(self.splitter)

	self.setLayout(layout)


	QtCore.QObject.connect(
	    self.group_view.selectionModel(),
	    QtCore.SIGNAL("currentChanged(QModelIndex, QModelIndex)"),
	    self.setSelection
	)

	self.setTitleFromGroup(group)


    def setSelection(self, current, old):
	current = self.proxy_model.mapToSource(current)

	row = current.row()
	group = self.proxy_model.sourceModel().groups[row]

	model = self.members.model()

	model.layoutAboutToBeChanged.emit()
	model.group = group
	model.layoutChanged.emit()

	self.setTitleFromGroup(group)

    def setTitleFromGroup(self, group):
	self.title_widget.setFromElement(group)


class AOVSelectorWidget(QtGui.QTreeView):


    def __init__(self, parent=None):
        super(AOVSelectorWidget, self).__init__(parent)

        self.setAlternatingRowColors(True)
        self.setHeaderHidden(True)

        self.setAcceptDrops(True)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

        self.root = ht.sohohooks.models.TreeNode(None)


#        model = ht.sohohooks.models.PlaneTreeModel(self.root)
#        self.setModel(model)

#        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
#        self.customContextMenuRequested.connect(self.openMenu)















class AOVTreeWidget(QtGui.QTreeView):

    def __init__(self, parent=None):

        super(AOVTreeWidget, self).__init__(parent)

        self.setAlternatingRowColors(True)
        self.setHeaderHidden(True)

        self.setAcceptDrops(True)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

        self.root = ht.sohohooks.models.TreeNode(None)

        model = ht.sohohooks.models.PlaneTreeModel(self.root)
        self.setModel(model)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openMenu)



    def addItemToTree(self, item):
        self.model().insertRows([item])

    def treeContainsItem(self, item):
        model_items = self.model().items

        return item in model_items

    def removeItemFromTree(self, item):
        index = self.findItemModelIndex(item)

        if index is not None:
            self.model().removeRows(index)


    def findItemModelIndex(self, item):
        index = None

        model_items = self.model().items

        if item in model_items:
            index = self.model().createIndex(model_items.index(item), 0)

        return index

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("text/csv"):
            data = pickle.loads(event.mimeData().data("text/csv"))
            event.acceptProposedAction()

        else:
            super(LayerListWidget, self).dragEnterEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat("text/csv"):
            data = pickle.loads(event.mimeData().data("text/csv"))

            if event.keyboardModifiers() == QtCore.Qt.ControlModifier and isinstance(data, AOVGroup):
                self.model().insertRows(data.aovs)

            else:
                self.model().insertRows([data])

            event.acceptProposedAction()

        else:
            super(LayerListWidget, self).dropEvent(event)

    def keyPressEvent(self, event):
        key = event.key()

        if key == QtCore.Qt.Key_Delete:
            self.removeSelected()

        elif key == QtCore.Qt.Key_E:
            self.extractSelected()

        super(AOVTreeWidget, self).keyPressEvent(event)


    def extractSelected(self, plane_groups=None):
        indexes = self.selectedIndexes()

        for index in reversed(indexes):
            row = index.row()

            item = self.model().items[row]

            if isinstance(item, AOV):
                continue

            aovs = reversed(item.aovs)

            self.model().removeRows(index)
            self.model().insertRows(aovs, row)


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

        items = self.model().items

        # Expand/collapse

        show_expand = False
        show_collapse = False

        for idx in indices:
            item = items[idx.row()]

            if isinstance(item, AOVGroup):
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

        show_extract = False

        for idx in indices:
            item = items[idx.row()]

            if isinstance(item, AOVGroup):
                show_extract = True
                break

        if show_extract:
            extract_action = menu.addAction(
                "Extract aovs from group",
                self.extractSelected,
                QtGui.QKeySequence(QtCore.Qt.Key_E),
            )


        menu.exec_(self.mapToGlobal(position))



class TreeToolBar(QtGui.QToolBar):

    def __init__(self, source, parent=None):
        super(TreeToolBar, self).__init__(parent)

        self._source = source

        self._apply_as_parms = False

        self.setStyleSheet("QToolBar {border: 0;}")
        self.setIconSize(QtCore.QSize(24, 24))

        # Apply action and button
        apply_action = QtGui.QAction(
            QtGui.QIcon(hou.findFile("help/icons/large/DATATYPES/boolean.png")),
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
            QtGui.QIcon(hou.findFile("help/icons/large/COMMON/file.png")),
            "Load from",
            self,
            triggered=self.applyToNodes
        )


        load_menu = QtGui.QMenu(self)

        load_group = QtGui.QActionGroup(load_menu, exclusive=True)



        from_node = QtGui.QAction(
            "From node",
            load_group,
            checkable=True,
            triggered=self.loadFromNode
        )


        load_group.addAction(from_node)


        from_file = QtGui.QAction(
            "From file",
            load_group,
            checkable=True,
            triggered=self.loadFromFile
        )

        load_group.addAction(from_file)

        from_node.setChecked(True)

        load_menu.addAction(from_node)
        load_menu.addAction(from_file)




        load_action.setToolTip("Load AOVs from a file or node.")
        load_action.setMenu(load_menu)

        c = QtGui.QToolButton(self)
        c.setDefaultAction(load_action)

        self.addWidget(c)











    @property
    def source(self):
        return self._source


    def loadFromNode(self):
        pass

    def loadFromFile(self):
        pass


    def setAsParameters(self):
        self._apply_as_parms = True

    def setAtRendertime(self):
        self._apply_as_parms = False

    def applyToNodes(self):
        nodes = self._getSelectedNodes()

        if self._apply_as_parms:
            self._applyAsParms(nodes)

        else:
            self._applyAsString(nodes)


    def _applyAsString(self, nodes):
        elements = self.source.model().items

        value = listAsString(elements)

        for node in nodes:
            if not node.parm("auto_aovs"):
                parm_template = hou.StringParmTemplate(
                    "auto_aovs",
                    "Automatic AOVs",
                    1,
                )

                node.addSpareParmTuple(parm_template)

            parm = node.parm("auto_aovs")
            parm.set(value)


    def _applyAsParms(self, nodes):
        elements = self.source.model().items
        aovs = flattenList(elements)

        for node in nodes:
            applyToNodeAsParms(node, aovs)



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




class AOVsToAddWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(AOVsToAddWidget, self).__init__(parent)


        layout = QtGui.QVBoxLayout()

        bold_font = QtGui.QFont()
        bold_font.setBold(True)

        label = QtGui.QLabel("AOVs to Add")
        label.setFont(bold_font)
        layout.addWidget(label)

        # Tree View

        self.tree = AOVTreeWidget()

        layout.addWidget(self.tree)



        # Tool bar

        toolbar = TreeToolBar(self.tree, parent=self)






        layout.addWidget(toolbar)

        self.setLayout(layout)


    def addItemToTree(self, item):
        self.tree.addItemToTree(item)

    def findItemModelIndex(self, item):
        return self.tree.findItemModelIndex(item)

    def treeContainsItem(self, item):
        return self.tree.treeContainsItem(item)

    def removeItemFromTree(self, item):
        self.tree.removeItemFromTree(item)


