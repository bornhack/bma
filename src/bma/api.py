from ninja import NinjaAPI

from files.api import router as files_router
from utils.parser import ORJSONParser
from utils.parser import ORJSONRenderer

# define the v1 api for various formats
api_v1_json = NinjaAPI(
    version="1",
    csrf=True,
    parser=ORJSONParser(),
    renderer=ORJSONRenderer(),
    urls_namespace="api-v1-json",
)

api_v1_json.add_router("/files/", files_router, tags=["files"])
