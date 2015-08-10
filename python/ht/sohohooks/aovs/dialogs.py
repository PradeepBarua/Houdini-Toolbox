"""This module contains custom dialogs for creating and editing AOVs and
AOVGroups.

"""

# =============================================================================
# IMPORTS
# =============================================================================

# Python Imports
from PySide import QtCore, QtGui
import os
import re

# Houdini Toolbox Imports
from ht.sohohooks.aovs import data, widgets, utils
from ht.sohohooks.aovs import manager
from ht.sohohooks.aovs.aov import AOV, AOVGroup

# Houdini Imports
import hou

# =============================================================================
# CLASSES
# =============================================================================

class DialogOperation(object):
    """Fake enum class for dialog operations."""
    New = 1
    Edit = 2
    Duplicate = 3

# =============================================================================
# Create/Edit Dialogs
# =============================================================================

class AOVDialog(QtGui.QDialog):
    """This dialog is for creating and editing AOVs."""

    validInputSignal = QtCore.Signal(bool)
    newAOVSignal = QtCore.Signal(AOV)

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    def __init__(self, operation=DialogOperation.New, parent=None):
        super(AOVDialog, self).__init__(parent)

        self._operation = operation

        self.setStyleSheet(hou.ui.qtStyleSheet())

        # UI elements are valid.
        self._variable_valid = False
        self._file_valid = False

        self.initUI()

        self.setMinimumWidth(450)
        self.setFixedHeight(525)

        if self._operation == DialogOperation.New:
            self.setWindowTitle("Create AOV")

        else:
            self.setWindowTitle("Edit AOV")

    # =========================================================================
    # NON-PUBLIC METHODS
    # =========================================================================

    def _enableCreation(self, enable):
        """Enable the Ok button."""
        self.button_box.button(QtGui.QDialogButtonBox.Ok).setEnabled(enable)

    def _enableComponents(self, enable):
        """Enable the Export Components field."""
        self.components_label.setEnabled(enable)
        self.components.setEnabled(enable)

    def _enableExports(self, value):
        """Enable the Light Mask and Light Selection fields."""
        # Current index must be 2 or 3 to enable the fields.
        enable = value in (2, 3)

        self.light_mask_label.setEnabled(enable)
        self.light_mask.setEnabled(enable)

        self.light_select_label.setEnabled(enable)
        self.light_select.setEnabled(enable)

    # =========================================================================
    #  METHODS
    # =========================================================================

    def accept(self):
        """Accept the operation."""
        aov_data = {
            "variable": self.variable_name.text(),
            "vextype": self.type_box.itemData(self.type_box.currentIndex())
        }

        channel_name = self.channel_name.text()

        if channel_name:
            aov_data["channel"] = channel_name

        quantize = self.quantize_box.itemData(self.quantize_box.currentIndex())

        if not utils.isValueDefault(quantize, "quantize"):
            aov_data["quantize"] = quantize

        sfilter = self.sfilter_box.itemData(self.sfilter_box.currentIndex())
        if not utils.isValueDefault(sfilter, "sfilter"):
            aov_data["sfilter"] = sfilter

        pfilter = self.pfilter_widget.value()

        if not utils.isValueDefault(pfilter, "pfilter"):
            aov_data["pfilter"] = pfilter

        if self.componentexport.isChecked():
            aov_data["componentexport"] = True
            aov_data["components"] = self.components.text().split()

        lightexport = self.lightexport.itemData(self.lightexport.currentIndex())

        if lightexport:
            aov_data["lightexport"] = lightexport

            if lightexport != "per-category":
                aov_data["lightexport_scope"] = self.light_mask.text()
                aov_data["lightexport_select"] = self.light_select.text()

        comment = self.comment.text()

        if comment:
            aov_data["comment"] = comment

        new_aov = AOV(aov_data)

        self.new_aov = new_aov
        new_aov.path = os.path.expandvars(self.file_widget.getPath())

        writer = utils.AOVFileWriter()

        writer.addAOV(new_aov)

        writer.writeToFile(
            os.path.expandvars(self.file_widget.getPath())
        )

        self.newAOVSignal.emit(new_aov)
        return super(AOVDialog, self).accept()

    def initFromAOV(self, aov):
        """Initialize the dialog from an AOV."""
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

    def initUI(self):
        """Initialize the UI."""
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        grid_layout = QtGui.QGridLayout()
        layout.addLayout(grid_layout)

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
        grid_layout.addWidget(self.type_box, 2, 1)

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

        # =====================================================================

        grid_layout.addWidget(QtGui.QLabel("Channel Name"), 3, 0)

        self.channel_name = QtGui.QLineEdit()
        grid_layout.addWidget(self.channel_name, 3, 1)

        self.channel_name.setToolTip(
            "Optional channel name Mantra will rename the AOV to."
        )

        # =====================================================================

        grid_layout.addWidget(QtGui.QLabel("Quantize"), 4, 0)

        self.quantize_box = QtGui.QComboBox()
        grid_layout.addWidget(self.quantize_box, 4, 1)

        for entry in data.QUANTIZE_MENU_ITEMS:
            self.quantize_box.addItem(entry[1], entry[0])

        self.quantize_box.setCurrentIndex(2)

        # =====================================================================

        grid_layout.addWidget(QtGui.QLabel("Sample Filter"), 5, 0)

        self.sfilter_box = QtGui.QComboBox()
        grid_layout.addWidget(self.sfilter_box, 5, 1)

        for entry in data.SFILTER_MENU_ITEMS:
            self.sfilter_box.addItem(entry[1], entry[0])

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

        grid_layout.addWidget(
            QtGui.QLabel("Export variable for each component"),
            8,
            1
        )

        # =====================================================================

        self.components_label = QtGui.QLabel("Export Components")
        grid_layout.addWidget(self.components_label, 9, 0)

        self.components_label.setDisabled(True)

        self.components = QtGui.QLineEdit()
        grid_layout.addWidget(self.components, 9, 1)

        self.components.setDisabled(True)
        self.components.setToolTip(
            "Shading component names.  Leaving this field empty will use the components" \
            " selected on the Mantra ROP."
        )

        self.componentexport.stateChanged.connect(self._enableComponents)

        # =====================================================================

        grid_layout.setRowMinimumHeight(10, 25)

        # =====================================================================

        grid_layout.addWidget(QtGui.QLabel("Light Exports"), 11, 0)

        self.lightexport = QtGui.QComboBox()
        grid_layout.addWidget(self.lightexport, 11, 1)

        for entry in data.LIGHTEXPORT_MENU_ITEMS:
            self.lightexport.addItem(entry[1], entry[0])

        self.lightexport.currentIndexChanged.connect(self._enableExports)

        # =====================================================================

        self.light_mask_label = QtGui.QLabel("Light Mask")
        grid_layout.addWidget(self.light_mask_label, 12, 0)

        self.light_mask_label.setDisabled(True)

        self.light_mask = QtGui.QLineEdit()
        grid_layout.addWidget(self.light_mask, 12, 1)

        self.light_mask.setText("*")
        self.light_mask.setDisabled(True)

        # =====================================================================

        self.light_select_label = QtGui.QLabel("Light Selection")
        grid_layout.addWidget(self.light_select_label, 13, 0)

        self.light_select_label.setDisabled(True)

        self.light_select = QtGui.QLineEdit()
        grid_layout.addWidget(self.light_select, 13, 1)

        self.light_select.setText("*")
        self.light_select.setDisabled(True)

        # =====================================================================

        grid_layout.setRowMinimumHeight(14, 25)

        # =====================================================================

        grid_layout.addWidget(QtGui.QLabel("Priority"), 15, 0)

        self.priority = widgets.CustomSpinBox()
        grid_layout.addWidget(self.priority, 15, 1)

        self.priority.setMinimum(-1)
        self.priority.setValue(-1)

        # =====================================================================

        grid_layout.setRowMinimumHeight(16, 25)

        # =====================================================================

        grid_layout.addWidget(QtGui.QLabel("Comment"), 17, 0)

        self.comment = QtGui.QLineEdit()
        grid_layout.addWidget(self.comment, 17, 1)

        self.comment.setToolTip(
            "Optional comment, eg. 'This AOV represents X'."
        )

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

        self.status_widget = widgets.StatusMessageWidget()
        layout.addWidget(self.status_widget)

        if self._operation == DialogOperation.New:
            self.status_widget.addInfo(0, "Enter a variable name")
            self.status_widget.addInfo(1, "Choose a file")

        # =====================================================================

        self.button_box = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel
        )
        layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        if self._operation == DialogOperation.New:
            self._enableCreation(False)

        else:
            self._enableCreation(True)

            self.button_box.addButton(QtGui.QDialogButtonBox.Reset)

            reset_button = self.button_box.button(QtGui.QDialogButtonBox.Reset)
            reset_button.clicked.connect(self.reset)

        self.validInputSignal.connect(self._enableCreation)

    def reset(self):
        """Reset any changes made."""
        self.initFromAOV(self._aov)

    def validateAllValues(self):
        """Check all the values are valid."""
        valid = True

        if not self._variable_valid:
            valid = False

        if not self._file_valid:
            valid = False

        self.validInputSignal.emit(valid)

    def validateFilePath(self):
        """Check that the file path is valid."""
        self.status_widget.clear(1)

        path = self.file_widget.getPath()

        self._file_valid = utils.filePathIsValid(path)

        if not self._file_valid:
            self.status_widget.addError(1, "Invalid file path")

        self.validateAllValues()

    def validateVariableName(self):
        """Check that the variable name is valid."""
        self.status_widget.clear(0)

        self._variable_valid = True

        variable_name = self.variable_name.text()

        # Only allow letters, numbers and underscores.
        result = re.match("^\\w+$", variable_name)

        if result is None:
            self._variable_valid = False
            self.status_widget.addError(0, "Invalid variable name")

        self.validateAllValues()


