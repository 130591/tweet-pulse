"""
Integration tests for StreamConsumer component.
Testing deterministic behavior for message consumption.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from tweetpulse.ingestion.consumer import StreamConsumer


class TestConsumerIntegration:
    """Test StreamConsumer with deterministic behavior."""
    
    @pytest.mark.asyncio
    async def test_consumer_initialization(self, clean_redis):
        """Test consumer initializes correctly."""
        processor = AsyncMock()
        
        consumer = StreamConsumer(
            redis=clean_redis,
            stream_key="test:stream",
            group_name="test_group",
            consumer_name="worker-0",
            processor=processor
        )
        
        assert consumer.stream_key == "test:stream"
        assert consumer.group_name == "test_group"
        assert consumer.consumer_name == "worker-0"
        assert consumer.processor == processor
    
    @pytest.mark.asyncio
    async def test_consumer_processes_single_message(self, clean_redis, sample_tweet_data):
        """Test consumer processes a single message correctly."""
        processed_messages = []

        async def test_processor(message):
            processed_messages.append(message)

        # Mock Redis methods without asserting on internal calls
        clean_redis.xgroup_create = MagicMock()
        clean_redis.xreadgroup = MagicMock()
        clean_redis.xack = MagicMock()

        message_data = {k: str(v) for k, v in sample_tweet_data.items()}
        clean_redis.xreadgroup.side_effect = [
            [("test:stream", [(b"msg-1", message_data)])],
            []
        ]

        consumer = StreamConsumer(
            redis=clean_redis,
            stream_key="test:stream",
            group_name="test_group",
            consumer_name="worker-0",
            processor=test_processor
        )

        task = asyncio.create_task(consumer.start())
        await asyncio.sleep(0.2)
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        # BEHAVIOR: Processor should be called with decoded message
        assert len(processed_messages) == 1
        assert processed_messages[0]['id'] == str(sample_tweet_data['id'])
        assert processed_messages[0]['text'] == str(sample_tweet_data['text'])

    @pytest.mark.asyncio
    async def test_consumer_processes_batch_messages(self, clean_redis, sample_tweets_batch):
        """Test consumer processes multiple messages correctly."""
        processed_messages = []

        async def test_processor(message):
            processed_messages.append(message['id'])

        clean_redis.xgroup_create = MagicMock()
        clean_redis.xreadgroup = MagicMock()
        clean_redis.xack = MagicMock()

        # Create batch of messages
        messages = [
            (f"msg-{i}".encode(), {k: str(v) for k, v in tweet.items()})
            for i, tweet in enumerate(sample_tweets_batch[:3])
        ]

        clean_redis.xreadgroup.side_effect = [
            [("test:stream", messages)],
            []
        ]

        consumer = StreamConsumer(
            redis=clean_redis,
            stream_key="test:stream",
            group_name="test_group",
            consumer_name="worker-0",
            processor=test_processor
        )

        task = asyncio.create_task(consumer.start())
        await asyncio.sleep(0.3)
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        # BEHAVIOR: All messages should be processed in order
        assert len(processed_messages) == 3
        assert processed_messages[0] == "tweet_00000"
        assert processed_messages[1] == "tweet_00001"
        assert processed_messages[2] == "tweet_00002"

    @pytest.mark.asyncio
    async def test_consumer_decodes_bytes_to_strings(self, clean_redis):
        """Test consumer correctly decodes byte strings."""
        processed_data = []

        async def test_processor(message):
            processed_data.append(message)

        clean_redis.xgroup_create = MagicMock()
        clean_redis.xreadgroup = MagicMock()
        clean_redis.xack = MagicMock()

        # Message with bytes that should be decoded
        message_with_bytes = {
            b"id": b"123",
            b"text": b"Test tweet",
            "already_string": "value"
        }

        clean_redis.xreadgroup.side_effect = [
            [("test:stream", [(b"msg-1", message_with_bytes)])],
            []
        ]

        consumer = StreamConsumer(
            redis=clean_redis,
            stream_key="test:stream",
            group_name="test_group",
            consumer_name="worker-0",
            processor=test_processor
        )

        task = asyncio.create_task(consumer.start())
        await asyncio.sleep(0.2)
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        # BEHAVIOR: Bytes should be decoded to strings
        assert len(processed_data) == 1
        assert processed_data[0]['id'] == "123"
        assert processed_data[0]['text'] == "Test tweet"
        assert processed_data[0]['already_string'] == "value"

    @pytest.mark.asyncio
    async def test_consumer_handles_processing_errors_gracefully(self, clean_redis, sample_tweet_data):
        """Test consumer handles processor errors without crashing."""
        error_count = 0

        async def failing_processor(message):
            nonlocal error_count
            error_count += 1
            raise Exception("Processing failed")

        clean_redis.xgroup_create = MagicMock()
        clean_redis.xreadgroup = MagicMock()
        clean_redis.xack = MagicMock()

        message_data = {k: str(v) for k, v in sample_tweet_data.items()}
        clean_redis.xreadgroup.side_effect = [
            [("test:stream", [(b"msg-1", message_data)])],
            []
        ]

        consumer = StreamConsumer(
            redis=clean_redis,
            stream_key="test:stream",
            group_name="test_group",
            consumer_name="worker-0",
            processor=failing_processor
        )

        task = asyncio.create_task(consumer.start())
        await asyncio.sleep(0.2)
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        # BEHAVIOR: Processor should still be called even if it fails
        assert error_count == 1

    @pytest.mark.asyncio
    async def test_consumer_handles_empty_stream(self, clean_redis):
        """Test consumer handles empty Redis stream correctly."""
        processed_count = 0

        async def test_processor(message):
            nonlocal processed_count
            processed_count += 1

        clean_redis.xgroup_create = MagicMock()
        clean_redis.xreadgroup = MagicMock(return_value=[])

        consumer = StreamConsumer(
            redis=clean_redis,
            stream_key="test:stream",
            group_name="test_group",
            consumer_name="worker-0",
            processor=test_processor
        )

        task = asyncio.create_task(consumer.start())
        await asyncio.sleep(0.3)
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        # BEHAVIOR: No messages should be processed when stream is empty
        assert processed_count == 0
