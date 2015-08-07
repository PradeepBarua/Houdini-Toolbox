

import json



# =============================================================================
# CONSTANTS
# =============================================================================

# Allowable values for various settings.
ALLOWABLE_VALUES = {
    "lightexport": ("per-category", "per-light", "single"),
    "quantization": ("8", "16", "half", "float"),
    "vextype": ("float", "vector", "vector4")
}


# TODO: add some sort of priority, so you can control how things are overriden
# in the case of conflicts.

# TODO: Handle hidden plane parms?

class AOV(object):

    def __init__(self, data):

        self._componentexport = False
        self._components = []
        self._channel = None
        self._comment = ""
        self._lightexport = None
        self._lightexport_scope = "*"
        self._lightexport_select = "*"
        self._path = None
        self._pfilter = None
        self._planefile = None
        self._priority = -1
        self._quantize = None
        self._sfilter = None
        self._variable = None
        self._vextype = None


        for name, value in data.iteritems():
            if value is None:
                continue

            if name == "conditionals":
                continue

            # Check if there is a restriction on the data type.
            if name in ALLOWABLE_VALUES:
                # Get the allowable types for this data.
                allowable = ALLOWABLE_VALUES[name]

                # If the value isn't in the list, raise an exception.
                if value not in allowable:
                    raise InvalidAOVValueError(name, value, allowable)

            # If the key corresponds to attributes on this object we store
            # the data.
            if hasattr(self, name):
                setattr(self, name, value)

        if self.variable is None:
            raise MissingVariableError(variable)

        if self.vextype is None:
            raise MissingVexTypeError(variable)

    # =========================================================================
    # SPECIAL METHODS
    # =========================================================================

    def __cmp__(self, other):
        if isinstance(other, self.__class__):
            return cmp(self.variable, other.variable)

        return -1

    def __hash__(self):
        return hash(self.variable)

    def __repr__(self):
        return "<AOV {0} ({1})>".format(self.variable, self.vextype)

    def __str__(self):
        return self.variable

    # =========================================================================
    # INSTANCE PROPERTIES
    # =========================================================================

    @property
    def channel(self):
        """(str) The name of the output aov's channel."""
        return self._channel

    @channel.setter
    def channel(self, channel):
        self._channel = channel

    @property
    def comment(self):
        """(str) Optional comment about this AOV."""
        return self._comment

    @comment.setter
    def comment(self, comment):
        self._comment = comment

    @property
    def componentexport(self):
        return self._componentexport

    @componentexport.setter
    def componentexport(self, componentexport):
        self._componentexport = componentexport

    @property
    def components(self):
        return self._components

    @components.setter
    def components(self, components):
        self._components = components

