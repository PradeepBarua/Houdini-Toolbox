"""This module contains support functions for AOVs."""

# =============================================================================
# IMPORTS
# =============================================================================

# Python Imports
from PySide import QtGui
import json
import os

# Houdini Toolbox Imports
from ht.sohohooks.aovs import data
from ht.sohohooks.aovs.aov import AOV, AOVGroup, ALLOWABLE_VALUES
from ht.utils import convertFromUnicode

# Houdini Imports
import hou


# =============================================================================
# NON-FUNCTIONS
# =============================================================================

class AOVFileWriter(object):

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    def __init__(self):
        self._data = {}

    # =========================================================================
    # PROPERTIES
    # =========================================================================

    @property
    def data(self):
        return self._data

    # =========================================================================
    # METHODS
    # =========================================================================

    def addAOV(self, aov):
        definitions = self.data.setdefault("definitions", [])

        definitions.append(aov.data())

    def addGroup(self, group):
        groups = self.data.setdefault("groups", {})

        groups.update(group.data())

    def writeToFile(self, path):

        if os.path.exists(path):

            with open(path, 'r') as fp:
                data = json.load(fp, object_hook=convertFromUnicode)

                if "groups" in self.data:
                    groups = data.setdefault("groups", {})

                    for name, group_data in self.data["groups"].iteritems():
                        groups[name] = group_data

                if "definitions" in self.data:
                    definitions = data.setdefault("definitions", [])

                    for definition in self.data["definitions"]:
                        definitions.append(definition)

            with open(path, 'w') as fp:
                json.dump(data, fp, indent=4)

        else:
            with open(path, 'w') as fp:
                json.dump(self.data, fp, indent=4)


# =============================================================================
# NON-FUNCTIONS
# =============================================================================

def _getItemMenuIndex(items, item):
    """Function to determine which index an item represents."""
    idx = 0

    for itm in items:
        if item == itm[0]:
            return idx

        idx += 1

    return 0


# =============================================================================
# FUNCTIONS
# =============================================================================

def applyElementsAsParms(elements, nodes):
    """Apply a list of elemenents are multiparms."""
    aovs = flattenList(elements)

    for node in nodes:
        applyToNodeAsParms(node, aovs)


def applyElementsAsString(elements, nodes):
    """Apply a list of elements at rendertime."""
    value = listAsString(elements)

    for node in nodes:
        # Need to create the auto_aovs parameter if it doesn't exist.
        if not node.parm("auto_aovs"):
            ptg = node.parmTemplateGroup()

            # Toggle to enable/disable AOVs.
            parm_template = hou.ToggleParmTemplate(
                "enable_auto_aovs",
                "Automatic AOVs",
                1,
                help="Enable automatically adding AOVs."
            )

            parm_template.hideLabel(True)
            parm_template.setJoinWithNext(True)

            ptg.append(parm_template)

            # String parameter complete with group/AOV menu.
            parm_template = hou.StringParmTemplate(
                "auto_aovs",
                "Automatic AOVs",
                1,
                item_generator_script="from ht.sohohooks.aovs import manager\n\nreturn manager.buildMenuScript()",
                item_generator_script_language=hou.scriptLanguage.Python,
                menu_type=hou.menuType.StringToggle,
                help="Automatically add AOVs at IFD generation time."
            )

            parm_template.setConditional(
                hou.parmCondType.DisableWhen,
                "{ enable_auto_aovs == 0 }"
            )

            ptg.append(parm_template)
            node.setParmTemplateGroup(ptg)

        parm = node.parm("auto_aovs")
        parm.set(value)


# TODO: How to handle varying components?
def applyToNodeAsParms(node, aovs):
    """Apply a list of AOVs to a Mantra node using multiparm entries."""
    num_aovs = len(aovs)

    node.parm("vm_numaux").set(num_aovs)

    for idx, aov in enumerate(aovs, 1):
        node.parm("vm_variable_plane{}".format(idx)).set(aov.variable)
        node.parm("vm_vextype_plane{}".format(idx)).set(aov.vextype)

        if aov.channel is not None and aov.channel != aov.variable:
            node.parm("vm_channel_plane{}".format(idx)).set(aov.channel)

        if aov.planefile is not None:
            node.parm("vm_usefile_plane{}".format(idx)).set(True)
            node.parm("vm_filename_plane{}".format(idx)).set(aov.planefile)

        if aov.quantize is not None:
            node.parm("vm_quantize_plane{}".format(idx)).set(aov.quantize)

        if aov.sfilter is not None:
            node.parm("vm_sfilter_plane{}".format(idx)).set(aov.sfilter)

        if aov.pfilter is not None:
            node.parm("vm_pfilter_plane{}".format(idx)).set(aov.pfilter)

        if aov.componentexport:
            node.parm("vm_componentexport{}".format(idx)).set(True)

        if aov.lightexport is not None:
            menu_idx = ALLOWABLE_VALUES["lightexport"].index(aov.lightexport)
            node.parm("vm_lightexport{}".format(idx)).set(menu_idx)
            node.parm("vm_lightexport_scope{}".format(idx)).set(aov.lightexport_scope)
            node.parm("vm_lightexport_select{}".format(idx)).set(aov.lightexport_select)


def findSelectedMantraNodes():
    """Find any currently selected Mantra (ifd) nodes."""
    nodes = hou.selectedNodes()

    mantra_type = hou.nodeType("Driver/ifd")

    nodes = [node for node in nodes if node.type() == mantra_type]

    if not nodes:
        hou.ui.displayMessage(
            "No mantra nodes selected.",
            severity=hou.severityType.Error
        )

    return tuple(nodes)


# TODO: care about priority
def flattenList(elements):
    """Flatten a list of elements into a list of AOVs."""
    aovs = set()

    for element in elements:
        if isinstance(element, AOV):
            aovs.add(element)

        else:
            for aov in element.aovs:
                aovs.add(aov)

    return aovs


def getIconFromGroup(group):
    """Get the icon for an AOVGroup."""
    # Group has a custom icon path so use. it.
    if group.icon is not None:
        return QtGui.QIcon(group.icon)

    return QtGui.QIcon(":ht/rsc/icons/sohohooks/aovs/group.png")


def getIconFromVexType(vextype):
    """Get the icon corresponding to a VEX type."""
    return QtGui.QIcon(
        ":ht/rsc/icons/sohohooks/aovs/{}.png".format(
            vextype
        )
    )


def getLightExportMenuIndex(lightexport):
    """Find the menu index of the lightexport value."""
    return _getItemMenuIndex(
        data.LIGHTEXPORT_MENU_ITEMS,
        lightexport
    )


def getQuantizeMenuIndex(quantize):
    """Find the menu index of the quantize value."""
    return _getItemMenuIndex(
        data.QUANTIZE_MENU_ITEMS,
        quantize
    )


def getSFilterMenuIndex(sfilter):
    """Find the menu index of the sfilter value."""
    return _getItemMenuIndex(
        data.SFILTER_MENU_ITEMS,
        sfilter
    )


def getVexTypeMenuIndex(vextype):
    """Find the menu index of the vextype value."""
    return _getItemMenuIndex(
        data.VEXTYPE_MENU_ITEMS,
        vextype
    )


def isValueDefault(value, field):
    return data.DEFAULT_VALUES[field] == value


def listAsString(elements):
    """Flatten a list of elements into a space separated string."""
    names = []

    for element in elements:
        if isinstance(element, AOVGroup):
            names.append("@{}".format(element.name))

        else:
            names.append(element.variable)

    return " ".join(names)
