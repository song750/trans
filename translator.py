"""OpenAI 번역 로직."""

import os

import openai
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = "gpt-6-astra"
MAX_INPUT_CHARS = 5000

# 버튼 라벨 -> 프롬프트에 전달할 언어명. 언어 추가 시 여기에만 항목을 추가한다.
LANGUAGES = {
    "영어": "English",
    "일본어": "Japanese (日本語)",
    "베트남어": "Vietnamese (Tiếng Việt)",
}

SYSTEM_PROMPT = (
    "너는 전문 번역가다. 사용자가 준 텍스트를 {language}로 자연스럽게 번역하라. "
    "번역문만 출력하고 설명, 따옴표, 원문은 덧붙이지 마라. "
    "줄바꿈과 문단 구조는 유지하라."
)


class TranslationError(Exception):
    """사용자에게 그대로 보여줄 수 있는 한국어 메시지를 담는 예외."""


def get_api_key() -> str | None:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    return key or None


def get_model() -> str:
    return os.getenv("OPENAI_MODEL", "").strip() or DEFAULT_MODEL


def translate(text: str, target_language: str) -> str:
    """text를 target_language(LANGUAGES의 버튼 라벨)로 번역한다."""
    if target_language not in LANGUAGES:
        raise TranslationError(f"지원하지 않는 언어입니다: {target_language}")
    if not text.strip():
        raise TranslationError("번역할 글을 먼저 입력해 주세요.")
    if len(text) > MAX_INPUT_CHARS:
        raise TranslationError(
            f"입력은 최대 {MAX_INPUT_CHARS:,}자까지 가능합니다. (현재 {len(text):,}자)"
        )

    api_key = get_api_key()
    if not api_key:
        raise TranslationError("`.env` 파일에 OPENAI_API_KEY가 설정되어 있지 않습니다.")

    model = get_model()
    # 기본 timeout(600초)이면 네트워크 장애 시 화면이 오래 멈추므로 짧게 제한한다.
    client = OpenAI(api_key=api_key, timeout=60, max_retries=1)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.format(language=LANGUAGES[target_language])},
                {"role": "user", "content": text},
            ],
        )
    except openai.AuthenticationError:
        raise TranslationError("API 키가 올바르지 않습니다. `.env` 파일을 확인해 주세요.") from None
    except openai.NotFoundError:
        raise TranslationError(
            f"설정한 모델({model})을 사용할 수 없습니다. `.env`의 OPENAI_MODEL을 확인해 주세요."
        ) from None
    except openai.RateLimitError:
        raise TranslationError("요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.") from None
    except (openai.APIConnectionError, openai.APITimeoutError):
        raise TranslationError("번역 중 오류가 발생했습니다: 네트워크에 연결할 수 없습니다.") from None
    except openai.APIError as e:
        # 키가 포함될 수 있는 원본 요청 정보는 빼고 메시지만 노출한다.
        raise TranslationError(f"번역 중 오류가 발생했습니다: {getattr(e, 'message', type(e).__name__)}") from None

    content = response.choices[0].message.content or ""
    return content.strip()