class AOVGroupDialog(QtGui.QDialog):
    """This dialog is for creating and editing AOVGroups."""

    validInputSignal = QtCore.Signal(bool)
    newAOVGroupSignal = QtCore.Signal(AOVGroup)
    groupUpdatedSignal = QtCore.Signal(AOVGroup)

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    def __init__(self, operation=DialogOperation.New, parent=None):
        super(AOVGroupDialog, self).__init__(parent)

        self._operation = operation

        self.setStyleSheet(hou.ui.qtStyleSheet())

        # UI elements are valid.
        self._group_name_valid = False
        self._file_valid = False
        self._aovs_valid = False

        self.initUI()

        self.resize(450, 475)
        self.setMinimumWidth(450)

        if self._operation == DialogOperation.New:
            self.setWindowTitle("Create AOV Group")
        else:
            self.setWindowTitle("Edit AOV Group")

        self.validInputSignal.connect(self._enableCreation)

    # =========================================================================
    # NON-PUBLIC METHODS
    # =========================================================================

    def _enableCreation(self, enable):
        """Enable the Ok button."""
        self.button_box.button(QtGui.QDialogButtonBox.Ok).setEnabled(enable)

    # =========================================================================
    # METHODS
    # =========================================================================

    def accept(self):
        """Accept the operation."""
        group_name = self.group_name.text()

        if self._operation == DialogOperation.Edit:
            # Want to edit the existing group so use it and clear out the
            # current AOVs.
            group = self._group
            group.clear()
        else:
            group = AOVGroup(group_name)

        file_path = os.path.expandvars(self.file_widget.getPath())

        group.path = file_path
        group.comment = self.comment.text()

        # Find the AOVs to be in this group.
        aovs = self.aov_list.getSelectedAOVs()

        group.aovs.extend(aovs)

        # Emit appropriate signal based on operation type.
        if self._operation == DialogOperation.New:
            self.newAOVGroupSignal.emit(group)

        else:
            self.groupUpdatedSignal.emit(group)

        # Construct a writer and write the group to disk.
        writer = utils.AOVFileWriter()
        writer.addGroup(group)
        writer.writeToFile(file_path)

        return super(AOVGroupDialog, self).accept()

    def initFromGroup(self, group):
        """Initialize the dialog from a group."""
        self._group = group

        self.group_name.setText(group.name)
        self.file_widget.setPath(group.path)

        self.setSelectedAOVs(group.aovs)

    def initUI(self):
        """Intialize the UI."""
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        grid_layout = QtGui.QGridLayout()
        layout.addLayout(grid_layout)

        # =====================================================================

        grid_layout.addWidget(QtGui.QLabel("Group Name"), 1, 0)

        self.group_name = QtGui.QLineEdit()
        grid_layout.addWidget(self.group_name, 1, 1)

        self.group_name.textChanged.connect(self.validateGroupName)

        self.group_name.setFocus()

        if self._operation == DialogOperation.Edit:
            self.group_name.setEnabled(False)

        # =====================================================================

        grid_layout.addWidget(QtGui.QLabel("File Path"), 2, 0)

        self.file_widget = widgets.FileChooser()
        grid_layout.addWidget(self.file_widget, 2, 1)

        self.file_widget.field.textChanged.connect(self.validateFilePath)

        if self._operation == DialogOperation.Edit:
            self.file_widget.enable(False)

        # =====================================================================

        grid_layout.addWidget(QtGui.QLabel("Comment"), 3, 0)

        self.comment = QtGui.QLineEdit()
        grid_layout.addWidget(self.comment, 3, 1)

        self.comment.setToolTip(
            "Optional comment, eg. 'This group is for X'."
        )

        # ====================================================================

        self.aov_list = widgets.NewGroupAOVListWidget(self)
        layout.addWidget(self.aov_list)

        # Signal triggered when check boxes are toggled.
        self.aov_list.model().sourceModel().dataChanged.connect(self.validateAOVs)

        # =====================================================================

        self.filter = widgets.AOVFilterWidget()
        layout.addWidget(self.filter)

        QtCore.QObject.connect(
            self.filter.field,
            QtCore.SIGNAL("textChanged(QString)"),
            self.aov_list.proxy_model.setFilterWildcard
        )

        # =====================================================================

        self.status_widget = widgets.StatusMessageWidget()
        layout.addWidget(self.status_widget)

        # Set default messages for new groups.
        if self._operation == DialogOperation.New:
            self.status_widget.addInfo(0, "Enter a group name")
            self.status_widget.addInfo(1, "Choose a file")
            self.status_widget.addInfo(2, "Select AOVs for group")

        # =====================================================================

        self.button_box = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel
        )
        layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        if self._operation == DialogOperation.New:
            # Disable Ok button by default.
            self._enableCreation(False)

        else:
            self._enableCreation(True)

            # Add a Reset button.
            self.button_box.addButton(QtGui.QDialogButtonBox.Reset)

            reset_button = self.button_box.button(QtGui.QDialogButtonBox.Reset)
            reset_button.clicked.connect(self.reset)

    def reset(self):
        """Reset any changes made."""
        # Reset the dialog by just calling the initFromGroup function again.
        self.initFromGroup(self._group)

    def setSelectedAOVs(self, aovs):
        """Set a list of AOVs to be selected."""
        source_model = self.aov_list.model().sourceModel()

        source_model.beginResetModel()

        source_model.uncheckAll()

        for aov in aovs:
            try:
                row = source_model.aovs.index(aov)

            except ValueError:
                continue

            source_model.checked[row] = True

        source_model.endResetModel()

        self.validateAOVs()

    def validateAOVs(self):
        """Check that one or more AOVs is selected."""
        self.status_widget.clear(2)

        num_checked = len(self.aov_list.getSelectedAOVs())

        self._aovs_valid = num_checked > 0

        if not self._aovs_valid:
            self.status_widget.addError(2, "No AOVs selected")

        self.validateAllValues()

    def validateAllValues(self):
        """Check all values are valid."""
        valid = True

        if not self._group_name_valid:
            valid = False

        if not self._file_valid:
            valid = False

        if not self._aovs_valid:
            valid = False

        self.validInputSignal.emit(valid)

    def validateFilePath(self):
        """Check that the file path is valid."""
        self.status_widget.clear(1)

        path = self.file_widget.getPath()
        self._file_valid = utils.filePathIsValid(path)

        if not self._file_valid:
            self.status_widget.addError(1, "Invalid file path")

        self.validateAllValues()

    def validateGroupName(self):
        """Check that the group name is valid."""
        self.status_widget.clear(0)

        self._group_name_valid = True

        msg = "Invalid group name"

        group_name = self.group_name.text()

        # Only allow letters, numbers and underscores.
        result = re.match("^\\w+$", group_name)

        if result is None:
            self._group_name_valid = False
            self.status_widget.addError(0, msg)

        # Check if the group exists when creating a new group.
        elif self._operation == DialogOperation.New:
            if group_name in manager.MANAGER.groups:
                self._group_name_valid = False
                msg = "Group already exists"
                self.status_widget.addWarning(0, msg)

        self.validateAllValues()

