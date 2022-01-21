from __future__ import annotations

from cloudshell.shell.core.driver_context import (
    AutoLoadAttribute,
    AutoLoadCommandContext,
    AutoLoadDetails,
    AutoLoadResource,
)

from cloudshell.cp.vcenter.constants import STATIC_SHELL_NAME


class StaticVcenterVMConfig:
    def __init__(self, name: str, attributes: dict | None = None):
        if attributes is None:
            attributes = {}
        self.attributes = attributes
        self.resources = {}
        self._cloudshell_model_name = STATIC_SHELL_NAME
        self._name = name

    def add_sub_resource(self, relative_path, sub_resource):
        self.resources[relative_path] = sub_resource

    @classmethod
    def create_from_context(
        cls, context: AutoLoadCommandContext
    ) -> StaticVcenterVMConfig:
        return StaticVcenterVMConfig(
            context.resource.name, context.resource.attributes.copy()
        )

    def create_autoload_details(self, relative_path=""):
        resources = [
            AutoLoadResource(
                model=self.resources[r].cloudshell_model_name,
                name=self.resources[r].name,
                relative_address=self._get_relative_path(r, relative_path),
            )
            for r in self.resources
        ]
        attributes = [
            AutoLoadAttribute(relative_path, a, self.attributes[a])
            for a in self.attributes
        ]
        autoload_details = AutoLoadDetails(resources, attributes)
        for r in self.resources:
            curr_path = relative_path + "/" + r if relative_path else r
            curr_auto_load_details = self.resources[r].create_autoload_details(
                curr_path
            )
            autoload_details = self._merge_autoload_details(
                autoload_details, curr_auto_load_details
            )
        return autoload_details

    def _get_relative_path(self, child_path, parent_path):
        """Combines relative path.

        :param child_path: Path of a model within it parent model, i.e 1
        :type child_path: str
        :param parent_path: Full path of parent model, i.e 1/1. Might be empty for
            root model
        :type parent_path: str
        :return: Combined path
        :rtype str
        """
        return parent_path + "/" + child_path if parent_path else child_path

    @staticmethod
    def _merge_autoload_details(autoload_details1, autoload_details2):
        """Merges two instances of AutoLoadDetails into the first one.

        :param autoload_details1:
        :type autoload_details1: AutoLoadDetails
        :param autoload_details2:
        :type autoload_details2: AutoLoadDetails
        :return:
        :rtype AutoLoadDetails
        """
        for attribute in autoload_details2.attributes:
            autoload_details1.attributes.append(attribute)
        for resource in autoload_details2.resources:
            autoload_details1.resources.append(resource)
        return autoload_details1

    @property
    def vm_name(self):
        return (
            self.attributes[f"{STATIC_SHELL_NAME}.VM Name"]
            if f"{STATIC_SHELL_NAME}.VM Name" in self.attributes
            else None
        )

    @vm_name.setter
    def vm_name(self, value):
        self.attributes[f"{STATIC_SHELL_NAME}.VM Name"] = value

    @property
    def vcenter_resource_name(self):
        return (
            self.attributes[f"{STATIC_SHELL_NAME}.vCenter Resource Name"]
            if f"{STATIC_SHELL_NAME}.vCenter Resource Name" in self.attributes
            else None
        )

    @vcenter_resource_name.setter
    def vcenter_resource_name(self, value):
        self.attributes[f"{STATIC_SHELL_NAME}.vCenter Resource Name"] = value

    @property
    def vcenter_port(self):
        return (
            self.attributes[f"{STATIC_SHELL_NAME}.vCenter Port"]
            if f"{STATIC_SHELL_NAME}.vCenter Port" in self.attributes
            else None
        )

    @vcenter_port.setter
    def vcenter_port(self, value="443"):
        self.attributes[f"{STATIC_SHELL_NAME}.vCenter Port"] = value

    @property
    def user(self):
        return (
            self.attributes[f"{STATIC_SHELL_NAME}.User"]
            if f"{STATIC_SHELL_NAME}.User" in self.attributes
            else None
        )

    @user.setter
    def user(self, value):
        self.attributes[f"{STATIC_SHELL_NAME}.User"] = value

    @property
    def password(self):
        return (
            self.attributes[f"{STATIC_SHELL_NAME}.Password"]
            if f"{STATIC_SHELL_NAME}.Password" in self.attributes
            else None
        )

    @password.setter
    def password(self, value):
        self.attributes[f"{STATIC_SHELL_NAME}.Password"] = value

    @property
    def public_ip(self):
        return (
            self.attributes[f"{STATIC_SHELL_NAME}.Public IP"]
            if f"{STATIC_SHELL_NAME}.Public IP" in self.attributes
            else None
        )

    @public_ip.setter
    def public_ip(self, value):
        self.attributes[f"{STATIC_SHELL_NAME}.Public IP"] = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def cloudshell_model_name(self):
        return self._cloudshell_model_name

    @cloudshell_model_name.setter
    def cloudshell_model_name(self, value):
        self._cloudshell_model_name = value


