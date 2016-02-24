from django.db.models import Model, Q

from .relationship import RelationshipType, Relationship

def get_related(entity, rel_type_name=''):
    """Get related entities of an entity of a RelationshipType"""
    if not isinstance(entity, Model):
        raise TypeError("entity is not a models.Model instance")

    entity_name = entity.__class__.__name__.lower()
    pk = entity.pk
    if rel_type_name:
        rel_types = [RelationshipType.objects.get(name=rel_type_name)]
    else:
        rel_types = RelationshipType.objects.filter(Q(entity_head=entity_name) | Q(entity_tail=entity_name))
    links = []
    for rel_type in rel_types:
        links.extend(Relationship.objects.filter(Q(relationshiptype=rel_type), Q(head_id=pk) | Q(tail_id=pk)))
    return links
