import subprocess
import tempfile
import os
import sys
import platform
import re

def execute_code(code: str, language: str) -> dict:
    """
    Returns:
    {
        "success": bool,
        "stdout": str,
        "stderr": str,
        "error_type": str,   # "compile_error" | "runtime_error" | "timeout" | None
        "clean_error": str
    }
    """
    timeout = 10

    if language == "Python":
        return _run_python(code, timeout)
    elif language == "C++":
        return _run_cpp(code, timeout)
    elif language == "Java":
        return _run_java(code, timeout)
    return {"success": False, "stdout": "", "stderr": "Unsupported language",
            "error_type": "unknown", "clean_error": "Unsupported language"}


def _run_python(code, timeout):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py',
                                     delete=False, encoding='utf-8') as f:
        f.write(code)
        fname = f.name
    try:
        result = subprocess.run([sys.executable, fname],
                                capture_output=True, text=True, timeout=timeout)
        os.unlink(fname)
        if result.returncode != 0:
            return {"success": False, "stdout": result.stdout, "stderr": result.stderr,
                    "error_type": "runtime_error",
                    "clean_error": _clean_python_error(result.stderr)}
        return {"success": True, "stdout": result.stdout, "stderr": "",
                "error_type": None, "clean_error": ""}
    except subprocess.TimeoutExpired:
        os.unlink(fname)
        return {"success": False, "stdout": "", "stderr": "", "error_type": "timeout",
                "clean_error": "⏱ Time limit exceeded (10s). Check for infinite loops."}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e),
                "error_type": "runtime_error", "clean_error": str(e)}


def _run_cpp(code, timeout):
    try:
        subprocess.run(["g++", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {"success": False, "stdout": "", "stderr": "", "error_type": "compile_error",
                "clean_error": "⚠️ g++ not found. Windows: install MinGW. Linux/Mac: install gcc."}

    with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp',
                                     delete=False, encoding='utf-8') as f:
        f.write(code)
        cpp_file = f.name
    exe_file = cpp_file.replace('.cpp', '.exe' if platform.system() == 'Windows' else '_out')

    try:
        compile_result = subprocess.run(
            ["g++", "-o", exe_file, cpp_file, "-std=c++17"],
            capture_output=True, text=True, timeout=30)
        if compile_result.returncode != 0:
            os.unlink(cpp_file)
            return {"success": False, "stdout": "", "stderr": compile_result.stderr,
                    "error_type": "compile_error",
                    "clean_error": _clean_cpp_error(compile_result.stderr)}
        run_result = subprocess.run([exe_file], capture_output=True, text=True, timeout=timeout)
        os.unlink(cpp_file)
        if os.path.exists(exe_file):
            os.unlink(exe_file)
        if run_result.returncode != 0:
            return {"success": False, "stdout": run_result.stdout, "stderr": run_result.stderr,
                    "error_type": "runtime_error", "clean_error": run_result.stderr.strip()[:400]}
        return {"success": True, "stdout": run_result.stdout, "stderr": "",
                "error_type": None, "clean_error": ""}
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "", "error_type": "timeout",
                "clean_error": "⏱ Time limit exceeded (10s). Check for infinite loops."}


def _run_java(code, timeout):
    try:
        subprocess.run(["javac", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {"success": False, "stdout": "", "stderr": "", "error_type": "compile_error",
                "clean_error": "⚠️ javac not found. Install JDK from https://adoptium.net"}

    match = re.search(r'public\s+class\s+(\w+)', code)
    class_name = match.group(1) if match else "Solution"
    tmpdir = tempfile.mkdtemp()
    java_file = os.path.join(tmpdir, f"{class_name}.java")
    with open(java_file, 'w', encoding='utf-8') as f:
        f.write(code)

    try:
        compile_result = subprocess.run(["javac", java_file],
                                        capture_output=True, text=True, timeout=30)
        if compile_result.returncode != 0:
            return {"success": False, "stdout": "", "stderr": compile_result.stderr,
                    "error_type": "compile_error",
                    "clean_error": _clean_java_error(compile_result.stderr)}
        run_result = subprocess.run(["java", "-cp", tmpdir, class_name],
                                    capture_output=True, text=True, timeout=timeout)
        if run_result.returncode != 0:
            return {"success": False, "stdout": run_result.stdout, "stderr": run_result.stderr,
                    "error_type": "runtime_error", "clean_error": run_result.stderr.strip()[:400]}
        return {"success": True, "stdout": run_result.stdout, "stderr": "",
                "error_type": None, "clean_error": ""}
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "", "error_type": "timeout",
                "clean_error": "⏱ Time limit exceeded (10s). Check for infinite loops."}


def _clean_python_error(stderr):
    lines = stderr.strip().split('\n')
    error_line = next((l for l in reversed(lines) if l.strip()), stderr)
    line_info = next((l for l in lines if 'line' in l.lower() and 'File' in l), "")
    if line_info:
        return f"{line_info.strip()}\n→ {error_line.strip()}"
    return error_line.strip()

def _clean_cpp_error(stderr):
    lines = stderr.strip().split('\n')
    errors = [l for l in lines if 'error:' in l.lower()]
    if errors:
        parts = errors[0].split(':')
        line_num = parts[2].strip() if len(parts) > 2 and parts[2].strip().isdigit() else ""
        clean = errors[0].split('error:')[-1].strip()
        return f"Line {line_num}: error: {clean}" if line_num else f"Compile error: {clean}"
    return stderr[:400]

def _clean_java_error(stderr):
    lines = stderr.strip().split('\n')
    errors = [l for l in lines if 'error:' in l.lower()]
    if errors:
        return f"Compile error: {errors[0].split('error:')[-1].strip()}"
    return stderr[:400]
