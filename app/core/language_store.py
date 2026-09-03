"""语言配置存储：内置默认语言 + 动态注册语言（内存为主，JSON 落盘）。

- 内置默认语言（python / cpp）来自 judge 的 DEFAULT_LANGUAGES，始终存在；
- 动态注册的语言追加到内存，并落盘到 data/languages.json（仅保存动态语言）。
"""

import json
from pathlib import Path

from app.core.judge import DEFAULT_LANGUAGES
from app.models import Language


class LanguageStore:
    def __init__(self, data_file: Path):
        self.data_file = Path(data_file)
        self._languages: dict[str, Language] = dict(DEFAULT_LANGUAGES)
        self._load_dynamic()

    # ---- 加载 ----
    def _load_dynamic(self) -> None:
        if not self.data_file.exists():
            return
        try:
            data = json.loads(self.data_file.read_text(encoding="utf-8"))
            for item in data:
                lang = Language(**item)
                self._languages[lang.name] = lang
        except (json.JSONDecodeError, OSError, ValueError):
            # 文件损坏时忽略，保持内置默认语言可用
            pass

    # ---- 查询 ----
    def list_names(self) -> list[str]:
        return list(self._languages.keys())

    def get(self, name: str) -> Language | None:
        return self._languages.get(name)

    # ---- 注册 ----
    def add(self, language: Language) -> None:
        self._languages[language.name] = language
        self._save()

    # ---- 内部 ----
    def _save(self) -> None:
        dynamic = [lang for name, lang in self._languages.items() if name not in DEFAULT_LANGUAGES]
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(
            json.dumps([lang.model_dump() for lang in dynamic], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
