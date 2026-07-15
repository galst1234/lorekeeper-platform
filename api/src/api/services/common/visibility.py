from sqlalchemy import Select

from api.models import CampaignEntityBase, MemberRole


def apply_visibility_filter(query: Select, model: type[CampaignEntityBase], requester_role: MemberRole) -> Select:
    if requester_role == MemberRole.GM:
        return query
    return query.where(model.restricted.is_(False))
