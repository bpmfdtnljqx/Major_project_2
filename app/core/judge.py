"""评测器核心（Step 2）。

职责：编译用户代码 → 逐个测试点运行 → 时间/内存限制 → 输出比对 → 判定结果。

评测为阻塞操作（subprocess），异步由调用方通过 asyncio.to_thread 实现。
"""

import shlex
import subprocess
import threading
import time
from pathlib import Path

import psutil

from app.models import Language

# 系统默认资源限制（秒 / MB）
DEFAULT_TIME_LIMIT = 3.0
DEFAULT_MEMORY_LIMIT = 128

# 默认支持的编程语言
DEFAULT_LANGUAGES: dict[str, Language] = {
    "python": Language(name="python", file_ext=".py", run_cmd="python3 {src}"),
    "cpp": Language(name="cpp", file_ext=".cpp", compile_cmd="g++ {src} -o {exe}", run_cmd="{exe}"),
}


def normalize_output(text: str) -> str:
    """规范化输出：忽略每行行末空格与最后一行多余换行。"""
    lines = text.rstrip("\n").split("\n")
    return "\n".join(line.rstrip() for line in lines)


def _compile(lang: Language, src: Path, exe: Path, work_dir: Path) -> tuple[bool, str]:
    """编译源码，返回 (是否成功, 编译输出信息)。"""
    cmd = lang.compile_cmd.format(src=shlex.quote(str(src)), exe=shlex.quote(str(exe)))
    try:
        proc = subprocess.run(
            shlex.split(cmd), cwd=work_dir,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10,
        )
    except subprocess.TimeoutExpired:
        return False, "compile timeout"
    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout).decode(errors="replace")
        # 去掉绝对路径，只保留文件名（避免泄露本地沙箱目录，也更整洁）
        msg = msg.replace(str(src), src.name).replace(str(exe), exe.name)
        return False, msg.strip()
    return True, ""


def _run_one(lang, src, exe, input_data, time_limit, memory_limit, work_dir):
    """运行单个测试点，返回 (status, stdout, time_used, peak_memory)。

    status 取值：OK（正常结束）/ TLE / MLE / RE。
    """
    cmd = lang.run_cmd.format(src=shlex.quote(str(src)), exe=shlex.quote(str(exe)))
    argv = shlex.split(cmd)
    try:
        proc = subprocess.Popen(
            argv, cwd=work_dir,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except OSError:
        return "RE", "", 0.0, 0

    holder = {"status": None, "peak": 0.0}

    def monitor():
        try:
            p = psutil.Process(proc.pid)
            while proc.poll() is None:
                try:
                    mem_mb = p.memory_info().rss / (1024 * 1024)
                except psutil.NoSuchProcess:
                    break
                holder["peak"] = max(holder["peak"], mem_mb)
                if mem_mb > memory_limit:
                    holder["status"] = "MLE"
                    proc.kill()
                    return
                time.sleep(0.02)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()

    start = time.perf_counter()
    try:
        out, _ = proc.communicate(input=input_data.encode(), timeout=time_limit)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        return "TLE", "", time_limit, round(holder["peak"], 1)

    elapsed = round(time.perf_counter() - start, 3)

    if holder["status"] == "MLE":
        return "MLE", "", elapsed, round(holder["peak"], 1)

    if proc.returncode != 0:
        return "RE", "", elapsed, round(holder["peak"], 1)

    return "OK", out.decode(errors="replace"), elapsed, round(holder["peak"], 1)


def judge(code, lang, testcases, time_limit, memory_limit, work_dir):
    """评测一份代码。

    返回 (compile_result, details)：
    - compile_result：{"result", "message"}；解释型语言为 None
    - details：每个测试点 {"id", "result", "time", "memory"}
    """
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    src = work_dir / f"main{lang.file_ext}"
    exe = work_dir / "main"
    src.write_text(code, encoding="utf-8")

    compile_result = None
    if lang.compile_cmd:
        ok, msg = _compile(lang, src, exe, work_dir)
        compile_result = {"result": "success" if ok else "CE", "message": msg}
        if not ok:
            details = [
                {"id": i, "result": "CE", "time": 0.0, "memory": 0}
                for i in range(1, len(testcases) + 1)
            ]
            return compile_result, details

    details = []
    for i, tc in enumerate(testcases, start=1):
        status, stdout, time_used, mem_used = _run_one(
            lang, src, exe, tc.input, time_limit, memory_limit, work_dir
        )
        if status == "TLE":
            result = "TLE"
        elif status == "MLE":
            result = "MLE"
        elif status == "RE":
            result = "RE"
        elif normalize_output(stdout) == normalize_output(tc.output):
            result = "AC"
        else:
            result = "WA"
        details.append({"id": i, "result": result, "time": time_used, "memory": mem_used})

    return compile_result, details