# =============================================================================
# Info Dialogs
# =============================================================================

class AOVInfoDialog(QtGui.QDialog):
    """Dialog for displaying information about an AOV."""

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    def __init__(self, aov, parent=None):
        super(AOVInfoDialog, self).__init__(parent)

        self._aov = aov

        self.setWindowTitle("View AOV Info")
        self.setStyleSheet(hou.ui.qtStyleSheet())

        self.initUI()

    def initUI(self):
        """Initialize the UI."""
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        self.aov_chooser = QtGui.QComboBox()
        layout.addWidget(self.aov_chooser)

        # Start menu index.
        start_idx = -1

        # Populate the AOV chooser with all the existing AOVs.
        for idx, aov in enumerate(manager.MANAGER.aovs.values()):
            # If a channel is specified, put it into the display name.
            if aov.channel is not None:
                label = "{0} ({1})".format(
                    aov.variable,
                    aov.channel
                )

            else:
                label = aov.variable

            self.aov_chooser.addItem(
                utils.getIconFromVexType(aov.vextype),
                label,
                aov
            )

            # The AOV matches our start AOV so set the start index.
            if aov == self._aov:
                start_idx = idx

        if start_idx != -1:
            self.aov_chooser.setCurrentIndex(start_idx)

        self.aov_chooser.currentIndexChanged.connect(self.updateModel)

        # =====================================================================

        self.table = widgets.AOVInfoTableView(self._aov)
        layout.addWidget(self.table)

        # =====================================================================

        self.button_box = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok
        )
        layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)

        edit_button = QtGui.QPushButton(
            QtGui.QIcon(":/ht/rsc/icons/sohohooks/aovs/edit.png"),
            "Edit"
        )

        self.button_box.addButton(edit_button, QtGui.QDialogButtonBox.HelpRole)
        edit_button.clicked.connect(self.edit)

        # =====================================================================

        self.table.resizeColumnToContents(1)
        self.setMinimumSize(self.table.size())

    def edit(self):
        """Launch the Edit dialog for the currently selected group."""
        # Accept the dialog so it closes.
        self.accept()

        active = QtGui.QApplication.instance().activeWindow()

        self.dialog = AOVDialog(
            DialogOperation.Edit,
            active
        )

        self.dialog.initFromAOV(self._aov)
        self.dialog.show()

    def updateModel(self, index):
        """Update the data displays with the currently selected AOV."""
        aov = self.aov_chooser.itemData(index)

        model = self.table.model()
        model.beginResetModel()
        model.initDataFromAOV(aov)
        model.endResetModel()

