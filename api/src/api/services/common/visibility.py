from sqlalchemy import Select

from api.models import Character, ChronicleEntry, Item, Location, MemberRole

_RestrictableModel = type[Character] | type[Item] | type[ChronicleEntry] | type[Location]


def apply_visibility_filter(query: Select, model: _RestrictableModel, requester_role: MemberRole) -> Select:
    if requester_role == MemberRole.GM:
        return query
    return query.where(model.restricted.is_(False))
