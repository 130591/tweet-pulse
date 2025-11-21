from elasticsearch.exceptions import RequestError
from tweetpulse.models.tweet import Tweet
from tweetpulse.core.elasticsearch.schemas.schema import TWEET_INDEX_MAPPING
from tweetpulse.core.elasticsearch.schemas.mapper import TweetDocumentMapper
from tweetpulse.core.dependencies import get_elasticsearch_client
from tweetpulse.core.dependencies import depends

class SearchService:
  def __init__(self, client: depends(get_elasticsearch_client), mapper: TweetDocumentMapper = None):
    self.client = client
    self.index_name = "tweets"
    self.mapper = mapper or TweetDocumentMapper()

  async def create_index(self):
    if not await self.client.indices.exists(index=self.index_name):
      try:
        await self.client.indices.create(index=self.index_name, body=TWEET_INDEX_MAPPING)
      except RequestError as e:
        print(f"Error creating index: {e}")
    else:
      print(f"Index '{self.index_name}' already exists.")

  async def index_tweet(self, tweet: Tweet):
    document = self.mapper.to_document(tweet)
    await self.client.index(index=self.index_name, id=str(tweet.id), document=document)
