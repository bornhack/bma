from ninja import Schema


class MessageSchema(Schema):
    """The schema used for all API messages."""

    message: str