class GenericVPort:
    def __init__(self, name):
        self.attributes = {}
        self.resources = {}
        self._cloudshell_model_name = f"{STATIC_SHELL_NAME}.GenericVPort"
        self._name = name

    def add_sub_resource(self, relative_path, sub_resource):
        self.resources[relative_path] = sub_resource

    @classmethod
    def create_from_context(cls, context):
        """Creates an instance of NXOS by given context.

        :param context: cloudshell.shell.core.driver_context.ResourceCommandContext
        :type context: cloudshell.shell.core.driver_context.ResourceCommandContext
        :return:
        :rtype GenericVPort
        """
        result = GenericVPort(name=context.resource.name)
        for attr in context.resource.attributes:
            result.attributes[attr] = context.resource.attributes[attr]
        return result

    def create_autoload_details(self, relative_path=""):
        resources = [
            AutoLoadResource(
                model=self.resources[r].cloudshell_model_name,
                name=self.resources[r].name,
                relative_address=self._get_relative_path(r, relative_path),
            )
            for r in self.resources
        ]
        attributes = [
            AutoLoadAttribute(relative_path, a, self.attributes[a])
            for a in self.attributes
        ]
        autoload_details = AutoLoadDetails(resources, attributes)
        for r in self.resources:
            curr_path = relative_path + "/" + r if relative_path else r
            curr_auto_load_details = self.resources[r].create_autoload_details(
                curr_path
            )
            autoload_details = self._merge_autoload_details(
                autoload_details, curr_auto_load_details
            )
        return autoload_details

    def _get_relative_path(self, child_path, parent_path):
        """Combines relative path.

        :param child_path: Path of a model within it parent model, i.e 1
        :type child_path: str
        :param parent_path: Full path of parent model, i.e 1/1. Might be empty for
            root model
        :type parent_path: str
        :return: Combined path
        :rtype str
        """
        return parent_path + "/" + child_path if parent_path else child_path

    @staticmethod
    def _merge_autoload_details(autoload_details1, autoload_details2):
        """Merges two instances of AutoLoadDetails into the first one.

        :param autoload_details1:
        :type autoload_details1: AutoLoadDetails
        :param autoload_details2:
        :type autoload_details2: AutoLoadDetails
        :return:
        :rtype AutoLoadDetails
        """
        for attribute in autoload_details2.attributes:
            autoload_details1.attributes.append(attribute)
        for resource in autoload_details2.resources:
            autoload_details1.resources.append(resource)
        return autoload_details1

    @property
    def requested_vnic_name(self):
        return (
            self.attributes[f"{STATIC_SHELL_NAME}.GenericVPort.Requested vNIC Name"]
            if f"{STATIC_SHELL_NAME}.GenericVPort.Requested vNIC Name"
            in self.attributes
            else None
        )

    @requested_vnic_name.setter
    def requested_vnic_name(self, value):
        self.attributes[f"{STATIC_SHELL_NAME}.GenericVPort.Requested vNIC Name"] = value

    @property
    def bandwidth(self):
        return (
            self.attributes[f"{STATIC_SHELL_NAME}.GenericVPort.Bandwidth"]
            if f"{STATIC_SHELL_NAME}.GenericVPort.Bandwidth" in self.attributes
            else None
        )

    @bandwidth.setter
    def bandwidth(self, value):
        self.attributes[f"{STATIC_SHELL_NAME}.GenericVPort.Bandwidth"] = value

    @property
    def mac_address(self):
        return (
            self.attributes[f"{STATIC_SHELL_NAME}.GenericVPort.MAC Address"]
            if f"{STATIC_SHELL_NAME}.GenericVPort.MAC Address" in self.attributes
            else None
        )

    @mac_address.setter
    def mac_address(self, value):
        self.attributes[f"{STATIC_SHELL_NAME}.GenericVPort.MAC Address"] = value

    @property
    def ip_address(self):
        return (
            self.attributes[f"{STATIC_SHELL_NAME}.GenericVPort.IP Address"]
            if f"{STATIC_SHELL_NAME}.GenericVPort.IP Address" in self.attributes
            else None
        )

    @ip_address.setter
    def ip_address(self, value):
        self.attributes[f"{STATIC_SHELL_NAME}.GenericVPort.IP Address"] = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def cloudshell_model_name(self):
        return self._cloudshell_model_name

    @cloudshell_model_name.setter
    def cloudshell_model_name(self, value):
        self._cloudshell_model_name = value

    @property
    def model_name(self):
        return (
            self.attributes["CS_Port.Model Name"]
            if "CS_Port.Model Name" in self.attributes
            else None
        )

    @model_name.setter
    def model_name(self, value):
        self.attributes["CS_Port.Model Name"] = value
