import orjson
import yaml
from ninja.parser import Parser
from ninja.renderers import BaseRenderer


class ORJSONParser(Parser):
    def parse_body(self, request):
        return orjson.loads(request.body)


class ORJSONRenderer(BaseRenderer):
    media_type = "application/json"

    def render(self, request, data, *, response_status):
        return orjson.dumps(data)


class YamlParser(Parser):
    def parse_body(self, request):
        return yaml.safe_load(request.body)


class YamlRenderer(BaseRenderer):
    media_type = "application/yaml"

    def render(self, request, data, *, response_status):
        return yaml.dump(data)
