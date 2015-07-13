
from ht.sohohooks.aovs.aov import AOV, AOVGroup

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

        if aov.variable != aov.channel:
            node.parm("vm_channel_plane{0}".format(idx)).set(aov.channel)

        if aov.planefile is not None:
            node.parm("vm_usefile_plane{0}".format(idx)).set(True)
            node.parm("vm_filename_plane{0}".format(idx)).set(aov.planefile)

        node.parm("vm_quantize_plane{0}".format(idx)).set(aov.quantize)
        node.parm("vm_sfilter_plane{0}".format(idx)).set(aov.sfilter)

        if aov.pfilter is not None:
            node.parm("vm_pfilter_plane{0}".format(idx)).set(aov.pfilter)

        if aov.lightexport is not None:
            menu_idx = ALLOWABLE_VALUES["lightexport"].index(aov.lightexport)
            node.parm("vm_lightexport{0}".format(idx)).set(menu_idx)
            node.parm("vm_lightexport_scope{0}".format(idx)).set(aov.lightexport_scope)
            node.parm("vm_lightexport_select{0}".format(idx)).set(aov.lightexport_select)

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




# TODO: Create disable toggle too?

def applyElementsAsString(elements, nodes):
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



