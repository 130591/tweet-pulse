from elasticsearch import AsyncElasticsearch
from typing import Optional
from ..config import get_settings

settings = get_settings()

# Singleton Elasticsearch client
_elastic_client: Optional[AsyncElasticsearch] = None


def get_elastic_client() -> AsyncElasticsearch:
	global _elastic_client
	if _elastic_client is None:
		_elastic_client = AsyncElasticsearch(
			hosts=[settings.ELASTICSEARCH_URL],
			verify_certs=False,
			ssl_show_warn=False
		)
	return _elastic_client
