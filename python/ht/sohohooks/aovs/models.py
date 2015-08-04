
# =============================================================================
# IMPORTS
# =============================================================================

# Standard Library Imports
from PySide import QtCore, QtGui

import pickle

import ht.ui.icons

from ht.sohohooks.aovs.aov import AOV, AOVGroup
from ht.sohohooks.aovs.manager import findOrCreateSessionAOVManager
from ht.sohohooks.aovs import utils


_ROW_TITLES = (
    "VEX Variable (variable)",
    "VEX Type (vextype)",
    "Channel Name (channel)",
    "Different File (planefile)",
    "Quantize (quantize)",
    "Sample Filter (sfilter)",
    "Pixel Filter (pfilter)",
    "Light Exports (lightexport)",
    "Light Mask (lightexport_scope)",
    "Light Selection (lightexport_select)",
)


# =============================================================================
# TREE NODES
# =============================================================================


class TreeNode(object):
    """The base node in a TreeListView.

    """

    def __init__(self, parent=None):
        self._children = []
        self._parent = parent

        # If we have a parent, add this node to the parent's list of children.
        if parent is not None:
            parent.addChild(self)

    # TODO: FIX THIS to be less ghetto
    def __cmp__(self, node):
        return cmp(self.name, node.name)

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self.name)

    @property
    def children(self):
        return self._children

    @property
    def icon(self):
        return QtGui.QIcon(":ht/rsc/icons/sohohooks/aovs/root.png")

    @property
    def name(self):
        return "root"

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        self._parent = parent

    @property
    def row(self):
        if self.parent is not None:
            return self.parent.children.index(self)

    def addChild(self, child):
        self._children.append(child)

        child.parent = self

    def insertChild(self, position, child):
        if position < 0 or position > len(self.children):
            return False

        self.children.insert(position, child)
        child.parent = self

        return True

    def removeAllChildren(self):
        self._children = []

    def removeChild(self, position):
        if position < 0 or position > len(self.children):
            return False

        child = self.children.pop(position)

        child.parent = None

        return True

    def tooltip(self):
        return


class FolderNode(TreeNode):
    def __init__(self, name, parent=None):
        super(FolderNode, self).__init__(parent)

        self._name = name

    @property
    def icon(self):
        return QtGui.QIcon(":ht/rsc/icons/sohohooks/aovs/folder.png")

    @property
    def items(self):
        return [child.item for child in self.children]

    @property
    def name(self):
        return self._name


class AOVBaseNode(TreeNode):
    def __init__(self, item, parent=None):
        super(AOVBaseNode, self).__init__(parent)

        self._item = item

    @property
    def item(self):
        return self._item

    @property
    def name(self):
        return self._item.name

    @property
    def path(self):
        return self._item.filePath


class AOVNode(AOVBaseNode):
    def __init__(self, aov, parent=None):
        super(AOVNode, self).__init__(aov, parent)

    @property
    def icon(self):
        return utils.getIconFromVexType(self.item.vextype)

    @property
    def name(self):
        return self.item.variable

    @property
    def aov(self):
        return self.item

    @property
    def group(self):
        return self.parent.group

    def tooltip(self):
        aov = self.aov

        lines = [
            "VEX Variable: {0}".format(aov.variable),
            "VEX Type: {0}".format(aov.vextype),
        ]

        if aov.channel is not None:
            lines.append("Channel Name: {0}".format(aov.channel))

        if aov.quantize is not None:
            lines.append("Quantize: {0}".format(aov.quantize))

        if aov.sfilter is not None:
            lines.append("Sample Filter: {0}".format(aov.sfilter))

        if aov.pfilter is not None:
            lines.append("Pixel Filter: {0}".format(aov.pfilter))

        if aov.componentexport:
            lines.append("\nExport variable for each component: {0}".format(aov.componentexport))
            lines.append("Export Components: {0}".format(", ".join(aov.components)))

        if aov.lightexport is not None:
            lines.append("\nLight Exports: {0}".format(aov.lightexport))
            lines.append("Light Mask: {0}".format(aov.lightexport_scope))
            lines.append("Light Selection: {0}".format(aov.lightexport_select))

        if aov.comment:
            lines.append("\nComment: {0}".format(aov.comment))

        if aov.priority > -1:
            lines.append("\nPriority: {0}".format(aov.priority))

        if aov.path is not None:
            lines.append("\n{0}".format(aov.path))

        return '\n'.join(lines)


