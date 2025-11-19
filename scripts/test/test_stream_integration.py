#!/usr/bin/env python3
"""
Script de teste para validar a integração do simulador com o pipeline.

Este script:
1. Envia alguns tweets usando o simulador
2. Lê os tweets do Redis Stream
3. Valida que foram enviados corretamente
"""

import asyncio
import json
import logging
from pathlib import Path

from redis.asyncio import Redis
from tweetpulse.core.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


async def test_stream_integration():
    logger.info("=== Starting Stream Integration Test ===\n")
    
    logger.info(f"Connecting to Redis at {settings.REDIS_URL}")
    redis = await Redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    try:
        await redis.ping()
        logger.info("✓ Redis connection successful\n")
        
        stream_key = "ingest:stream"
        
        # Limpa o stream para teste limpo
        logger.info(f"Cleaning stream '{stream_key}' for fresh test...")
        try:
            await redis.delete(stream_key)
            logger.info("✓ Stream cleaned\n")
        except Exception as e:
            logger.warning(f"Could not clean stream: {e}\n")
        
        # Carrega alguns tweets do dataset
        dataset_path = Path("data/fake_tweets_dataset.json")
        logger.info(f"Loading tweets from {dataset_path}")
        
        with open(dataset_path, 'r', encoding='utf-8') as f:
            all_tweets = json.load(f)
        
        # Pega apenas os primeiros 5 tweets para teste
        test_tweets = all_tweets[:5]
        logger.info(f"✓ Loaded {len(test_tweets)} tweets for testing\n")
        
        # Envia tweets para o stream
        logger.info("Sending tweets to stream...")
        sent_ids = []
        
        for i, tweet in enumerate(test_tweets, 1):
            message = {
                "id": str(tweet["id"]),
                "text": tweet["text"],
                "author_id": str(tweet["author_id"]),
                "created_at": tweet["created_at"],
                "source": "test",
                "lang": tweet.get("lang", "en"),
            }
            
            # Adiciona ao stream
            msg_id = await redis.xadd(stream_key, message, maxlen=100000)
            sent_ids.append(msg_id)
            
            logger.info(f"  {i}. Sent tweet {tweet['id']}: {tweet['text'][:50]}...")
        
        logger.info(f"✓ Sent {len(sent_ids)} tweets\n")
        
        # Lê tweets do stream
        logger.info("Reading tweets from stream...")
        
        # XREAD para ler do início
        result = await redis.xread({stream_key: '0'}, count=10)
        
        if not result:
            logger.error("✗ No tweets found in stream!")
            return False
        
        stream_data = result[0][1]  # [(stream_key, [(msg_id, data), ...])]
        logger.info(f"✓ Read {len(stream_data)} tweets from stream\n")
        
        # Valida os tweets
        logger.info("Validating tweets...")
        success = True
        
        for i, (msg_id, data) in enumerate(stream_data, 1):
            tweet_id = data.get('id')
            text = data.get('text', '')
            
            logger.info(f"  {i}. ID: {tweet_id} | Text: {text[:50]}...")
            
            # Valida campos obrigatórios
            required_fields = ['id', 'text', 'author_id', 'created_at']
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                logger.error(f"    ✗ Missing fields: {missing_fields}")
                success = False
            else:
                logger.info(f"    ✓ All required fields present")
        
        # Informações do stream
        logger.info("\nStream information:")
        stream_info = await redis.xinfo_stream(stream_key)
        logger.info(f"  Length: {stream_info['length']}")
        logger.info(f"  First entry ID: {stream_info.get('first-entry', ['N/A'])[0]}")
        logger.info(f"  Last entry ID: {stream_info.get('last-entry', ['N/A'])[0]}")
        
        # Resultado final
        logger.info("\n=== Test Results ===")
        if success:
            logger.info("✓ ALL TESTS PASSED")
            logger.info("\nYou can now:")
            logger.info("1. Run the simulator: python scripts/simulate_tweet_stream.py")
            logger.info("2. Run the consumer to process tweets")
            logger.info("3. Check Redis with: redis-cli XREAD COUNT 10 STREAMS ingest:stream 0")
            return True
        else:
            logger.error("✗ SOME TESTS FAILED")
            return False
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await redis.close()
        logger.info("\nRedis connection closed")


async def main():
    """Função principal."""
    success = await test_stream_integration()
    exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
