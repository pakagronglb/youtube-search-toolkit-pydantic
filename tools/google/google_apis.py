import os
import logging
from rich.logging import RichHandler
from rich.console import Console
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

logging.getLogger('googleapiclient.discovery').setLevel(logging.ERROR)
logging.getLogger("openai").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)

def setup_logger(logger_name: str = None):
    if logger_name is None:
        logger_name = __name__

    console = Console()
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=False)]
    )
    logger = logging.getLogger(logger_name)
    return logger

logger = setup_logger('GoogleTool')

def create_service(client_secret_file, api_name, api_version, *scopes, prefix=''):
    """
    Create a Google API service instance.
    
    Args:
        client_secret_file: Path to the client secret JSON file
        api_name: Name of the API service
        api_version: Version of the API
        scopes: Authorization scopes required by the API
        prefix: Optional prefix for token filename
        
    Returns:
        Google API service instance or None if creation failed
    """
    CLIENT_SECRET_FILE = client_secret_file
    API_SERVICE_NAME = api_name
    API_VERSION = api_version
    SCOPES = [scope for scope in scopes[0]]
    
    creds = None
    working_dir = os.getcwd()
    token_dir = 'token files'
    token_file = f'token_{API_SERVICE_NAME}_{API_VERSION}{prefix}.json'

    if not os.path.exists(os.path.join(working_dir, token_dir)):
        os.mkdir(os.path.join(working_dir, token_dir))
        logger.info(f"Created token directory: {token_dir}")

    if os.path.exists(os.path.join(working_dir, token_dir, token_file)):
        creds = Credentials.from_authorized_user_file(os.path.join(working_dir, token_dir, token_file), SCOPES)
        logger.debug(f"Loaded existing credentials from {token_file}")
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired credentials")
            creds.refresh(Request())
        else:
            logger.info("Obtaining new credentials")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(os.path.join(working_dir, token_dir, token_file), 'w') as token:
            token.write(creds.to_json())
            logger.info(f"Saved credentials to {token_file}")

    try:
        service = build(API_SERVICE_NAME, API_VERSION, credentials=creds, static_discovery=False)
        logger.info(f"{API_SERVICE_NAME} {API_VERSION} service created successfully")
        return service
    except Exception as e:
        logger.error(f"Failed to create service instance for {API_SERVICE_NAME}")
        logger.exception(e)
        os.remove(os.path.join(working_dir, token_dir, token_file))
        logger.warning(f"Removed invalid token file: {token_file}")
        return None
