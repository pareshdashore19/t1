import inspect
import re
from typing import Dict, List, Union, get_args, get_origin

from pydantic_core import PydanticUndefined

from src.tools.utils.output_templates import (
    ARGS_TEMPLATE_DEFAULT,
    ARGS_TEMPLATE_NO_DEFAULT,
    TOOL_CONFIG_TEMPLATE,
    TOOLS_OUTPUT_TEMPLATE,
)


def is_builtin_type(obj):
    return isinstance(obj, type) and getattr(obj, "__module__", None) == "builtins"


def get_annotation_name(annotation) -> str:
    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is Union:
        non_none_args = [a for a in args if a is not type(None)]
        if len(non_none_args) == 1:
            return f"Optional[{get_annotation_name(non_none_args[0])}]"
        else:
            return f"Union[{', '.join(get_annotation_name(a) for a in args)}]"
    elif origin is not None:
        origin_name = getattr(origin, "__name__", str(origin))
        args_str = ", ".join(get_annotation_name(a) for a in args)
        return f"{origin_name}[{args_str}]"
    else:
        return getattr(annotation, "__name__", str(annotation))


def configure_tools_definitions(all_tools: List[Dict]) -> str:
    """
    This function will aggregate the docstrings of all the tools passed by the LOB to MACAW and process them for information that will be put into the tools prompt.

    Args:
        macaw_config (MacawConfig): MacawConfig object that is passed in.

    Returns:
        str: The configured definition of tools.
    """
    all_tool_configs = []
    description_pattern = r"Description:\s*\n(.*?)(?=\n[A-Z][a-z]*:|\Z)"
    examples_pattern = r"Examples:\n((?:\>\>\> # Usage Example:\n.*\n?)+)"
    all_tool_configs = []
    counter = 1
    for tool in all_tools:
        tool_name = tool["tool_name"]
        tool_function = tool["tool_func"]
        inspected_tool = inspect.getfullargspec(tool_function)
        docstring = inspect.getdoc(tool_function)
        signature = inspect.signature(tool_function)
        signature_return_annotation = signature.return_annotation
        output_class_name = None
        output_code = None
        if signature_return_annotation:
            output_class_name = signature_return_annotation.__name__
        if signature.return_annotation:
            if not is_builtin_type(signature.return_annotation):
                output_code = inspect.getsource(signature.return_annotation)
            else:
                output_code = signature_return_annotation
        description_match = re.search(description_pattern, docstring, re.DOTALL)
        extracted_description = ""
        extracted_examples = ""
        extracted_examples = ""
        if description_match:
            extracted_description = description_match.group(1).strip()

        examples_match = re.search(examples_pattern, docstring, re.DOTALL)
        if examples_match:
            extracted_examples = examples_match.group(1).strip()
        inspected_tool_annotations = inspected_tool.annotations
        input_args = []
        if "kwargs" in inspected_tool_annotations:
            tool_args = inspected_tool_annotations["kwargs"]
            tool_fields = tool_args.model_fields
            for field_name in tool_fields:
                if (
                    tool_fields[field_name].json_schema_extra
                    and "context" in tool_fields[field_name].json_schema_extra
                    and tool_fields[field_name].json_schema_extra["context"]
                ):
                    continue
                if tool_fields[field_name].default is PydanticUndefined:
                    current_arg = ARGS_TEMPLATE_NO_DEFAULT.render(
                        FIELD_NAME=field_name,
                        FIELD_TYPE=get_annotation_name(
                            tool_fields[field_name].annotation
                        ),
                        FIELD_DESCRIPTION=tool_fields[field_name].description,
                    )
                else:
                    current_arg = ARGS_TEMPLATE_DEFAULT.render(
                        FIELD_NAME=field_name,
                        FIELD_DEFAULT=tool_fields[field_name].default,
                        FIELD_TYPE=get_annotation_name(
                            tool_fields[field_name].annotation
                        ),
                        FIELD_DESCRIPTION=tool_fields[field_name].description,
                    )
                input_args.append(current_arg)
        input_args_merged = "\n".join(input_args) if input_args else None
        tool_config_result = TOOL_CONFIG_TEMPLATE.render(
            TOOL_NUMBER=counter,
            TOOL_NAME=tool_name,
            TOOL_DEFINITION=extracted_description,
            TOOL_ARGS=input_args_merged,
            TOOL_EXAMPLES=extracted_examples,
            TOOL_OUTPUT=TOOLS_OUTPUT_TEMPLATE.render(
                CLASS_NAME=output_class_name, CODE=output_code
            ),
        )
        counter += 1
        all_tool_configs.append(tool_config_result)

    return "\n".join(all_tool_configs)
