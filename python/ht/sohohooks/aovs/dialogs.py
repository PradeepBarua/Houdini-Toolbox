
import os
import re


from PySide import QtCore, QtGui

from ht.sohohooks.aovs import aov, data, manager, widgets, utils

import hou


class DialogOperation:
    New = 1
    Edit = 2
    Info = 3

class DialogErrorWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(DialogErrorWidget, self).__init__(parent)

        self._mappings = {}

        self.setContentsMargins(0,0,0,0)

        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)

        self.icon = QtGui.QLabel()
        self.icon.setFixedSize(24, 24)
        self.icon.setPixmap(
            QtGui.QIcon(":/ht/rsc/icons/sohohooks/aovs/warning.png").pixmap(24, 24)
        )

        self.icon.hide()

        layout.addWidget(self.icon)

        self.display = QtGui.QLabel()

        layout.addWidget(self.display)

        self.setLayout(layout)
        self.setFixedHeight(24)


    def _updateDisplay(self):
        error = self.getError()

        if error:
            self.display.setText(error)
            self.display.show()
            self.icon.show()

        else:
            self.display.clear()
            self.display.hide()
            self.icon.hide()


    def addError(self, level, msg):
        self._mappings[level] = msg

        self._updateDisplay()

    def clearError(self, level):
        if level in self._mappings:
            del self._mappings[level]

        self._updateDisplay()

    def getError(self):
        levels = self._mappings.keys()

        if levels:
            highest = sorted(levels)[0]

            return self._mappings[highest]

        return ""

    def setMessage(self, msg):
        self.display.setText(msg)


class AOVGroupDialog(QtGui.QDialog):

    validInputSignal = QtCore.Signal(bool)
    newAOVGroupSignal = QtCore.Signal(aov.AOVGroup)

    def __init__(self, operation=DialogOperation.New, parent=None):
        super(AOVGroupDialog, self).__init__(parent)

        self._operation = operation

        self.setStyleSheet(hou.ui.qtStyleSheet())

        self.error_widget = DialogErrorWidget()

        self._group_name_valid = False
        self._file_valid = False

        layout = QtGui.QVBoxLayout()

        self.widget = self.init_ui()

        layout.addWidget(self.widget)

        self.resize(450, 475)

        self.setMinimumWidth(450)

        if self._operation == DialogOperation.New:
            self.setWindowTitle("Create AOV Group")
        else:
            self.setWindowTitle("Edit AOV Group")

        self.setWindowIcon(
            QtGui.QIcon(":ht/rsc/icons/sohohooks/aovs/create_group.png")
        )

        self._buttonBox = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel
        )

        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)

        layout.addWidget(self._buttonBox)

        if self._operation == DialogOperation.New:
            self._enableCreation(False)
            self.validInputSignal.connect(self._enableCreation)

        else:
            self._enableCreation(True)

            self._buttonBox.addButton(QtGui.QDialogButtonBox.Reset)

            reset_button = self._buttonBox.button(QtGui.QDialogButtonBox.Reset)
            reset_button.clicked.connect(self.reset)

        self.setLayout(layout)

