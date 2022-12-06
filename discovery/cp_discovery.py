from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from itertools import islice
from logging import Logger
from threading import Lock
from typing import Iterable, TypeVar
from uuid import uuid4

import attr
from cloudshell.api.cloudshell_api import (
    AttributeNameValue,
    ResourceAttributesUpdateRequest,
)
from cloudshell.api.common_cloudshell_api import CloudShellAPIError

from discovery.cs_api_with_sandbox import CsApiWithSandbox


class AutoloadFailed(Exception):
    def __init__(self, resource_name: str):
        self.resource_name = resource_name
        super().__init__(f"Autoload failed for {resource_name}")


class DiscoveryFailed(Exception):
    def __init__(self, vm_names: list[str]):
        super().__init__(f"Discovery failed for {vm_names}. See logs for details")


@attr.s(auto_attribs=True)
class CloudProviderVmInfo:
    path: str
    uuid: str
    resource_path: ResourceFullPath

    @classmethod
    def create(
        cls, path: str, uuid: str, api: CsApiWithSandbox, cp_name: str
    ) -> CloudProviderVmInfo:
        resource_path = ResourceFullPath.create(api, cp_name, path)
        return cls(path, uuid, resource_path)


@attr.s(auto_attribs=True)
class DiscoverVms:
    cp_name: str
    resource_model: str
    port_model: str
    api: CsApiWithSandbox
    logger: Logger
    max_workers: int = 10
    discover_max_vms: int | None = None
    start_discover_from_num: int = 0

    def __attrs_post_init__(self):
        self.failed_vms: list[CloudProviderVmInfo] = []
        self.discovered_lock = Lock()
        self.discovered_resources: list[Resource] = []

    def discover(self) -> None:
        vms = self._get_vms()
        vms = self._limit_discovering_vms(vms)
        self._create_folders(vms)
        self._discover_resources_in_parallel(vms)
        self._raise_for_failed_vms()

    def clear(self):
        for r in self.api.FindResources(resourceModel=self.resource_model).Resources:
            self.api.DeleteResource(r.FullName)

    def _get_vms(self) -> list[CloudProviderVmInfo]:
        res = self.api.run_resource_command(self.cp_name, "get_vms")
        list_of_dicts = json.loads(res.Output)
        vms = [
            CloudProviderVmInfo.create(vm["path"], vm["uuid"], self.api, self.cp_name)
            for vm in list_of_dicts
        ]
        return vms

    def _limit_discovering_vms(
        self, vms: list[CloudProviderVmInfo]
    ) -> list[CloudProviderVmInfo]:
        if self.discover_max_vms:
            start = self.start_discover_from_num
            stop = self.start_discover_from_num + self.discover_max_vms
            vms = vms[start:stop]
        else:
            vms = vms[self.start_discover_from_num :]
        return vms

    @staticmethod
    def _create_folders(vms: list[CloudProviderVmInfo]) -> None:
        created_folders = set()
        for vm in vms:
            if vm.resource_path.folders not in created_folders:
                vm.resource_path.create_folders()
                created_folders.add(vm.resource_path.folders)

    def _discover_resources(self, vms: list[CloudProviderVmInfo]) -> None:
        for i, vm in enumerate(vms, start=1):
            self._print_progress(i, len(vms), vm.path)

            self.logger.debug(f"Discovering VM {vm.path}")
            resource = self._get_or_create_resource(vm)
            self.logger.debug(f"Resource {resource.resource_path.name} created")
            try:
                resource.autoload()
                self.logger.debug(f"Resource {resource.resource_path.name} autoloaded")
            except AutoloadFailed:
                self.failed_vms.append(vm)
                return

            with resource.run_in_reservation():
                self.logger.debug(
                    f"Resource {resource.resource_path.name} in reservation"
                )
                resource.refresh_ip()
                self.logger.debug(
                    f"Resource {resource.resource_path.name} IP refreshed"
                )
                resource.refresh_vm_details()
                self.logger.debug(
                    f"Resource {resource.resource_path.name} VM details refreshed"
                )

    def _print_progress(self, i: int, total: int, vm_path: str) -> None:
        len_total = len(str(total))
        self.logger.debug(f"{i:0>{len_total}}/{total}: Discovering VM {vm_path}")

    def _discover_resources_in_parallel(self, vms: list[CloudProviderVmInfo]) -> None:
        executor = ThreadPoolExecutor(max_workers=self.max_workers)
        executor.map(self._discover_resource_in_parallel, vms)
        executor.shutdown(wait=True)

        for resource_pool in get_slices(self.discovered_resources, self.max_workers):
            names = [r.resource_path.name for r in resource_pool]
            self.api.add_to_reservation(names)
            self.logger.debug(f"{names} added to reservation")
            self.api.refresh_vm_details(None)  # run for all Apps in reservation
            self.logger.debug(f"VM details refreshed for {names}")
            self.api.remove_from_reservation(names)
            self.logger.debug(f"{names} removed from reservation")

    def _discover_resource_in_parallel(self, vm: CloudProviderVmInfo) -> None:
        self.logger.debug(f"Discovering VM {vm.path}")
        resource = self._get_or_create_resource(vm)
        self.logger.debug(f"Resource {resource.resource_path.name} created")
        try:
            resource.autoload()
            self.logger.debug(f"Resource {resource.resource_path.name} autoloaded")
        except AutoloadFailed:
            self.failed_vms.append(vm)
            return

        with resource.run_in_reservation():
            self.logger.debug(f"Resource {resource.resource_path.name} in reservation")
            resource.refresh_ip()
            self.logger.debug(f"Resource {resource.resource_path.name} IP refreshed")

        with self.discovered_lock:
            self.discovered_resources.append(resource)

    def _get_or_create_resource(self, vm: CloudProviderVmInfo) -> Resource:
        try:
            resource = self._get_resource(vm)
        except ValueError:
            resource = self._create_resource(vm)
        return resource

    def _get_resource(self, vm: CloudProviderVmInfo) -> Resource:
        name_pattern = get_resource_name_patter(vm.resource_path.name)
        for resource_name in self.api.iterate_resources(vm.resource_path.folders):
            if name_pattern.match(resource_name):
                info = self.api.GetResourceDetails(resource_name)
                if info.VmDetails and info.VmDetails.UID == vm.uuid:
                    vm.resource_path.name = resource_name
                    resource = Resource(
                        self.api,
                        self.cp_name,
                        vm.resource_path,
                        self.resource_model,
                        self.port_model,
                        address=info.Address,
                        logger=self.logger,
                    )
                    return resource
        raise ValueError(f"Resource with path {vm.resource_path} not found")

    def _create_resource(self, vm: CloudProviderVmInfo) -> Resource:
        resource = Resource.create(
            self.api,
            self.cp_name,
            self.resource_model,
            self.port_model,
            vm.path,
            resource_path=vm.resource_path,
            logger=self.logger,
        )
        return resource

    def _raise_for_failed_vms(self):
        if self.failed_vms:
            vm_names = [vm.path for vm in self.failed_vms]
            raise DiscoveryFailed(vm_names)


