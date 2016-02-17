import sys
import inspect
import json

from django.views.generic import View, ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView

from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import (
    QueryDict, HttpResponse, HttpResponseBadRequest,
    JsonResponse, HttpResponseNotAllowed, Http404
)

from django.core import serializers

from .forms import *

def get_classes(module_name):
    """Get a list of classes in a module"""
    #Currently used in creating a white list of form class which can be shown throgh generic view
    classes = []
    for name, obj in inspect.getmembers(sys.modules[module_name]):
        if inspect.isclass(obj) and obj.__module__ == module_name:
            classes.append(name)
    return classes

def short_form_name(fullname):
    return fullname.lower().replace('form','')

def nomalise_form_name(target):
    return target.capitalize() + 'Form'

def index(request):
    things = get_classes('bman.forms')
    for i in range(len(things)):
        things[i] = short_form_name(things[i])
    return render(request, "startup.html", context={'title':'Welcome', 'things': things})

#This is for very generic views for quick development
class SkeletonView(View):
    """Base skeleton view based on some built-in criteria with general methods for mixins"""
    allowed_classess = get_classes('bman.forms') #Only models have form can be interacted with
    dispatch_kwargs = None
    form_class = None
    context = {
        'title': 'Very generic form',
        'form': None,
    }

    def dispatch(self, *args, **kwargs):
        form_to_load = nomalise_form_name(kwargs['target'])
        self.dispatch_kwargs = kwargs #Other extended classes may need this
        print("Dispatch method called from %s for : " % self.__class__.__name__, form_to_load)
        if form_to_load in self.allowed_classess:
            self.form_class = getattr(sys.modules['bman.forms'], form_to_load)
            self.context['title'] = form_to_load.replace('Form','')
            return super(SkeletonView, self).dispatch(*args, **kwargs)
        else:
            return HttpResponseBadRequest("Bad request - out of range")

    def get_object(self):
        instance = None
        if 'id' in self.dispatch_kwargs:
            model = self.form_class.Meta.model
            try:
                instance = model.objects.get(pk=self.dispatch_kwargs['id'])
            except model.DoesNotExist:
                raise Http404("Object does not exist")
        else:
            #Never should be here
            print("No id, what to do?")
        return instance

    def get_queryset(self):
        model = self.form_class.Meta.model
        return model.objects.all()

    def get_success_url(self):
        target = short_form_name(self.form_class.__name__)
        return reverse('objects', kwargs={'target': target})

class FormsCreateView(SkeletonView, CreateView):
    template_name = 'generic_form.html'

class FormsUpdateView(SkeletonView, UpdateView):
    template_name = 'generic_form.html'

class ObjectsView(SkeletonView, DetailView):
    """View class for reading object or objects"""
    template_name = 'generic_detail.html'

class ObjectList(SkeletonView, ListView):
    """View class for reading object or objects"""
    template_name = 'generic_list.html'

#Valid data, how to reuse form class' validator?
def object_should_be_saved(obj):
    print("In validator which is called object_should_be_saved for now")
    print(obj.object)
    return True

# This view is mainly used for RESTful clients, JS like, to call upon
# Might worth to check if HttpRequest.is_ajax()
# This view can deal with single or multiple in theory
# RESTful url design pattern: http://blog.mwaysolutions.com/2014/06/05/10-best-practices-for-better-restful-api/
# Need to be able to handle token for security by extending dispatch.
class ApiObjectsView(SkeletonView):
    def get(self, request, *args, **kwargs):
        data = []
        if 'id' in self.dispatch_kwargs:
            try:
                instance = self.get_object()
                data = serializers.serialize('json', (instance, ))
            except Http404:
                data = json.dumps({})
        else:
            data = serializers.serialize('json', self.get_queryset())
        return HttpResponse(data,  content_type="application/json")

    #For creation
    def post(self, request, *args, **kwargs):
        if 'id' in self.dispatch_kwargs:
            return JsonResponse({'message': 'id cannot be used with POST method'}, status=405)

        print(request.META['CONTENT_TYPE'])
        #curl localhost:8000/objects/person/1/ -X PosT --data @test.json -H "Content-Type: application/json"
        #1. form: application/x-www-form-urlencoded, use QueryDict to get elements in a from
        #self.form_class then use form validation and other methods
        #2. json raw -H "Content-Type: application/json" if only json is to be used
        #pure json
        try:
            data = json.loads(request.body.decode("utf-8"))
            print(data)
            for deserialized_object in serializers.deserialize("json", request.body):
                print(deserialized_object)
                if object_should_be_saved(deserialized_object):
                    deserialized_object.save()
        except Exception as e:
            print("Bad data? - more error handling is needed, see error below")
            print(e)
        return JsonResponse({'result': 'post result is coming'})

    # delete and put currently only support single object
    def delete(self, request, *args, **kwargs):
        if 'id' in self.dispatch_kwargs:
            return JsonResponse({'result': 'deletion result is coming'})
        else:
            return JsonResponse({'message': 'Missing id'}, status=400)

    def put(self, request, *args, **kwargs):
        if 'id' in self.dispatch_kwargs:
            #print(QueryDict(request.body))
            print(json.loads(request.body.decode("utf-8")))
            return JsonResponse({'result': 'put result is coming'})
        else:
            return JsonResponse({'message': 'Missing id'}, status=400)
