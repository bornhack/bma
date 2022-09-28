from ninja import Schema


class Message(Schema):
    """The schema used for all API messages."""

    message: str
