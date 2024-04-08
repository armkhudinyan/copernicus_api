"""Module providing customized error handling exceptions"""
class AttributeNotFoundError(Exception):
    """Custom helper exception to handle cases when product specific attributes
    passed as filtering argument do not exist in product's metadata.
    """
    def __init__(self, error: Exception) -> None:
        self.message = f"'{error.args[0]}' is not found in the product attributes."
        super().__init__(self.message)


class WKTError(Exception):
    """Custom exception to handle the Well-Known_Text format for query area input
    """

    def __init__(self, error: Exception) -> None:
        self.message = (f"{error.__class__.__name__}: {error} \n"
                    "AOI will not be considered for this query")
        super().__init__(self.message)


class TokenGenerationError(Exception):
    pass


class QueryError(Exception):
    pass
