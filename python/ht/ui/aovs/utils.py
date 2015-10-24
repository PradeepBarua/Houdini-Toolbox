"""This module contains support functions for AOVs."""

# =============================================================================
# IMPORTS
# =============================================================================

# Python Imports
from PySide import QtCore, QtGui
import json
import os

# Houdini Toolbox Imports
from ht.sohohooks.aovs.aov import AOV, AOVGroup, ALLOWABLE_VALUES
from ht.ui.aovs import uidata
from ht.utils import convertFromUnicode

# Houdini Imports
import hou

# =============================================================================
# CLASSES
# =============================================================================

class AOVViewerInterface(QtCore.QObject):
    """This class acts as an interface between viewer related UI elements
    and the AOVManager.

    """

    # Signals for when AOVs are created or changed.
    aovAddedSignal = QtCore.Signal(AOV)
    aovRemovedSignal = QtCore.Signal(AOV)
    aovUpdatedSignal = QtCore.Signal(AOV)

    # Signals for when AOVGroups are created or changed.
    groupAddedSignal = QtCore.Signal(AOVGroup)
    groupRemovedSignal = QtCore.Signal(AOVGroup)
    groupUpdatedSignal = QtCore.Signal(AOVGroup)

    def __init__(self, parent=None):
        super(AOVViewerInterface, self).__init__(parent)

# =============================================================================
# NON-PUBLIC FUNCTIONS
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


def buildAOVsFromMultiparm(node):
    """Build a list of AOVs from a Mantra node's multiparm."""
    aovs = []

    num_aovs = node.evalParm("vm_numaux")

    for idx in range(1, num_aovs+1):
        aov_data = {
            "variable": node.evalParm("vm_variable_plane{}".format(idx)),
            "vextype": node.evalParm("vm_vextype_plane{}".format(idx))
        }

        channel = node.evalParm("vm_channel_plane{}".format(idx))
        if channel:
            aov_data["channel"] = channel

        aov_data["quantize"] = node.evalParm("vm_quantize_plane{}".format(idx))

        aov_data["sfilter"] = node.evalParm("vm_sfilter_plane{}".format(idx))

        pfilter = node.evalParm("vm_pfilter_plane{}".format(idx))

        if pfilter:
            aov_data["pfilter"] = node.evalParm("vm_pfilter_plane{}".format(idx))

        aov_data["componentexport"] = node.evalParm("vm_componentexport{}".format(idx))

        lightexport = node.evalParm("vm_lightexport{}".format(idx))
        lightexport = uidata.LIGHTEXPORT_MENU_ITEMS[lightexport][0]

        if lightexport:
            aov_data["lightexport"] = lightexport
            aov_data["lightexport_scope"] = node.evalParm("vm_lightexport_scope{}".format(idx))
            aov_data["lighexport_select"] = node.evalParm("vm_lightexport_select{}".format(idx))

        aovs.append(AOV(aov_data))

    return aovs


def filePathIsValid(path):
    """Check if a file path is valid."""
    if path:
        dirname = os.path.dirname(path)
        file_name = os.path.basename(path)

        if not dirname or not file_name:
            return False

        elif not os.path.splitext(file_name)[1]:
            return False

        return True

    return False


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


def getAOVNamesFromMultiparm(node):
    """Get a list of AOV names from a Mantra node's multiparm."""
    names = []

    num_aovs = node.evalParm("vm_numaux")

    for idx in range(1, num_aovs+1):
        names.append(node.evalParm("vm_variable_plane{}".format(idx)))

    return names


def getIconFromGroup(group):
    """Get the icon for an AOVGroup."""
    # Group has a custom icon path so use. it.
    if group.icon is not None:
        return QtGui.QIcon(group.icon)

    return QtGui.QIcon(":ht/rsc/icons/aovs/group.png")


def getIconFromVexType(vextype):
    """Get the icon corresponding to a VEX type."""
    return QtGui.QIcon(
        ":ht/rsc/icons/aovs/{}.png".format(
            vextype
        )
    )


def getLightExportMenuIndex(lightexport):
    """Find the menu index of the lightexport value."""
    return _getItemMenuIndex(
        uidata.LIGHTEXPORT_MENU_ITEMS,
        lightexport
    )


def getQuantizeMenuIndex(quantize):
    """Find the menu index of the quantize value."""
    return _getItemMenuIndex(
        uidata.QUANTIZE_MENU_ITEMS,
        quantize
    )


def getSFilterMenuIndex(sfilter):
    """Find the menu index of the sfilter value."""
    return _getItemMenuIndex(
        uidata.SFILTER_MENU_ITEMS,
        sfilter
    )


def getVexTypeMenuIndex(vextype):
    """Find the menu index of the vextype value."""
    return _getItemMenuIndex(
        uidata.VEXTYPE_MENU_ITEMS,
        vextype
    )


def isValueDefault(value, field):
    """Check if a value for a field is default."""
    return uidata.DEFAULT_VALUES[field] == value


def listAsString(elements):
    """Flatten a list of elements into a space separated string."""
    names = []

    for element in elements:
        if isinstance(element, AOVGroup):
            names.append("@{}".format(element.name))

        else:
            names.append(element.variable)

    return " ".join(names)
