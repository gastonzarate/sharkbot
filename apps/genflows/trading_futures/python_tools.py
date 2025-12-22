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
                    "⚠️ USE ONLY FOR COMPLEX MATHEMATICAL CALCULATIONS - NOT FOR DISPLAYING DATA ⚠️\n\n"
                    "This tool executes Python code for advanced mathematical computations that help in "
                    "trading decisions. DO NOT use this tool to format, print, or display data that is "
                    "already available in your context.\n\n"
                    "❌ WRONG USAGE (DO NOT DO THIS):\n"
                    "- Printing market data that's already given to you\n"
                    "- Formatting prices, indicators, or balance information\n"
                    "- Creating summary reports or analysis displays\n"
                    "- Repeating data that's already in your context\n\n"
                    "✅ CORRECT USAGE (ONLY use for these purposes):\n"
                    "- Complex position sizing calculations with multiple variables\n"
                    "- Advanced technical indicator calculations not provided in market_data\n"
                    "- Statistical analysis requiring numpy/pandas operations\n"
                    "- Risk management calculations with complex formulas\n"
                    "- Portfolio optimization or correlation analysis\n\n"
                    "AVAILABLE LIBRARIES (pre-imported):\n"
                    "- numpy (as 'np'): Arrays, linear algebra, advanced math\n"
                    "- pandas (as 'pd'): Data frames, time series analysis\n"
                    "- math, statistics: Standard mathematical functions\n"
                    "- Decimal: Precise decimal arithmetic\n"
                    "- datetime, timedelta: Date/time operations\n\n"
                    "GOOD EXAMPLES:\n\n"
                    "1. Calculate optimal position size with Kelly Criterion:\n"
                    "   ```python\n"
                    "   win_rate = 0.55\n"
                    "   avg_win = 200\n"
                    "   avg_loss = 100\n"
                    "   win_loss_ratio = avg_win / avg_loss\n"
                    "   kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio\n"
                    "   optimal_fraction = max(0, min(kelly * 0.5, 0.25))  # Half-Kelly with cap\n"
                    "   print(f'Optimal position fraction: {optimal_fraction:.2%}')\n"
                    "   ```\n\n"
                    "2. Calculate correlation between two assets:\n"
                    "   ```python\n"
                    "   btc_returns = np.array([0.02, -0.01, 0.03, -0.02, 0.01])\n"
                    "   eth_returns = np.array([0.03, -0.015, 0.025, -0.018, 0.012])\n"
                    "   correlation = np.corrcoef(btc_returns, eth_returns)[0, 1]\n"
                    "   print(f'BTC-ETH correlation: {correlation:.3f}')\n"
                    "   ```\n\n"
                    "3. Calculate Sharpe ratio for strategy evaluation:\n"
                    "   ```python\n"
                    "   returns = np.array([0.02, 0.01, -0.01, 0.03, 0.015])\n"
                    "   risk_free_rate = 0.001\n"
                    "   excess_returns = returns - risk_free_rate\n"
                    "   sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)\n"
                    "   print(f'Annualized Sharpe Ratio: {sharpe:.2f}')\n"
                    "   ```\n\n"
                    "CRITICAL RULES:\n"
                    "- Output results using print() - they will be captured\n"
                    "- If you just want to show data you already have, DON'T use this tool\n"
                    "- Only use when you need to CALCULATE something new and complex\n"
                    "- Code is sandboxed: no file I/O, network, or system commands\n"
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
