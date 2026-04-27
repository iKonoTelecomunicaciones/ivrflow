check_template_doc = """
    ---
    summary: Render data using Jinja template
    description: Render data using Jinja template
    tags:
        - Mis
    requestBody:
        required: true
        content:
            application/x-www-form-urlencoded:
                schema:
                    type: object
                    properties:
                        template:
                            type: string
                            description: The jinja template to be checked
                            example: "Hello {{ name }}"
                        variables:
                            type: string
                            description: >
                                The variables to be used in the template, in `yaml` or `json` format
                            example: "{'name': 'world'}"
                        string_format:
                            type: boolean
                            description: If True, the result will be returned as a string
                            example: True
                        flags:
                            type: string
                            description: The flags to be used in the rendering
                            example: "{'REMOVE_QUOTES': True, 'LITERAL_EVAL': True, 'CONVERT_TO_TYPE': True, 'CUSTOM_ESCAPE': False}"
                            default: "{'REMOVE_QUOTES': True, 'LITERAL_EVAL': True, 'CONVERT_TO_TYPE': True, 'CUSTOM_ESCAPE': False}"
                            description: |
                                Available flags:
                                - `REMOVE_QUOTES`: If true, the quotes will be removed from the rendered data
                                - `LITERAL_EVAL`: If true, the rendered data will be evaluated as a literal
                                - `CONVERT_TO_TYPE`: If true, the rendered data will be converted to the appropriate type
                                - `CUSTOM_ESCAPE`: If true, the custom escape will be used to escape the rendered data
                    required:
                        - template
    responses:
        '200':
            $ref: '#/components/responses/CheckTemplateSuccess'
        '400':
            $ref: '#/components/responses/CheckTemplateBadRequest'
        '422':
            $ref: '#/components/responses/CheckTemplateUnprocessable'
        '500':
            $ref: '#/components/responses/InternalServerError'
"""
