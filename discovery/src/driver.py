from __future__ import annotations

from cloudshell.shell.core.driver_context import (
    AutoLoadCommandContext,
    AutoLoadDetails,
    ResourceCommandContext,
)
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext
from tool.cp_discovery import DiscoverVms
from tool.cs_api_with_sandbox import CsApiWithSandbox, run_with_sandbox


class CloudProviderAutodiscovery2GDriver(ResourceDriverInterface):
    def initialize(self, context):
        pass

    def __init__(self):
        pass

    def get_inventory(self, context: AutoLoadCommandContext) -> AutoLoadDetails:
        with LoggingSessionContext(context) as logger:
            api = CloudShellSessionContext(context).get_api()

            with run_with_sandbox(api) as rid:
                api = CsApiWithSandbox.create(api, rid)
                tool = self._get_tool(context, api, logger)
                tool.discover()

        return AutoLoadDetails([], [])

    def remove_discovered_resources(self, context: ResourceCommandContext):
        with LoggingSessionContext(context) as logger:
            api = CloudShellSessionContext(context).get_api()

            with run_with_sandbox(api) as rid:
                api = CsApiWithSandbox.create(api, rid)
                tool = self._get_tool(context, api, logger)
                tool.clear()

    @staticmethod
    def _get_tool(context, api: CsApiWithSandbox, logger) -> DiscoverVms:
        def _get_attr(name):
            return context.resource.attributes[f"{namespace}{name}"]

        namespace = f"{context.resource.model}."
        cp_name = _get_attr("Cloud Provider Resource Name")
        max_workers = int(_get_attr("Max Workers"))
        discover_max_vms = int(_get_attr("Discover Max VMs"))
        start_discover_from_num = int(_get_attr("Start Discover From Number"))

        tool = DiscoverVms(
            cp_name,
            "Generic Static VM 2G",
            "Generic Static VM 2G.GenericVPort",
            api,
            logger,
            max_workers=max_workers,
            discover_max_vms=discover_max_vms,
            start_discover_from_num=start_discover_from_num,
        )
        return tool

    def cleanup(self):
        pass