class AOVGroupNode(AOVBaseNode):
    def __init__(self, group, parent=None):
        super(AOVGroupNode, self).__init__(group, parent)

    @property
    def icon(self):
        return utils.getIconFromGroup(self.group)

    @property
    def group(self):
        return self.item

    def tooltip(self):
        group = self.group

        lines = ["Name: {0}".format(group.name)]

        if group.comment:
            lines.append("\nComment: {0}".format(group.comment))

        if group.priority > -1:
            lines.append("\nPriority: {0}".format(group.priority))

        if group.icon is not None:
            lines.append("\nIcon: {0}".format(group.icon))

        if group.path is not None:
            lines.append("\n{0}".format(group.path))

        return '\n'.join(lines)

# =============================================================================
# PROXY MODELS
# =============================================================================


class LeafFilterProxyModel(QtGui.QSortFilterProxyModel):


    def __init__(self, parent=None):
        super(LeafFilterProxyModel, self).__init__(parent)


        self.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.setFilterRole(BaseAOVTreeModel.filterRole)

    def filterAcceptsRow(self, row_num, source_parent):
        if self.filter_accepts_row_itself(row_num, source_parent):
            return True

        # Traverse up all the way to root and check if any of them match
        if self.filter_accepts_any_parent(source_parent):
            return True

        return self.has_accepted_children(row_num, source_parent)

    def filter_accepts_row_itself(self, row_num, source_parent):
        return super(LeafFilterProxyModel, self).filterAcceptsRow(
            row_num,
            source_parent
        )

    def filter_accepts_any_parent(self, parent):
        ''' Traverse to the root node and check if any of the
            ancestors match the filter
        '''
        while parent.isValid():
            if self.filter_accepts_row_itself(parent.row(), parent.parent()):
                return True
            parent = parent.parent()

        return False

    def has_accepted_children(self, row_num, parent):
        ''' Starting from the current node as root, traverse all
            the descendants and test if any of the children match
        '''
        model = self.sourceModel()
        source_index = model.index(row_num, 0, parent)

        children_count =  model.rowCount(source_index)

        for i in xrange(children_count):
            if self.filterAcceptsRow(i, source_index):
                return True

        return False


    def insertRows(self, data, position=None, parent=QtCore.QModelIndex()):
	return self.sourceModel().insertRows(data)

    def removeRows(self, idx, parent=QtCore.QModelIndex()):
	return self.sourceModel().removeRows(
            self.mapToSource(idx),
            self.mapToSource(parent)
        )


# =============================================================================
# TREE MODELS
# =============================================================================

class BaseAOVTreeModel(QtCore.QAbstractItemModel):

    filterRole = QtCore.Qt.UserRole

    def __init__(self, root, parent=None):
        super(BaseAOVTreeModel, self).__init__(parent)

        self._root = root

    # =========================================================================

    @property
    def items(self):
        return [child.item for child in self.root.children]

    @property
    def root(self):
        return self._root

    # =========================================================================

    def columnCount(self, parent):
        return 1

    def rowCount(self, parent):
        if not parent.isValid():
            node = self.root
        else:
            node = parent.internalPointer()

        return len(node.children)

    def getNode(self, index):
        if index.isValid():
            node = index.internalPointer()
            if node:
                return node

        return self.root

    def index(self, row, column, parent):
        parent = self.getNode(parent)

        if row < len(parent.children):
            childItem = parent.children[row]

            if childItem:
                return self.createIndex(row, column, childItem)

        return QtCore.QModelIndex()

    def parent(self, index):
        node = self.getNode(index)

        parent = node.parent

        if parent == self.root:
            return QtCore.QModelIndex()

        return self.createIndex(parent.row, 0, parent)

    def data(self, index, role):
        if not index.isValid():
            return None

        # Get the tree node.
        node = index.internalPointer()
        parent = node.parent

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            # If the item is an AOV who has an explicit channel set
            # then display the channel as well.
            if isinstance(node, AOVNode):
                aov = node.item

                if aov.channel is not None:
                    return "{0} ({1})".format(aov.variable, aov.channel)

            return  node.name

        if role == QtCore.Qt.DecorationRole:
            return node.icon

        if role == QtCore.Qt.ToolTipRole:
            return node.tooltip()

        if role == QtCore.Qt.ForegroundRole:
            brush = QtGui.QBrush()

            if isinstance(parent, AOVGroupNode):
                brush.setColor(QtGui.QColor(131, 131, 131))
                return brush

            return None

        # TODO: type "Render", want to see regular Render_Time AND aov in group.
        if role == BaseAOVTreeModel.filterRole:
            if isinstance(node, FolderNode):
                return True

            if isinstance(node, AOVGroupNode):
                return node.name

            if isinstance(node.parent, AOVGroupNode):
                return True

            if isinstance(node, AOVNode):
                return node.name

            return True

