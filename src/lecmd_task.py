import os  # For os.path.exists and os.access

from .app import celery
from .utils import _run_ez_tool  # Import from the new utils.py

# --- LECmd Task ---
LECMD_TASK_NAME = "openrelik-worker-eztools.tasks.lecmd"
LECMD_TASK_METADATA = {
    "display_name": "EZTool: LECmd (LNK File Parser)",
    "description": "Runs LECmd.exe from Eric Zimmermann's EZTools to parse LNK files. Captures standard output.",
    # Configuration that will be rendered as a web for in the UI, and any data entered
    # by the user will be available to the task function when executing (task_config).
    "task_config": [
        {
            "name": "lecmd_arguments",
            "label": "LECmd Arguments (Optional)",
            "description": "Additional command-line arguments for LECmd.exe (e.g., '--csv C:\\temp\\out'). The input file path will be appended automatically. Note: This worker captures standard output; ensure arguments are compatible.",
            "type": "textarea",
            "required": False,
        },
        {
            "name": "output_file_extension",
            "label": "Output File Extension",
            "description": "File extension for the output (e.g., 'csv', 'json', 'txt'). LECmd's standard output will be saved with this extension.",
            "type": "text",
            "required": True,
        },
        {
            "name": "output_data_type",
            "label": "Output Data Type (Optional)",
            "description": "A specific data type for the output file, used for metadata in OpenReLiK (e.g., 'lnk_file_analysis').",
            "type": "text",
            "required": False,
        },
    ],
}


@celery.task(bind=True, name=LECMD_TASK_NAME, metadata=LECMD_TASK_METADATA)
def lecmd_command(
    self,
    pipe_result: str = None,
    input_files: list = None,
    output_path: str = None,
    workflow_id: str = None,
    task_config: dict = None,
) -> str:
    """Run LECmd on input LNK files.

    Args:
        pipe_result: Base64-encoded result from the previous Celery task, if any.
        input_files: List of input file dictionaries (unused if pipe_result exists).
        output_path: Path to the output directory.
        workflow_id: ID of the current workflow.
        task_config: User configuration for the task.

    Returns:
        Base64-encoded dictionary containing task results.
    """
    # Ensure task_config is not None, providing an empty dict if it is,
    # as _run_ez_tool expects it.
    # The OpenReLiK core should always provide this, but defensive coding is good.
    effective_task_config = task_config if task_config is not None else {}

    # Path to the dotnet executable (installed via dotnet-install.sh, typically in ~/.dotnet/dotnet)
    dotnet_executable_path = os.path.expanduser("~/.dotnet/dotnet")
    # Path to the LECmd.dll built from source
    lecmd_dll_path = "/opt/LECmd_built_from_source/LECmd.dll"

    # Form the command list for executing: dotnet /path/to/LECmd.dll
    executable_list_for_lecmd = [
        dotnet_executable_path,
        lecmd_dll_path,
    ]

    return _run_ez_tool(
        executable_command_list=executable_list_for_lecmd,
        tool_display_name="LECmd.exe",  # For display, logging, and output file naming
        tool_file_argument_flag="-f",  # LECmd uses -f for files
        tool_specific_args_key="lecmd_arguments",
        pipe_result=pipe_result,
        input_files=input_files,
        output_path=output_path,
        workflow_id=workflow_id,
        task_config=effective_task_config,
    )