#        self.init_from_group(manager.findOrCreateSessionAOVManager().groups['default'])

    def init_from_group(self, group):
        self._group = group

        self.group_name.setText(group.name)
        self.file_widget.setPath(group.path)

        self.setSelectedItems(group.aovs)

    def reset(self):
        self.init_from_group(self._group)

    def init_ui(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()

        grid_layout = QtGui.QGridLayout()

        # =====================================================================

        grid_layout.addWidget(QtGui.QLabel("Group Name"), 1, 0)

        self.group_name = QtGui.QLineEdit()
        grid_layout.addWidget(self.group_name, 1, 1)

        self.group_name.setFocus()

        if self._operation == DialogOperation.Edit:
            self.group_name.setEnabled(False)

        self.group_name.textChanged.connect(self.validateGroupName)

        # =====================================================================

        grid_layout.addWidget(QtGui.QLabel("File Path"), 2, 0)


        self.file_widget = widgets.FileChooser()

        self.file_widget.field.textChanged.connect(self.validateFilePath)

        if self._operation == DialogOperation.Edit:
            self.file_widget.enable(False)

        grid_layout.addWidget(self.file_widget, 2, 1)

        layout.addLayout(grid_layout)

        # =====================================================================

        grid_layout.addWidget(QtGui.QLabel("Comment"), 3, 0)

        self.comment = QtGui.QLineEdit()
        self.comment.setToolTip(
            "Optional comment, eg. 'This group is for X'."
        )

        grid_layout.addWidget(self.comment, 3, 1)


        # =====================================================================

        self.list = widgets.NewGroupAOVListWidget(self)

        layout.addWidget(self.list)


        # =====================================================================

        self.filter = widgets.AOVFilterWidget()
        layout.addWidget(self.filter)

        QtCore.QObject.connect(
            self.filter.field,
           QtCore.SIGNAL("textChanged(QString)"),
            self.list.proxy_model.setFilterWildcard
        )

        # =====================================================================

        self.error_widget.setMessage("Enter a group name.")
        layout.addWidget(self.error_widget)

        widget.setLayout(layout)

        return widget

    def validateGroupName(self):
        self.error_widget.clearError(0)

        group_name = self.group_name.text()
        group_name = group_name.strip()

        self._group_name_valid = True
        msg = "Invalid group name"

        if group_name:
            mgr = manager.findOrCreateSessionAOVManager()

            if ' ' in group_name:
                self._group_name_valid = False

            elif not group_name.isalnum():
                self._group_name_valid = False

            elif group_name in mgr.groups:
                self._group_name_valid = False
                msg = "Group already exists"
        else:
            self._group_name_valid = False

        if not self._group_name_valid:
            self.error_widget.addError(0, msg)

        self.validateAllValues()


    def validateFilePath(self):
        self.error_widget.clearError(1)

        self._file_valid = True

        path = self.file_widget.getPath()

        if path:
            dirname = os.path.dirname(path)
            file_name = os.path.basename(path)

            if not dirname or not file_name:
                self._file_valid = False

            elif not os.path.splitext(file_name)[1]:
                self._file_valid = False

        else:
            self._file_valid = False

        if not self._file_valid:
            self.error_widget.addError(1, "Invalid file path")

        self.validateAllValues()


    def validateAllValues(self):
        valid = True

        if not self._group_name_valid:
            valid = False

        if not self._file_valid:
            valid = False

        self.validInputSignal.emit(valid)

    def _enableCreation(self, enable):
        self._buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(enable)

    def setSelectedItems(self, items):
        model = self.list.model()
        source_model = model.sourceModel()

        model_items = source_model.aovs

        items = utils.flattenList(items)

        source_model.beginResetModel()

        source_model.uncheckAll()

        for item in items:
            try:
                index = source_model.aovs.index(item)

            except ValueError:
                continue

            source_model._checked[index] = True

        source_model.endResetModel()

    def accept(self):
        group_name = self.group_name.text()
        file_path = self.file_widget.getPath()

        if self._operation == DialogOperation.Edit:
            new_group = self._group
            new_group.clear()
        else:
            new_group = aov.AOVGroup(group_name)

        aovs = self.list.model().sourceModel().checkedAOVs()

        # TODO: Disable OK button if no items selected
        if not aovs:
            hou.ui.displayMessage(
                "No AOVs were selected.",
                severity=hou.severityType.Error
            )

        else:
            new_group.aovs.extend(aovs)

            if self._operation == DialogOperation.New:
                self.newAOVGroupSignal.emit(new_group)

        return super(AOVGroupDialog, self).accept()

class AOVDialog(QtGui.QDialog):

    validInputSignal = QtCore.Signal(bool)
    newAOVSignal = QtCore.Signal(aov.AOV)

    def __init__(self, operation=DialogOperation.New, parent=None):
        super(AOVDialog, self).__init__(parent)

        self._operation = operation

        self.setStyleSheet(hou.ui.qtStyleSheet())

        self.error_widget = DialogErrorWidget()

        self._variable_valid = False
        self._file_valid = False

        layout = QtGui.QVBoxLayout()

        self.widget = self.init_ui()

        layout.addWidget(self.widget)

        self.resize(450, 525)

        self.setMinimumWidth(450)
        self.setFixedHeight(525)

        if self._operation == DialogOperation.New:
            self.setWindowTitle("Create AOV")
            self.setWindowIcon(
                QtGui.QIcon(":ht/rsc/icons/sohohooks/aovs/create_aov.png")
            )

        else:
            self.setWindowTitle("Edit AOV")
            self.setWindowIcon(
                QtGui.QIcon(":ht/rsc/icons/sohohooks/aovs/edit_aov.png")
            )


        self._buttonBox = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel
        )

        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)


        if self._operation == DialogOperation.New:
            self._enableCreation(False)

            self.validInputSignal.connect(self._enableCreation)

        else:
            self._enableCreation(True)

            self._buttonBox.addButton(QtGui.QDialogButtonBox.Reset)

            reset_button = self._buttonBox.button(QtGui.QDialogButtonBox.Reset)
            reset_button.clicked.connect(self.reset)


        layout.addWidget(self._buttonBox)

        self.setLayout(layout)

    def reset(self):
        self.initFromAOV(self._aov)


    def init_ui(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()

        grid_layout = QtGui.QGridLayout()

        # =====================================================================

        grid_layout.addWidget(QtGui.QLabel("VEX Variable"), 1, 0)

        self.variable_name = QtGui.QLineEdit()
        grid_layout.addWidget(self.variable_name, 1, 1)

        if self._operation == DialogOperation.New:
            self.variable_name.setFocus()
            self.variable_name.textChanged.connect(self.validateVariableName)

        else:
            self.variable_name.setEnabled(False)

        # =====================================================================

        grid_layout.addWidget(QtGui.QLabel("VEX Type"), 2, 0)

        self.type_box = QtGui.QComboBox()

        for entry in data.VEXTYPE_MENU_ITEMS:
            icon = utils.getIconFromVexType(entry[0])

            self.type_box.addItem(
                icon,
                entry[1],
                entry[0]
            )

        if self._operation == DialogOperation.New:
            self.type_box.setCurrentIndex(1)

        else:
            self.type_box.setEnabled(False)

        grid_layout.addWidget(self.type_box, 2, 1)

        # =====================================================================

        grid_layout.addWidget(QtGui.QLabel("Channel Name"), 3, 0)

        self.channel_name = QtGui.QLineEdit()
        self.channel_name.setToolTip(
            "Optional channel name Mantra will rename the AOV to."
        )

        grid_layout.addWidget(self.channel_name, 3, 1)

        # =====================================================================

        grid_layout.addWidget(QtGui.QLabel("Quantize"), 4, 0)

        self.quantize_box = QtGui.QComboBox()

        for entry in data.QUANTIZE_MENU_ITEMS:
            self.quantize_box.addItem(entry[1], entry[0])

        self.quantize_box.setCurrentIndex(2)

        grid_layout.addWidget(self.quantize_box, 4, 1)

        # =====================================================================

        grid_layout.addWidget(QtGui.QLabel("Sample Filter"), 5, 0)

        self.sfilter_box = QtGui.QComboBox()

        for entry in data.SFILTER_MENU_ITEMS:
            self.sfilter_box.addItem(entry[1], entry[0])

        grid_layout.addWidget(self.sfilter_box, 5, 1)

        # =====================================================================

        grid_layout.addWidget(QtGui.QLabel("Pixel Filter"), 6, 0)

        self.pfilter_widget = widgets.MenuField(
            data.PFILTER_MENU_ITEMS
        )

        grid_layout.addWidget(self.pfilter_widget, 6, 1)

        # =====================================================================

        grid_layout.setRowMinimumHeight(7, 25)

        # =====================================================================

        self.componentexport = QtGui.QCheckBox()

        grid_layout.addWidget(self.componentexport, 8, 0)
        grid_layout.addWidget(QtGui.QLabel("Export variable for each component"), 8, 1)

        # =====================================================================

        self.components_label = QtGui.QLabel("Export Components")
        self.components_label.setDisabled(True)

        grid_layout.addWidget(self.components_label, 9, 0)

        self.components = QtGui.QLineEdit()
        self.components.setToolTip(
            "Shading component names.  Leaving this field empty will use the components" \
            " selected on the Mantra ROP."
        )

#        self.components.setText("diffuse reflect coat refract volume")
        self.components.setDisabled(True)

        self.componentexport.stateChanged.connect(self._enableComponents)

        grid_layout.addWidget(self.components, 9, 1)

        # =====================================================================

        grid_layout.setRowMinimumHeight(10, 25)

        # =====================================================================

        grid_layout.addWidget(QtGui.QLabel("Light Exports"), 11, 0)

        self.lightexport = QtGui.QComboBox()

        for entry in data.LIGHTEXPORT_MENU_ITEMS:
            self.lightexport.addItem(entry[1], entry[0])

        grid_layout.addWidget(self.lightexport, 11, 1)

        # =====================================================================

        self.light_mask_label = QtGui.QLabel("Light Mask")
        self.light_mask_label.setDisabled(True)

        grid_layout.addWidget(self.light_mask_label, 12, 0)

        self.light_mask = QtGui.QLineEdit()
        self.light_mask.setText("*")
        self.light_mask.setDisabled(True)

        self.lightexport.currentIndexChanged.connect(self._enableExports)

        grid_layout.addWidget(self.light_mask, 12, 1)

        # =====================================================================

        self.light_select_label = QtGui.QLabel("Light Selection")
        self.light_select_label.setDisabled(True)

        grid_layout.addWidget(self.light_select_label, 13, 0)

        self.light_select = QtGui.QLineEdit()
        self.light_select.setText("*")
        self.light_select.setDisabled(True)

        self.lightexport.currentIndexChanged.connect(self._enableExports)

        grid_layout.addWidget(self.light_select, 13, 1)

        # =====================================================================

        grid_layout.setRowMinimumHeight(14, 25)

        # =====================================================================

        grid_layout.addWidget(QtGui.QLabel("Priority"), 15, 0)

        self.priority = widgets.CustomSpinBox()
        self.priority.setMinimum(-1)
        self.priority.setValue(-1)

        grid_layout.addWidget(self.priority, 15, 1)

        # =====================================================================

        grid_layout.setRowMinimumHeight(16, 25)

        # =====================================================================

        grid_layout.addWidget(QtGui.QLabel("Comment"), 17, 0)

        self.comment = QtGui.QLineEdit()
        self.comment.setToolTip(
            "Optional comment, eg. 'This AOV represents X'."
        )

        grid_layout.addWidget(self.comment, 17, 1)

        # =====================================================================

        grid_layout.setRowMinimumHeight(18, 25)

        # =====================================================================

        grid_layout.addWidget(QtGui.QLabel("File Path"), 19, 0)

        self.file_widget = widgets.FileChooser()

        grid_layout.addWidget(self.file_widget, 19, 1)

        if self._operation == DialogOperation.New:
            self.file_widget.field.textChanged.connect(self.validateFilePath)

        else:
            self.file_widget.setEnabled(False)

        # =====================================================================

        layout.addLayout(grid_layout)

        self.error_widget.setMessage("Enter a variable name.")
        layout.addWidget(self.error_widget)

        widget.setLayout(layout)

        return widget


    def _enableCreation(self, enable):
        self._buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(enable)

    def _enableComponents(self, enable):
        self.components_label.setEnabled(enable)
        self.components.setEnabled(enable)

    def _enableExports(self, value):
        enable = value in (2, 3)

        self.light_mask_label.setEnabled(enable)
        self.light_mask.setEnabled(enable)

        self.light_select_label.setEnabled(enable)
        self.light_select.setEnabled(enable)


    def initFromAOV(self, aov):
        self._aov = aov

        self.variable_name.setText(aov.variable)

        self.type_box.setCurrentIndex(utils.getVexTypeMenuIndex(aov.vextype))

        if aov.channel is not None:
            self.channel_name.setText(aov.channel)

        if aov.quantize is not None:
            self.quantize_box.setCurrentIndex(utils.getQuantizeMenuIndex(aov.quantize))

        if aov.sfilter is not None:
            self.sfilter_box.setCurrentIndex(utils.getSFilterMenuIndex(aov.sfilter))

        if aov.pfilter is not None:
            self.pfilter_widget.set(aov.pfilter)

        if aov.componentexport:
            self.componentexport.setChecked(True)

            if aov.components:
                self.components.setText(" ".join(aov.componenets))

        if aov.comment:
            self.comment.setText(aov.comment)


        self.file_widget.setPath(aov.path)



    def validateVariableName(self):
        self.error_widget.clearError(0)

        variable_name = self.variable_name.text()

        self._variable_valid = True

        result = re.match("^\\w+$", variable_name)

        if result is None:
            self._variable_valid = False

        if not self._variable_valid:
            self.error_widget.addError(0, "Invalid variable name")

        self.validateAllValues()


    def validateFilePath(self):
        self.error_widget.clearError(1)

        self._file_valid = True

        path = self.file_widget.getPath()

        if path:
            dirname = os.path.dirname(path)
            file_name = os.path.basename(path)

            if not dirname or not file_name:
                self._file_valid = False

            elif not os.path.splitext(file_name)[1]:
                self._file_valid = False

        else:
            self._file_valid = False

        if not self._file_valid:
            self.error_widget.addError(1, "Invalid file path")

        self.validateAllValues()


    def validateAllValues(self):
        valid = True

        if not self._variable_valid:
            valid = False

        if not self._file_valid:
            valid = False

        self.validInputSignal.emit(valid)


    def accept(self):
        data = {
            "variable": self.variable_name.text(),
            "vextype": self.type_box.itemData(self.type_box.currentIndex())
        }

        channel_name = self.channel_name.text()

        if channel_name:
           data["channel"] = channel_name

        data["quantize"] = self.quantize_box.itemData(self.quantize_box.currentIndex())
        data["sfilter"] = self.sfilter_box.itemData(self.sfilter_box.currentIndex())

        pfilter = self.pfilter_widget.value()

        if pfilter:
            data["pfilter"] = pfilter

        comment = self.comment.text()

        if self.componentexport.isChecked():
            data["componentexport"] = True
            data["components"] = self.components.text().split()

        lightexport = self.lightexport.itemData(self.lightexport.currentIndex())

        if lightexport:
            data["lightexport"] = lightexport

            if lightexport != "per-category":
                data["lightexport_scope"] = self.light_mask.text()
                data["lightexport_select"] = self.light_select.text()


        if comment:
            data["comment"] = comment

        new_aov = aov.AOV(data)

        self.new_aov = new_aov

        writer = utils.AOVFileWriter()

        writer.addAOV(new_aov)

#        writer.writeToFile(
#            os.path.expandvars(self.file_widget.getPath())
#        )

        self.newAOVSignal.emit(new_aov)
        return super(AOVDialog, self).accept()


    def reject(self):
        return super(AOVDialog, self).reject()


class AOVInfoDialog(QtGui.QDialog):

    def __init__(self, aov, parent=None):
        super(AOVInfoDialog, self).__init__(parent)

        self.setWindowTitle("View AOV Info")

        self.setStyleSheet(hou.ui.qtStyleSheet())

        self._aov = aov

        layout = QtGui.QVBoxLayout()

        mgr = manager.findOrCreateSessionAOVManager()

        self.chooser = QtGui.QComboBox()

        start_idx = -1

        for idx, aov in enumerate(mgr.aovs):
            if aov.channel is not None:
                label = "{0} ({1})".format(
                    aov.variable,
                    aov.channel
                )

            else:
                label = aov.variable

            self.chooser.addItem(
                utils.getIconFromVexType(aov.vextype),
                label,
                aov
            )

            if aov == self.aov:
                start_idx = idx

        if start_idx != -1:
            self.chooser.setCurrentIndex(start_idx)

        layout.addWidget(self.chooser)

        self.table = widgets.AOVInfoTableView(self.aov)
        layout.addWidget(self.table)

        self._buttonBox = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok
        )


        edit_button = QtGui.QPushButton(
            QtGui.QIcon("/opt/hfs15.0.179/houdini/help/icons/large/BUTTONS/edit.png"),
            "Edit"
        )

        self._buttonBox.addButton(edit_button, QtGui.QDialogButtonBox.HelpRole)

        edit_button.clicked.connect(self.edit)

        self._buttonBox.accepted.connect(self.accept)

        layout.addWidget(self._buttonBox)

        self.setLayout(layout)

        self.chooser.currentIndexChanged.connect(self.updateModel)

        self.table.resizeColumnToContents(1)
        self.setMinimumSize(self.table.size())


    @property
    def aov(self):
        return self._aov


    def edit(self):
        self.accept()

        active = QtGui.QApplication.instance().activeWindow()

        self.dialog = AOVDialog(
            DialogOperation.Edit,
            active
        )

        self.dialog.initFromAOV(self.aov)

        self.dialog.show()

    def updateModel(self, index):
        aov = self.chooser.itemData(index)

        model = self.table.model()

        model.beginResetModel()
        model.initDataFromAOV(aov)

        model.endResetModel()