# =============================================================================

class AOVGroupInfoDialog(QtGui.QDialog):
    """Dialog for displaying information about an AOVGroup."""

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    def __init__(self, group, parent=None):
        super(AOVGroupInfoDialog, self).__init__(parent)

        self._group = group

        self.setWindowTitle("View AOV Group Info")
        self.setStyleSheet(hou.ui.qtStyleSheet())

        self.initUI()

    def initUI(self):
        """Initialize the UI."""
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        # =====================================================================

        self.group_chooser = QtGui.QComboBox()
        layout.addWidget(self.group_chooser)

        # Start menu index.
        start_idx = -1

        # Populate the group chooser with all the existing groups.
        for idx, group in enumerate(manager.MANAGER.groups.values()):
            label = group.name

            self.group_chooser.addItem(
                utils.getIconFromGroup(group),
                label,
                group
            )

            # The group matches our start group so set the start index.
            if group == self._group:
                start_idx = idx

        if start_idx != -1:
            self.group_chooser.setCurrentIndex(start_idx)

        self.group_chooser.currentIndexChanged.connect(self.updateModel)

        # =====================================================================

        self.table = widgets.AOVGroupInfoTableWidget(self._group)
        layout.addWidget(self.table)

        # =====================================================================

        self.members = widgets.GroupMemberListWidget(self._group)
        layout.addWidget(self.members)

        # =====================================================================

        self.button_box = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok
        )
        layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)

        # Button to launch the Edit dialog on the current group.
        edit_button = QtGui.QPushButton(
            QtGui.QIcon(":/ht/rsc/icons/sohohooks/aovs/edit.png"),
            "Edit"
        )

        # Use HelpRole to force the button to the left size of the dialog.
        self.button_box.addButton(edit_button, QtGui.QDialogButtonBox.HelpRole)
        edit_button.clicked.connect(self.edit)

        # =====================================================================

        self.table.resizeColumnToContents(1)
        self.setMinimumSize(self.table.size())

    # =========================================================================
    # METHODS
    # =========================================================================

    def edit(self):
        """Launch the Edit dialog for the currently selected group."""
        # Accept the dialog so it closes.
        self.accept()

        active = QtGui.QApplication.instance().activeWindow()

        self.dialog = AOVGroupDialog(
            DialogOperation.Edit,
            active
        )

        self.dialog.initFromGroup(self._group)
        self.dialog.show()

    def updateModel(self, index):
        """Update the data displays with the currently selected group."""
        group = self.group_chooser.itemData(index)

        table_model = self.table.model()
        table_model.beginResetModel()
        table_model.initDataFromGroup(group)
        table_model.endResetModel()

        member_model = self.members.model().sourceModel()
        member_model.beginResetModel()
        member_model.initDataFromGroup(group)
        member_model.endResetModel()
