import datetime

import jwt
import pytest
import respx
from pydantic_core import ValidationError

from tests.base_user import BaseUser, UserCredentials
from tests.mock_api import mock_api, SECRET_TOKEN, JWT_ALGORITHM


class TestSync:
    @pytest.fixture
    def user_model(self, base_maker, sync_maker, router) -> type[BaseUser]:
        base = base_maker(router)
        return sync_maker(router, base)

    def test_get(self, user_model):
        user = user_model.get(1)
        assert user_model.test_validate(user)

    def test_list(self, user_model):
        users = user_model.list(per_page=6)
        assert all(user_model.test_validate(user) for user in users)

        with pytest.raises(ValidationError):
            user_model.list(per_page=9)

    def test_delete(self, user_model):
        user = user_model.get(1)
        assert user_model.test_validate(user.delete())

        user = user_model.get(1)
        user.id = -100

        with pytest.raises(ValidationError):
            user.delete()

    def test_login(self, user_model, base_url):
        user = user_model.get(1)

        with respx.mock() as mock:
            mock_api(mock, base_url, '/token')
            token = user.login()

        assert isinstance(token, str)

        payload = jwt.decode(token, SECRET_TOKEN, algorithms=JWT_ALGORITHM)
        assert payload['sub'] == user.email

    def test_update(self, user_model):
        user = user_model.get(1)

        res = user.update(name="Brandy", job="Data Scientist")
        assert user.first_name == "Brandy"
        assert isinstance(res, datetime.datetime)

    def test_change(self, user_model):
        user = user_model.get(1)
        res = user.change(name="Brandy", job="Data Scientist")
        assert isinstance(res, bytes)

    def test_sign_up(self, user_model, base_url):
        email = "helloworld@gmail.com"

        with respx.mock() as mock:
            mock_api(mock, base_url, '/register')
            token = user_model.sign_up(UserCredentials(email=email, password="mypassword"))

        assert isinstance(token, str)

        payload = jwt.decode(token, SECRET_TOKEN, algorithms=JWT_ALGORITHM)
        assert payload['sub'] == email

    def test_user_headers(self, user_model):
        headers = user_model.user_headers()
        assert isinstance(headers, dict)

    def test_allowed_methods(self, user_model):
        methods = sorted(['GET', 'HEAD', 'PUT', 'PATCH', 'POST', 'DELETE'])
        assert methods == sorted(user_model.allowed_http_methods())
