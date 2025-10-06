from jinja2 import Template

TOOL_CONFIG_TEMPLATE = Template(
    """
############# Tool Number: {{TOOL_NUMBER}} #############  

Tool Name:

    {{TOOL_NAME}}

Definition: 

    {{TOOL_DEFINITION}}

Args: 

    {{TOOL_ARGS}}

Usage Examples: 

    {{TOOL_EXAMPLES}}

Output:

    {{TOOL_OUTPUT}}

####################################################
"""
)


ARGS_TEMPLATE_DEFAULT = Template(
    """
    {{FIELD_NAME}}: {{FIELD_TYPE}} = Field(
    default={{FIELD_DEFAULT}},
    description={{FIELD_DESCRIPTION}},
)
"""
)

ARGS_TEMPLATE_NO_DEFAULT = Template(
    """
    {{FIELD_NAME}}: {{FIELD_TYPE}} = Field(
    description={{FIELD_DESCRIPTION}},
)
"""
)

TOOLS_OUTPUT_TEMPLATE = Template(
    """
Pydantic class {{CLASS_NAME}} object with the following schema.

{{CODE}}
"""
)

PARAMETER_INSTRUCTIONS_TEMPLATE_NO_ADDITIONAL_INFO = Template(
    """
{{NEED_NAME}}:

* For the need {{NEED_NAME}}, you need at least one of the list items to invoke the tool for this need. If nothing is provided, just ask for 1 of them.
{{NEED_PARAMETERS}}

"""
)
