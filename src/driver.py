from __future__ import annotations

from contextlib import contextmanager

import jsonpickle
from cloudshell.api.cloudshell_api import CloudShellAPISession, InputNameValue
from cloudshell.shell.core.driver_context import AutoLoadCommandContext, AutoLoadDetails
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext


class GenericStaticVMShell2GDriver(ResourceDriverInterface):
    def initialize(self, context):
        pass

    def __init__(self):
        pass

    def get_inventory(self, context: AutoLoadCommandContext) -> AutoLoadDetails:
        with LoggingSessionContext(context) as logger:
            logger.info("Start Autoload process")
            api = CloudShellSessionContext(context).get_api()
            cp_name = context.resource.attributes[
                f"{context.resource.model}.Cloud Provider Resource Name"
            ]
            vm_path = context.resource.attributes[f"{context.resource.model}.VM Name"]
            params = {
                "vm_path": vm_path,
                "model": context.resource.model,
                "port_model": f"{context.resource.model}.GenericVPort",
            }
            command_inputs = [InputNameValue(k, v) for k, v in params.items()]

            with run_with_sandbox(api) as rid:
                json_data = api.ExecuteCommand(
                    rid,
                    cp_name,
                    "Resource",
                    "get_autoload_details_for_vm",
                    command_inputs,
                ).Output

            autoload_details = jsonpickle.decode(json_data)

            info = api.GetResourceDetails(context.resource.name)
            if info.VmDetails:
                for attr in autoload_details.attributes[:]:
                    if attr.attribute_name == "VmDetails":
                        autoload_details.attributes.remove(attr)
                        break

        return autoload_details

    def cleanup(self):
        pass


@contextmanager
def run_with_sandbox(api: CloudShellAPISession) -> str:
    username = api.GetAllUsersDetails().Users[0].Name
    r_name = "Quali CloudProvider Autodiscovery"
    reservations = api.GetCurrentReservations(username).Reservations
    for r in reservations:
        if r.Name == r_name:
            rid = r.Id
            existed_reservation = True
            break
    else:
        rid = api.CreateImmediateReservation(r_name, username, 120).Reservation.Id
        existed_reservation = False
    try:
        yield rid
    finally:
        if not existed_reservation:
            api.EndReservation(rid)
