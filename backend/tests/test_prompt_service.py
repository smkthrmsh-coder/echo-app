"""
Characterization tests for DefaultPromptConstructionService — must produce output
byte-identical to the inline ternary it replaced in anthropic_provider.py / chat_provider.py:

    system = (brain_context + "\\n\\n" + base_prompt) if brain_context else base_prompt
"""

from app.experience_os.services.prompt_service import DefaultPromptConstructionService


def _legacy_ternary(brain_context, base_prompt):
    return (brain_context + "\n\n" + base_prompt) if brain_context else base_prompt


def test_build_system_prompt_with_brain_context():
    service = DefaultPromptConstructionService()
    base_prompt = "You are Echo."
    brain_context = "[ECHO BRAIN]\n• likes coffee\n[/ECHO BRAIN]"
    actual = service.build_system_prompt(brain_context, base_prompt)
    assert actual == _legacy_ternary(brain_context, base_prompt)


def test_build_system_prompt_without_brain_context():
    service = DefaultPromptConstructionService()
    base_prompt = "You are Echo."
    assert service.build_system_prompt(None, base_prompt) == _legacy_ternary(None, base_prompt)
    assert service.build_system_prompt(None, base_prompt) == base_prompt


def test_build_system_prompt_empty_string_brain_context_is_falsy():
    service = DefaultPromptConstructionService()
    base_prompt = "You are Echo."
    assert service.build_system_prompt("", base_prompt) == _legacy_ternary("", base_prompt)
    assert service.build_system_prompt("", base_prompt) == base_prompt
