import streamlit as st

from translator import LANGUAGES, MAX_INPUT_CHARS, TranslationError, get_api_key, get_model, translate

st.set_page_config(page_title="다국어 번역기", page_icon="🌐", layout="wide")

# 국기 이모지는 Windows에서 "US" 같은 글자로 보이고, 원어 표기는 좁은 버튼에서 잘리므로 언어 코드를 쓴다.
LANG_CODES = {"영어": "EN", "일본어": "JA", "베트남어": "VI"}

# 테마 색을 직접 지정하지 않고 Streamlit 테마 변수를 써서 라이트/다크 모두 대응한다.
st.markdown(
    """
    <style>
    .block-container { max-width: 1100px; padding-top: 2.5rem; }
    h1, h3 { word-break: keep-all; }
    .char-count { text-align: right; font-size: 0.85rem; opacity: 0.7; margin-top: -0.5rem; }
    .char-count.over { color: #e5484d; opacity: 1; font-weight: 600; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("사용 방법")
    st.markdown(
        "1. 왼쪽 입력창에 번역할 글을 입력합니다.\n"
        "2. 원하는 언어 버튼을 누릅니다.\n"
        "3. 오른쪽 결과의 복사 버튼으로 번역문을 복사합니다."
    )
    st.divider()
    st.caption(f"사용 모델: `{get_model()}`")
    st.caption(f"최대 입력: {MAX_INPUT_CHARS:,}자")

st.title("🌐 다국어 번역기")
st.caption("번역할 글을 입력하고 언어를 선택하세요.")

has_key = get_api_key() is not None
if not has_key:
    st.error("`.env` 파일에 OPENAI_API_KEY가 설정되어 있지 않습니다.")

left, right = st.columns(2, gap="large")

with left:
    st.subheader("원문")
    text = st.text_area(
        "번역할 글",
        height=260,
        placeholder="여기에 번역할 글을 입력하세요.",
        label_visibility="collapsed",
        # max_chars는 한도 초과 붙여넣기를 안내 없이 통째로 무시하므로 쓰지 않는다.
    )
    over = len(text) > MAX_INPUT_CHARS
    st.markdown(
        f'<div class="char-count{" over" if over else ""}">{len(text):,} / {MAX_INPUT_CHARS:,}자</div>',
        unsafe_allow_html=True,
    )

    clicked = None
    for col, label in zip(st.columns(len(LANGUAGES)), LANGUAGES):
        if col.button(f"{label} {LANG_CODES.get(label, '')}".strip(), width="stretch", disabled=not has_key):
            clicked = label

    if clicked:
        if not text.strip():
            st.warning("번역할 글을 먼저 입력해 주세요.")
        elif over:
            st.warning(f"입력은 최대 {MAX_INPUT_CHARS:,}자까지 가능합니다. (현재 {len(text):,}자)")
        else:
            with st.spinner(f"{clicked}로 번역 중..."):
                try:
                    st.session_state["result"] = translate(text, clicked)
                    st.session_state["result_lang"] = clicked
                except TranslationError as e:
                    st.error(str(e))

# Streamlit은 입력창에서 포커스가 빠져야 값을 서버로 보내므로, 글자 수는 브라우저에서 바로 갱신한다.
st.html(
    f"""
    <script>
    if (!window.__charCountBound) {{
      window.__charCountBound = true;
      const max = {MAX_INPUT_CHARS};
      document.addEventListener("input", (e) => {{
        if (e.target.tagName !== "TEXTAREA") return;
        const el = document.querySelector(".char-count");
        if (!el) return;
        const n = e.target.value.length;
        el.textContent = n.toLocaleString("en-US") + " / " + max.toLocaleString("en-US") + "자";
        el.classList.toggle("over", n > max);
      }});
    }}
    </script>
    """,
    unsafe_allow_javascript=True,
)

with right:
    if "result" in st.session_state:
        st.subheader(f"번역 결과 ({st.session_state['result_lang']})")
        with st.container(border=True):
            st.code(st.session_state["result"], language=None, wrap_lines=True)
    else:
        st.subheader("번역 결과")
        with st.container(border=True):
            st.caption("언어 버튼을 누르면 이곳에 번역 결과가 표시됩니다.")