class AOVSelectModel(BaseAOVTreeModel):

    def __init__(self, root, parent=None):
        super(AOVSelectModel, self).__init__(root, parent)

    def flags(self, index):
        if not index.isValid():
            return None

        node = index.internalPointer()
        parent = node.parent

        if isinstance(parent, AOVGroupNode):
            return QtCore.Qt.ItemIsEnabled

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled

    def mimeData(self, indexes):

        nodes = [self.getNode(index) for index in indexes]

        items = []

        for node in nodes:
            if isinstance(node, FolderNode):
                for child in node.children:
                    items.append(child.item)
            else:
                items.append(node.item)

        mime_data = QtCore.QMimeData()

        mime_data.setData("text/csv", pickle.dumps(items))

        return mime_data

    def findNamedFolder(self, name):
        node = self.getNode(QtCore.QModelIndex())

        for row in range(len(node.children)):
            child = node.children[row]

            if child.name == name:
                return self.createIndex(row, 0, child)

        return None

    def insertNamedFolder(self, name):

        parent = QtCore.QModelIndex()
        parentNode = self.getNode(parent)

        position = len(parentNode.children)

        self.beginInsertRows(parent, position, position)

        folder = FolderNode(name)
        parentNode.addChild(folder)

        self.endInsertRows()

        return self.findNamedFolder(name)

    def insertAOV(self, aov):
        index = self.findNamedFolder("AOVs")

        if index is None:
            index = self.insertNamedFolder("AOVs")

        parentNode = self.getNode(index)

        position = len(parentNode.children)

        self.beginInsertRows(index, position, position)

        AOVNode(aov, parentNode)

        self.endInsertRows()

        return True


    def insertGroup(self, group):
        index = self.findNamedFolder("Groups")

        if index is None:
            index = self.insertNamedFolder("Groups")

        parentNode = self.getNode(index)

        position = len(parentNode.children)

        self.beginInsertRows(index, position, position)

        group_node = AOVGroupNode(group, parentNode)

        for aov in group.aovs:
            AOVNode(aov, group_node)

        self.endInsertRows()

        return True

# =============================================================================

class AOVsToAddModel(BaseAOVTreeModel):

    def __init__(self, root, parent=None):
        super(AOVsToAddModel, self).__init__(root, parent)

    def flags(self, index):
        if not index.isValid():
            return None

        node = index.internalPointer()
        parent = node.parent

        if parent == self.root:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled

        if isinstance(parent, AOVGroupNode):
            return QtCore.Qt.ItemIsEnabled

        return 0


    def dropMimeData(self, data, action, row, column, parent):
        if not data.hasFormat("text/csv"):
            return False

        self.insertRows(pickle.loads(data.data("text/csv")))

        return True

    def insertRows(self, data, position=None, parent=QtCore.QModelIndex()):

        data = [item for item in data if item not in self.items]

        parentNode = self.getNode(parent)

        if position is None:
	    position = len(self.items)

        rows = len(data)

        if not rows:
            return False

	self.beginInsertRows(parent, position, position + rows - 1)

        for item in data:
            if isinstance(item, AOV):
                child_node = AOVNode(item)
                parentNode.insertChild(position, child_node)

            else:
                child_node = AOVGroupNode(item)

                parentNode.insertChild(position, child_node)

                for aov in item.aovs:
                    aov_node = AOVNode(aov, child_node)

	self.endInsertRows()

	return True

    # TODO: make better?  Accept multiple rows perhaps?
    def removeRows(self, idx, parent=QtCore.QModelIndex()):
        parentNode = self.getNode(parent)

	row = idx.row()

	self.beginRemoveRows(parent, row, row)

        parentNode.removeChild(row)

	self.endRemoveRows()

	return True


    # TODO: Update move left/right.
    def clear(self):
        self.beginResetModel()

        self.root.removeAllChildren()

        self.endResetModel()


class AOVGroupEditListModel(QtCore.QAbstractListModel):

    def __init__(self, parent=None):
	super(AOVGroupEditListModel, self).__init__(parent)

        manager = findOrCreateSessionAOVManager()
        self._aovs = manager.aovs

        self._checked = [False] * len(self._aovs)

    @property
    def aovs(self):
        return self._aovs

    def checkedAOVs(self):
        return [aov for checked, aov in zip(self._checked, self.aovs)
                if checked]

    def uncheckAll(self):
        self._checked = [False] * len(self._aovs)

    def rowCount(self, parent):
	return len(self.aovs)

    def data(self, index, role):
	row = index.row()
	value = self.aovs[row]

	if role == QtCore.Qt.DisplayRole:
	    return value.variable

        if role == QtCore.Qt.DecorationRole:
            return utils.getIconFromVexType(value.vextype)

        if role == QtCore.Qt.CheckStateRole:
            return self._checked[row]

    def setData(self, index, value, role):
        if role == QtCore.Qt.CheckStateRole:
            row = index.row()

            self._checked[row] = not self._checked[row]

            self.dataChanged.emit(index, index)

            return True

    def flags(self, index):
	return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable


