from __future__ import annotations

from json import JSONDecodeError
from logging import Logger, getLogger

from aiohttp import web

from ...db.flow import Flow as DBFlow
from ...db.module import Module as DBModule
from ...db.module_backup import ModuleBackup
from ..base import get_config, routes
from ..docs.module import (
    create_module_doc,
    delete_module_doc,
    get_module_backup_doc,
    get_module_doc,
    get_module_list_doc,
    update_module_doc,
)
from ..responses import resp
from ..util import docstring, generate_uuid

log: Logger = getLogger("ivrflow.api.module")


@routes.get("/v1/{flow_id}/module", allow_head=False)
@docstring(get_module_doc)
async def get_module(request: web.Request) -> web.Response:
    uuid = generate_uuid()
    log.info(f"({uuid}) -> '{request.method}' '{request.path}' Getting module")

    try:
        flow_id = int(request.match_info["flow_id"])

        if not await DBFlow.check_exists(flow_id):
            return resp.not_found(f"Flow with ID {flow_id} not found in the database", uuid)

    except (KeyError, ValueError):
        return resp.bad_request("Invalid or missing flow ID", uuid)
    except Exception as e:
        return resp.internal_error(e, uuid, log)

    module_id = request.query.get("id", None)
    name = request.query.get("name", None)

    try:
        if module_id:
            module = await DBModule.get_by_id(int(module_id), flow_id)
            if not module:
                return resp.not_found(f"Module with ID {module_id} not found")

            data = module.serialize()
            log_msg = f"Returning module_id: {module_id}"

        elif name:
            module = await DBModule.get_by_name(name, flow_id)
            if not module:
                return resp.not_found(f"Module with name '{name}' not found")
            data = module.serialize()
            log_msg = f"Returning module_name: {name}"

        else:
            modules = [module.serialize() for module in await DBModule.all(flow_id)]
            data = {"modules": {module.pop("name"): module for module in modules}}
            log_msg = f"Returning {len(data['modules'])} modules"

    except Exception as e:
        return resp.internal_error(e, uuid, log)

    return resp.success_response(data=data, uuid=uuid, log_msg=log_msg)


@routes.post("/v1/{flow_id}/module")
@docstring(create_module_doc)
async def create_module(request: web.Request) -> web.Response:
    uuid = generate_uuid()
    log.info(f"({uuid}) -> '{request.method}' '{request.path}' Creating new module")

    try:
        flow_id = int(request.match_info["flow_id"])
        data: dict = await request.json()

        if not await DBFlow.check_exists(flow_id):
            return resp.not_found(f"Flow with ID {flow_id} not found in the database", uuid)

    except JSONDecodeError:
        return resp.body_not_json(uuid)
    except (KeyError, ValueError):
        return resp.bad_request("Invalid or missing flow ID", uuid)
    except Exception as e:
        return resp.internal_error(e, uuid, log)

    name = data.get("name")
    if not name:
        return resp.bad_request("Parameter 'name' is required", uuid)

    if await DBModule.check_exists_by_name(name, flow_id):
        return resp.bad_request(
            f"Module with name '{data['name']}' already exists in flow_id {flow_id}",
            uuid,
        )

    nodes_ids = set()
    for node in data.get("nodes", []):
        node_id = node.get("id")
        msg = f"Node with ID '{node_id}'"

        if node_id in nodes_ids:
            return resp.conflict(f"{msg} is repeated", uuid, {"module_name": ""})

        if _node := await DBModule.get_node_by_id(flow_id, node_id, True):
            return resp.conflict(
                f"{msg} already exists", uuid, {"module_name": _node.get("module_name")}
            )

        nodes_ids.add(node_id)

    try:
        log.debug(f"({uuid}) -> Creating new module '{name}' in flow_id '{flow_id}'")
        new_module = DBModule(
            name=name,
            flow_id=flow_id,
            nodes=data.get("nodes", []),
            position=data.get("position", {}),
        )

        module_id = await new_module.insert()
    except Exception as e:
        return resp.internal_error(e, uuid, log)

    return resp.created(
        message="Module created successfully", uuid=uuid, data={"module_id": module_id}
    )


