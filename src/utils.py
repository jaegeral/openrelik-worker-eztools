# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess
import os
import tempfile
import shutil
from pathlib import Path

from openrelik_worker_common.file_utils import create_output_file
from openrelik_worker_common.task_utils import create_task_result, get_input_files


def _run_ez_tool(
    executable_command_list: list,
    tool_display_name: str,  # e.g., "LECmd.dll" for logging and output file naming
    tool_file_argument_flag: str,  # e.g., "-f" for file or "-d" for directory
    tool_specific_args_key: str,
    tool_output_format_config: dict,  # New: e.g. {"csv": {"flag": "--csv", "pattern": "LECmd_*.csv"}}
    pipe_result: str,
    input_files: list,
    output_path: str,
    workflow_id: str,
    task_config: dict,
) -> str:
    """
    Helper function to run an EZTool, supporting both stdout capture and
    direct file output generation by the tool.
    """
    input_files = get_input_files(pipe_result, input_files or [])
    output_files = []

    user_provided_args_str = task_config.get(tool_specific_args_key, "")
    user_provided_args_list = (
        user_provided_args_str.split() if user_provided_args_str else []
    )

    selected_output_format = task_config.get(
        "output_format", "stdout"
    )  # Default to stdout
    output_data_type = task_config.get(
        "output_data_type", "text_file"
    )  # Remains the same

    # For reporting purposes, show the tool name and user arguments
    reporting_command_string = (
        f"{tool_display_name} {tool_file_argument_flag} <input_file_path>"
    )
    if user_provided_args_str:  # Only add if there are actual arguments
        reporting_command_string += f" {user_provided_args_str}"
    # Add format flag to reporting string if a specific format is chosen
    if (  # Ensure tool_output_format_config is not None before accessing
        tool_output_format_config
        and selected_output_format != "stdout"
        and selected_output_format in tool_output_format_config
    ):
        reporting_command_string += f" {tool_output_format_config[selected_output_format]['flag']} <worker_temp_dir>"

    # Determine output file extension based on selected format
    output_extension = (
        selected_output_format
        if selected_output_format != "stdout"
        else task_config.get("output_file_extension", "txt")
    )
    if not input_files:
        raise ValueError(f"No input files provided to {tool_display_name}.")

    for input_file in input_files:
        input_file_path = input_file.get("path")
        input_file_display_name = input_file.get("display_name", "unknown_file")
        temp_output_dir = None  # For tool-generated file output

        if not input_file_path:
            print(
                f"Error: Input file for {tool_display_name} is missing a valid 'path'. "
                f"Input file details: {input_file}"
            )
            raise ValueError(
                f"Invalid or missing file path for input: {input_file_display_name}"
            )

        print(
            f"Attempting to process file for {tool_display_name}: '{input_file_path}'"
        )
        if not os.path.exists(input_file_path):
            print(
                f"Error: File does NOT exist at path: '{input_file_path}' (checked with os.path.exists)"
            )
            raise FileNotFoundError(
                f"Input file for {tool_display_name} not found by worker at specified path: {input_file_path}"
            )
        if not os.access(input_file_path, os.R_OK):
            print(
                f"Error: File exists but is NOT readable at path: '{input_file_path}' (checked with os.access)"
            )
            raise PermissionError(
                f"Input file for {tool_display_name} is not readable by worker at path: {input_file_path}"
            )
        print(f"File '{input_file_path}' exists and is readable by the worker.")

        output_file_obj = create_output_file(
            output_path,
            display_name=f"{tool_display_name}_output_for_{input_file_display_name}",
            extension=output_extension,
            data_type=output_data_type,
        )
        current_command_to_run = list(executable_command_list)
        current_command_to_run.extend([tool_file_argument_flag, input_file_path])
        current_command_to_run.extend(user_provided_args_list)

        # Modify command if a specific file output format is chosen
        if (  # Ensure tool_output_format_config is not None
            selected_output_format != "stdout"
            and tool_output_format_config
            and selected_output_format in tool_output_format_config
        ):
            format_details = tool_output_format_config[selected_output_format]
            format_flag = format_details["flag"]
            # Get the output_target_type, defaulting to "file" if not specified
            output_target_type = format_details.get("output_target_type", "file")

            # Check if user accidentally provided the same flag
            if format_flag in user_provided_args_list:
                print(
                    f"Warning: User provided '{format_flag}' in arguments while also selecting '{selected_output_format}' format. "
                    f"The worker will manage the '{format_flag}' argument. Please remove it from custom arguments if this was unintentional."
                )

            temp_output_dir = tempfile.mkdtemp(
                prefix=f"eztool_{selected_output_format}_"
            )

            # Determine the actual argument to pass to the tool for its output destination
            tool_output_destination_arg = ""
            if output_target_type == "directory":
                tool_output_destination_arg = temp_output_dir
            elif (
                output_target_type == "file"
                or output_target_type == "directory_with_filename"
            ):
                # For "file" and "directory_with_filename", the worker constructs a full file path
                # that the tool is expected to write to.
                base_input_filename = Path(input_file_path).stem
                # The filename includes the tool's display name and the selected format (which becomes the extension)
                # Example: inputfile_LECmd.exe.csv or inputfile_AppCompatCacheParser.exe.csvf
                temp_output_filename = f"{base_input_filename}_{tool_display_name}.{selected_output_format}"
                full_temp_output_path = Path(temp_output_dir) / temp_output_filename
                tool_output_destination_arg = str(full_temp_output_path)
            else:
                # Fallback for unknown or misconfigured output_target_type
                print(
                    f"Warning: Unknown output_target_type '{output_target_type}' for format '{selected_output_format}'. "
                    f"Defaulting to constructing a file path argument."
                )
                base_input_filename = Path(input_file_path).stem
                temp_output_filename = f"{base_input_filename}_{tool_display_name}.{selected_output_format}"
                full_temp_output_path = Path(temp_output_dir) / temp_output_filename
                tool_output_destination_arg = str(full_temp_output_path)

            current_command_to_run.extend([format_flag, tool_output_destination_arg])

        print(
            f"Executing command for {tool_display_name}: {' '.join(current_command_to_run)}"
        )

        try:
            # Run the process. We don't use check=True initially to handle errors manually.
            # Tools might write to stderr even on success, or for warnings.
            process = subprocess.run(
                current_command_to_run, capture_output=True, text=False, check=False
            )  # text=False to handle binary from file

            captured_stdout_for_log = (
                process.stdout.decode(errors="ignore") if process.stdout else ""
            )
            captured_stderr = (
                process.stderr.decode(errors="ignore") if process.stderr else ""
            )

            if captured_stdout_for_log:
                print(
                    f"Tool {tool_display_name} stdout for {input_file_path}:\n{captured_stdout_for_log[:1000]}..."
                )
            if captured_stderr:
                print(
                    f"Tool {tool_display_name} stderr for {input_file_path}:\n{captured_stderr[:1000]}..."
                )

            output_content = b""

            if (  # Ensure tool_output_format_config is not None
                selected_output_format != "stdout"
                and tool_output_format_config
                and selected_output_format in tool_output_format_config
            ):
                if process.returncode != 0:
                    # Even if the tool fails, it might have created partial files or error logs we want to see.
                    print(
                        f"Warning: {tool_display_name} exited with code {process.returncode} when attempting to generate '{selected_output_format}' file."
                    )

                format_details = tool_output_format_config[selected_output_format]
                filename_pattern = format_details["pattern"]
                # Since we create a specific file, we can check for its existence directly
                # or use the pattern if it's more general and matches the constructed name.
                # For robustness, let's use the glob with the pattern.
                # If output_target_type is directory, search recursively
                if (
                    tool_output_format_config[selected_output_format].get(
                        "output_target_type"
                    )
                    == "directory"
                ):
                    all_matches = list(Path(temp_output_dir).rglob(filename_pattern))
                    generated_files = [p for p in all_matches if p.is_file()]

                else:
                    all_matches = list(Path(temp_output_dir).glob(filename_pattern))
                    generated_files = [p for p in all_matches if p.is_file()]
                if not generated_files:
                    error_message = (
                        f"Error: {tool_display_name} did not produce the expected '{selected_output_format}' file "
                        f"(pattern: '{filename_pattern}') in {temp_output_dir}.\n"
                        f"Command: '{' '.join(current_command_to_run)}'.\n"
                        f"Return code: {process.returncode}\nStdout: {captured_stdout_for_log}\nStderr: {captured_stderr}"
                    )
                    # If we want to fail hard here: raise RuntimeError(error_message)
                    # For now, we'll write any stderr to the output file if no primary output found.
                    output_content = (
                        process.stderr if process.stderr else error_message.encode()
                    )
                    print(error_message)  # Ensure it's logged
                elif len(generated_files) > 1:
                    # Simple strategy: take the newest file if multiple match
                    generated_files.sort(key=os.path.getmtime, reverse=True)
                    print(
                        f"Warning: Multiple files matched pattern '{filename_pattern}'. Using the newest: {generated_files[0]}"
                    )
                    with open(generated_files[0], "rb") as f_in:
                        output_content = f_in.read()
                else:  # Exactly one file
                    with open(generated_files[0], "rb") as f_in:
                        output_content = f_in.read()
            else:  # Capture stdout
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(
                        process.returncode,
                        current_command_to_run,
                        output=process.stdout,
                        stderr=process.stderr,
                    )
                output_content = process.stdout

            with open(output_file_obj.path, "wb") as fh:  # Write as binary
                fh.write(output_content)

        except subprocess.CalledProcessError as e:
            # This will now primarily catch failures when stdout is the expected output
            # or if we re-raise for file output modes after initial checks.
            stdout_decoded = (
                e.stdout.decode(errors="ignore")
                if isinstance(e.stdout, bytes)
                else e.stdout
            )
            stderr_decoded = (
                e.stderr.decode(errors="ignore")
                if isinstance(e.stderr, bytes)
                else e.stderr
            )
            error_message = (
                f"Error running {tool_display_name} on {input_file_path}.\n"
                f"Command: '{' '.join(e.cmd)}'.\n"
                f"Return code: {e.returncode}\n"
                f"Stdout: {stdout_decoded}\nStderr: {stderr_decoded}"
            )
            # Write error details to the output file for debugging
            with open(output_file_obj.path, "w", encoding="utf-8") as fh_err:
                fh_err.write(error_message)
            print(error_message)  # Log it as well
            # We've written the error to the file, so we can append and continue,
            # or decide to raise the error to stop the workflow for this file.
            # For now, let's allow it to be part of the results.
            # If a hard fail is desired: raise RuntimeError(error_message) from e

        except FileNotFoundError as e:  # This is for dotnet or the DLL itself
            if (
                e.filename in executable_command_list
            ):  # Check if it's dotnet or the DLL path
                raise FileNotFoundError(
                    f"The command or DLL '{e.filename}' was not found. "
                    "Ensure .NET is installed and DLL paths are correct."
                )
            else:
                print(f"Unexpected FileNotFoundError for: {e.filename}")
                raise
        finally:
            if temp_output_dir:
                print(f"Cleaning up temporary directory: {temp_output_dir}")
                shutil.rmtree(temp_output_dir, ignore_errors=True)

        output_files.append(output_file_obj.to_dict())

    if not output_files:
        raise RuntimeError(f"No output files were generated by {tool_display_name}.")

    return create_task_result(
        output_files=output_files,
        workflow_id=workflow_id,
        command=reporting_command_string,
        meta={},
    )
