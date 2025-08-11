from logging import Logger, getLogger

from ..util import parse_template_indent

log: Logger = getLogger("ivrflow.docs.module")


template_nodes = """
nodes:
    - id: goto_ivr
      type: goto_on_exit
      context: "Menu-Principal"
      extension: "s-Menu-Principal"
      priority: "Begin"
"""

template_position = """
position:
    x: 632.8705383300783
    y: 357.11742401123036
    scale: 0.4092324994498387
"""

template_body_create = f"""
name: "example"
{parse_template_indent(template_nodes)}
{parse_template_indent(template_position)}
"""

get_module_doc = """
    ---
    summary: Get module by ID or client MXID.
    tags:
        - Module

    parameters:
        - in: path
          name: flow_id
          schema:
            type: integer
          required: true
          description: The flow ID to get the modules.
        - in: query
          name: id
          schema:
            type: integer
          description: The module ID to get.
        - in: query
          name: name
          schema:
            type: string
          description: The module name to get.

    responses:
        '200':
            $ref: '#/components/responses/GetModuleSuccess'
        '400':
            $ref: '#/components/responses/GetModuleBadRequest'
        '404':
            $ref: '#/components/responses/GetModuleNotFound'
        '500':
            $ref: '#/components/responses/InternalServerError'
"""

create_module_doc = f"""
    ---
    summary: Create a new module.
    tags:
        - Module

    parameters:
        - name: flow_id
          in: path
          required: true
          description: The ID of the flow to update the module.
          schema:
            type: integer

    requestBody:
        required: true
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        name:
                            type: string
                            description: The name of the module.
                        nodes:
                            type: array
                            items:
                                type: object
                        position:
                            type: object
                    required:
                        - name
                example:
                    {parse_template_indent(template_body_create, 20)}
    responses:
        '201':
            $ref: '#/components/responses/CreateModuleSuccess'
        '400':
            $ref: '#/components/responses/CreateModuleBadRequest'
        '404':
            $ref: '#/components/responses/CreateModuleNotFound'
        '500':
            $ref: '#/components/responses/InternalServerError'
  """

update_module_doc = f"""
    ---
    summary: Update an existing module.
    description: Update the properties of an existing module.

    tags:
        - Module

    parameters:
        - name: flow_id
          in: path
          required: true
          description: The ID of the flow to update the module.
          schema:
            type: integer
        - name: module_id
          in: path
          required: true
          description: The ID of the module to update.
          schema:
            type: integer
          example: 1

    requestBody:
        required: true
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        name:
                            type: string
                        nodes:
                            type: array
                            items:
                                type: object
                        position:
                            type: object
                examples:
                    UpdateName:
                        value:
                            name: "example"
                    UpdateNodes:
                        value:
                            {parse_template_indent(template_nodes, 28)}
                    UpdatePosition:
                        value:
                            {parse_template_indent(template_position, 28)}
                    UpdateAll:
                        value:
                            {parse_template_indent(template_body_create, 28)}

    responses:
        '200':
            $ref: '#/components/responses/UpdateModuleSuccess'
        '400':
            $ref: '#/components/responses/UpdateModuleBadRequest'
        '404':
            $ref: '#/components/responses/UpdateModuleNotFound'
        '500':
            $ref: '#/components/responses/InternalServerError'
  """

delete_module_doc = """
    ---
    summary: Delete an existing module.
    description: Delete an existing module.

    tags:
        - Module

    parameters:
        - name: flow_id
          in: path
          required: true
          description: The ID of the flow to delete the module.
          schema:
            type: integer
        - name: module_id
          in: path
          required: true
          description: The ID of the module to delete.
          schema:
            type: integer
          example: 1

    responses:
        '200':
            $ref: '#/components/responses/DeleteModuleSuccess'
        '400':
            $ref: '#/components/responses/DeleteModuleBadRequest'
        '404':
            $ref: '#/components/responses/DeleteModuleNotFound'
        '500':
            $ref: '#/components/responses/InternalServerError'
  """

get_module_list_doc = """
    ---
    summary: Get a list of modules.
    description: Get a list of modules.

    tags:
        - Module

    parameters:
        - name: flow_id
          in: path
          required: true
          description: The ID of the flow to get the modules.
          schema:
            type: integer
        - in: query
          name: fields
          schema:
            type: array
            default: ["id", "name"]
            items:
              type: string
          description: Fields to return the list of modules.
    responses:
        '200':
            $ref: '#/components/responses/GetListModulesSuccess'
        '400':
            $ref: '#/components/responses/GetListModulesBadRequest'
        '404':
            $ref: '#/components/responses/GetListModulesNotFound'
        '500':
            $ref: '#/components/responses/InternalServerError'
"""

get_module_backup_doc = """
    ---
    summary: Get module backups by flow ID.
    tags:
        - Module

    parameters:
        - in: path
          name: flow_id
          description: The flow ID to get the module backups.
          required: true
          schema:
            type: integer

        - in: query
          name: limit
          description: The limit of backups to get.
          schema:
            type: integer

        - in: query
          name: offset
          description: The offset of backups to get.
          schema:
            type: integer

        - in: query
          name: backup_id
          description: The backup ID to get.
          schema:
              type: integer

    responses:
        '200':
            $ref: '#/components/responses/GetFlowBackupsSuccess'
        '404':
            $ref: '#/components/responses/GetFlowBackupsNotFound'
        '500':
            $ref: '#/components/responses/InternalServerError'
"""
