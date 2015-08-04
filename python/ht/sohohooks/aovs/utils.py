
from PySide import QtCore, QtGui

from ht.sohohooks.aovs.aov import AOV, AOVGroup, ALLOWABLE_VALUES
from ht.sohohooks.aovs import data

import hou

def listAsString(elements):
    names = []

    for element in elements:
        if isinstance(element, AOV):
            names.append(element.variable)

        else:
            names.append("@{}".format(element.name))

    return " ".join(names)

def applyToNodeAsParms(node, aovs):
    num_aovs = len(aovs)

    node.parm("vm_numaux").set(num_aovs)

    for idx, aov in enumerate(aovs, 1):
        node.parm("vm_variable_plane{0}".format(idx)).set(aov.variable)
        node.parm("vm_vextype_plane{0}".format(idx)).set(aov.vextype)

        if aov.channel is not None and aov.channel != aov.variable:
            node.parm("vm_channel_plane{0}".format(idx)).set(aov.channel)

        if aov.planefile is not None:
            node.parm("vm_usefile_plane{0}".format(idx)).set(True)
            node.parm("vm_filename_plane{0}".format(idx)).set(aov.planefile)

        if aov.quantize is not None:
            node.parm("vm_quantize_plane{0}".format(idx)).set(aov.quantize)

        if aov.sfilter is not None:
            node.parm("vm_sfilter_plane{0}".format(idx)).set(aov.sfilter)

        if aov.pfilter is not None:
            node.parm("vm_pfilter_plane{0}".format(idx)).set(aov.pfilter)

        # TODO: How to handle varying components?
        if aov.componentexport:
            node.parm("vm_componentexport{0}".format(idx)).set(True)

        if aov.lightexport is not None:
            menu_idx = ALLOWABLE_VALUES["lightexport"].index(aov.lightexport)
            node.parm("vm_lightexport{0}".format(idx)).set(menu_idx)
            node.parm("vm_lightexport_scope{0}".format(idx)).set(aov.lightexport_scope)
            node.parm("vm_lightexport_select{0}".format(idx)).set(aov.lightexport_select)


# TODO: care about priority
def flattenList(elements):
    aovs = set()

    for element in elements:
        if isinstance(element, AOV):
            aovs.add(element)

        else:
            for aov in element.aovs:
                aovs.add(aov)

    return aovs



def applyElementsAsParms(elements, nodes):
    aovs = flattenList(elements)

    for node in nodes:
        applyToNodeAsParms(node, aovs)


def applyElementsAsString(elements, nodes):
    value = listAsString(elements)

    for node in nodes:
        if not node.parm("auto_aovs"):
            ptg = node.parmTemplateGroup()

            parm_template = hou.ToggleParmTemplate(
                "enable_auto_aovs",
                "Automatic AOVs",
                1,
                help="Enable automatically adding AOVs."
            )

            parm_template.hideLabel(True)
            parm_template.setJoinWithNext(True)

            ptg.append(parm_template)


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



def getIconFromVexType(vextype):
    return QtGui.QIcon(
        ":ht/rsc/icons/sohohooks/aovs/{0}.png".format(
            vextype
        )
    )

def getIconFromGroup(group):
    if group.icon is not None:
        return QtGui.QIcon(group.icon)

    return QtGui.QIcon(":ht/rsc/icons/sohohooks/aovs/group.png")







def _getItemMenuIndex(items, item):
    idx = 0

    for data in items:
        if item == data[0]:
            return idx

        idx += 1

    return 0


def getVexTypeMenuIndex(vextype):
    return _getItemMenuIndex(
        data.VEXTYPE_MENU_ITEMS,
        vextype
    )

def getQuantizeMenuIndex(quantize):
    return _getItemMenuIndex(
        data.QUANTIZE_MENU_ITEMS,
        quantize
    )

def getSFilterMenuIndex(sfilter):
    return _getItemMenuIndex(
        data.SFILTER_MENU_ITEMS,
        sfilter
    )


def getLightExportMenuIndex(lightexport):
    return _getItemMenuIndex(
        data.LIGHTEXPORT_MENU_ITEMS,
        lightexport
    )


def findSelectedMantraNodes():
    nodes = hou.selectedNodes()

    mantra_type = hou.nodeType("Driver/ifd")

    nodes = [node for node in nodes if node.type() == mantra_type]

    if not nodes:
        hou.ui.displayMessage(
            "No mantra nodes selected.",
            severity=hou.severityType.Error
        )

    return tuple(nodes)

