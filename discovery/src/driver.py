from __future__ import annotations

from cloudshell.shell.core.driver_context import (
    AutoLoadCommandContext,
    AutoLoadDetails,
    ResourceCommandContext,
)
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext
from resource_config import StaticResourceConfig
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
            r_configs = StaticResourceConfig.from_context(context)

            for r_config in r_configs:
                with run_with_sandbox(api, r_config.cp_name) as rid:
                    api = CsApiWithSandbox.create(api, rid)
                    tool = self._get_tool(r_config, api, logger)
                    tool.discover()

        return AutoLoadDetails([], [])

    def remove_discovered_resources(self, context: ResourceCommandContext):
        with LoggingSessionContext(context) as logger:
            api = CloudShellSessionContext(context).get_api()
            r_config = StaticResourceConfig.from_context(context)[0]

            with run_with_sandbox(api, r_config.cp_name) as rid:
                api = CsApiWithSandbox.create(api, rid)
                tool = self._get_tool(r_config, api, logger)
                tool.clear()

    @staticmethod
    def _get_tool(
        r_config: StaticResourceConfig, api: CsApiWithSandbox, logger
    ) -> DiscoverVms:
        tool = DiscoverVms(
            r_config.cp_name,
            "Generic Static VM 2G",
            "Generic Static VM 2G.GenericVPort",
            api,
            logger,
            max_workers=r_config.max_workers,
            discover_max_vms=r_config.discover_max_vms,
            start_discover_from_num=r_config.start_discover_from_num,
        )
        return tool

    def cleanup(self):
        pass