@attr.s(auto_attribs=True)
class Resource:
    api: CsApiWithSandbox
    cp_name: str
    resource_path: ResourceFullPath
    resource_model: str
    port_model: str
    address: str
    logger: Logger

    @classmethod
    def create(
        cls,
        api: CsApiWithSandbox,
        cp_name: str,
        resource_model: str,
        port_model: str,
        vm_path: str,
        logger: Logger,
        address: str = "N.A",
        resource_path: ResourceFullPath | None = None,
    ) -> Resource:
        if not resource_path:
            resource_path = ResourceFullPath.create(api, cp_name, vm_path)
            resource_path.create_folders()
        create_uniq_resource(api, resource_path, resource_model, address, logger)
        self = cls(
            api, cp_name, resource_path, resource_model, port_model, address, logger
        )
        self.set_attributes(
            {"VM Name": str(vm_path), "Cloud Provider Resource Name": cp_name}
        )
        return self

    def set_attributes(self, attributes: dict[str, str]) -> None:
        attributes = [
            AttributeNameValue(f"{self.resource_model}.{key}", value)
            for key, value in attributes.items()
        ]
        self.api.SetAttributesValues(
            [ResourceAttributesUpdateRequest(self.resource_path.name, attributes)]
        )

    def autoload(self):
        try:
            self.api.AutoLoad(self.resource_path.name)
        except CloudShellAPIError:
            self.api.DeleteResource(self.resource_path.name)
            self.logger.exception(
                f"Failed to autoload resource {self.resource_path.name}, removed it"
            )
            raise AutoloadFailed(self.resource_path.name)

    def refresh_ip(self) -> None:
        try:
            self.api.run_connected_command(
                self.resource_path.name, "remote_refresh_ip", "connectivity"
            )
        except CloudShellAPIError:
            # VM can be powered off
            self.logger.debug(f"Refresh IP fail for {self.resource_path.name}")

    def refresh_vm_details(self) -> None:
        try:
            self.api.refresh_vm_details([self.resource_path.name])
        except CloudShellAPIError:
            self.logger.debug(f"Refresh VM details fail for {self.resource_path.name}")

    @contextmanager
    def run_in_reservation(self) -> None:
        self.api.add_to_reservation([self.resource_path.name])
        try:
            yield
        finally:
            self.api.remove_from_reservation([self.resource_path.name])


