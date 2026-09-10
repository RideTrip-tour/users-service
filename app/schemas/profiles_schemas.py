from datetime import datetime

import pycountry
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .validators.phone_number import normalize_phone_number

MIN_LEN_NAME = 2
MAX_LEN_NAME = 15
PATTERN_NAME = r"^[A-Za-zА-Яа-яЁё]+(?:[ -][A-Za-zА-Яа-яЁё]+)?$"
MAX_LEN_ABOUT_ME = 200
MAX_LEN_ACTIVITIES = 25
MIN_LEN_COUNTRY = 2
MAX_LEN_COUNTRY = 25
MIN_LEN_CITY = 2
MAX_LEN_CITY = 25
PATTERN_CITY = r"^[A-Za-zА-Яа-яЁё]+(?:[ -][A-Za-zА-Яа-яЁё]+)+$"
MIN_LEN_CITIZENSHIP = 2
MAX_LEN_CITIZENSHIP = 15
MAX_LEN_CURRENCY = 3
MIN_LEN_CURRENCY = MAX_LEN_CURRENCY


class ProfileBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=15,
        pattern=PATTERN_NAME,
    )
    last_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=15,
        pattern=PATTERN_NAME,
    )
    phone_number: str | None = None
    age: int | None = None
    about_me: str | None = Field(
        default=None,
        max_length=MAX_LEN_ABOUT_ME,
        description="Произвольная информация о себе.",
    )
    activities: list[str] = Field(
        default_factory=list,
        max_length=MAX_LEN_ACTIVITIES,
        description="External activity identifiers from activities service",
    )
    country: str | None = Field(
        default=None, min_length=MIN_LEN_COUNTRY, max_length=MAX_LEN_COUNTRY
    )
    city: str | None = Field(
        default=None, min_length=MIN_LEN_CITY, max_length=MAX_LEN_CITY
    )
    citizenship: str | None = Field(
        default=None, min_length=MIN_LEN_CITIZENSHIP, max_length=MAX_LEN_CITIZENSHIP
    )
    currency: str | None = Field(
        default=None, min_length=MIN_LEN_CURRENCY, max_length=MAX_LEN_CURRENCY
    )
    # Времено отключено по просьбе тестеров. До подключения бакета
    # avatar_url: Optional[str] = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, phone_number: str | None) -> str | None:
        if phone_number is not None:
            return normalize_phone_number(phone_number)
        return None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.upper()
            if not pycountry.currencies.get(alpha_3=value):
                raise ValueError("Invalid currency code")
        return value


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(ProfileBase):
    pass


class ProfileResponse(ProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    role: str
    created_at: datetime
    updated_at: datetime


class FavoriteLocationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    location_id: int = Field(gt=0)


class FavoriteLocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    location_id: int
    created_at: datetime


class FavoriteLocationsResponse(BaseModel):
    location_ids: list[FavoriteLocationResponse]
