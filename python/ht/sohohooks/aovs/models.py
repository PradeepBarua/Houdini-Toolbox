
# =============================================================================
# IMPORTS
# =============================================================================

# Standard Library Imports
from PySide import QtCore, QtGui

import pickle

import ht.ui.icons

from ht.sohohooks.aovs import AOV, AOVGroup
from ht.sohohooks.planes import buildPlaneGroups,_findPlaneDefinitions, RenderPlane, RenderPlaneGroup
import ht.sohohooks.manager


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
    "Light Selection (lightexport_select)"
)


def getIcon(obj):
    if isinstance(obj, AOV):
	vextype = obj.vextype

	return ":houdini/planeviewer/rsc/icons/{0}.png".format(vextype)

    return ":houdini/planeviewer/rsc/icons/plane.png"

class AOVApplyModel(QtCore.QAbstractListModel):

    def __init__(self, parent=None):
	super(AOVApplyModel, self).__init__(parent)

	self._items = []


    @property
    def items(self):
        return self._items


    def rowCount(self, parent):
	return len(self.items)


    def data(self, index, role):

	row = index.row()

	obj = self.items[row]

	if role == QtCore.Qt.DisplayRole:
	    if isinstance(obj, AOV):
		return obj.channel
	    else:
		return obj.name

	if role == QtCore.Qt.DecorationRole:
	    return QtGui.QIcon(getIcon(obj))

    def flags(self, index):
	return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled


    def insertRows(self, data, parent=QtCore.QModelIndex()):
	if data in self.items:
	    return False


	start = len(self.items) - 1
	self.beginInsertRows(parent, start, start +1)

	self.items.append(data)

	self.endInsertRows()

	return True


    def removeRows(self, idx, parent=QtCore.QModelIndex()):
	row = idx.row()

	self.beginRemoveRows(parent, row, row+1)

	self.items.remove(self.items[row])

	self.endRemoveRows()

	return True


class AOVGroupListModel(QtCore.QAbstractListModel):

    def __init__(self, parent=None):
	super(AOVGroupListModel, self).__init__(parent)

#	self._groups = buildPlaneGroups()
        manager = ht.sohohooks.manager.findOrCreateSessionAOVManager()
        self._groups = manager.groups.values()


    @property
    def groups(self):
        return self._groups

    def rowCount(self, parent):
	return len(self._groups)


    def mimeData(self, index):
	row = index[0].row()

	value = self._groups[row]

	mime_data = QtCore.QMimeData()

	mime_data.setData("text/csv", pickle.dumps(value))

	return mime_data



    def data(self, index, role):

	if role == QtCore.Qt.DisplayRole:
	    row = index.row()
	    value = self.groups[row]

	    return value.name

        if role == QtCore.Qt.DecorationRole:
	    return QtGui.QIcon(":houdini/planeviewer/rsc/icons/plane.png")


    def flags(self, index):
	return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled



class AOVChoiceListModel(QtCore.QAbstractListModel):

    def __init__(self, parent=None):
	super(AOVChoiceListModel, self).__init__(parent)

#	self._aovs = _findPlaneDefinitions().values()
        manager = ht.sohohooks.manager.findOrCreateSessionAOVManager()
        self._aovs = manager.aovs

    @property
    def aovs(self):
        return self._aovs

    def rowCount(self, parent):
	return len(self.aovs)


    def mimeData(self, index):
	row = index[0].row()

	value = self.aovs[row]

	mime_data = QtCore.QMimeData()

	dataType = self._aovs[row].vextype


	data = {
	    "name": value.channel,
	    "icon":":houdini/planeviewer/rsc/icons/{0}.png".format(dataType)
	}


#	mime_data.setData("text/csv", pickle.dumps(data))
	mime_data.setData("text/csv", pickle.dumps(value))
	return mime_data

    def data(self, index, role):

	row = index.row()
	value = self.aovs[row]

	if role == QtCore.Qt.DisplayRole:
	    return value.channel

        if role == QtCore.Qt.DecorationRole:
	    dataType = value.vextype

	    return QtGui.QIcon(
		":houdini/planeviewer/rsc/icons/{0}.png".format(dataType)
	    )

    def flags(self, index):
	return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled


class MySortFilterProxyModel(QtGui.QSortFilterProxyModel):

    def __init__(self, parent=None):
	super(MySortFilterProxyModel, self).__init__(parent)

    def insertRows(self, data):
	return self.sourceModel().insertRows(data)


class AOVListModel(QtCore.QAbstractListModel):

    def __init__(self, parent=None):
	super(AOVListModel, self).__init__(parent)