class AOVGroupInfoDialog(QtGui.QDialog):

    def __init__(self, group, parent=None):
        super(AOVGroupInfoDialog, self).__init__(parent)

        self._group = group

        self.setWindowTitle("View AOV Group Info")

        self.setStyleSheet(hou.ui.qtStyleSheet())

        layout = QtGui.QVBoxLayout()

        mgr = manager.findOrCreateSessionAOVManager()

        self.chooser = QtGui.QComboBox()

        start_idx = -1

        for idx, group in enumerate(mgr.groups.values()):
            label = group.name

            self.chooser.addItem(
                utils.getIconFromGroup(group),
                label,
                group
            )

            if group == self._group:
                start_idx = idx

        layout.addWidget(self.chooser)


        self.table = widgets.AOVGroupInfoTableWidget(self._group)
        layout.addWidget(self.table)

        self.members = widgets.GroupMemberListWidget(self._group)

        layout.addWidget(self.members)


        self._buttonBox = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok
        )

        self._buttonBox.accepted.connect(self.accept)

        edit_button = QtGui.QPushButton(
            QtGui.QIcon("/opt/hfs15.0.179/houdini/help/icons/large/BUTTONS/edit.png"),
            "Edit"
        )

        self._buttonBox.addButton(edit_button, QtGui.QDialogButtonBox.HelpRole)

        edit_button.clicked.connect(self.edit)


        layout.addWidget(self._buttonBox)


        self.table.resizeColumnToContents(1)

        self.setMinimumSize(self.table.size())

        self.setLayout(layout)

        self.chooser.currentIndexChanged.connect(self.updateModel)

        if start_idx != -1:
            self.chooser.setCurrentIndex(start_idx)


    def edit(self):
        self.accept()

        active = QtGui.QApplication.instance().activeWindow()

        self.dialog = AOVGroupDialog(
            DialogOperation.Edit,
            active
        )

        self.dialog.init_from_group(self._group)

        self.dialog.show()

    def updateModel(self, index):
        group = self.chooser.itemData(index)

        table_model = self.table.model()
        table_model.beginResetModel()
        table_model.initDataFromGroup(group)
        table_model.endResetModel()

        member_model = self.members.model()
        member_model.beginResetModel()
        member_model.initDataFromGroup(group)
        member_model.endResetModel()
