"""
Immutable value objects passed between the bot, the API and the dialog storage.

Dialog data must be JSON-serializable (it is stored in Redis), so ORM objects
are converted into these value objects and stored via ``to_dict()``. They are
restored with ``from_dict()`` / ``from_api()`` when a window is rendered.
"""

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any, Self

from .models import Faculty, Group, User


@dataclass(frozen=True, slots=True)
class UserProfile:
    """Read-only snapshot of a user's profile for display in the bot."""

    id: int
    first_name: str
    second_name: str
    surname: str | None
    faculty: str
    group: str
    interests: tuple[str, ...]
    phone_number: str

    @classmethod
    def from_user(cls, user: User, faculty: Faculty | None, group: Group | None) -> Self:
        """
        Build a profile from ORM objects.

        Args:
            user: User with interests loaded.
            faculty: The user's faculty, if found.
            group: The user's group, if found.

        Returns:
            UserProfile: A detached, serializable snapshot.

        """
        return cls(
            id=user.id,
            first_name=user.first_name,
            second_name=user.second_name,
            surname=user.surname,
            faculty=faculty.name if faculty else "",
            group=group.name if group else "",
            interests=tuple(interest.name for interest in user.interests),
            phone_number=user.phone_number,
        )

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> Self:
        """Restore a profile previously stored with ``to_dict()``."""
        return cls(
            id=int(raw["id"]),
            first_name=raw["first_name"],
            second_name=raw["second_name"],
            surname=raw.get("surname"),
            faculty=raw["faculty"],
            group=raw["group"],
            interests=tuple(raw["interests"]),
            phone_number=raw["phone_number"],
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible types for dialog storage."""
        data = asdict(self)
        data["interests"] = list(self.interests)
        return data

    @property
    def full_name(self) -> str:
        """Family name, first name and patronymic, skipping empty parts."""
        return " ".join(part for part in (self.second_name, self.first_name, self.surname) if part)


@dataclass(frozen=True, slots=True)
class MatchCandidate:
    """A single search result returned by the matching API."""

    id: int
    name: str
    interests: tuple[str, ...]
    score: float  # cosine similarity of interest embeddings, in [-1, 1]

    @classmethod
    def from_api(cls, raw: Mapping[str, Any]) -> Self:
        """Build a candidate from a ``/search`` result item or a stored dict."""
        return cls(
            id=int(raw["id"]),
            name=str(raw["name"]),
            interests=tuple(raw.get("interests", ())),
            score=float(raw["score"]),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible types for dialog storage."""
        data = asdict(self)
        data["interests"] = list(self.interests)
        return data

    def is_relevant(self, threshold: float) -> bool:
        """Return True if the similarity score is above the threshold."""
        return self.score > threshold