#	self._aovs = _findPlaneDefinitions().values()
        manager = ht.sohohooks.manager.findOrCreateSessionAOVManager()
        self._aovs = manager.aovs


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
	    dataType = value.vextype

	    return QtGui.QIcon(
		":houdini/planeviewer/rsc/icons/{0}.png".format(dataType)
	    )

    def flags(self, index):
	return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable


class AOVDisplayTableModel(QtCore.QAbstractTableModel):

    def __init__(self, plane=None, parent=None):
        super(AOVDisplayTableModel, self).__init__(parent)

        self._plane = plane

    @property
    def plane(self):
        return self._plane

    @plane.setter
    def plane(self, plane):
        self._plane = plane

    def rowCount(self, parent):
        return 10

    def columnCount(self, parent):
        return 2

    def data(self, index, role):
        if not index.isValid():
            return None

        elif role != QtCore.Qt.DisplayRole:
            return None

        if self.plane is None:
            return

        row = index.row()
        col = index.column()

        if col == 0:
            return _ROW_TITLES[row]

        if row == 0:
            return self.plane.variable

        elif row == 1:
            return self.plane.vextype

        elif row == 2:
            channel = self.plane.channel

            if channel is None:
                channel = ""

            if channel == self.plane.variable:
                channel = ""

            return channel

        elif row == 3:
            return self.plane.planefile

        elif row == 4:
            return self.plane.quantize

        elif row == 5:
            return self.plane.sfilter

        elif row == 6:
            return self.plane.pfilter

        elif row in (7, 8, 9):
            lightexport = self.plane.lightexport

            if lightexport:
                if row == 7:
                    return lightexport

                elif row == 8:
                    return self.plane.lightexport_scope

                elif row == 9:
                    return self.plane.lightexport_select

            return None


    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return ("Property", "Value")[col]

        return None

    def flags(self, index):

        row = index.row()

        if row == 2:
            channel = self.plane.channel

            if channel is None:
                return 0

            if channel == self.plane.variable:
                return 0

        elif row == 3:
            if self.plane.planefile is None:
                return 0

        elif row == 6:
            if self.plane.pfilter is None:
                return 0

        elif row in (7, 8, 9):
            lightexport = self.plane.lightexport

            if not lightexport:
                return 0

	return QtCore.Qt.ItemIsEnabled


class GroupMemberModel(QtCore.QAbstractListModel):

    def __init__(self, group=None,parent=None):
	super(GroupMemberModel, self).__init__(parent)

	self._group = group

    @property
    def group(self):
        return self._group

    @group.setter
    def group(self, group):
        self._group = group

    def rowCount(self, parent):
	return len(self.group.aovs)


    def data(self, index, role):
	row = index.row()

        plane = self.group.aovs[row]

	if role == QtCore.Qt.DisplayRole:
	    return plane.variable

        if role == QtCore.Qt.DecorationRole:
	    dataType = plane.vextype

	    return QtGui.QIcon(
		":houdini/planeviewer/rsc/icons/{0}.png".format(dataType)
	    )

    def flags(self, index):
	return QtCore.Qt.ItemIsEnabled








