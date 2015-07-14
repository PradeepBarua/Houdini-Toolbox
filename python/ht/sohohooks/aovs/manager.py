
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
        self._interface = None


	self._initAOVs()

    def __repr__(self):
        return "<AOVManager>"


    @property
    def interface(self):
        return self._interface

    def initInterface(self):
        import ht.sohohooks.aovs.viewer
        self._interface = ht.sohohooks.aovs.viewer.AOVViewerInterface()


    # TODO: Why is this a list of values?
    # Why is _aovs a dict???
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

                self.addAOV(aov)
#		self._aovs[variable] = aov


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

#                self.groups[name] = group
                self.addGroup(group)


    def _loadDataFromFiles(self):
	paths = _findAOVFiles()

	return [self._loadDataFromFile(path) for path in paths]


    def _loadDataFromFile(self, path):
	with open(path) as f:
	    data = json.load(f, object_hook=convertFromUnicode)

	data["filepath"] = path

	return data


    def addAOV(self, aov):
        self._aovs[aov.variable] = aov

        if self.interface is not None:
            self.interface.aovAddedSignal.emit(aov)


    def addGroup(self, group):
        self.groups[group.name] = group

        if self.interface is not None:
            self.interface.groupAddedSignal.emit(group)


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
                if name in self._aovs:
                    aovs.append(self._aovs[name])

        return aovs

    @staticmethod
    def addAOVsToIfd(wrangler, cam, now):
        import soho

        # The parameter that defines which automatic aovs to add.
        parms = {
            "auto_aovs": soho.SohoParm("auto_aovs", "str", [""], skipdefault=False),
            "disable": soho.SohoParm("disable_auto_aovs", "int", [0], skipdefault=False)
        }

        # Attempt to evaluate the parameter.
        plist = cam.wrangle(wrangler, parms, now)

        if plist:
            if plist["disable_auto_aovs"].Value[0] == 1:
                return

            aov_str = plist["auto_aovs"].Value[0]

            manager = AOVManager()

            # Parse the string to get any aovs/groups.
            aovs = manager.getAOVsFromString(aov_str)

            # Write any found items to the ifd.
            for aov in aovs:
                aov.writeToIfd(wrangler, cam, now)


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


class AOVWriter(object):


    def __init__(self):
        self._data = {}

    @property
    def data(self):
        return self._data


    def addAOV(self, aov):
        definitions = self.data.setdefault("definitions", [])

        definitions.append(aov.data())

    def addGroup(self, group):
        groups = self.data.setdefault("groups", {})

        groups.update(group.data())



    def writeToFile(self, path):
        with open(path, 'w') as f:
            json.dump(self.data, f, indent=4)




