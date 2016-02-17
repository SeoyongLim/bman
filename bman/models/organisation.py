from django.db import models

def get_child_ids_of(top_id, rtype=None):
    from .relationship import RelationshipType, Relationship
    if rtype is None:
        rtype = RelationshipType.objects.get(name='Organisation')
    children = Relationship.objects.filter(relationshiptype=rtype, tail_id=top_id)
    child_ids = {}
    for child in children:
        child_ids[str(child.head_id)] = get_child_ids_of(child.head_id, rtype)
    return child_ids


class Organisation(models.Model):
    name = models.TextField(blank=False)
    description = models.TextField(blank=True, default='')
    site = models.URLField('URL of website', blank=True, default='')
    #~ #Currently is not used, may be used for performance ?
    #~ independent = models.BooleanField(default=False, help_text='If it can exist without other organisations.') #If it is can only be the root tail node in a relationship graph
    abbreviation = models.CharField(max_length=30, blank=True, default='')
    address = models.TextField(blank=True, default='')
    insightly_id = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return self.name

    def get_child_ids(self):
        return get_child_ids_of(self.pk)

    def get_all_services(self):
        """All services this Person linked to"""
        from .person import Account
        #accounts = Account.objects.all().filter(role__organisation__pk=5)
        accounts = Account.objects.all().filter(billing_org__pk=self.pk)
        services = []
        for account in accounts:
            services.extend(account.role.get_all_services())
        return services
