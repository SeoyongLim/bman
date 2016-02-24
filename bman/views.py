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

FORM_MODULE_NAME = __name__.split('.')[0] + '.forms'

def get_classes(module_name):
    """Get a list of classes in a module"""
    #Currently used in creating a white list of form class which can be shown throgh generic view
    classes = []
    for name, obj in inspect.getmembers(sys.modules[module_name]):
        if inspect.isclass(obj) and obj.__module__ == module_name:
            classes.append(name)
    return classes

# Utility functions to convert to and from XXXForm class names to Model names
def _form_to_model(fullname):
    return fullname.lower().replace('form','').capitalize()

def _nomalise_form_name(target):
    return target.capitalize() + 'Form'

def index(request):
    # Use form classes to define a list of what can be seen
    things = [_form_to_model(thing) for thing in get_classes(FORM_MODULE_NAME)]
    return render(request, "startup.html", context={'title':'Welcome', 'things': things})


#This is for very generic views for quick development
class SkeletonView(View):
    """Base skeleton view based on some built-in criteria with general methods for mixins
    """

    # Except dispatch, other functions in Django are defined in ContextMixin
    allowed_classess = get_classes(FORM_MODULE_NAME) #Only models have form can be interacted with
    dispatch_kwargs = None
    dispatch_args = None
    form_class = None

    def dispatch(self, request, *args, **kwargs):
        to_be_loaded = _nomalise_form_name(kwargs['target'])
        self.dispatch_kwargs = kwargs #Other extended classes may need this
        self.dispatch_args = request.GET
        print("Dispatch method called from %s for : " % self.__class__.__name__, to_be_loaded)
        if to_be_loaded in self.allowed_classess:
            self.form_class = getattr(sys.modules[FORM_MODULE_NAME], to_be_loaded)
            return super(SkeletonView, self).dispatch(request, *args, **kwargs)
        else:
            return HttpResponseBadRequest("Bad request - out of range")

    def get_context_data(self, **kwargs):
        context = super(SkeletonView, self).get_context_data(**kwargs)
        context['title'] = context['object_name'] = _form_to_model(self.form_class.__name__)
        context['opts'] = self.dispatch_args
        return context

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
            raise RuntimeError("No id, check code and url config")
        return instance

    def get_queryset(self):
        model = self.form_class.Meta.model
        return model.objects.all()

    def get_success_url(self):
        target = _form_to_model(self.form_class.__name__)
        return reverse('objects', kwargs={'target': target})


class FormsCreateView(SkeletonView, CreateView):
    template_name = 'generic_form.html'


class FormsUpdateView(SkeletonView, UpdateView):
    template_name = 'generic_form.html'


class ObjectsView(SkeletonView, DetailView):
    """View class for reading object or objects"""
    template_name = 'generic_detail.html'
    TEMPLATES = {'Person': 'person_detail.html',
                 'Organisation': 'organisation_detail.html'}

    def get_template_names(self):
        return self.TEMPLATES.get(_form_to_model(self.form_class.__name__), self.template_name)


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