@routes.patch("/v1/{flow_id}/module/{module_id}")
@docstring(update_module_doc)
async def update_module(request: web.Request) -> web.Response:
    uuid = generate_uuid()
    log.info(f"({uuid}) -> '{request.method}' '{request.path}' Updating module")
    config = get_config()

    try:
        flow_id = int(request.match_info["flow_id"])
        module_id = int(request.match_info["module_id"])
        data: dict = await request.json()

        new_name = data.get("name")
        new_nodes = data.get("nodes")
        new_position = data.get("position")

        if not new_name and new_nodes is None and new_position is None:
            return resp.bad_request(
                "At least one of the parameters name, nodes or position is required", uuid
            )

        if not await DBFlow.check_exists(flow_id):
            return resp.not_found(f"Flow with ID '{flow_id}' not found in the database", uuid)

        module = await DBModule.get_by_id(module_id, flow_id)

    except JSONDecodeError:
        return resp.body_not_json(uuid)
    except (KeyError, ValueError, TypeError):
        return resp.bad_request("Flow ID and module ID must be valid integers", uuid)
    except Exception as e:
        return resp.internal_error(e, uuid, log)

    if not module:
        return resp.not_found(f"Module with ID '{module_id}' not found in flow_id '{flow_id}'")

    new_data = {}
    if new_name and new_name != module.name:
        if await DBModule.check_exists_by_name(new_name, flow_id, module_id):
            return resp.bad_request(
                f"Module with name '{new_name}' already exists in flow_id '{flow_id}'", uuid
            )
        new_data["name"] = new_name

    if new_nodes is not None and (new_nodes != module.nodes or new_nodes == []):
        nodes_ids = set()
        for node in new_nodes:
            node_id = node.get("id")
            msg = f"Node with ID '{node_id}'"

            if node_id in nodes_ids:
                return resp.conflict(f"{msg} is repeated", uuid, {"module_name": ""})

            if _node := await DBModule.get_node_by_id(flow_id, node_id, True):
                if not _node.get("module_name") == module.name:
                    return resp.conflict(
                        f"{msg} already exists", uuid, {"module_name": _node.get("module_name")}
                    )
            nodes_ids.add(node_id)

        new_data["nodes"] = new_nodes

    if new_position is not None and (new_position != module.position or new_position == {}):
        new_data["position"] = new_position

    if new_data:
        try:
            backup_id = await module.backup_module(config)
            log.debug(f"({uuid}) -> Backup module '{module.name}' created with ID {backup_id}")

            for key, value in new_data.items():
                setattr(module, key, value)

            log.debug(f"({uuid}) -> Updating module '{module.name}' in flow_id '{flow_id}'")
            await module.update()

        except Exception as e:
            return resp.internal_error(e, uuid, log)

    return resp.success_response(
        message="Module updated successfully", uuid=uuid, data={"module_id": module_id}
    )


@routes.delete("/v1/{flow_id}/module/{module_id}")
@docstring(delete_module_doc)
async def delete_module(request: web.Request) -> web.Response:
    uuid = generate_uuid()
    log.info(f"({uuid}) -> '{request.method}' '{request.path}' Deleting module")

    try:
        flow_id = int(request.match_info["flow_id"])
        module_id = int(request.match_info["module_id"])

        if not await DBFlow.check_exists(flow_id):
            return resp.not_found(f"Flow with ID '{flow_id}' not found in the database", uuid)

        module = await DBModule.get_by_id(module_id, flow_id)
        if not module:
            return resp.not_found(
                f"Module with ID {module_id} not found in flow_id {flow_id}", uuid
            )

        log.debug(f"({uuid}) -> Deleting module '{module.name}' in flow_id '{flow_id}'")
        await module.delete()

    except (KeyError, ValueError, TypeError):
        return resp.bad_request("Flow ID and module ID must be valid integers", uuid)
    except Exception as e:
        return resp.internal_error(e, uuid, log)

    return resp.success_response(
        message="Module deleted successfully", uuid=uuid, data={"module_id": module_id}
    )


@routes.get("/v1/{flow_id}/module/list", allow_head=False)
@docstring(get_module_list_doc)
async def get_module_list(request: web.Request) -> web.Response:
    uuid = generate_uuid()
    log.info(f"({uuid}) -> '{request.method}' '{request.path}' Getting module")

    fields = request.query.getall("fields", ["id", "name"])

    try:
        flow_id = int(request.match_info["flow_id"])

        if not await DBFlow.check_exists(flow_id):
            return resp.not_found(f"Flow with ID {flow_id} not found in the database", uuid)
    except (KeyError, ValueError):
        return resp.bad_request("Invalid or missing flow ID", uuid)
    except Exception as e:
        return resp.internal_error(e, uuid, log)

    try:
        modules = {"modules": await DBModule.get_by_fields(flow_id, fields)}
    except Exception as e:
        return resp.internal_error(e, uuid, log)

    return resp.success_response(
        data=modules, uuid=uuid, log_msg=f"Returning {len(modules['modules'])} modules"
    )


@routes.get("/v1/{flow_id}/module/backup", allow_head=False)
@docstring(get_module_backup_doc)
async def get_backup(request: web.Request) -> web.Response:
    uuid = generate_uuid()
    log.info(f"({uuid}) -> '{request.method}' '{request.path}' Getting module backup")

    offset = int(request.query.get("offset", 0))
    limit = int(request.query.get("limit", 10))
    backup_id = request.query.get("backup_id")
    flow_id = int(request.match_info["flow_id"])

    if not await DBFlow.check_exists(flow_id):
        return resp.not_found(f"Flow with ID {flow_id} not found in the database", uuid)

    if backup_id:
        backup = await ModuleBackup.get_by_id(int(backup_id))
        if not backup:
            return resp.not_found(f"Backup with ID {backup_id} not found", uuid)
        return resp.success_response(backup.to_dict(), uuid)

    count = await ModuleBackup.get_count_by_flow_id(flow_id=flow_id)
    backups = await ModuleBackup.all_by_flow_id(flow_id=flow_id, offset=offset, limit=limit)
    data = {"count": count, "backups": [backup.to_dict() for backup in backups]}

    return resp.success_response(uuid=uuid, data=data, log_msg=f"Returning {count} backups")
