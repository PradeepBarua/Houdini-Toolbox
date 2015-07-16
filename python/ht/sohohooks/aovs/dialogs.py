
import os


from PySide import QtCore, QtGui

from ht.sohohooks.aovs import aov, data, manager, widgets, utils

import hou


class NewAOVGroupDialog(QtGui.QDialog):

    validInputSignal = QtCore.Signal(bool)
    newAOVGroupSignal = QtCore.Signal(aov.AOVGroup)

    def __init__(self, parent=None):
        super(NewAOVGroupDialog, self).__init__(parent)

        self.setStyleSheet(hou.ui.qtStyleSheet())

	self._variable_name_valid = False
	self._file_valid = False

	layout = QtGui.QVBoxLayout()

        self.widget = self.init_ui()

        layout.addWidget(self.widget)



	self.resize(450, 475)

	self.setMinimumWidth(450)
#	self.setFixedHeight(275)


	self.setWindowTitle("Create AOV Group")

	self.setWindowIcon(
	    QtGui.QIcon(":ht/rsc/icons/sohohooks/aovs/create_group.png")
	)

        self._buttonBox = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel
        )

        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)

	layout.addWidget(self._buttonBox)

	self._enableCreation(False)

	self.validInputSignal.connect(self._enableCreation)

        self.setLayout(layout)

    def init_ui(self):
	widget = QtGui.QWidget()
	layout = QtGui.QVBoxLayout()

	grid_layout = QtGui.QGridLayout()

	# =====================================================================

	grid_layout.addWidget(QtGui.QLabel("Group Name"), 1, 0)

	self.group_name = QtGui.QLineEdit()
	grid_layout.addWidget(self.group_name, 1, 1)

	self.group_name.setFocus()

	self.group_name.textChanged.connect(self.validateGroupName)

	# =====================================================================

	grid_layout.addWidget(QtGui.QLabel("File Path"), 2, 0)


	file_widget = QtGui.QWidget()

	file_layout = QtGui.QHBoxLayout()
	file_layout.setSpacing(0)
	file_layout.setContentsMargins(0, 0, 0, 0)

	self.file_path = QtGui.QLineEdit()
	file_layout.addWidget(self.file_path)

	file_button = QtGui.QPushButton(
	    QtGui.QIcon(":ht/rsc/icons/sohohooks/aovs/chooser_file.png"),
	    ""
	)

	file_button.setFlat(True)
	file_button.setIconSize(QtCore.QSize(16, 16))
	file_button.setMaximumSize(QtCore.QSize(24, 24))

	file_button.clicked.connect(self.chooseFile)

	file_layout.addWidget(file_button)

	file_widget.setLayout(file_layout)


	self.file_path.textChanged.connect(self.validateFilePath)

	grid_layout.addWidget(file_widget, 2, 1)

        layout.addLayout(grid_layout)

	# =====================================================================


        self.list = widgets.NewGroupAOVListWidget(self)

        layout.addWidget(self.list)

	# =====================================================================

	error_widget = QtGui.QWidget()
	error_widget.setContentsMargins(0,0,0,0)

	error_layout = QtGui.QHBoxLayout()
	error_layout.setContentsMargins(0,0,0,0)

	self.error_icon = QtGui.QLabel()
        self.error_icon.setFixedSize(24, 24)
        self.error_icon.setPixmap(
            QtGui.QIcon(":/ht/rsc/icons/sohohooks/aovs/warning.png").pixmap(24, 24)
        )
        self.error_icon.hide()

	error_layout.addWidget(self.error_icon)

	self.error = QtGui.QLabel("Enter a group name.")

	error_layout.addWidget(self.error)

	error_widget.setLayout(error_layout)
	error_widget.setFixedHeight(24)

	layout.addWidget(error_widget)


        widget.setLayout(layout)

        return widget

    def chooseFile(self):
	current = self.file_path.text()

	start_directory = None
	default_value = None

	if current:
	    dirname = os.path.dirname(current)
	    default_value = os.path.basename(current)

	result = hou.ui.selectFile(
	    start_directory=start_directory,
	    pattern="*.json",
	    default_value=default_value,
	    chooser_mode=hou.fileChooserMode.Write
	)

	if not result:
	    return

	ext = os.path.splitext(result)[1]

	if not ext:
	    result = "{0}.json".format(result)

	self.file_path.setText(result)



    def clearError(self):
	self.error.clear()
	self.error.hide()
	self.error_icon.hide()


    def setError(self, msg):
	self.error.setText(msg)
	self.error.show()
	self.error_icon.show()

    def validateGroupName(self):
	self.clearError()

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

	if not self._group_name_valid:
	    self.setError(msg)

	self.validateAllValues()


    def validateFilePath(self):
	self.clearError()

	self._file_valid = True

	path = self.file_path.text()

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
	    self.setError("Invalid file path")

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
        model_items = model.aovs

        sel_model = self.list.selectionModel()

        items = utils.flattenList(items)

        for item in items:
            try:
                index = model_items.index(item)

            except ValueError:
                continue

            sel_model.select(model.index(index), sel_model.Select)

    def accept(self):
        group_name = self.group_name.text()
        file_path = self.file_path.text()

        new_group = aov.AOVGroup(group_name)

        indexes = self.list.selectionModel().selectedIndexes()

        for index in indexes:
            new_group.aovs.append(self.list.model().aovs[index.row()])



        self.newAOVGroupSignal.emit(new_group)
	return super(NewAOVGroupDialog, self).accept()

