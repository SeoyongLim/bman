from django.core import validators

from django.apps import apps

from django.db import models
#from django.contrib.contenttypes.models import ContentType

from .organisation import Organisation

#Used in django.apps.get_model and in case re-package this module in the future for a better name
app_name = __name__.split('.')[0]

class RelationshipType(models.Model):
    """Describe two entities from tail to head as in direct graph"""
    #ENTITY has to be checked whenever new RelationshipType is defined and updated when necessary
    ENTITY = (('organisation', 'Organisation'), ('person', 'Person'))
    name = models.CharField(max_length=30, unique=True,
        help_text='One word describes relationshiop of two types of entity, has to be unique',
        validators=[validators.RegexValidator(r'^[\w.-]+$',
                                      'One word contains only letters, numbers and . - _.',
                                      'invalid')])
    description = models.CharField(help_text='Verbose description the relationship of the entities', max_length=300, blank=True)
    entity_tail = models.CharField(max_length=30, choices=ENTITY)
    entity_head = models.CharField(max_length=30, choices=ENTITY)
    forward = models.CharField(help_text='Label read from tail to head', max_length=30)
    backward = models.CharField(help_text='Label read from head to tail', max_length=30)

    def __str__(self):
        return "%s: %s and %s. \n\tforward: %s,\n\tbackward: %s" % (self.name, self.entity_tail, self.entity_head, self.forward, self.backward)


class RelationshipManager(models.Manager):
    def create(self, **kwargs):
        """Accept relationshiptype instance or name when creating"""
        #relationshiptype is defined by name not instance
        if isinstance(kwargs['relationshiptype'], str):
            rel_type = RelationshipType.objects.get(name=kwargs['relationshiptype'])
        else:
            rel_type = kwargs['relationshiptype']

        # Not ready to go ContextType route yet as I am still thinking these are not simple fk: it needs RelationshipType
        # and get_model is flexible enough
        # We accept either two Entity instances or tail_id and head_id pair but not both
        #~ instances = ('tail', 'head')
        #~ for instance in instances:
            #~ if instance in kwargs and instance+'_id' in kwargs:
                #~ raise KeyError('Either provide an instance or id but cannot be both')

        values = {'relationshiptype': rel_type, 'tail_id': kwargs['tail_id'], 'head_id': kwargs['head_id']}
        return super(RelationshipManager, self).create(**values)


#May valid if tail and head objects exist
class Relationship(models.Model):
    DIRECTION = (
        ('F', 'Forward'),
        ('R', 'Reverse'),
    )
    #Need customrised query to support this at this point
    relationshiptype = models.ForeignKey(RelationshipType)
    #tail and head should hold actual object ids. Without using froeignkey, integration is a bit comprimised
    #tail_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    tail_id = models.PositiveIntegerField()
    #tail = GenericForeignKey('tail_type', 'tail_id')

    #head_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    head_id = models.PositiveIntegerField()
    #head = GenericForeignKey('head_type', 'head_id')
    direction = models.CharField(max_length=1, choices=DIRECTION, default='F') # default is tail to head.
    objects = RelationshipManager()

    class Meta:
        ordering = ['tail_id', 'relationshiptype']

    def __str__(self):
        r = self.relationshiptype

        tail = apps.get_model(app_name, r.entity_tail).objects.get(pk=self.tail_id)
        head = apps.get_model(app_name, r.entity_head).objects.get(pk=self.head_id)

        if self.direction == 'F':
            return "%s %s %s" % (tail, r.forward, head)
        else:
            return "%s %s %s" % (head, r.backward, tail)

    @classmethod
    def as_end(cls, rel_type, entity, end='tail'):
        # Name is not the best
        """Check if there are instances of Relationship of an entity at the query
           end of a RelationshipType. Default is the instance at the tail end.

           rel_type can either be the name string of RelationshipType or an instance.
        """
        if isinstance(rel_type, str):
            rel_type = RelationshipType.objects.get(name=rel_type)

        if end == 'head':
            return Relationship.objects.filter(relationshiptype=rel_type, head_id=entity.pk)
        else:
            return Relationship.objects.filter(relationshiptype=rel_type, tail_id=entity.pk)