class AOVInfoModel(QtCore.QAbstractTableModel):

    def __init__(self, parent=None):
        super(AOVInfoModel, self).__init__(parent)

        self._headers = []
        self._values = []

#        self.initDataFromAOV(aov)

    def initDataFromAOV(self, aov):
        self._headers = []
        self._values = []

        self._headers.append("VEX Variable")
        self._values.append(aov.variable)

        self._headers.append("VEX Type")
        self._values.append(aov.vextype)

        if aov.channel is not None:
            self._headers.append("Channel Name")
            self._values.append(aov.channel)

        if aov.quantize is not None:
            self._headers.append("Quantize")
            self._values.append(aov.quantize)

        if aov.sfilter is not None:
            self._headers.append("Sample Filter")
            self._values.append(aov.sfilter)

        if aov.pfilter is not None:
            self._headers.append("Pixel Filter")
            self._values.append(aov.pfilter)

        if aov.componentexport:
            self._headers.append("Export Each Component")
            self._values.append(str(aov.componentexport))

            if aov.components:
                self._headers.append("Export Components")
                self._values.append(", ".join(aov.components))

        if aov.lightexport is not None:
            self._headers.append("Light Exports")
            self._values.append(aov.lightexport)

            self._headers.append("Light Mask")
            self._values.append(aov.lightexport_scope)

            self._headers.append("Light Selection")
            self._values.append(aov.lightexport_select)


        if aov.priority > -1:
            self._headers.append("Priority")
            self._values.append(aov.priority)

        if aov.comment:
            self._headers.append("Comment")
            self._values.append(aov.comment)

        if aov.path is not None:
            self._headers.append("File Path")
            self._values.append(aov.path)

    def flags(self, index):
	return QtCore.Qt.ItemIsEnabled

    def columnCount(self, parent):
        return 2

    def rowCount(self, parent):
        return len(self._headers)

    def index(self, row, column, parent=QtCore.QModelIndex()):
        return self.createIndex(row, column, parent)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        column = index.column()

        if role == QtCore.Qt.DisplayRole:
            if column == 0:
                return self._headers[row]
            else:
                return self._values[row]



class AOVGroupInfoModel(QtCore.QAbstractTableModel):

    def __init__(self, parent=None):
        super(AOVGroupInfoModel, self).__init__(parent)

        self._headers = []
        self._values = []

    def initDataFromGroup(self, group):
        self._headers = []
        self._values = []

        self._headers.append("Name")
        self._values.append(group.name)

        if group.comment:
            self._headers.append("Comment")
            self._values.append(group.comment)

        if group.icon:
            self._headers.append("Icon")
            self._values.append(group.icon)

        if group.path is not None:
            self._headers.append("File Path")
            self._values.append(group.path)


    def flags(self, index):
	return QtCore.Qt.ItemIsEnabled

    def columnCount(self, parent):
        return 2

    def rowCount(self, parent):
        return len(self._headers)

    def index(self, row, column, parent=QtCore.QModelIndex()):
        return self.createIndex(row, column, parent)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        column = index.column()

        if role == QtCore.Qt.DisplayRole:
            if column == 0:
                return self._headers[row]
            else:
                return self._values[row]



class AOVMemberListModel(QtCore.QAbstractListModel):

    def __init__(self, parent=None):
	super(AOVMemberListModel, self).__init__(parent)

        self._aovs = []

        self._checked = [False] * len(self._aovs)

    @property
    def aovs(self):
        return self._aovs

    def rowCount(self, parent):
	return len(self.aovs)

    def data(self, index, role):
	row = index.row()
	value = self.aovs[row]

	if role == QtCore.Qt.DisplayRole:
	    return value.variable

        if role == QtCore.Qt.DecorationRole:
            return utils.getIconFromVexType(value.vextype)

    def flags(self, index):
	return QtCore.Qt.ItemIsEnabled

    def initDataFromGroup(self, group):
        self.beginResetModel()
        self._aovs = group.aovs
        self.endResetModel()

