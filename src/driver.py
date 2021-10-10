import jsonpickle
from cloudshell.cp.vcenter.commands.load_vm import VMLoader
from cloudshell.cp.vcenter.common.model_factory import ResourceModelParser
from cloudshell.cp.vcenter.common.vcenter.task_waiter import SynchronousTaskWaiter
from cloudshell.cp.vcenter.common.vcenter.vmomi_service import pyVmomiService
from cloudshell.cp.vcenter.network.dvswitch.name_generator import DvPortGroupNameGenerator
from cloudshell.cp.vcenter.vm.ip_manager import VMIPManager
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import InitCommandContext, ResourceCommandContext, AutoLoadResource, \
    AutoLoadAttribute, AutoLoadDetails, CancellationContext, ApiVmDetails
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext
from pyVim.connect import SmartConnect, Disconnect

from data_model import GenericStaticVcenterVMShell2G, GenericVPort
from pyVmomi import vim


class GenericStaticVcenterVMShell2GDriver(ResourceDriverInterface):

    def initialize(self, context):
        pass

    def __init__(self):
        self.model_parser = ResourceModelParser()
        self.ip_manager = VMIPManager()
        self.task_waiter = SynchronousTaskWaiter()
        self.pv_service = pyVmomiService(SmartConnect, Disconnect, self.task_waiter,
                                         port_group_name_generator=DvPortGroupNameGenerator())

    def get_inventory(self, context):
        """ Will locate vm in vcenter and fill its uuid """

        with LoggingSessionContext(context) as logger:
            logger.info("Start Autoload process")

            static_vm_config = GenericStaticVcenterVMShell2G.create_from_context(context)

            session = CloudShellSessionContext(context).get_api()

            vcenter_vm = static_vm_config.vm_name.replace("\\", "/")
            vcenter_name = static_vm_config.vcenter_resource_name

            logger.info("Start AutoLoading VM_Path: {0} on vCenter: {1}".format(vcenter_vm, vcenter_name))

            vm_api_res = session.GetResourceDetails(context.resource.name)
            vcenter_api_res = session.GetResourceDetails(vcenter_name)
            vcenter_resource = self.model_parser.convert_to_vcenter_model(vcenter_api_res)
            logger.info(f"Credentials are {vcenter_resource.user} at {vcenter_api_res.Address}")
            si = None

            try:
                logger.info("Connecting to vCenter ({0})".format(vcenter_api_res.Address))
                si = self._get_connection_to_vcenter(self.pv_service, session, vcenter_resource,
                                                     vcenter_api_res.Address,
                                                     static_vm_config.vcenter_port)

                logger.info("Loading VMs UUID")
                vm_loader = VMLoader(self.pv_service)

                vfw_uuid = vm_loader.load_vm_uuid_by_name(si, vcenter_resource, vcenter_vm)
                logger.info("Loading the IP of the VM")
                vfw_ip = self._try_get_ip(self.pv_service, si, vfw_uuid, vcenter_resource, logger)
                if vfw_ip:
                    session.UpdateResourceAddress(context.resource.name, vfw_ip)

                if not context.resource.address and not vfw_ip:
                    raise Exception("Determination of PanOS vFirewall IP address failed."
                                    "Please, verify that VM is up and running")

                vm = self.pv_service.get_vm_by_uuid(si, vfw_uuid)

                phys_interfaces = []

                for device in vm.config.hardware.device:
                    if isinstance(device, vim.vm.device.VirtualEthernetCard):
                        phys_interfaces.append(device)

                for port_number, phys_interface in enumerate(phys_interfaces):
                    network_adapter_number = phys_interface.deviceInfo.label.lower().strip("network adapter ")
                    relative_address = "P{}".format(network_adapter_number)
                    port = GenericVPort("Port {}".format(network_adapter_number))
                    port.mac_address = phys_interface.macAddress
                    port.requested_vnic_name = network_adapter_number
                    static_vm_config.add_sub_resource(relative_address, port)
                    logger.info(f"Added Port: model: {port.cloudshell_model_name} "
                                f"name: {port.name}, address: {relative_address}")

                result = static_vm_config.create_autoload_details("")
                if not vm_api_res.VmDetails:
                    result.attributes.append(AutoLoadAttribute("",
                                                               "VmDetails",
                                                               self._get_vm_details(vfw_uuid, vcenter_name)))
                    logger.info("UUID updated")
                elif vm_api_res.VmDetails.UID != vfw_uuid:
                    raise Exception("Detected VM UID doesn't match existing one.")

            finally:
                if si:
                    self.pv_service.disconnect(si)

            return result

    def _try_get_ip(self, pv_service, si, uuid, vcenter_resource, logger):
        ip = None
        try:
            vm = pv_service.get_vm_by_uuid(si, uuid)
            ip_res = self.ip_manager.get_ip(vm,
                                            vcenter_resource.holding_network,
                                            self.ip_manager.get_ip_match_function(None),
                                            cancellation_context=None,
                                            timeout=None,
                                            logger=logger)
            if ip_res.ip_address:
                ip = ip_res.ip_address
        except Exception:
            logger.debug("Error while trying to load VM({0}) IP".format(uuid), exc_info=True)
        return ip

    @staticmethod
    def _get_vm_details(uuid, vcenter_name):

        vm_details = ApiVmDetails()
        vm_details.UID = uuid
        vm_details.CloudProviderName = vcenter_name
        vm_details.CloudProviderFullName = vcenter_name
        vm_details.VmCustomParams = []
        str_vm_details = jsonpickle.encode(vm_details, unpicklable=False)
        return str_vm_details

    def _get_connection_to_vcenter(self, pv_service, session, vcenter_resource, address, port):
        password = self._decrypt_password(session, vcenter_resource.password)
        si = pv_service.connect(address,
                                vcenter_resource.user,
                                password,
                                port)
        return si

    @staticmethod
    def _decrypt_password(session, password):
        return session.DecryptPassword(password).Value

    def cleanup(self):
        pass