#    @property
#    def conditionals(self):
#        """([RenderConditional]) RenderConditional objects for the aov."""
#        return self._conditionals

    @property
    def lightexport(self):
        """(str) The light output mode."""
        return self._lightexport

    @lightexport.setter
    def lightexport(self, lightexport):
        self._lightexport = lightexport

    @property
    def lightexport_scope(self):
        """(str) The light mask."""
        return self._lightexport_scope

    @lightexport_scope.setter
    def lightexport_scope(self, lightexport_scope):
        self._lightexport_scope = lightexport_scope

    @property
    def lightexport_select(self):
        """(str) The light selection (categories)."""
        return self._lightexport_select

    @lightexport_select.setter
    def lightexport_select(self, lightexport_select):
        self._lightexport_select = lightexport_select

    @property
    def path(self):
        """(str) The path containing the aov definition."""
        return self._path

    @path.setter
    def path(self, path):
        self._path = path

    @property
    def pfilter(self):
        """(str) The name of the output aov's pixel filter."""
        return self._pfilter

    @pfilter.setter
    def pfilter(self, pfilter):
        self._pfilter = pfilter

    @property
    def planefile(self):
        """(str) The name of the output aov's specific file, if any."""
        return self._planefile

    @planefile.setter
    def planefile(self, planefile):
        self._planefile = planefile

    @property
    def priority(self):
        return self._priority

    @priority.setter
    def priority(self, priority):
        self._priority = priority

    @property
    def quantize(self):
        """(str) The type of quantization for the output aov."""
        return self._quantize

    @quantize.setter
    def quantize(self, quantize):
        self._quantize = quantize

    @property
    def sfilter(self):
        """(str) The name of the output aov's sample filter."""
        return self._sfilter

    @sfilter.setter
    def sfilter(self, sfilter):
        self._sfilter = sfilter

    @property
    def variable(self):
        """(str) The name of the output aov's vex variable."""
        return self._variable

    @variable.setter
    def variable(self, variable):
        self._variable = variable

    @property
    def vextype(self):
        """(str) The data type of the output aov."""
        return self._vextype

    @vextype.setter
    def vextype(self, vextype):
        self._vextype = vextype

    # =========================================================================


    def data(self):
        d = {
            "variable": self.variable,
            "vextype": self.vextype,
        }

        if self.channel is not None:
            d["channel"] = self.variable

        if self.quantize is not None:
            d["quantize"] = self.quantize

        if self.sfilter is not None:
            d["sfilter"] = self.sfilter

        if self.pfilter is not None:
            d["pfilter"] = self.pfilter

        if self.componentexport is not None:
            d["componentexport"] = self.componentexport

            if self.components:
                d["components"] = self.components

        if self.lightexport is not None:
            d["lightexport"] = self.lightexport
            d["lightexport_scope"] = self.lightexport_scope
            d["lightexport_select"] = self.lightexport_select

        if self.comment is not None:
            d["comment"] = self.comment

        if self.priority > -1:
            d["priority"] = self.priority

        return d


    def writeToIfd(self, wrangler, cam, now):
        """Output all necessary aovs.

        Args:
            wrangler : (Object)
                A wrangler object.

            cam : (soho.SohoObject)
                The camera being rendered.

            now : (float)
                The parameter evaluation time.

        Raises:
            N/A

        Returns:
            None

        """
        import soho

        # The base data to pass along.
        data = self.data()

        # Apply any conditionals before the light export phase.
