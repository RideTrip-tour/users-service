from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from dateutil.relativedelta import relativedelta
from pydantic import ValidationError

from app.schemas.admin_schemas import ProfileCreate as AdminProfileCreate
from app.schemas.admin_schemas import ProfileUpdate as AdminProfileUpdate
from app.schemas.profiles_schemas import (
    FavoriteLocationCreate,
    FavoriteLocationResponse,
    FavoriteLocationsResponse,
    ProfileResponse,
)
from tests.conftest import INVALID_PROFILE_FIELDS


@pytest.fixture(
    params=[
        (
            AdminProfileCreate,
            {"user_id": 7, "first_name": "Ann"},
        ),
        (
            AdminProfileUpdate,
            {"first_name": "Ann"},
        ),
    ]
)
def profile_schema(request):
    return request.param


def make_profile(**overrides):
    profile = {
        "id": 1,
        "user_id": 7,
        "role": "user",
        "first_name": "Ann",
        "last_name": None,
        "phone_number": None,
        "age": None,
        "about_me": None,
        "activities": [],
        "country": None,
        "city": None,
        "citizenship": None,
        "currency": None,
        "created_at": datetime(2024, 1, 1, tzinfo=UTC),
        "updated_at": datetime(2024, 1, 1, tzinfo=UTC),
    }
    profile.update(overrides)
    return profile


def test_profile_response_accepts_orm_attributes():
    profile = SimpleNamespace(**make_profile(first_name="Ann"))

    response = ProfileResponse.model_validate(profile)

    assert response.id == 1
    assert response.user_id == 7
    assert response.first_name == "Ann"


def test_admin_profile_create_requires_positive_user_id():
    with pytest.raises(ValidationError):
        AdminProfileCreate(first_name="Ann")

    with pytest.raises(ValidationError):
        AdminProfileCreate(user_id=0, first_name="Ann")

    assert AdminProfileCreate(user_id=7, first_name="Ann").user_id == 7


def test_admin_profile_update_rejects_user_id():
    with pytest.raises(ValidationError):
        AdminProfileUpdate(user_id=8, first_name="Ann")


@pytest.mark.parametrize(
    ("phone_number", "expected"),
    [
        ("+7 (918) 999-99-99", "+79189999999"),
        ("+7 777 123 45 67", "+77771234567"),
        ("+7 (918) 8888888", "+79188888888"),
    ],
)
def test_profile_phone_number_is_normalized(profile_schema, phone_number, expected):
    schema, data = profile_schema
    profile = schema(**data, phone_number=phone_number)
    assert profile.phone_number == expected


@pytest.mark.parametrize(
    "phone_number",
    [
        "12345",
        "abcdef",
        "+799912345",
        "+799912345678901",
        "+7",
        "   ",
    ],
)
def test_profile_rejects_invalid_phone_number(profile_schema, phone_number):
    schema, data = profile_schema
    with pytest.raises(ValidationError):
        schema(**data, phone_number=phone_number)


def test_profile_phone_number_can_be_none(profile_schema):
    schema, data = profile_schema
    profile = schema(**data, phone_number=None)
    assert profile.phone_number is None


def test_favorite_location_create_accepts_positive_location_id():
    favorite_location = FavoriteLocationCreate(location_id=10)
    assert favorite_location.location_id == 10


@pytest.mark.parametrize("location_id", [0, -1, -10])
def test_favorite_location_create_rejects_non_positive_location_id(
    location_id,
):
    with pytest.raises(ValidationError):
        FavoriteLocationCreate(location_id=location_id)


def test_favorite_location_create_rejects_extra_fields():
    with pytest.raises(ValidationError):
        FavoriteLocationCreate(location_id=10, profile_id=1)


def test_favorite_location_response_accepts_orm_attributes():
    favorite_location = SimpleNamespace(
        location_id=10,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )
    response = FavoriteLocationResponse.model_validate(favorite_location)
    assert response.location_id == 10
    assert response.created_at == datetime(2024, 1, 1, tzinfo=UTC)


