from logging import Logger, getLogger

log: Logger = getLogger("ivrflow.docs.channel")

get_variables_doc = """
    ---
    summary: Get variables from a channel.
    tags:
        - Channel

    parameters:
        - name: uniqueid
          in: path
          required: true
          description: The uniqueid of the channel.
          schema:
            type: string

        - name: scopes
          in: query
          required: false
          description: The scopes of the variables to get. If not provided, all variables will be returned.
          schema:
            type: array
            default: [route, hook]
            items:
              type: string

    responses:
        '200':
            $ref: '#/components/responses/GetVariablesSuccess'
        '404':
            $ref: '#/components/responses/GetVariablesNotFound'
        '500':
            $ref: '#/components/responses/InternalServerError'
    """
