from marshmallow import EXCLUDE, Schema
import ujson


class UjsonSchema(Schema):
    """
    Base schema with a faster json library
    """

    class Meta:
        render_module = ujson
        unknown = EXCLUDE
