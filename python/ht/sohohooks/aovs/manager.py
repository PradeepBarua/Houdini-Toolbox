
import glob
import json
import os



from ht.sohohooks.aovs.aov import AOV, AOVGroup
from ht.utils import convertFromUnicode




import hou





class AOVManager(object):


    def __init__(self):

	self._aovs = {}
	self._groups = {}


	self._initAOVs()


    @property
    def aovs(self):
	return sorted(self._aovs.values())

    @property
    def groups(self):
	return self._groups

    def _initAOVs(self):
	all_data = self._loadDataFromFiles()

	self._createAOVs(all_data)
	self._createGroups(all_data)


    def _createAOVs(self, all_data):
	for data in all_data:
	    if "definitions" not in data:
		continue

	    for definition in data["definitions"]:
		variable = definition["variable"]

		if variable in self._aovs:
		    continue

		aov = AOV(definition)

		self._aovs[variable] = aov


    def _createGroups(self, all_data):

	for data in all_data:
	    if "groups" not in data:
		continue

	    for name, group_data in data["groups"].iteritems():
                # Skip existing groups.
                if name in self.groups:
                    continue

		group = AOVGroup(name)

		if "include" in group_data:
		    includes = group_data["include"]

		    for include_name in includes:
			if include_name in self._aovs:
			    group.aovs.append(self._aovs[include_name])

                self.groups[name] = group


    def _loadDataFromFiles(self):
	paths = _findAOVFiles()

	return [self._loadDataFromFile(path) for path in paths]


    def _loadDataFromFile(self, path):
	with open(path) as f:
	    data = json.load(f, object_hook=convertFromUnicode)

	data["filepath"] = path

	return data




    def clear(self):
        self._aovs = {}
        self._groups = {}

    def reload(self):
	self._initAOVs()



    def load(self, path):
	data = [self._loadDataFromFile(path)]

	self._createAOVs(data)
	self._createGroups(data)



    def save(self):
	pass





    def getAOVsFromString(self, aov_str):
        aovs = []

        aov_str = aov_str.replace(',', ' ')

        for name in aov_str.split():
            if name.startswith('@'):
                name = name[1:]

                if name in self.groups:
                    aovs.append(self.groups[name])

            else:
                if name in self.aovs:
                    aovs.append(self.aovs[name])

        # TODO: Flatten?

        return aovs

    @staticmethod
    def addAOVsToIfd(wrangler, cam, now):
        import soho

        if _disableAOVs(wrangler, cam, now):
            return

        # The parameter that defines which automatic aovs to add.
        parms = {"auto_aovs": soho.SohoParm("auto_aovs", "str", [""])}

        # Attempt to evaluate the parameter.
        plist = cam.wrangle(wrangler, parms, now)

        if plist:
            aov_str = plist["auto_aovs"].Value[0]

            aov_list = aov_str.split()







def _disableAOVs(wrangler, cam, now):
    import soho

    # The parameter that defines if planes should be disabled or not.
    parms = {"disable": soho.SohoParm("disable_auto_aovs", "int", [False])}

    # Attempt to evaluate the parameter.
    plist = cam.wrangle(wrangler, parms, now)

    # Parameter exists.
    if plist:
        # If the parameter is set, return True to disable the aovs.
        if plist["disable"].Value[0] == 1:
            return True

    return False





def _findAOVFiles():

    try:
	directories = hou.findDirectories("config/aovs")

    except hou.OperationFailed:
	directories = []

    all_files = []

    for directory in directories:
	all_files.extend(glob.glob(os.path.join(directory, "*.json")))

    return all_files





def createSessionAOVManager():
    manager = AOVManager()
    hou.session.aov_manager = manager

    return manager

def findOrCreateSessionAOVManager():
    manager = None

    if hasattr(hou.session, "aov_manager"):
        manager = hou.session.aov_manager

    else:
        manager = createSessionAOVManager()

    return manager

