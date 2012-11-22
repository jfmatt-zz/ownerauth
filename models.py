from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect


class OwnerAuthModel(models.Model):
    owner = models.ForeignKey(User, blank=True, null=True)

    class Meta:
        abstract = True


class OwnerAuthModelAdmin(admin.ModelAdmin):
    exclude = ()

    '''
    Auto-add user in edit mode
    Force non-admins to report as themselves in case there's any tricky way around it
    '''
    def save_model(self, request, obj, form, change):
        if not obj.owner or not request.user.is_superuser:
            obj.owner = request.user
        obj.save()

    '''
    Auto-add owner in formset mode
    '''
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.owner:
                instance.owner = request.user
            instance.save()

    '''
    Hide owner option in admin when not superuser
    '''
    def get_form(self, request, obj=None, **kwargs):
        if request.user.is_superuser:
            self.exclude = ()
        else:
            self.exclude = ('owner', )
        return super(OwnerAuthModelAdmin, self).get_form(request, obj=None, **kwargs)

    '''
    Filter list of editable posts on admin page
    '''
    def queryset(self, request):
        qs = super(OwnerAuthModelAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

    '''
    Next three: Prevent sneakiness by redirecting if someone tries a direct link
    '''
    def change_view(self, request, object_id, extra_context=None):
        if not self.queryset(request).filter(id=object_id).exists():
            return HttpResponseRedirect(reverse('admin:myapp_mymodel_changelist'))

        return super(OwnerAuthModelAdmin, self).change_view(request, object_id, extra_context)

    def delete_view(self, request, object_id, extra_context=None):
        if not self.queryset(request).filter(id=object_id).exists():
            return HttpResponseRedirect(reverse('admin:myapp_mymodel_changelist'))

        return super(OwnerAuthModelAdmin, self).delete_view(request, object_id, extra_context)

    def history_view(self, request, object_id, extra_context=None):
        if not self.queryset(request).filter(id=object_id).exists():
            return HttpResponseRedirect(reverse('admin:myapp_mymodel_changelist'))

        return super(OwnerAuthModelAdmin, self).history_view(request, object_id, extra_context)
