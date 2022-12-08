from __future__ import annotations

import re

import attr


@attr.s(auto_attribs=True)
class StaticResourceConfig:
    cp_name: str
    max_workers: int
    discover_max_vms: int
    start_discover_from_num: int

    @classmethod
    def from_context(cls, context) -> list[StaticResourceConfig]:
        def _get_attr(name):
            return context.resource.attributes[f"{namespace}{name}"]

        namespace = f"{context.resource.model}."
        cp_names = _get_attr("Cloud Provider Resource Name")
        max_workers = int(_get_attr("Max Workers"))
        discover_max_vms = int(_get_attr("Discover Max VMs"))
        start_discover_from_num = int(_get_attr("Start Discover From Number"))

        configs = [
            cls(cp_name, max_workers, discover_max_vms, start_discover_from_num)
            for cp_name in map(str.strip, re.split(r"[;,]", cp_names))
        ]
        return configs