#        if self.conditionals:
#            for conditional in self.conditionals:
#                data.update(conditional.getData(wrangler, cam, now))

        channel = self.channel

        if channel is None:
            channel = self.variable

        if self.componentexport:
            components = self.components

            if not components:
                parms =  {
                    "components": soho.SohoParm("vm_exportcomponents", "str", [""], skipdefault=False),
                }

                plist = cam.wrangle(wrangler, parms, now)

                if plist:
                    components = plist["vm_exportcomponents"].Value[0]
                    components = components.split()

            for component in components:
                data["channel"] = "{}_{}".format(channel, component)
                data["component"] = component

                self.lightExportPlanes(data, wrangler, cam, now)

        else:
            data["channel"] = channel

            self.lightExportPlanes(data, wrangler, cam, now)

    def lightExportPlanes(self, data, wrangler, cam, now):
        base_channel = data["channel"]

        # Handle any light exporting.
        if self.lightexport is not None:
            # Get a list of lights matching our mask and selection.
            lights = cam.objectList(
                "objlist:light",
                now,
                self.lightexport_scope,
                self.lightexport_select
            )

            if self.lightexport == "per-light":
                # Process each light.
                for light in lights:
                    # Try and find the suffix using the 'vm_export_suffix'
                    # parameter.  If it doesn't exist, use an emptry string.
                    suffix = light.getDefaultedString(
                        "vm_export_suffix", now, ['']
                    )[0]

                    prefix = []

                    # Look for the prefix parameter.  If it doesn't exist, use
                    # the light's name and replace the '/' with '_'.  The
                    # default value of 'vm_export_prefix' is usually $OS.
                    if not light.evalString("vm_export_prefix", now, prefix):
                        prefix = [light.getName()[1:].replace('/', '_')]

                    # If there is a prefix we construct the channel name using
                    # it and the suffix.
                    if prefix:
                        channel = "{0}_{1}{2}".format(
                            prefix[0],
                            base_channel,
                            suffix
                        )

                    # If not and there is a valid suffix, add it to the channel
                    # name.
                    elif suffix:
                        channel = "{0}{1}".format(base_channel, suffix)

                    # Throw an error because all the per-light channels will
                    # have the same name.
                    else:
                        soho.error("Empty suffix for per-light exports.")

                    data["channel"] = channel
                    data["lightexport"] = light.getName()

                    # Write this light export to the ifd.
                    self.writeDataToIfd(data, wrangler, cam, now)

            elif self.lightexport == "single":
                # Take all the light names and join them together.
                lightexport = ' '.join([light.getName() for light in lights])

                # If there are no lights, we can't pass in an empty string
                # since then mantra will think that light exports are
                # disabled.  So pass down an string that presumably doesn't
                # match any light name.
                if not lightexport:
                    lightexport = "__nolights__"

                data["lightexport"] = lightexport

                # Write the combined light export to the ifd.
                self.writeDataToIfd(data, wrangler, cam, now)

            elif self.lightexport == "per-category":
                # A mapping between category names and their member lights.
                categoryMap = {}

                # Process each selected light.
                for light in lights:
                    # Get the category for the light.
                    categories = []
                    light.evalString("categories", now, categories)

                    # Light doesn't have a 'categories' parameter.
                    if not categories:
                        continue

                    # Get the raw string.
                    categories = categories[0]

                    # Since the categories value can be space or comma
                    # separated we replace the commas with spaces then split.
                    categories = categories.replace(',', ' ')
                    categories = categories.split()

                    # If the categories list was empty, put the light in a fake
                    # category.
                    if not categories:
                        noCatLights = categoryMap.setdefault("__none__", [])
                        noCatLights.append(light)

                    else:
                        # For each category the light belongs to, add it to
                        # the list.
                        for category in categories:
                            catLights = categoryMap.setdefault(category, [])
                            catLights.append(light)

                # Process all the found categories and their member lights.
                for category, lights in categoryMap.iteritems():
                    # Construct the export string to contain all the member
                    # lights.
                    lightexport = ' '.join(
                        [light.getName() for light in lights]
                    )

                    data["lightexport"] = lightexport

                    # The channel is the regular channel named prefixed with
                    # the category name.
                    data["channel"] = "{0}_{1}".format(category, base_channel)

                    # Write the per-category light export to the ifd.
                    self.writeDataToIfd(data, wrangler, cam, now)

        else:
            # Write a normal aov definition.
            self.writeDataToIfd(data, wrangler, cam, now)

    @staticmethod
    def writeDataToIfd(data, wrangler, cam, now):
        """Write aov data to the ifd.

        Args:
            data : (dict)
                The data dictionary containing output information.

            wrangler : (Object)
                A wrangler object.

            cam : (soho.SohoObject)
                The camera being rendered.

            now : (float)
                The parameter evaluation time.

        Raises:
            N/A

        Returns:
            None

        """
        import IFDapi

        # Call the 'pre_defplane' hook.  If the function returns True,
        # return.
        if _callPreDefPlane(data, wrangler, cam, now):
            return

        # Start of plane block in IFD.
        IFDapi.ray_start("plane")

        # Primary block information.
        IFDapi.ray_property("plane", "variable", [data["variable"]])
        IFDapi.ray_property("plane", "vextype", [data["vextype"]])
        IFDapi.ray_property("plane", "channel", [data["channel"]])

        if "quantize" in data:
            IFDapi.ray_property("plane", "quantize", [data["quantize"]])

        # Optional aov information.
        if "planefile" in data:
            planefile = data["planefile"]

            if planefile is not None:
                IFDapi.ray_property("plane", "planefile", [planefile])

        if "lightexport" in data:
            IFDapi.ray_property("plane", "lightexport", [data["lightexport"]])

        if "pfilter" in data:
            IFDapi.ray_property("plane", "pfilter", [data["pfilter"]])

        if "sfilter" in data:
            IFDapi.ray_property("plane", "sfilter", [data["sfilter"]])

        if "component" in data:
            IFDapi.ray_property("plane", "component", [data["component"]])

        # Call the 'post_defplane' hook.
        if _callPostDefPlane(data, wrangler, cam, now):
            return

        # End the plane definition block.
        IFDapi.ray_end()


# TODO: Add support for overriding export components per group? @foo:diffuse,reflect,...?

