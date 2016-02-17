from .relationship import RelationshipType, Relationship
from .person import Person, Role, Account
from .organisation import Organisation
from .service import Catalog, AccessService, RDS, Nectar

from django.db import models

app_name = __name__.split('.')[0]

__all__ = ['Event', 'EventType', 'Organisation', 'Person', 'Role', 'Account',
           'RelationshipType', 'Relationship', 'AccessService', 'Catalog', 'RDS', 'Nectar']

#Will be managed by code only. Load from fixture
class EventType(models.Model):
    """Description of an Event"""
    entity = models.CharField(max_length=30, blank=True)
    name = models.CharField(max_length=30)
    full_name = models.CharField(max_length=30)
    description = models.CharField(max_length=255, blank=True,
                    help_text='describe parent and child relationship, used when someone decide if it applicable to two entities')

    class Meta:
        unique_together = ("entity", "name")

    def __str__(self):
        return self.full_name if self.full_name else self.name

class Event(models.Model):
    """Event happend to entities"""
    type = models.ForeignKey(EventType)
    entity_id = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now=True)
    data = models.TextField(blank=True)

#~ #ContentType to be coming
    #~ content_type = models.ForeignKey(ContentType, related_name="content_type_timelines")
    #~ object_id = models.PositiveIntegerField()
    #~ content_object = GenericForeignKey('content_type', 'object_id')

#~ # How to use it:
#~ t1 = Event(content_object=project_object, type=something)
#~ t1.save()
#~
#~ #To retrieve the TimeLine object with the project object, we have to follow these steps.
#~ #    Get the 'ContentType' object with the follwoing code.
#~
    #~ from django.contrib.contenttypes.models import ContentType
    #~ contenttype_obj = ContentType.objects.get_for_model(project_object)
#~
#~ #    "object_id" is stored with project_object.id
    #~ Event.objects.filter(object_id=project_object.id, content_type=contenttype_obj)

#~ #Or this one:
#~ def get_poll(related_object):
    #~ related_object_type = ContentType.objects.get_for_model(related_object)
    #~ poll = PollQuestion.objects.filter(
        #~ object_id=related_object.id,
        #~ content_type__pk=related_object_type.id
    #~ )

    def __str__(self):
        entity = apps.get_model(app_name, self.type.entity).objects.get(pk=self.entity_id)
        return "%s: %s %s" % (self.date, self.type, entity)

##This section is a to-do thing
#from django.db.models.signals import post_save
#from django.dispatch import receiver
#
#@receiver(post_save)
#def record_saves(sender, **kwargs):
#    if 'created' in kwargs and kwargs['created'] and sender in [Person, Organisation]:
#        print("\nRequest finished and need to register the event!\n")