class NewAOVDialog(QtGui.QDialog):

    validInputSignal = QtCore.Signal(bool)
    newAOVSignal = QtCore.Signal(aov.AOV)

    def __init__(self, parent=None):
	super(NewAOVDialog, self).__init__(parent)

        self.setStyleSheet(hou.ui.qtStyleSheet())

	self._variable_valid = False
	self._file_valid = False

#	self.setModal(False)

	layout = QtGui.QVBoxLayout()

	self.widget = self.init_ui()

	layout.addWidget(self.widget)

	self.resize(450, 500)

	self.setMinimumWidth(450)
	self.setFixedHeight(500)


	self.setWindowTitle("Create AOV")

	self.setWindowIcon(
	    QtGui.QIcon(":ht/rsc/icons/sohohooks/aovs/create_aov.png")
	)

        self._buttonBox = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel
        )

        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)

	layout.addWidget(self._buttonBox)

	self._enableCreation(False)

	self.validInputSignal.connect(self._enableCreation)

	self.setLayout(layout)


    def init_ui(self):
	widget = QtGui.QWidget()
	layout = QtGui.QVBoxLayout()

	grid_layout = QtGui.QGridLayout()

	# =====================================================================

	grid_layout.addWidget(QtGui.QLabel("VEX Variable"), 1, 0)

	self.variable_name = QtGui.QLineEdit()
	grid_layout.addWidget(self.variable_name, 1, 1)

	self.variable_name.setFocus()

	self.variable_name.textChanged.connect(self.validateVariableName)

	# =====================================================================

	grid_layout.addWidget(QtGui.QLabel("VEX Type"), 2, 0)

	self.type_box = QtGui.QComboBox()

	for entry in data.VEXTYPE_MENU_ITEMS:
	    self.type_box.addItem(
		QtGui.QIcon(entry[2]),
		entry[1],
		entry[0]
	    )

	self.type_box.setCurrentIndex(1)

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

	pfilter_widget = QtGui.QWidget()


	pfilter_layout = QtGui.QHBoxLayout()
	pfilter_layout.setSpacing(1)
	pfilter_layout.setContentsMargins(0, 0, 0, 0)

	self.pfilter_name = QtGui.QLineEdit()
	pfilter_layout.addWidget(self.pfilter_name)

	pfilter_button = QtGui.QPushButton(
#	    QtGui.QIcon(":ht/rsc/icons/sohohooks/aovs/flyout_menu.png"),
	)

	pfilter_button.setIconSize(QtCore.QSize(16, 16))
	pfilter_button.setMaximumSize(QtCore.QSize(24, 24))

	pfilter_menu = QtGui.QMenu(pfilter_button)

	for item in data.PFILTER_MENU_ITEMS:
	    label, value = item

	    action = pfilter_menu.addAction(label)

	    action.triggered.connect(lambda value=value: self.pfilter_name.setText(value))

	pfilter_button.setMenu(pfilter_menu)

	pfilter_layout.addWidget(pfilter_button)


	pfilter_widget.setLayout(pfilter_layout)

	grid_layout.addWidget(pfilter_widget, 6, 1)

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
	    "Shading component names."
	)

        self.components.setText("diffuse reflect coat refract volume")
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
#	self.light_mask.setToolTip(
#	    "Shading component names."
#	)

        self.light_mask.setText("*")
        self.light_mask.setDisabled(True)

        self.lightexport.currentIndexChanged.connect(self._enableExports)

	grid_layout.addWidget(self.light_mask, 12, 1)

	# =====================================================================

        self.light_select_label = QtGui.QLabel("Light Selection")
        self.light_select_label.setDisabled(True)

        grid_layout.addWidget(self.light_select_label, 13, 0)

	self.light_select = QtGui.QLineEdit()
