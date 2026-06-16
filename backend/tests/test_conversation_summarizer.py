"""Tests for the rolling per-conversation summary (app/services/llm/conversation_summarizer.py)."""

import uuid
from unittest.mock import MagicMock

import pytest

from app.db.database import Base, SessionLocal, get_engine
from app.db.models import Conversation
from app.services.llm.conversation_summarizer import (
    get_conversation_summary_block,
    summarize_conversation,
)


@pytest.fixture(scope="module", autouse=True)
def _create_tables():
    Base.metadata.create_all(bind=get_engine())


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_conversation_defaults_to_no_summary(db):
    conv = Conversation(id=str(uuid.uuid4()))
    db.add(conv)
    db.commit()
    assert conv.summary == ""
    assert conv.summarized_through_count == 0


def test_get_conversation_summary_block_returns_empty_for_none_id(db):
    assert get_conversation_summary_block(db, None) == ""


def test_get_conversation_summary_block_returns_empty_when_no_summary(db):
    conv = Conversation(id=str(uuid.uuid4()))
    db.add(conv)
    db.commit()
    assert get_conversation_summary_block(db, conv.id) == ""


def test_get_conversation_summary_block_formats_existing_summary(db):
    conv = Conversation(id=str(uuid.uuid4()), summary="The user is preparing for a job interview.")
    db.add(conv)
    db.commit()
    block = get_conversation_summary_block(db, conv.id)
    assert block.startswith("[CONVERSATION SO FAR]")
    assert block.endswith("[/CONVERSATION SO FAR]")
    assert "preparing for a job interview" in block


@pytest.mark.asyncio
async def test_summarize_conversation_returns_model_text(monkeypatch):
    import anthropic

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Updated rolling summary.")]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    monkeypatch.setattr(anthropic, "Anthropic", MagicMock(return_value=mock_client))

    result = await summarize_conversation(
        previous_summary="",
        new_messages=[{"role": "user", "content": "I have a big presentation tomorrow."}],
        api_key="test_key",
    )
    assert result == "Updated rolling summary."
    mock_client.messages.create.assert_called_once()
    assert mock_client.messages.create.call_args.kwargs["model"] == "claude-haiku-4-5-20251001"


@pytest.mark.asyncio
async def test_summarize_conversation_propagates_api_failure(monkeypatch):
    import anthropic

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = RuntimeError("API down")
    monkeypatch.setattr(anthropic, "Anthropic", MagicMock(return_value=mock_client))

    with pytest.raises(RuntimeError):
        await summarize_conversation(
            previous_summary="old summary",
            new_messages=[{"role": "user", "content": "hello"}],
            api_key="test_key",
        )


@pytest.mark.asyncio
async def test_summarize_conversation_no_op_without_new_messages():
    result = await summarize_conversation("existing summary", [], "test_key")
    assert result == "existing summary"
