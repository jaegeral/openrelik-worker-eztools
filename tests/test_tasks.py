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

"""Tests tasks."""

import pytest
from unittest.mock import patch, MagicMock
import os

from src.lecmd_task import lecmd_command, LECMD_OUTPUT_FORMAT_CONFIG
from src.appcompatcacheparser_task import (
    appcompatcacheparser_command,
    ACC_OUTPUT_FORMAT_CONFIG,
)
from src.rbcmd_task import rbcmd_command, RBCMD_OUTPUT_FORMAT_CONFIG


@patch("src.lecmd_task._run_ez_tool")
def test_lecmd_command_task(mock_run_ez_tool):
    """Test the lecmd_command task function."""
    # Mock the return value of _run_ez_tool
    expected_result_str = "mocked_ez_tool_result_base64_encoded"
    mock_run_ez_tool.return_value = expected_result_str

    # Define test inputs for the task
    test_pipe_result = None
    test_input_files = [{"path": "/test/input.lnk", "display_name": "input.lnk"}]
    test_output_path = "/test/output"
    test_workflow_id = "test_workflow_123"
    test_task_config = {
        "output_format": "csv",
        "lecmd_arguments": "--all",  # Example user-provided arguments
    }

    # Call the task function
    result = lecmd_command(
        pipe_result=test_pipe_result,
        input_files=test_input_files,
        output_path=test_output_path,
        workflow_id=test_workflow_id,
        task_config=test_task_config,
    )

    # Assert that _run_ez_tool was called once
    mock_run_ez_tool.assert_called_once()

    # Assert that _run_ez_tool was called with the correct arguments
    args, kwargs = mock_run_ez_tool.call_args

    expected_dotnet_path = os.path.expanduser("~/.dotnet/dotnet")
    expected_dll_path = "/opt/LECmd_built_from_source/LECmd.dll"
    expected_executable_list = [expected_dotnet_path, expected_dll_path]

    assert kwargs["executable_command_list"] == expected_executable_list
    assert kwargs["tool_display_name"] == "LECmd.exe"
    assert kwargs["tool_file_argument_flag"] == "-f"
    assert kwargs["tool_specific_args_key"] == "lecmd_arguments"
    assert kwargs["tool_output_format_config"] == LECMD_OUTPUT_FORMAT_CONFIG
    assert kwargs["pipe_result"] == test_pipe_result
    assert kwargs["input_files"] == test_input_files
    assert kwargs["output_path"] == test_output_path
    assert kwargs["workflow_id"] == test_workflow_id
    assert kwargs["task_config"] == test_task_config

    # Assert that the task returned the result from _run_ez_tool
    assert result == expected_result_str


@patch("src.rbcmd_task._run_ez_tool")
def test_rbcmd_command_task(mock_run_ez_tool):
    """Test the rbcmd_command task function."""
    # Mock the return value of _run_ez_tool
    expected_result_str = "mocked_rbcmd_ez_tool_result_base64_encoded"
    mock_run_ez_tool.return_value = expected_result_str

    # Define test inputs for the task
    test_pipe_result = None
    test_input_files = [{"path": "/test/$IXXXXXX.bin", "display_name": "$IXXXXXX.bin"}]
    test_output_path = "/test/output_rbcmd"
    test_workflow_id = "test_workflow_rbcmd_789"
    test_task_config = {
        "output_format": "csv",
        # RBCmd task in this setup does not take custom arguments via 'rbcmd_arguments'
    }

    # Call the task function
    result = rbcmd_command(
        pipe_result=test_pipe_result,
        input_files=test_input_files,
        output_path=test_output_path,
        workflow_id=test_workflow_id,
        task_config=test_task_config,
    )

    # Assert that _run_ez_tool was called once
    mock_run_ez_tool.assert_called_once()

    # Assert that _run_ez_tool was called with the correct arguments
    args, kwargs = mock_run_ez_tool.call_args

    expected_dotnet_path = os.path.expanduser("~/.dotnet/dotnet")
    expected_dll_path = "/opt/RBCmd_built_from_source/RBCmd.dll"
    expected_executable_list = [expected_dotnet_path, expected_dll_path]

    assert kwargs["executable_command_list"] == expected_executable_list
    assert kwargs["tool_display_name"] == "RBCmd.exe"
    assert kwargs["tool_file_argument_flag"] == "-f"  # RBCmd uses -f for files/dirs
    assert kwargs["tool_specific_args_key"] is None  # RBCmd task doesn't use this
    assert kwargs["tool_output_format_config"] == RBCMD_OUTPUT_FORMAT_CONFIG
    assert kwargs["pipe_result"] == test_pipe_result
    assert kwargs["input_files"] == test_input_files
    assert kwargs["output_path"] == test_output_path
    assert kwargs["workflow_id"] == test_workflow_id
    assert kwargs["task_config"] == test_task_config

    # Assert that the task returned the result from _run_ez_tool
    assert result == expected_result_str


@patch("src.appcompatcacheparser_task._run_ez_tool")
def test_appcompatcacheparser_command_task(mock_run_ez_tool):
    """Test the appcompatcacheparser_command task function."""
    # Mock the return value of _run_ez_tool
    expected_result_str = "mocked_acc_ez_tool_result_base64_encoded"
    mock_run_ez_tool.return_value = expected_result_str

    # Define test inputs for the task
    test_pipe_result = None
    test_input_files = [{"path": "/test/SYSTEM", "display_name": "SYSTEM.hive"}]
    test_output_path = "/test/output_acc"
    test_workflow_id = "test_workflow_acc_456"
    test_task_config = {
        "output_format": "csvf",
        "appcompatcacheparser_arguments": "--all",  # Example user-provided arguments
    }

    # Call the task function
    result = appcompatcacheparser_command(
        pipe_result=test_pipe_result,
        input_files=test_input_files,
        output_path=test_output_path,
        workflow_id=test_workflow_id,
        task_config=test_task_config,
    )

    # Assert that _run_ez_tool was called once
    mock_run_ez_tool.assert_called_once()

    # Assert that _run_ez_tool was called with the correct arguments
    args, kwargs = mock_run_ez_tool.call_args

    expected_dotnet_path = os.path.expanduser("~/.dotnet/dotnet")
    expected_dll_path = (
        "/opt/AppCompatCacheParser_built_from_source/AppCompatCacheParser.dll"
    )
    expected_executable_list = [expected_dotnet_path, expected_dll_path]

    assert kwargs["executable_command_list"] == expected_executable_list
    assert kwargs["tool_display_name"] == "AppCompatCacheParser.exe"
    assert kwargs["tool_file_argument_flag"] == "-f"
    assert kwargs["tool_specific_args_key"] == "appcompatcacheparser_arguments"
    assert kwargs["tool_output_format_config"] == ACC_OUTPUT_FORMAT_CONFIG
    assert kwargs["pipe_result"] == test_pipe_result
    assert kwargs["input_files"] == test_input_files
    assert kwargs["output_path"] == test_output_path
    assert kwargs["workflow_id"] == test_workflow_id
    assert kwargs["task_config"] == test_task_config

    # Assert that the task returned the result from _run_ez_tool
    assert result == expected_result_str
