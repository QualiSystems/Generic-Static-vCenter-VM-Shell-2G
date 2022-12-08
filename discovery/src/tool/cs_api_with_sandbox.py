from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from cloudshell.api.cloudshell_api import (
    CloudShellAPISession,
    CommandExecutionCompletedResultInfo,
    InputNameValue,
)


class CsApiWithSandbox(CloudShellAPISession):
    def __init__(self, *args, rid=None, **kwargs):
        super().__init__(*args, **kwargs)
        assert rid is not None
        self.rid = rid

    @classmethod
    def create(cls, api: CloudShellAPISession, rid: str) -> CsApiWithSandbox:
        return CsApiWithSandbox(
            api.host,
            api.username,
            api.password,
            api.domain,
            token_id=api.authentication.logon_manager.token_id,
            rid=rid,
        )

    def run_resource_command(
        self, resource: str, command: str, params: dict | None = None
    ) -> CommandExecutionCompletedResultInfo:
        params = params or {}
        command_inputs = [InputNameValue(k, v) for k, v in params.items()]
        return self.ExecuteCommand(
            self.rid, resource, "Resource", command, command_inputs
        )

    def run_connected_command(
        self, resource: str, command: str, tags: str
    ) -> CommandExecutionCompletedResultInfo:
        return self.ExecuteResourceConnectedCommand(self.rid, resource, command, tags)

    def refresh_vm_details(self, resources: list[str] | None) -> None:
        self.RefreshVMDetails(self.rid, resources)

    def add_to_reservation(self, resources: list[str]) -> None:
        self.AddResourcesToReservation(self.rid, resources)

    def remove_from_reservation(self, resources: list[str]) -> None:
        self.RemoveResourcesFromReservation(self.rid, resources)

    def iterate_resources(self, folder: str) -> Generator[str, None, None]:
        for entity in self.GetFolderContent(folder).ContentArray:
            if entity.Type == "Resource":
                yield entity.Name


@contextmanager
def run_with_sandbox(api: CloudShellAPISession, cp_name: str) -> str:
    username = api.GetAllUsersDetails().Users[0].Name
    r_name = f"Quali CloudProvider Autodiscovery - {cp_name}"
    rid = api.CreateImmediateReservation(r_name, username, 120).Reservation.Id
    try:
        yield rid
    finally:
        api.EndReservation(rid)