@attr.s(auto_attribs=True)
class ResourceFullPath:
    DISCOVERED_VMS_FOLDER = "Discovered VMs"
    api: CsApiWithSandbox
    _path: str

    def __str__(self) -> str:
        return self._path

    @classmethod
    def create(
        cls, api: CsApiWithSandbox, cp_name: str, vm_path: str
    ) -> ResourceFullPath:
        path = vm_path.replace("\\", "/")
        path = "/".join(map(get_valid_cs_name, path.split("/")))
        path = f"{cls.get_cp_folder(cp_name)}/{path}"
        return cls(api, path)

    @classmethod
    def get_cp_folder(cls, cp_name: str) -> str:
        return f"{cls.DISCOVERED_VMS_FOLDER}/{cp_name}"

    @property
    def name(self) -> str:
        return self._path.rsplit("/", 1)[-1]

    @name.setter
    def name(self, value: str) -> None:
        self._path = f"{self.folders}/{value}"

    @property
    def folders(self) -> str:
        return self._path.rsplit("/", 1)[0]

    def create_folders(self) -> None:
        self.api.CreateFolder(self.folders)


def get_valid_cs_name(name: str) -> str:
    # Valid chars are a-zA-Z0-9 .-|_[]
    return re.sub(r"[^\w .-|_[\]]", "_", name)


def get_resource_uniq_name(name: str) -> str:
    uuid = uuid4()
    suffix = str(uuid)[:4]
    return f"{name}-{suffix}"


def get_resource_name_patter(vm_name: str) -> re.Pattern:
    name = re.escape(vm_name)
    return re.compile(rf"^{name}(-\w{{4}})?$")


def create_uniq_resource(
    api: CsApiWithSandbox,
    resource_path: ResourceFullPath,
    model: str,
    address: str,
    logger: Logger,
) -> None:
    name = resource_path.name
    for _ in range(10):
        try:
            resp = api.CreateResource(
                resourceModel=model,
                resourceName=name,
                resourceAddress=address,
                folderFullPath=resource_path.folders,
            )
        except CloudShellAPIError as e:
            logger.debug(f"name {name} already exists")
            if str(e.code) != "114":
                raise
            name = get_resource_uniq_name(name)
        else:
            resource_path.name = resp.Name
            break


T = TypeVar("T")


def get_slices(iterable: Iterable[T], size: int) -> Iterable[list[T]]:
    iterator = iter(iterable)
    while True:
        chunk = list(islice(iterator, size))
        if not chunk:
            return
        yield chunk


assert get_resource_name_patter("vm name").match("vm name-c2d2")
assert get_resource_name_patter("vm name").match("vm name")
