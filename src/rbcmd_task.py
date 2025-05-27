import os

from .app import celery
from .utils import _run_ez_tool  # Import from the new utils.py

# Task name used to register and route the task to the correct queue.
RBCMD_TASK_NAME = "openrelik-worker-eztools.tasks.rbcmd"

# Task metadata for registration in the core system.
RBCMD_TASK_METADATA = {
    "display_name": "EZTool: RBCmd (Recycle Bin Parser)",
    "description": "Runs RBCmd.exe from Eric Zimmermann's EZTools to parse Recycle Bin artifacts. Captures standard output.",
    "task_config": [
        {
            "name": "rbcmd_arguments",
            "label": "RBCmd Arguments (Optional)",
            "description": "Additional command-line arguments for RBCmd.exe (e.g., '-d C:\\path\\to\\recyclebin --csv C:\\temp\\out'). The input file path (if applicable for specific RBCmd use cases, e.g. processing a single $I file) or directory will be appended. Note: This worker captures standard output; ensure arguments are compatible.",
            "type": "textarea",
            "required": False,
        },
        {
            "name": "output_file_extension",
            "label": "Output File Extension",
            "description": "File extension for the output (e.g., 'csv', 'txt'). RBCmd's standard output will be saved with this extension.",
            "type": "text",
            "required": True,
        },
        {
            "name": "output_data_type",
            "label": "Output Data Type (Optional)",
            "description": "A specific data type for the output file, used for metadata in OpenReLiK (e.g., 'recycle_bin_analysis').",
            "type": "text",
            "required": False,
        },
    ],
}


@celery.task(bind=True, name=RBCMD_TASK_NAME, metadata=RBCMD_TASK_METADATA)
def rbcmd_command(
    self,
    pipe_result: str = None,
    input_files: list = None,
    output_path: str = None,
    workflow_id: str = None,
    task_config: dict = None,
) -> str:
    """Run RBCmd.exe on input Recycle Bin artifacts or directories."""
    effective_task_config = task_config if task_config is not None else {}

    dotnet_executable_path = os.path.expanduser("~/.dotnet/dotnet")
    rbcmd_dll_path = "/opt/RBCmd_built_from_source/RBCmd.dll"
    executable_list_for_rbcmd = [dotnet_executable_path, rbcmd_dll_path]

    return _run_ez_tool(
        executable_command_list=executable_list_for_rbcmd,
        tool_display_name="RBCmd.exe",
        tool_file_argument_flag="-f",  # Verify this flag for RBCmd
        tool_specific_args_key="rbcmd_arguments",
        pipe_result=pipe_result,
        input_files=input_files,
        output_path=output_path,
        workflow_id=workflow_id,
        task_config=effective_task_config,
    )
