"""题目存储层：内存为主，磁盘（JSON 文件）持久化。

设计（已与用户确认）：
- 启动时：确保 problems/ 目录存在；若其为空，则从 seed/ 播种初始题目；
- 加载：将 problems/ 下所有 *.json 读入内存（dict，按题目 id 索引）；
- 增删改查：操作内存，并同步回写 / 删除 problems/ 下对应的 JSON 文件。
"""

import json
from pathlib import Path

from app.models import Problem


class ProblemStore:
    """题目的内存存储，负责加载、增删改查与落盘。"""

    def __init__(self, problems_dir: Path, seed_dir: Path):
        self.problems_dir = problems_dir
        self.seed_dir = seed_dir
        self._problems: dict[str, Problem] = {}
        self.load()

    # ---- 加载 ----
    def load(self) -> None:
        """初始化数据目录并加载所有题目进内存。"""
        self.problems_dir.mkdir(parents=True, exist_ok=True)
        self._seed_if_empty()
        self._problems.clear()
        for path in sorted(self.problems_dir.glob("*.json")):
            problem = Problem.model_validate_json(path.read_text(encoding="utf-8"))
            self._problems[problem.id] = problem

    def _seed_if_empty(self) -> None:
        """problems/ 为空时，从 seed/ 复制初始题目（首次播种）。"""
        if any(self.problems_dir.glob("*.json")):
            return
        if not self.seed_dir.is_dir():
            return
        for path in sorted(self.seed_dir.glob("*.json")):
            target = self.problems_dir / path.name
            target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    # ---- 查询 ----
    def list_all(self) -> list[Problem]:
        """返回全部题目（保持加载顺序）。"""
        return list(self._problems.values())

    def get(self, problem_id: str) -> Problem | None:
        """按 id 查询题目，不存在返回 None。"""
        return self._problems.get(problem_id)

    def exists(self, problem_id: str) -> bool:
        return problem_id in self._problems

    # ---- 增删改 ----
    def add(self, problem: Problem) -> None:
        """新增题目（调用前应已检查 id 不存在）。"""
        self._problems[problem.id] = problem
        self._write(problem)

    def update(self, problem: Problem) -> None:
        """覆盖更新题目（调用前应已检查 id 存在）。"""
        self._problems[problem.id] = problem
        self._write(problem)

    def delete(self, problem_id: str) -> None:
        """按 id 删除题目（内存与磁盘同步删除）。"""
        self._problems.pop(problem_id, None)
        (self.problems_dir / f"{problem_id}.json").unlink(missing_ok=True)

    def update_public_cases(self, problem_id: str, public_cases: bool) -> Problem | None:
        """更新题目的日志可见性，返回更新后的题目；不存在返回 None。"""
        problem = self._problems.get(problem_id)
        if problem is None:
            return None
        problem.public_cases = public_cases
        self._write(problem)
        return problem

    # ---- 内部 ----
    def _write(self, problem: Problem) -> None:
        path = self.problems_dir / f"{problem.id}.json"
        data = json.dumps(problem.model_dump(), ensure_ascii=False, indent=2)
        path.write_text(data, encoding="utf-8")