#	self.light_select.setToolTip(
#	    "Shading component names."
#	)

        self.light_select.setText("*")
        self.light_select.setDisabled(True)

        self.lightexport.currentIndexChanged.connect(self._enableExports)

	grid_layout.addWidget(self.light_select, 13, 1)

	# =====================================================================

	grid_layout.setRowMinimumHeight(14, 25)

	# =====================================================================

	grid_layout.addWidget(QtGui.QLabel("Comment"), 15, 0)

	self.comment = QtGui.QLineEdit()
	self.comment.setToolTip(
	    "Optional comment, eg. 'This AOV represents X'."
	)

	grid_layout.addWidget(self.comment, 15, 1)


	# =====================================================================

	grid_layout.setRowMinimumHeight(16, 25)

	# =====================================================================

	grid_layout.addWidget(QtGui.QLabel("File Path"), 17, 0)


	file_widget = QtGui.QWidget()

	file_layout = QtGui.QHBoxLayout()
	file_layout.setSpacing(0)
	file_layout.setContentsMargins(0, 0, 0, 0)

	self.file_path = QtGui.QLineEdit()
	file_layout.addWidget(self.file_path)

	file_button = QtGui.QPushButton(
	    QtGui.QIcon(":ht/rsc/icons/sohohooks/aovs/chooser_file.png"),
	    ""
	)

	file_button.setFlat(True)
	file_button.setIconSize(QtCore.QSize(16, 16))
	file_button.setMaximumSize(QtCore.QSize(24, 24))

	file_button.clicked.connect(self.chooseFile)

	file_layout.addWidget(file_button)

	file_widget.setLayout(file_layout)


	self.file_path.textChanged.connect(self.validateFilePath)

	grid_layout.addWidget(file_widget, 17, 1)


	# =====================================================================

	layout.addLayout(grid_layout)

	error_widget = QtGui.QWidget()
	error_widget.setContentsMargins(0,0,0,0)

	error_layout = QtGui.QHBoxLayout()
	error_layout.setContentsMargins(0,0,0,0)

	self.error_icon = QtGui.QLabel()
        self.error_icon.setFixedSize(24, 24)
        self.error_icon.setPixmap(
            QtGui.QIcon(":/ht/rsc/icons/sohohooks/aovs/warning.png").pixmap(24, 24)
        )
        self.error_icon.hide()

	error_layout.addWidget(self.error_icon)

	self.error = QtGui.QLabel("Enter a variable name.")

	error_layout.addWidget(self.error)

	error_widget.setLayout(error_layout)
	error_widget.setFixedHeight(24)

	layout.addWidget(error_widget)


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

    def clearError(self):
	self.error.clear()
	self.error.hide()
	self.error_icon.hide()


    def setError(self, msg):
	self.error.setText(msg)
	self.error.show()
	self.error_icon.show()

    def validateVariableName(self):
	self.clearError()

	variable_name = self.variable_name.text()
	variable_name = variable_name.strip()

	self._variable_valid = True

	if variable_name:
	    if ' ' in variable_name:
		self._variable_valid = False

	    elif not variable_name.isalnum():
		self._variable_valid = False

	if not self._variable_valid:
	    self.setError("Invalid variable name")

	self.validateAllValues()


    def validateFilePath(self):
	self.clearError()

	self._file_valid = True

	path = self.file_path.text()

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
	    self.setError("Invalid file path")

	self.validateAllValues()


    def validateAllValues(self):
	valid = True

	if not self._variable_valid:
	    valid = False

	if not self._file_valid:
	    valid = False

	self.validInputSignal.emit(valid)


    def chooseFile(self):
	current = self.file_path.text()

	start_directory = None
	default_value = None

	if current:
	    dirname = os.path.dirname(current)
	    default_value = os.path.basename(current)

	result = hou.ui.selectFile(
	    start_directory=start_directory,
	    pattern="*.json",
	    default_value=default_value,
	    chooser_mode=hou.fileChooserMode.Write
	)

	if not result:
	    return

	ext = os.path.splitext(result)[1]

	if not ext:
	    result = "{0}.json".format(result)

	self.file_path.setText(result)


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

	pfilter = self.pfilter_name.text()

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

	writer = manager.AOVWriter()

	writer.addAOV(new_aov)

#	writer.writeToFile(
#	    os.path.expandvars(self.file_path.text())
#	)


        self.newAOVSignal.emit(new_aov)
	return super(NewAOVDialog, self).accept()


    def reject(self):
	return super(NewAOVDialog, self).reject()

