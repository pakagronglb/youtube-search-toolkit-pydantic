""" YouTube Tools based on Google YouTube Data API """
import re
import time
from googleapiclient.discovery import Resource
from pydantic import BaseModel, Field
from youtube_transcript_api import YouTubeTranscriptApi
from tools.google.google_apis import setup_logger, create_service

logger = setup_logger('YouTubeTool')

class PlaylistInfo(BaseModel):
    playlist_id: str = Field(..., description='Playlist ID')
    playlist_title: str = Field(..., description='Playlist Title')
    channel_id: str = Field(..., description='Channel ID')
    description: str = Field(..., description='Playlist Description')
    published_at: str = Field(..., description='Playlist Published Time')

class PlaylistResults(BaseModel):
    total_results: int = Field(..., description='Total number of results')
    playlists: list[PlaylistInfo] = Field(..., description='Playlist Information')

class ChannelInfo(BaseModel):
    channel_id: str = Field(..., description='Channel ID')
    channel_title: str = Field(..., description='Channel Title')
    description: str = Field(..., description='Channel Description')
    published_at: str = Field(..., description='Channel Published Time')
    country: str = Field(None, description='Channel Country')
    view_count: int = Field(None, description='View Count')
    subscriber_count: int = Field(None, description='Subscriber Count')
    video_count: int = Field(None, description='Video Count')

class ChannelResults(BaseModel):
    total_results: int = Field(..., description='Total number of results')
    channels: list[ChannelInfo] = Field(..., description='Channel Information')

class VideoInfo(BaseModel):
    channel_id: str = Field(..., description='Channel ID')
    channel_title: str = Field(..., description='Channel Title')
    video_id: str = Field(..., description='Video ID')
    video_title: str = Field(..., description='Video Title')
    description: str = Field(..., description='Video Description')
    published_at: str = Field(..., description='Video Published Time')

    # Additional Information (optional)
    tags: list[str] = Field(None, description='Video Tags')
    duration: str = Field(None, description='Video Duration')
    dimension: str = Field(None, description='Video Dimension')
    view_count: int = Field(None, description='View Count')
    like_count: int = Field(None, description='Like Count')
    comment_count: int = Field(None, description='Comment Count')  # default to 0 to avoid type error
    topic_categories: list[str] = Field(None, description='Topic Categories')
    has_paid_product_placement: bool = Field(None, description='Has Paid Product Placement')

class VideoResults(BaseModel):
    total_results: int = Field(..., description='Total number of results')
    videos: list[VideoInfo] = Field(..., description='Video Information')


def extract_video_id(input_str: str) -> str | None:
    """
    Extract YouTube video ID from a URL or ID string.

    Args:
        input_str: URL or ID string to extract video ID from.

    Returns:
        str: Extracted YouTube video ID.
    """
    url_pattern = re.compile(
        r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})'
    )
    match = url_pattern.match(input_str)

    if match:
        return match.group(1)

    id_pattern = re.compile(r'^[a-zA-Z0-9_-]{11}$')
    if id_pattern.match(input_str):
        return input_str

    return None

def download_transcript(video_id: str, include_timestamp: bool = False) -> str:
    """
    Download the transcript for a YouTube video.

    Args:
        video_id: YouTube video ID or URL.

    Returns:
        str: Transcript text of the video.
    """
    video_id = extract_video_id(video_id)
    if not video_id:
        return 'Invalid YouTube video ID or URL.'
    
    logger.info(f"Downloading transcript for video ID: {video_id}")
    logger.debug(f"Include timestamp: {include_timestamp}")

    try:
        if include_timestamp:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = str(transcript)
        else:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = '\n'.join([entry['text'] for entry in transcript])

        return transcript_text
    except Exception as e:
        return f'Error downloading transcript: {str(e)}'


