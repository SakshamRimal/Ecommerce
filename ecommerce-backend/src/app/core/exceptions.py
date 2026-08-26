class AppException(Exception):
    """Base class for all application exceptions."""
    status_code: int = 500
    detail = "Internal Server Error"
    
    def __init__(self , detail: str | None = None):
        if detail:
            self.detail = detail
        super().__init__(self.detail)
        
class ConflictError(AppException):
    status_code = 409
    detail = "Conflict Error"
    
class UnauthorizedError(AppException):
    status_code = 401
    detail = "Unauthorized Error"
    
class ForbiddenError(AppException):
    status_code = 403
    detail = "Forbidden Error"
    
class NotFoundError(AppException):
    status_code = 404
    detail = "Not Found Error"
    