def test_favorite_locations_response_accepts_favorite_locations():
    response = FavoriteLocationsResponse(
        location_ids=[
            FavoriteLocationResponse(
                location_id=10,
                created_at=datetime(2024, 1, 1, tzinfo=UTC),
            ),
            FavoriteLocationResponse(
                location_id=20,
                created_at=datetime(2024, 1, 2, tzinfo=UTC),
            ),
        ]
    )
    assert len(response.location_ids) == 2
    assert response.location_ids[0].location_id == 10
    assert response.location_ids[1].location_id == 20


def test_favorite_locations_response_accepts_empty_list():
    response = FavoriteLocationsResponse(location_ids=[])
    assert response.location_ids == []


@pytest.mark.parametrize("field", ["first_name", "last_name"])
@pytest.mark.parametrize(
    "name",
    [
        "Anna",
        "Anna Maria",
        "Anna-Maria",
        "Анна",
        "Анна Мария",
        "Анна-Мария",
        "A-B",
        "A B",
        "А-Б",
        "А Б",
        "Jo",
        "Ли",
        "Александрийский",
        "Анна-Екатерина",
    ],
)
def test_profile_accepts_valid_name(profile_schema, field, name):
    schema, data = profile_schema
    profile = schema(**{**data, field: name})
    assert getattr(profile, field) == name


@pytest.mark.parametrize("field", ["first_name", "last_name"])
@pytest.mark.parametrize(
    "name",
    [
        "A",
        "A" * 16,
        "А" * 16,
        "Anna123",
        "Anna_",
        "Анна--Мария",
        "Анна  Мария",
        "-A",
        "A-",
        "",
    ],
)
def test_profile_rejects_invalid_name(profile_schema, field, name):
    schema, data = profile_schema

    with pytest.raises(ValidationError):
        schema(**{**data, field: name})


@pytest.mark.parametrize("field,value", INVALID_PROFILE_FIELDS)
def test_profile_fields_length_validation(profile_schema, field, value):
    schema, data = profile_schema
    with pytest.raises(ValidationError):
        schema(**{**data, field: value})


@pytest.mark.parametrize(
    "field,value",
    [
        ("about_me", "О себе"),
        ("activities", ["A"]),
        ("country", "AB"),
        ("country", "A" * 25),
        ("city", "AB"),
        ("city", "A" * 25),
        ("citizenship", "AB"),
        ("citizenship", "A" * 15),
        ("currency", "RUB"),
    ],
)
def test_profile_fields_accept_valid_length(profile_schema, field, value):
    schema, data = profile_schema
    profile = schema(**{**data, field: value})

    assert getattr(profile, field) == value


@pytest.mark.parametrize(
    "field, expected",
    [
        ("first_name", None),
        ("last_name", None),
        ("about_me", None),
        ("phone_number", None),
        ("country", None),
        ("city", None),
        ("citizenship", None),
        ("currency", None),
        ("activities", []),
        ("birth_date", None),
    ],
)
def test_profile_fields_have_default_values(profile_schema, field, expected):
    schema, data = profile_schema
    profile = schema(**{**data, field: expected})
    assert getattr(profile, field) == expected


def test_birth_date_rejects_under_18(profile_schema, today):
    schema, data = profile_schema
    birth_date = today - relativedelta(years=18) + relativedelta(days=1)
    with pytest.raises(ValidationError):
        schema(**{**data, "birth_date": birth_date})


def test_birth_date_accepts_adult(profile_schema, today):
    schema, data = profile_schema
    birth_date = today - relativedelta(years=18)
    profile = schema(**{**data, "birth_date": birth_date})
    assert profile.birth_date == birth_date


def test_birth_date_rejects_future_date(profile_schema, today):
    schema, data = profile_schema
    birth_date = today + relativedelta(days=1)
    with pytest.raises(ValidationError):
        schema(**{**data, "birth_date": birth_date})
