from django.forms import ModelForm, Textarea
from .models import *

# Create the form class.
class RelationshiptypeForm(ModelForm):
    class Meta:
        model = RelationshipType
        fields = '__all__'


class RelationshipForm(ModelForm):
    class Meta:
        model = Relationship
        fields = '__all__'

class PersonForm(ModelForm):
    class Meta:
        model = Person
        fields = '__all__'

class OrganisationForm(ModelForm):
    class Meta:
        model = Organisation
        fields = '__all__'
        widgets = {
            'name': Textarea(attrs={'cols': 80, 'rows': 1}),
        }

class RoleForm(ModelForm):
    class Meta:
        model = Role
        fields = '__all__'

class AccountForm(ModelForm):
    class Meta:
        model = Account
        fields = '__all__'

class CatalogForm(ModelForm):
    class Meta:
        model = Catalog
        fields = '__all__'

class AccessForm(ModelForm):
    class Meta:
        model = AccessService
        fields = '__all__'

class RdsForm(ModelForm):
    class Meta:
        model = RDS
        fields = '__all__'

class NectarForm(ModelForm):
    class Meta:
        model = Nectar
        fields = '__all__'

