import pytest
from app.core.exceptions import (
    AppException,
    ConflictError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
)


class TestAppException:
    def test_base_exception_status_code(self):
        assert AppException.status_code == 500

    def test_base_exception_default_detail(self):
        exc = AppException()
        assert exc.detail == "Internal Server Error"

    def test_base_exception_custom_detail(self):
        exc = AppException("Something went wrong")
        assert exc.detail == "Something went wrong"

    def test_base_exception_is_exception(self):
        assert issubclass(AppException, Exception)


class TestConflictError:
    def test_status_code(self):
        assert ConflictError.status_code == 409

    def test_is_app_exception(self):
        assert issubclass(ConflictError, AppException)

    def test_custom_detail(self):
        exc = ConflictError("Email already exists")
        assert exc.detail == "Email already exists"
        assert exc.status_code == 409


class TestUnauthorizedError:
    def test_status_code(self):
        assert UnauthorizedError.status_code == 401

    def test_is_app_exception(self):
        assert issubclass(UnauthorizedError, AppException)


class TestForbiddenError:
    def test_status_code(self):
        assert ForbiddenError.status_code == 403

    def test_is_app_exception(self):
        assert issubclass(ForbiddenError, AppException)


class TestNotFoundError:
    def test_status_code(self):
        assert NotFoundError.status_code == 404

    def test_is_app_exception(self):
        assert issubclass(NotFoundError, AppException)
