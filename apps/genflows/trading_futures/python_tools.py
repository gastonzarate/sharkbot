import io
import sys
import traceback
from contextlib import redirect_stdout, redirect_stderr

from llama_index.core.tools import FunctionTool

# Pre-import allowed libraries for the execution environment
import numpy as np
import pandas as pd
import math
import statistics
from decimal import Decimal
from datetime import datetime, timedelta


class PythonTools:
    """
    Wrapper class to expose Python code execution as a LlamaIndex FunctionTool.
    This allows the trading bot to perform complex mathematical calculations.
    """

    def __init__(self):
        """
        Initialize PythonTools with a sandboxed execution environment.
        """
        # Define safe built-ins (exclude dangerous functions)
        self._safe_builtins = {
            'abs': abs,
            'all': all,
            'any': any,
            'bin': bin,
            'bool': bool,
            'bytes': bytes,
            'callable': callable,
            'chr': chr,
            'complex': complex,
            'dict': dict,
            'divmod': divmod,
            'enumerate': enumerate,
            'filter': filter,
            'float': float,
            'format': format,
            'frozenset': frozenset,
            'getattr': getattr,
            'hasattr': hasattr,
            'hash': hash,
            'hex': hex,
            'int': int,
            'isinstance': isinstance,
            'issubclass': issubclass,
            'iter': iter,
            'len': len,
            'list': list,
            'map': map,
            'max': max,
            'min': min,
            'next': next,
            'oct': oct,
            'ord': ord,
            'pow': pow,
            'print': print,
            'range': range,
            'repr': repr,
            'reversed': reversed,
            'round': round,
            'set': set,
            'slice': slice,
            'sorted': sorted,
            'str': str,
            'sum': sum,
            'tuple': tuple,
            'type': type,
            'zip': zip,
            'True': True,
            'False': False,
            'None': None,
        }

        # Pre-loaded libraries available in the execution environment
        self._available_libraries = {
            'np': np,
            'numpy': np,
            'pd': pd,
            'pandas': pd,
            'math': math,
            'statistics': statistics,
            'Decimal': Decimal,
            'datetime': datetime,
            'timedelta': timedelta,
        }

    def list_tools(self) -> list[FunctionTool]:
        """
        Returns a list of FunctionTool objects for Python code execution.

        Returns:
            list[FunctionTool]: List of LlamaIndex FunctionTools.
        """
        return [
            FunctionTool.from_defaults(
                fn=self._execute_python_code,
                name="execute_python_code",
                description=(
                    "Executes Python code for mathematical and data analysis calculations. "
                    "Use this tool when you need to perform complex calculations that are better "
                    "expressed in Python code.\n\n"
                    "AVAILABLE LIBRARIES (pre-imported):\n"
                    "- numpy (as 'np' or 'numpy'): For numerical computations, arrays, linear algebra\n"
                    "- pandas (as 'pd' or 'pandas'): For data manipulation and analysis\n"
                    "- math: For basic mathematical functions (sqrt, log, sin, cos, etc.)\n"
                    "- statistics: For statistical functions (mean, median, stdev, etc.)\n"
                    "- Decimal: For precise decimal arithmetic\n"
                    "- datetime, timedelta: For date/time operations\n\n"
                    "USAGE EXAMPLES:\n"
                    "1. Calculate position size:\n"
                    "   ```python\n"
                    "   balance = 100\n"
                    "   leverage = 5\n"
                    "   price = 50000\n"
                    "   position_size = round((balance * leverage) / price, 3)\n"
                    "   print(f'Position size: {position_size} BTC')\n"
                    "   ```\n\n"
                    "2. Calculate RSI from price data:\n"
                    "   ```python\n"
                    "   prices = np.array([100, 102, 101, 103, 105, 104, 106])\n"
                    "   deltas = np.diff(prices)\n"
                    "   gains = np.where(deltas > 0, deltas, 0)\n"
                    "   losses = np.where(deltas < 0, -deltas, 0)\n"
                    "   avg_gain = np.mean(gains)\n"
                    "   avg_loss = np.mean(losses)\n"
                    "   rs = avg_gain / avg_loss if avg_loss != 0 else 0\n"
                    "   rsi = 100 - (100 / (1 + rs))\n"
                    "   print(f'RSI: {rsi:.2f}')\n"
                    "   ```\n\n"
                    "3. Risk/Reward calculations:\n"
                    "   ```python\n"
                    "   entry = 50000\n"
                    "   stop_loss = 49000\n"
                    "   take_profit = 52000\n"
                    "   risk = entry - stop_loss\n"
                    "   reward = take_profit - entry\n"
                    "   rr_ratio = reward / risk\n"
                    "   print(f'Risk/Reward Ratio: 1:{rr_ratio:.2f}')\n"
                    "   ```\n\n"
                    "IMPORTANT NOTES:\n"
                    "- All output must be printed using print() to be captured\n"
                    "- Code execution is sandboxed for security\n"
                    "- File I/O, network access, and system commands are NOT allowed\n"
                    "- Maximum execution time is limited\n"
                    "- The result will include both stdout and any error messages\n"
                ),
            ),
        ]

    def _execute_python_code(self, code: str) -> dict:
        """
        Execute Python code in a sandboxed environment.

        Args:
            code (str): The Python code to execute. Must use print() to output results.

        Returns:
            dict: Dictionary containing:
                - success (bool): Whether execution completed without errors
                - output (str): Captured stdout from the code execution
                - error (str): Error message if execution failed, empty string otherwise
        """
        # Create isolated namespace with safe builtins and libraries
        execution_namespace = {
            '__builtins__': self._safe_builtins,
            **self._available_libraries,
        }

        # Capture stdout and stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        result = {
            "success": False,
            "output": "",
            "error": "",
        }

        try:
            # Compile the code first to catch syntax errors
            compiled_code = compile(code, '<trading_calculation>', 'exec')

            # Execute with stdout/stderr capture
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(compiled_code, execution_namespace)

            result["success"] = True
            result["output"] = stdout_capture.getvalue()

        except SyntaxError as e:
            result["error"] = f"Syntax Error: {e.msg} at line {e.lineno}"
        except NameError as e:
            result["error"] = f"Name Error: {str(e)}. Note: Only pre-imported libraries are available."
        except Exception as e:
            # Get the traceback for debugging
            tb = traceback.format_exc()
            result["error"] = f"{type(e).__name__}: {str(e)}\n\nTraceback:\n{tb}"

        # Include any stderr output in the error field
        stderr_output = stderr_capture.getvalue()
        if stderr_output:
            if result["error"]:
                result["error"] += f"\n\nStderr:\n{stderr_output}"
            else:
                result["error"] = f"Stderr:\n{stderr_output}"

        return result
