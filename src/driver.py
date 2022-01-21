from __future__ import annotations

from logging import Logger

import jsonpickle
from cloudshell.shell.core.driver_context import (
    ApiVmDetails,
    AutoLoadAttribute,
    AutoLoadCommandContext,
    AutoLoadDetails,
)
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext

from data_model import GenericVPort, StaticVcenterVMConfig

from cloudshell.cp.vcenter.actions.vm_network import VMNetworkActions
from cloudshell.cp.vcenter.exceptions import VMIPNotFoundException
from cloudshell.cp.vcenter.handlers.dc_handler import DcHandler
from cloudshell.cp.vcenter.handlers.si_handler import SiHandler
from cloudshell.cp.vcenter.handlers.vm_handler import VmHandler
from cloudshell.cp.vcenter.resource_config import VCenterResourceConfig


class GenericStaticVcenterVMShell2GDriver(ResourceDriverInterface):
    def initialize(self, context):
        pass

    def __init__(self):
        pass

    def get_inventory(self, context: AutoLoadCommandContext) -> AutoLoadDetails:
        with LoggingSessionContext(context) as logger:
            logger.info("Start Autoload process")
            static_vm_conf = StaticVcenterVMConfig.create_from_context(context)
            api = CloudShellSessionContext(context).get_api()
            vcenter_name = static_vm_conf.vcenter_resource_name
            resource_conf = VCenterResourceConfig.from_cs_resource_details(
                api.GetResourceDetails(vcenter_name), api=api
            )
            logger.info(
                f"Credentials are {resource_conf.user} at {resource_conf.address}"
            )
            si = SiHandler.from_config(resource_conf, logger)
            dc = DcHandler.get_dc(resource_conf.default_datacenter, si)
            vm = dc.get_vm_by_path(static_vm_conf.vm_name)

            logger.info("Loading the IP of the VM")
            vfw_ip = self._try_get_ip(dc, vm, resource_conf, logger)
            if vfw_ip:
                api.UpdateResourceAddress(context.resource.name, vfw_ip)
            if not context.resource.address and not vfw_ip:
                raise Exception(
                    "Determination of the VM IP address failed."
                    "Please, verify that the VM is up and running"
                )

            self._add_ports(vm, static_vm_conf, logger)

            result = static_vm_conf.create_autoload_details("")
            vm_api_res = api.GetResourceDetails(context.resource.name)
            if not vm_api_res.VmDetails:
                result.attributes.append(
                    AutoLoadAttribute(
                        "",
                        "VmDetails",
                        self._get_vm_details(vm.uuid, vcenter_name),
                    )
                )
                logger.info("UUID updated")
            elif vm_api_res.VmDetails.UID != vm.uuid:
                raise Exception("Detected VM UUID doesn't match existing one.")
            return result

    @staticmethod
    def _try_get_ip(
        dc: DcHandler,
        vm: VmHandler,
        resource_conf: VCenterResourceConfig,
        logger: Logger,
    ) -> str | None:
        default_net = dc.get_network(resource_conf.holding_network)
        try:
            ip = VMNetworkActions(resource_conf, logger).get_vm_ip(
                vm._entity,
                default_net._entity,
            )
        except VMIPNotFoundException:
            ip = None
        return ip

    @staticmethod
    def _add_ports(
        vm: VmHandler, static_vm_conf: StaticVcenterVMConfig, logger: Logger
    ):
        for vnic in vm.vnics:
            net_number = vnic.label.lower().strip("network adapter ")
            relative_address = f"P{net_number}"
            port = GenericVPort(f"Port{net_number}")
            port.mac_address = vnic.mac_address
            port.requested_vnic_name = net_number
            static_vm_conf.add_sub_resource(relative_address, port)
            logger.info(
                f"Added Port: model: {port.cloudshell_model_name} "
                f"name: {port.name}, address: {relative_address}"
            )

    @staticmethod
    def _get_vm_details(uuid: str, vcenter_name: str) -> str:
        vm_details = ApiVmDetails()
        vm_details.UID = uuid
        vm_details.CloudProviderName = vcenter_name
        vm_details.CloudProviderFullName = vcenter_name
        vm_details.VmCustomParams = []
        str_vm_details = jsonpickle.encode(vm_details, unpicklable=False)
        return str_vm_details

    def cleanup(self):
        pass