class TreeNode(object):
    """The base node in a TreeListView.

    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    def __init__(self, parent=None):
        self._children = []
        self._parent = parent

        # If we have a parent, add this node to the parent's list of children.
        if parent is not None:
            parent.addChild(self)

    @property
    def children(self):
        return self._children

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

    def removeChild(self, position):
        if position < 0 or position > len(self.children):
            return False

        child = self.children.pop(position)

        child.parent = None

        return True


class FolderNode(TreeNode):
    def __init__(self, name, parent=None):
        super(FolderNode, self).__init__(self)

        self._name = name

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
    def __init__(self, plane, parent=None):
        super(AOVNode, self).__init__(plane, parent)

    @property
    def name(self):
        return self.item.variable

    @property
    def plane(self):
        return self.item

    @property
    def planeGroup(self):
        return self.parent.planeGroup



class AOVGroupNode(AOVBaseNode):
    def __init__(self, planeGroup, parent=None):
        super(AOVGroupNode, self).__init__(planeGroup, parent)

    @property
    def planeGroup(self):
        return self.item





class AOVSelectorModel(QtCore.QAbstractItemModel):

    filter_role = QtCore.Qt.UserRole

    def __init__(self, root, parent=None):
        super(AOVSelectorModel, self).__init__(parent)

        self._root = root

    @property
    def rootNode(self):
        return self._rootNode

    def rowCount(self, parent):
        # Invalid parent node, so use the root.
        if not parent.isValid():
            parentNode = self.rootNode

        # Get the tree node.
        else:
            parentNode = parent.internalPointer()

        # Return the number of children for the node.
        return len(parentNode.children)

    def columnCount(self, parent):
        return 1


    def data(self, index, role):

        if not index.isValid():
            return None

        # Get the tree node.
        node = index.internalPointer()

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            # Get the column.
            column = index.column()

            if column == 0:
                return  node.name

        if role == QtCore.Qt.DecorationRole:
#            if isinstance(node, FolderNode):
            return QtGui.QIcon(
                hou.findFile("help/icons/large/DATATYPES/folder.png")
            )


        # When filtering we want to filter based on the plane set name so if
        # the current node is a AOVNode we should return its parent's
        # name.
        if role == PlaneTreeModel.filterRole:
            if isinstance(node, AOVNode):
                return node.parent.name

            return node.name



class PlaneTreeModel(QtCore.QAbstractItemModel):
    """The item model for the plane viewer.

    """

    # Use the base user role as our filter role.
    filterRole = QtCore.Qt.UserRole

    def __init__(self, root, parent=None):
        super(PlaneTreeModel, self).__init__(parent)
        self._rootNode = root

#        self._items = []


    @property
    def rootNode(self):
        return self._rootNode

    @property
    def items(self):
#        return self._items
        return [child.item for child in self.rootNode.children]




    def rowCount(self, parent):
        # Invalid parent node, so use the root.
        if not parent.isValid():
            parentNode = self.rootNode

        # Get the tree node.
        else:
            parentNode = parent.internalPointer()

        # Return the number of children for the node.
        return len(parentNode.children)

    def columnCount(self, parent):
        return 1

    def data(self, index, role):

        if not index.isValid():
            return None

        # Get the tree node.
        node = index.internalPointer()

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            # Get the column.
            column = index.column()

            if column == 0:
                return  node.name

            elif column == 1:
                return node.path

            elif column == 2:
                return node.name

            elif column == 3:
                return node.plane.channel

            elif column == 4:
                return node.plane.vextype

            elif column == 5:
                return node.plane.quantize

            elif column == 6:
                return node.plane.sfilter

            elif column == 7:
                pfilter = node.plane.pfilter
                if pfilter is not None:
                    return pfilter

            elif column == 8:
                planefile = node.plane.planefile
                if planefile is not None:
                    return planefile

            elif column == 9:
                lightexport = node.plane.lightexport
                if lightexport is not None:
                    return lightexport

            elif column == 10:
                lightmask = node.plane.lightmask
                if lightmask is not None:
                    return lightmask

            elif column == 11:
                lightselection = node.plane.lightselection
                if lightselection is not None:
                    return lightselection

            # If no values were specified, return a default string.
            return "Not Specified"

        if role == QtCore.Qt.DecorationRole:
            # For plane nodes we use the vex type information to determine
            # the icon.
            if isinstance(node, AOVNode):
                dataType = node.plane.vextype

                return QtGui.QIcon(
                    ":houdini/planeviewer/rsc/icons/{0}.png".format(dataType)
                )

            # For plane sets we just use a regular icon.
            else:
                return QtGui.QIcon(":houdini/planeviewer/rsc/icons/plane.png")

        # When filtering we want to filter based on the plane set name so if
        # the current node is a AOVNode we should return its parent's
        # name.
        if role == PlaneTreeModel.filterRole:
            if isinstance(node, AOVNode):
                return node.parent.name

            return node.name

    def flags(self, index):
        if not index.isValid():
            return None

        # Get the tree node.
        node = index.internalPointer()

        parent = node.parent

        if parent == self.rootNode:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled

        return 0


    def getNode(self, index):
        if index.isValid():
            node = index.internalPointer()
            if node:
                return node

        return self.rootNode

    def index(self, row, column, parent):
        # Get the parent node.
        parentNode = self.getNode(parent)

        if row < len(parentNode.children):
            # This node is the child node matching the row.
            childItem = parentNode.children[row]

            if childItem:
                return self.createIndex(row, column, childItem)

        return QtCore.QModelIndex()

    def parent(self, index):
        # Get the node for the index.
        node = self.getNode(index)

        parentNode = node.parent

        # If the parent is the root, return an invalid index.
        if parentNode == self.rootNode:
            return QtCore.QModelIndex()

        # Return the parent index.
        return self.createIndex(parentNode.row, 0, parentNode)


    def mimeData(self, index):

        if not index[0].isValid():
            return None

        # Get the tree node.
        node = index[0].internalPointer()




        mime_data = QtCore.QMimeData()
        mime_data.setData("text/csv", pickle.dumps(node))
        return mime_data


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

                for plane in item.aovs:
                    plane_node = AOVNode(plane, child_node)

	self.endInsertRows()

	return True

    def removeRows(self, idx, parent=QtCore.QModelIndex()):

        parentNode = self.getNode(parent)

	row = idx.row()

	self.beginRemoveRows(parent, row, row+1)

        parentNode.removeChild(row)


	self.endRemoveRows()

	return True

