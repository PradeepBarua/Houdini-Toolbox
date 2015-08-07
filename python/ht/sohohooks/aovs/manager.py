"""This module contains classes and funcions for high level interaction
with AOVs.

"""

# =============================================================================
# IMPORTS
# =============================================================================

# Python Imports
import glob
import json
import os

# Houdini Toolbox Imports
import ht.sohohooks.aovs.aov
#from ht.sohohooks.aovs.aov import AOV, AOVGroup
from ht.utils import convertFromUnicode

# Houdini Imports
import hou


# =============================================================================
# CLASSES
# =============================================================================

class AOVManager(object):

    def __init__(self):
        self._aovs = {}
        self._groups = {}
        self._interface = None

#        self._initAOVs()

        self._initFromFiles()

    def __repr__(self):
        return "<AOVManager>"

    @property
    def interface(self):
        return self._interface

    # TODO: Why is this a list of values?
    # Why is _aovs a dict???
    @property
    def aovs(self):
        return self._aovs
        return self._aovs.values()
        return sorted(self._aovs.values())

    @property
    def groups(self):
        return self._groups


    def _initFromFiles(self):
        file_paths = _findAOVFiles()

        readers = [AOVFileReader(file_path) for file_path in file_paths]

        self.mergeReaders(readers)

    def mergeReaders(self, readers):
        for reader in readers:
            for aov in reader.aovs:
                variable_name = aov.variable

                if variable_name in self._aovs:
                    if aov.priority > self._aovs[variable_name].priority:
                        self.addAOV(aov)

                else:
                    self.addAOV(aov)

        for reader in readers:
            for group in reader.groups:
                self._initGroupMembers(group)

                group_name = group.name

                if group_name in self.groups:
                    if group.priority > self.groups[group_name].priority:
                        self.addGroup(group)

                else:
                    self.addGroup(group)


    def _initGroupMembers(self, group):
        for include in group.includes:
            if include in self._aovs:
                group.aovs.append(self._aovs[include])


    def addAOV(self, aov):
        """Add an AOV to the manager."""
        self._aovs[aov.variable] = aov

        if self.interface is not None:
            self.interface.aovAddedSignal.emit(aov)


    def addGroup(self, group):
        """Add an AOVGroup to the manager."""
        self.groups[group.name] = group

        if self.interface is not None:
            self.interface.groupAddedSignal.emit(group)


    def clear(self):
        """Clear all definitions."""
        self._aovs = {}
        self._groups = {}


    def initInterface(self):
        import ht.sohohooks.aovs.viewer
        self._interface = ht.sohohooks.aovs.viewer.AOVViewerInterface()


    def reload(self):
        """Reload all definitions."""
        #self._initAOVs()
        self._initFromFiles()



    def load(self, path):
        readers = [AOVFileReader(path)]

        self.mergeReaders(readers)

    def save(self):
        pass

    def getAOVsFromString(self, aov_str):
        """Get a list of AOVs and AOVGroups from a string."""
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

    # TODO: Why is this static?  Couldn't sohohook instantiate and call?
    @staticmethod
    def addAOVsToIfd(wrangler, cam, now):
        """Add auto_aovs to the ifd."""
        import soho

        # The parameter that defines which automatic aovs to add.
        parms = {
            "enable": soho.SohoParm("enable_auto_aovs", "int", [1], skipdefault=False),
            "auto_aovs": soho.SohoParm("auto_aovs", "str", [""], skipdefault=False),
        }

        # Attempt to evaluate the parameter.
        plist = cam.wrangle(wrangler, parms, now)

        if plist:
            # Adding is disabled so bail out.
            if plist["enable_auto_aovs"].Value[0] == 0:
                return

            aov_str = plist["auto_aovs"].Value[0]

            # Construct a manager-laf
            manager = findOrCreateSessionAOVManager()

            # Parse the string to get any aovs/groups.
            aovs = manager.getAOVsFromString(aov_str)

            # Write any found items to the ifd.
            for aov in aovs:
                aov.writeToIfd(wrangler, cam, now)


class AOVFileReader(object):
    def __init__(self, path):
        self._aovs = []
        self._groups = []

        self._path = path

        self.test()

    @property
    def aovs(self):
        return self._aovs

    @property
    def groups(self):
        return self._groups

    @property
    def path(self):
        return self._path

    @staticmethod
    def readFromFile(path):
        with open(path) as fp:
            data = json.load(fp, object_hook=convertFromUnicode)

        data["path"] = path
        return data

    def test(self):
        data = self.readFromFile(self.path)

        if "definitions" in data:
            self.createAOVs(data["definitions"])

        if "groups" in data:
            self.createGroups(data["groups"])

    def createAOVs(self, data):
        for definition in data:
            definition["path"] = self.path

            aov = ht.sohohooks.aovs.aov.AOV(definition)

            print aov, aov.channel

            self.aovs.append(aov)

    def createGroups(self, data):
        for name, group_data in data.iteritems():
            # Skip existing groups.
            #if name in self.groups:
            #    continue

            group = ht.sohohooks.aovs.aov.AOVGroup(name)

            if "include" in group_data:
                group.includes.extend(group_data["include"])

            if "comment" in group_data:
                group.comment = group_data["comment"]

            if "icon" in group_data:
                group.icon = os.path.expandvars(group_data["icon"])

            group.path = self.path

            self.groups.append(group)



# =============================================================================
# NON-PUBLIC FUNCTIONS
# =============================================================================

# TODO: Use a custom scan path if available?
def _findAOVFiles():
    """Find any .json files that should be read."""

    try:
        directories = hou.findDirectories("config/aovs")

    except hou.OperationFailed:
        directories = []

    all_files = []

    for directory in directories:
        all_files.extend(glob.glob(os.path.join(directory, "*.json")))

    return all_files


# =============================================================================
# FUNCTIONS
# =============================================================================

def buildMenuScript():
    """Build a menu script for choosing AOVs and groups."""
    manager = findOrCreateSessionAOVManager()

    menu = []

    if manager.groups:
        for group in sorted(manager.groups.keys()):
            menu.extend(["@{0}".format(group), group])

        menu.extend(["_separator_", "---------"])

    for aov in manager.aovs:
        menu.extend([aov.variable, aov.variable])

    return menu


def createSessionAOVManager():
    """Create an AOVManager stored in hou.session."""
    manager = AOVManager()
    hou.session.aov_manager = manager

    return manager


def findOrCreateSessionAOVManager(rebuild=False):
    """Find or create an AOVManager from hou.session."""
    manager = None

    if hasattr(hou.session, "aov_manager") and not rebuild:
        manager = hou.session.aov_manager

    else:
        manager = createSessionAOVManager()

    return manager


# =============================================================================
# GLOBALS
# =============================================================================

MANAGER = findOrCreateSessionAOVManager(rebuild=True)
