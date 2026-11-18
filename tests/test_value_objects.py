"""Value objects stored in dialog_data must survive a JSON round trip (Redis storage)."""

import json

import pytest

from src.core.models import Faculty, Group, Interest, User
from src.core.value_objects import MatchCandidate, UserProfile


def make_profile(surname: str | None = None) -> UserProfile:
    user = User(
        id=7,
        first_name="Иван",
        second_name="Петров",
        surname=surname,
        phone_number="+79000000000",
        interests=[Interest(name="шахматы"), Interest(name="Python")],
    )
    return UserProfile.from_user(user, Faculty(name="ФБ"), Group(name="ФБ-101"))


def test_user_profile_json_round_trip() -> None:
    profile = make_profile()

    restored = UserProfile.from_dict(json.loads(json.dumps(profile.to_dict())))

    assert restored == profile


@pytest.mark.parametrize(
    ("surname", "expected"),
    [(None, "Петров Иван"), ("", "Петров Иван"), ("Сергеевич", "Петров Иван Сергеевич")],
)
def test_full_name_skips_missing_parts(surname: str | None, expected: str) -> None:
    assert make_profile(surname).full_name == expected


def test_profile_without_faculty_or_group() -> None:
    user = User(id=1, first_name="A", second_name="B", phone_number="0", interests=[])

    profile = UserProfile.from_user(user, None, None)

    assert (profile.faculty, profile.group, profile.interests) == ("", "", ())


def test_match_candidate_round_trip_and_threshold() -> None:
    candidate = MatchCandidate.from_api({"id": "3", "name": "A", "interests": ["x"], "score": 0.5})

    assert MatchCandidate.from_api(json.loads(json.dumps(candidate.to_dict()))) == candidate
    assert candidate.is_relevant(0.49)
    assert not candidate.is_relevant(0.5)  # strictly above the threshold
