from logging import Logger, getLogger

log: Logger = getLogger("ivrflow.docs.flow")


get_flow_doc = """
    ---
    summary: Get flow by ID or flow name.
    tags:
        - Flow

    parameters:
        - name: flow_id
          in: query
          description: Flow ID to get.
          schema:
            type: integer
          example: 1
        - name: flow_name
          in: query
          description: Flow name to get.
          schema:
              type: string
          example: "flow_name"

    responses:
        '200':
            $ref: '#/components/responses/GetFlowSuccess'
        '404':
            $ref: '#/components/responses/GetFlowNotFound'
    """

create_or_update_flow_doc = """
    ---
    summary: Creates a new flow or update it if exists.
    tags:
        - Flow

    requestBody:
        required: false
        description: A json with `id`, `name` and  `flow_vars` keys.
                     `id` is the flow ID to update, `flow_vars` is the flow content.
                     send only `name` and `flow_vars` to create a new flow.
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        id:
                            type: integer
                        name:
                            type: string
                        flow_vars:
                            type: object
                    example:
                        id: 1
                        name: "flow_name"
                        flow_vars:
                            var1: "value1"
                            var2: "value2"
    responses:
        '200':
            $ref: '#/components/responses/UpdateFlowSuccess'
        '201':
            $ref: '#/components/responses/CreateFlowSuccess'
        '400':
            $ref: '#/components/responses/CreateUpdateFlowBadRequest'
    """