class AOVGroup(object):
    """An object representing a group of AOV definitions.

    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    def __init__(self, name):
        """Initialize a AOVGroup.

        Args:
            name : (str)
                The name of the group.

            file_path : (str)
                The path containing the group definition.

        Raises:
            N/A

        Returns:
            N/A

        """
        self._aovs = []
        self._comment = ""
        self._icon = None
        self._name = name
        self._path = None
        self._priority = -1

        self._includes = []

    # =========================================================================
    # SPECIAL METHODS
    # =========================================================================

    def __repr__(self):
        return "<AOVGroup {0} ({1} aovs)>".format(
            self.name,
            len(self.aovs)
        )

    def __str__(self):
        return self.name

    def __cmp__(self, other):
        if isinstance(other, self.__class__):
            return cmp(self.name, other.name)

        return -1

    # =========================================================================
    # INSTANCE PROPERTIES
    # =========================================================================

    @property
    def aovs(self):
        """([AOV]) A list of AOVs in the group."""
        return self._aovs

    @property
    def comment(self):
        """(str) Optional comment about this AOV."""
        return self._comment

    @comment.setter
    def comment(self, comment):
        self._comment = comment

    @property
    def icon(self):
        return self._icon

    @icon.setter
    def icon(self, icon):
        self._icon = icon

    @property
    def includes(self):
        return self._includes

    @property
    def path(self):
        """(str) The path containing the group definition."""
        return self._path

    @path.setter
    def path(self, path):
        self._path = path

    @property
    def name(self):
        """(str) The name of the group."""
        return self._name

    @property
    def priority(self):
        return self._priority

    @priority.setter
    def priority(self, priority):
        self._priority = priority

    # =========================================================================
    # PUBLIC FUNCTIONS
    # =========================================================================

    def clear(self):
        self.aovs[:] = []

    def data(self):
        d = {
            self.name: {
                "include": [aov.variable for aov in self.aovs],
            }
        }

        if self.comment:
            d[self.name]["comment"] = self.comment

        return d



    def writeToIfd(self, wrangler, cam, now):
        """Write all aovs in the group to the ifd.

        Args:
            wrangler : (Object)
                A wrangler object.

            cam : (soho.SohoObject)
                The camera being rendered.

            now : (float)
                The parameter evaluation time.

        Raises:
            N/A

        Returns:
            None

        """
        for aov in self.aovs:
            aov.writeToIfd(wrangler, cam, now)







# =============================================================================
# EXCEPTIONS
# =============================================================================

class InvalidAOVValueError(Exception):
    """Exception for invalid aov setting values.

    """

    def __init__(self, name, value, allowable):
        super(InvalidAOVValueError, self).__init__()
        self.allowable = allowable
        self.name = name
        self.value = value

    def __str__(self):
        return "Invalid value '{0}' in '{1}': Must be one of {2}".format(
            self.value,
            self.name,
            self.allowable
        )


class MissingVariable(Exception):
    """Exception for missing 'variable' information.

    """

    def __init__(self, variable):
        super(MissingVariableError, self).__init__()
        self.variable = variable

    def __str__(self):
        return "Cannot create aov {0}: missing 'variable'.".format(
            self.variable
        )

class MissingVexTypeError(Exception):
    """Exception for missing 'vextype' information.

    """

    def __init__(self, vextype):
        super(MissingVexTypeError, self).__init__()
        self.vextype = vextype

    def __str__(self):
        return "Cannot create aov {0}: missing 'vextype'.".format(
            self.vextype
        )


def _callPostDefPlane(data, wrangler, cam, now):
    import IFDhooks

    return IFDhooks.call(
        "post_defplane",
        data["variable"],
        data["vextype"],
        -1,
        wrangler,
        cam,
        now,
        data.get("planefile"),
        data.get("lightexport")
    )

def _callPreDefPlane(data, wrangler, cam, now):
    import IFDhooks

    return IFDhooks.call(
        "pre_defplane",
        data["variable"],
        data["vextype"],
        -1,
        wrangler,
        cam,
        now,
        data.get("planefile"),
        data.get("lightexport")
    )
