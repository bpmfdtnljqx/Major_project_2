"""千问风格的代码块组件（带语言标签 + 亮/暗切换 + 复制按钮 + 简单高亮）。

基于 streamlit.components.v1.html 直接渲染 HTML+CSS+JS，避免被 Streamlit
默认 .stCodeBlock 黑块样式干扰。支持 Python/C++/JavaScript 简单关键字/字符串/数字高亮。
"""

import html as _html
import re as _re

import streamlit.components.v1 as components

# ---- 简单语法高亮（避免引入 pygments 等重依赖）----
_PY_KW = {"False","None","True","and","as","assert","async","await","break","class",
          "continue","def","del","elif","else","except","finally","for","from","global",
          "if","import","in","is","lambda","nonlocal","not","or","pass","raise",
          "return","try","while","with","yield","match","case"}
_CPP_KW = {"auto","break","case","catch","char","class","const","continue","default",
           "delete","do","double","else","enum","extern","float","for","goto","if",
           "inline","int","long","namespace","new","operator","private","protected",
           "public","register","return","short","signed","sizeof","static","struct",
           "switch","template","typedef","typename","union","unsigned","virtual","void",
           "volatile","while","true","false","nullptr","this","using","#include"}
_JS_KW = {"function","return","var","let","const","if","else","while","for","do",
          "switch","case","default","break","continue","new","delete","typeof",
          "instanceof","in","of","null","undefined","true","false","this","class",
          "extends","super","import","export","from","as","async","await","yield",
          "try","catch","finally","throw"}


def _tokenize(code: str, lang: str):
    """返回 tokens: [(kind, text), ...]"""
    L = (lang or "plain_text").lower()
    kw = _PY_KW if L == "python" else _CPP_KW if L == "cpp" else _JS_KW if L == "javascript" else set()

    # 顺序很重要：先匹配字符串、注释、数字、关键字，再普通 token
    patterns = [
        ("comment", r"#[^\n]*" if L == "python" else
                   r"//[^\n]*|/\*[\s\S]*?[*/]" if L in ("cpp", "javascript") else r"#[^\n]*"),
        ("string", r"\"\"\"[\s\S]*?\"\"\"|'''[\s\S]*?'''|\"[^\"\n]*\"|'[^'\n]*'"),
        ("number", r"\b\d+(\.\d+)?\b"),
        ("kw", r"\b[A-Za-z_][A-Za-z0-9_]*\b"),
    ]

    tokens = []
    i = 0
    while i < len(code):
        matched = False
        for kind, pat in patterns:
            m = _re.match(pat, code[i:])
            if m and (kind != "kw" or m.group() in kw):
                tokens.append((kind, m.group()))
                i += m.end()
                matched = True
                break
        if not matched:
            tokens.append(("plain", code[i]))
            i += 1
    return tokens


def _highlight(code: str, lang: str) -> str:
    out = []
    for kind, text in _tokenize(code, lang):
        safe = _html.escape(text)
        if kind == "plain":
            out.append(safe)
        elif kind == "comment":
            out.append(f'<span class="cb-c">{safe}</span>')
        elif kind == "string":
            out.append(f'<span class="cb-s">{safe}</span>')
        elif kind == "number":
            out.append(f'<span class="cb-n">{safe}</span>')
        elif kind == "kw":
            out.append(f'<span class="cb-k">{safe}</span>')
        else:
            out.append(safe)
    return "\n".join(out)


_LANG_LABEL = {
    "python": "python", "cpp": "C++", "c_cpp": "C++",
    "javascript": "javascript", "plain_text": "text",
}