class YouTubeTool:
    """  
    Toolkit for interacting with the YouTube Data API.

    Based on https://developers.google.com/youtube/v3/docs
    """
    API_NAME = 'youtube'
    API_VERSION = 'v3'
    SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

    def __init__(self, client_secret: str) -> None:
        logger.info("Initializing YouTubeTool")
        self.client_secret = client_secret
        self._init_youtube_service()
        logger.info("YouTubeTool initialized successfully")

    def _init_youtube_service(self):
        """
        Initialize the YouTube Data API service.
        """
        logger.info("Initializing YouTube Data API service")
        self.service = create_service(
            self.client_secret,
            self.API_NAME,
            self.API_VERSION,
            self.SCOPES
        )
        logger.debug(f"YouTube service created: {self.service is not None}")

    @property
    def youtube_service(self) -> Resource:
        """
        Return YouTube Data API service instance.
        """
        logger.debug("Accessing youtube_service property")
        return self.service

    def get_channel_info(self, channel_id: str) -> ChannelInfo:
        """
        Get information about a YouTube channel based on the provided channel ID.

        Args:
            channel_id (str): The ID of the YouTube channel.
        
        Returns:
            ChannelInfo: Information about the YouTube channel.
        """
        logger.info(f"Getting channel info for channel_id: {channel_id}")
        request = self.service.channels().list(
            part='snippet,statistics',
            id=channel_id
        )
        logger.debug("Executing channel info request")
        response = request.execute()
        logger.debug(f"Channel info response received with {len(response.get('items', []))} items")

        channel_info = ChannelInfo(
            channel_id=response['items'][0].get('id'),
            channel_title=response['items'][0]['snippet'].get('title'),
            description=response['items'][0]['snippet'].get('description'),
            published_at=response['items'][0]['snippet'].get('publishedAt'),
            country=response['items'][0]['snippet'].get('country', ''),
            view_count=response['items'][0]['statistics'].get('viewCount'),
            subscriber_count=response['items'][0]['statistics'].get('subscriberCount'),
            video_count=response['items'][0]['statistics'].get('videoCount')  # use get to avoid KeyError
        )
        logger.info(f"Retrieved channel info for: {channel_info.channel_title}")
        return channel_info.model_dump_json()

    
    def search_channel(self, channel_name: str,  published_after: str = None, published_before: str = None, region_code: str = 'US', order: str = 'relevance', max_results: int = 50) -> ChannelResults:
        """
        Searches for YouTube channels based on the provided channel name.
        
        Args:
            channel_name (str): The name of the channel to search for.
            published_after (str): The publishedAfter parameter indicates that the API response should only contain resources created at or after the specified time. The value is an RFC 3339 formatted date-time value (1970-01-01T00:00:00Z).
            published_before (str): The publishedBefore parameter indicates that the API response should only contain resources created before or at the specified time. The value is an RFC 3339 formatted date-time value (1970-01-01T00:00:00Z).
            region_code (str): The regionCode parameter instructs the API to return search results for the specified country. The parameter value is an ISO 3166-1 alpha-2 country code.
            order (str): The order in which to return results. Default is 'relevance'. Options include 'date', 'rating', 'relevance', 'title', 'videoCount', and 'viewCount'.
            max_results (int): The maximum number of results to return. Default is 50.

        Returns:
            ChannelResults: A list of channels that match the search
        """
        logger.info(f"Searching for channels with name: {channel_name}, max_results: {max_results}")
        logger.debug(f"Search parameters: published_after={published_after}, published_before={published_before}, region_code={region_code}, order={order}")
        
        lst = []
        total_results = 0
        next_page_token = None

        while len(lst) < max_results:
            current_max = min(50, max_results - len(lst))
            logger.debug(f"Fetching next {current_max} channel results, current count: {len(lst)}")
            
            request = self.service.search().list(
                part='snippet',
                q=channel_name,
                type='channel',
                maxResults=current_max,
                order=order,
                publishedAfter=published_after,
                publishedBefore=published_before,
                regionCode=region_code,
                pageToken=next_page_token
            )
            response = request.execute()

            time.sleep(1)  # Rate limit to avoid hitting API limits

            logger.debug(f"Channel search response received with {len(response.get('items', []))} items")

            for item in response['items']:
                channel_id = item['id'].get('channelId')
                channel_title = item['snippet'].get('title')
                channel_description = item['snippet'].get('description')
                channel_published_at = item['snippet'].get('publishedAt')
                channel_info = ChannelInfo(
                    channel_id=channel_id,
                    channel_title=channel_title,
                    description=channel_description,
                    published_at=channel_published_at
                )
                lst.append(channel_info)

            total_results = response['pageInfo']['totalResults']
            next_page_token = response.get('nextPageToken')
            logger.debug(f"Retrieved {len(response.get('items', []))} channels, next_page_token: {next_page_token}")

            if not next_page_token:
                logger.debug("No more pages available")
                break
        
        logger.info(f"Channel search completed. Found {total_results} total results, returning {len(lst)} channels")
        return ChannelResults(
            total_results=total_results,
            channels=lst
        ).model_dump_json()

    def search_playlist(self, query: str, published_after: str = None, published_before: str = None, region_code: str = 'US', order: str = 'date', max_results: int = 50) -> PlaylistResults:
        """
        Searches for YouTube playlists based on the provided query.

        Args:
            query (str): The query to search for.
            published_after (str): The publishedAfter parameter indicates that the API response should only contain resources created at or after the specified time. The value is an RFC 3339 formatted date-time value (1970-01-01T00:00:00Z).
            published_before (str): The publishedBefore parameter indicates that the API response should only contain resources created before or at the specified time. The value is an RFC 3339 formatted date-time value (1970-01-01T00:00:00Z).
            region_code (str): The regionCode parameter instructs the API to return search results for the specified country. The parameter value is an ISO 3166-1 alpha-2 country code.
            order (str): The order in which to return results. Default is 'date'. Options include 'date', 'rating', 'relevance', 'title', 'videoCount', and 'viewCount'.
            max_results (int): The maximum number of results to return. Default is 50.

        Returns:
            PlaylistResults: A list of playlists that match the search
        """
        logger.info(f"Searching for playlists with query: {query}, max_results: {max_results}")
        logger.debug(f"Search parameters: published_after={published_after}, published_before={published_before}, region_code={region_code}, order={order}")
        
        lst = []
        total_results = 0
        next_page_token = None

        while len(lst) < max_results:
            current_max = min(50, max_results - len(lst))
            logger.debug(f"Fetching next {current_max} playlist results, current count: {len(lst)}")
            
            request = self.service.search().list(
                part='snippet',
                q=query,
                type='playlist',
                maxResults=current_max,
                order=order,
                publishedAfter=published_after,
                publishedBefore=published_before,
                regionCode=region_code,                
                pageToken=next_page_token
            )
            response = request.execute()

            time.sleep(1)  # Rate limit to avoid hitting API limits

            logger.debug(f"Playlist search response received with {len(response.get('items', []))} items")

            for item in response['items']:
                playlist_id = item['id'].get('playlistId')
                playlist_title = item['snippet'].get('title')
                channel_id = item['snippet'].get('channelId')
                playlist_description = item['snippet'].get('description')
                playlist_published_at = item['snippet'].get('publishedAt')
                playlist_info = PlaylistInfo(
                    playlist_id=playlist_id,
                    playlist_title=playlist_title,
                    channel_id=channel_id,
                    description=playlist_description,
                    published_at=playlist_published_at
                )
                lst.append(playlist_info)

            total_results = response['pageInfo']['totalResults']
            next_page_token = response.get('nextPageToken')
            logger.debug(f"Retrieved {len(response.get('items', []))} playlists, next_page_token: {next_page_token}")

            if not next_page_token:
                logger.debug("No more pages available")
                break

        logger.info(f"Playlist search completed. Found {total_results} total results, returning {len(lst)} playlists")
        return PlaylistResults(
            total_results=total_results,
            playlists=lst
        ).model_dump_json()

    def search_videos(self, query: str,  published_after: str = None, published_before: str = None, region_code: str = 'US', video_duration: str = 'any', order: str = 'date', max_results: int = 50) -> VideoResults:
        """
        Searches for YouTube videos based on the provided query.

        Args:
            query (str): The query to search for.
            published_after (str): The publishedAfter parameter indicates that the API response should only contain resources created at or after the specified time. The value is an RFC 3339 formatted date-time value (1970-01-01T00:00:00Z).
            published_before (str): The publishedBefore parameter indicates that the API response should only contain resources created before or at the specified time. The value is an RFC 3339 formatted date-time value (1970-01-01T00:00:00Z).
            region_code (str): The regionCode parameter instructs the API to return search results for the specified country. The parameter value is an ISO 3166-1 alpha-2 country code.
            video_duration (str): The videoDuration parameter filters video search results based on their duration. Default is 'Any'. Options include 'any', 'long', 'medium', 'short'.
            order (str): The order in which to return results. Default is 'date'. Options include 'date', 'rating', 'relevance', 'title', 'videoCount', and 'viewCount'.
            max_results (int): The maximum number of results to return. Default is 50.

        Returns:
            VideoResults: A list of videos that match the search
        """
        logger.info(f"Searching for videos with query: {query}, max_results: {max_results}")
        logger.debug(f"Search parameters: published_after={published_after}, published_before={published_before}, region_code={region_code}, video_duration={video_duration}, order={order}")
        
        lst = []
        total_results = 0
        next_page_token = None

        while len(lst) < max_results:
            current_max = min(50, max_results - len(lst))
            logger.debug(f"Fetching next {current_max} video results, current count: {len(lst)}")
            
            request = self.service.search().list(
                part='snippet',
                q=query,
                type='video',
                maxResults=current_max,
                order=order,
                publishedAfter=published_after,
                publishedBefore=published_before,
                regionCode=region_code,
                videoDuration=video_duration,
                pageToken=next_page_token
            )
            response = request.execute()

            time.sleep(1)  # Rate limit to avoid hitting API limits

            logger.debug(f"Video search response received with {len(response.get('items', []))} items")

            for item in response['items']:
                channel_id = item['snippet'].get('channelId')
                channel_title = item['snippet'].get('channelTitle')
                video_id = item['id'].get('videoId')
                video_title = item['snippet'].get('title')
                video_description = item['snippet'].get('description')
                video_published = item['snippet'].get('publishTime')
                video_info = VideoInfo(
                    channel_id=channel_id,
                    channel_title=channel_title,
                    video_id=video_id,
                    video_title=video_title,
                    description=video_description,
                    published_at=video_published
                )
                lst.append(video_info)

            total_results = response['pageInfo']['totalResults']
            next_page_token = response.get('nextPageToken')
            logger.debug(f"Retrieved {len(response.get('items', []))} videos, next_page_token: {next_page_token}")

            if not next_page_token:
                logger.debug("No more pages available")
                break

        logger.info(f"Video search completed. Found {total_results} total results, returning {len(lst)} videos")
        return VideoResults(
            total_results=total_results,
            videos=lst
        ).model_dump_json()

    def get_video_info(self, video_ids: str, max_results: int = 50) -> VideoResults:
        """
        Retrieves detailed information about YouTube videos based on the provided video IDs in a comma-separated string.

        Args:
            video_ids (str): A comma-separated string of video IDs. For example: 'dQw4w9WgXcQ,3fumBcKC6RE'
            max_results (int): The maximum number of results to return. Default is 50.

        Returns:
            VideoResults: A list of videos with detailed information
        """
        logger.info(f"Getting video info for video_ids: {video_ids}, max_results: {max_results}")
        
        lst = []
        total_results = 0
        next_page_token = None

        while len(lst) < max_results:
            current_max = min(50, max_results - len(lst))
            logger.debug(f"Fetching next {current_max} video details, current count: {len(lst)}")
            
            request = self.service.videos().list(
                part='id,snippet,contentDetails,statistics,paidProductPlacementDetails,topicDetails', 
                id=video_ids,
                maxResults=current_max,
                pageToken=next_page_token
            )
            response = request.execute()

            time.sleep(1)  # Rate limit to avoid hitting API limits

            logger.debug(f"Video info response received with {len(response.get('items', []))} items")

            for item in response['items']:
                snippet = item['snippet']
                content_details = item.get('contentDetails', {})
                statistics = item.get('statistics', {})
                topic_details = item.get('topicDetails', {})

                video_info = VideoInfo(
                    channel_id=snippet['channelId'],
                    channel_title=snippet['channelTitle'],
                    video_id=item['id'],
                    video_title=snippet['title'],
                    description=snippet.get('description', ''),
                    published_at=snippet['publishedAt'],
                    tags=snippet.get('tags', []),
                    duration=content_details.get('duration'),
                    dimension=content_details.get('dimension'),
                    view_count=statistics.get('viewCount'),
                    like_count=statistics.get('likeCount', 0),
                    comment_count=statistics.get('commentCount', 0),
                    topic_categories=topic_details.get('topicCategories', []),
                    has_paid_product_placement=snippet.get('hasPaidPromotion', False)
                )
                lst.append(video_info)

            total_results = response['pageInfo']['totalResults']
            next_page_token = response.get('nextPageToken')
            logger.debug(f"Retrieved {len(response.get('items', []))} video details, next_page_token: {next_page_token}")

            if not next_page_token:
                logger.debug("No more pages available")
                break

        logger.info(f"Video info retrieval completed. Found {total_results} total results, returning {len(lst)} videos")
        return VideoResults(
            total_results=total_results,
            videos=lst
        ).model_dump_json()

    def get_channel_videos(self, channel_id: str, max_results: int = 10) -> VideoResults:
        """
        Return videos uploaded by a YouTube channel based on the provided channel ID.

        Args:
            channel_id (str): The ID of the YouTube channel.
            max_results (int): The maximum number of results to return. Default is 50.

        Returns:
            VideoResults: A list of videos uploaded by the channel
        """
        logger.info(f"Getting videos for channel_id: {channel_id}, max_results: {max_results}")
        
        lst = []
        total_results = 0
        next_page_token = None

        while len(lst) < max_results:
            logger.debug(f"Retrieving uploads playlist ID for channel: {channel_id}")
            request = self.service.channels().list(
                part='contentDetails',
                id=channel_id
            )
            response = request.execute()
            logger.debug(f"Channel details response received with {len(response.get('items', []))} items")

            uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists'].get('uploads')
            logger.debug(f"Found uploads playlist ID: {uploads_playlist_id}")

            current_max = min(50, max_results - len(lst))
            logger.debug(f"Fetching next {current_max} playlist items, current count: {len(lst)}")
            
            playlist_request = self.service.playlistItems().list(
                part='snippet',
                playlistId=uploads_playlist_id,
                maxResults=current_max,
                pageToken=next_page_token
            )
            playlist_response = playlist_request.execute()
            
            time.sleep(1)  # Rate limit to avoid hitting API limits

            logger.debug(f"Playlist items response received with {len(playlist_response.get('items', []))} items")

            for item in playlist_response['items']:
                snippet = item['snippet']

                video_info = VideoInfo(
                    channel_id=snippet['channelId'],
                    channel_title=snippet['channelTitle'],
                    video_id=snippet['resourceId']['videoId'],
                    video_title=snippet['title'],
                    description=snippet.get('description', ''),
                    published_at=snippet['publishedAt'],
                )
                lst.append(video_info)

            total_results = playlist_response['pageInfo']['totalResults']
            next_page_token = playlist_response.get('nextPageToken')
            logger.debug(f"Retrieved {len(playlist_response.get('items', []))} video items, next_page_token: {next_page_token}")

            if not next_page_token:
                logger.debug("No more pages available")
                break

        logger.info(f"Channel videos retrieval completed. Found {total_results} total videos, returning {len(lst)} videos")
        return VideoResults(
            total_results=total_results,
            videos=lst
        ).model_dump_json()
    
    def construct_hyperlink(self, id: str, type: str) -> str:
        """
        Construct a hyperlink based on the provided ID and type.

        Args:
            id (str): The ID of the YouTube resource.
            type (str): The type of the YouTube resource. Options include 'channel', 'playlist', and 'video'.

        Returns:
            str: The hyperlink to the YouTube resource.
        """
        logger.debug(f"Constructing hyperlink for {type} with id: {id}")
        
        if type == 'channel':
            link = f'https://www.youtube.com/channel/{id}'
        elif type == 'playlist':
            link = f'https://www.youtube.com/playlist?list={id}'
        elif type == 'video':
            link = f'https://www.youtube.com/watch?v={id}'
        else:
            logger.warning(f"Unknown resource type: {type}")
            link = ''
            
        logger.debug(f"Constructed hyperlink: {link}")
        return link