def code_block(code: str, language: str = "python", key: str | None = None) -> None:
    """千问风格代码块：顶部语言标签 + 亮/暗切换 + 复制按钮 + 行号 + 高亮。"""
    if code is None:
        code = ""
    L = language or "plain_text"
    label = _LANG_LABEL.get(L, L)
    highlighted = _highlight(code, L)

    cid = key or f"cb_{abs(hash(code)) % 100000}"

    html = f"""
<div class="cb-root" id="{cid}" data-state="light">
  <div class="cb-bar">
    <span class="cb-lang">{label}</span>
    <div class="cb-actions">
      <button type="button" class="cb-btn" data-act="theme" title="切换亮/暗">
        <span class="cb-ico-dark">🌙 暗色</span>
        <span class="cb-ico-light">☀️ 亮色</span>
      </button>
      <button type="button" class="cb-btn" data-act="copy" title="复制">
        <span class="cb-ico-copy">📋 复制</span>
        <span class="cb-ico-done">✓ 已复制</span>
      </button>
    </div>
  </div>
  <pre class="cb-pre"><code class="cb-code">{highlighted}</code></pre>
</div>

<style>
.cb-root {{
  border-radius: 10px; overflow: hidden; margin: .25rem 0 .5rem;
  border: 1px solid var(--cb-line, #d8d0c2);
  background: var(--cb-bg, #fbf9f4);
  color: var(--cb-text, #2a241d);
  box-shadow: 0 1px 2px rgba(0,0,0,.06);
}}
.cb-root[data-state="dark"] {{
  --cb-bg: #141b24; --cb-text: #e6ebf2; --cb-line: #2e3b4a;
  --cb-comment: #7c8896; --cb-string: #9ec590; --cb-number: #e6b47a; --cb-keyword: #e07b6a;
  background: var(--cb-bg); color: var(--cb-text); border-color: var(--cb-line);
}}
.cb-root[data-state="light"] {{
  --cb-bg: #fbf9f4; --cb-text: #2a241d; --cb-line: #d8d0c2;
  --cb-comment: #8a8172; --cb-string: #4a8c4a; --cb-number: #b5712c; --cb-keyword: #a86f2c;
}}
.cb-bar {{
  display:flex; justify-content:space-between; align-items:center;
  padding: .35rem .8rem; background: var(--cb-bg); border-bottom: 1px solid var(--cb-line);
  font-family: "Inter","PingFang SC","Microsoft YaHei",sans-serif;
}}
.cb-lang {{ font-size: .8rem; color: var(--cb-text); opacity: .85; font-weight: 600; }}
.cb-actions {{ display:flex; gap: .35rem; }}
.cb-btn {{
  background: transparent; border: 1px solid var(--cb-line); border-radius: 6px;
  color: var(--cb-text); font-size: .76rem; padding: .15rem .55rem; cursor: pointer;
  display:inline-flex; align-items:center; gap:.3rem; font-family: inherit;
}}
.cb-btn:hover {{ background: var(--cb-line); }}
.cb-root[data-state="light"] .cb-ico-light {{ display:none; }}
.cb-root[data-state="dark"]  .cb-ico-dark {{ display:none; }}
.cb-pre {{
  margin:0; padding: .75rem .9rem; overflow-x:auto; max-height: 420px; overflow-y:auto;
  font-family: "SF Mono","JetBrains Mono",Consolas,monospace;
  font-size: 13px; line-height: 1.55;
  counter-reset: cbline;
}}
.cb-code {{ display:block; }}
.cb-code .cb-line {{
  display:block; padding-left: 2.6rem; position: relative;
}}
.cb-code .cb-line::before {{
  counter-increment: cbline; content: counter(cbline);
  position:absolute; left: 0; width: 2rem; text-align:right;
  color: var(--cb-comment); opacity:.55; font-size: .78em;
}}
.cb-c {{ color: var(--cb-comment); font-style: italic; }}
.cb-s {{ color: var(--cb-string); }}
.cb-n {{ color: var(--cb-number); }}
.cb-k {{ color: var(--cb-keyword); font-weight: 600; }}
</style>

<script>
(function() {{
  var root = document.getElementById('{cid}');
  if (!root) return;
  // 把高亮后按 \n 拆分成多行 span 用于行号
  var code = root.querySelector('.cb-code');
  var html = code.innerHTML;
  code.innerHTML = html.split('\\n').map(function(line){{
    return line.length ? '<span class="cb-line">' + line + '</span>' : '<span class="cb-line"></span>';
  }}).join('');

  var buttons = root.querySelectorAll('.cb-btn');
  buttons.forEach(function(btn){{
    btn.addEventListener('click', function(e){{
      e.preventDefault();
      var act = btn.getAttribute('data-act');
      if (act === 'theme') {{
        var cur = root.getAttribute('data-state');
        root.setAttribute('data-state', cur === 'light' ? 'dark' : 'light');
      }} else if (act === 'copy') {{
        var text = `{_html.escape(code)}`;
        navigator.clipboard && navigator.clipboard.writeText(text);
        btn.querySelector('.cb-ico-copy').style.display='none';
        btn.querySelector('.cb-ico-done').style.display='inline';
        setTimeout(function(){{
          btn.querySelector('.cb-ico-copy').style.display='';
          btn.querySelector('.cb-ico-done').style.display='none';
        }}, 1500);
      }}
    }});
  }});
}})();
</script>
"""
    components.html(html, height=(60 + code.count("\n") * 21 + 50), scrolling=True)