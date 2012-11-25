from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect


# This metaclass will add an appropriately-named permission to each subclass
# http://stackoverflow.com/questions/725913/dynamic-meta-attributes-for-django-models
class OwnerAuthMetaClass(models.base.ModelBase):
    def __new__(cls, name, bases, attrs):
        klas = super(OwnerAuthMetaClass, cls).__new__(cls, name, bases, attrs)
        klas._ownerauth_manage_permission = 'can_manage_' + klas._meta.module_name
        klas._meta.permissions.append((klas._ownerauth_manage_permission, u'Can manage %s' % klas._meta.verbose_name))

        #Prepend app label so that it's in the format for has_perm()
        klas._ownerauth_manage_permission = klas._meta.app_label + '.' + klas._ownerauth_manage_permission

        return klas


class OwnerAuthModel(models.Model):
    __metaclass__ = OwnerAuthMetaClass

    owner = models.ForeignKey(User, blank=True, null=True)

    class Meta:
        abstract = True


class OwnerAuthModelAdmin(admin.ModelAdmin):
    exclude = ()

    def __init__(self, *args, **kwargs):
        super(OwnerAuthModelAdmin, self).__init__(*args, **kwargs)

        #Build redirect for use in case of direct link abuse
        #Actual reversing doesn't work here, presumably because the urls haven't been processed yet
        appname = self.model._meta.app_label
        modelname = self.model._meta.object_name.lower()
        self._ownerauth_redirect = 'admin:' + appname + '_' + modelname + '_changelist'

    '''
    Auto-add user in edit mode
    Force non-admins to report as themselves in case there's any tricky way around it
    '''
    def save_model(self, request, obj, form, change):
        # Non-managers get no choice no matter what
        if not request.user.has_perm(self.model._ownerauth_manage_permission):
            obj.owner = request.user

        #Autofill for admins only on first save
        elif not obj.owner and not obj.pk:
            obj.owner = request.user
        obj.save()

    '''
    Auto-add owner in formset mode
    '''
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            self.save_model(request, obj, form, change)

    '''
    Hide owner option in admin when not superuser
    '''
    def get_form(self, request, obj=None, **kwargs):
        if request.user.has_perm(self.model._ownerauth_manage_permission):
            self.exclude = ()
        else:
            self.exclude = ('owner', )
        return super(OwnerAuthModelAdmin, self).get_form(request, obj, **kwargs)

    '''
    Filter list of editable posts on admin page
    '''
    def queryset(self, request):
        qs = super(OwnerAuthModelAdmin, self).queryset(request)
        if request.user.has_perm(self.model._ownerauth_manage_permission):
            return qs
        return qs.filter(owner=request.user)

    '''
    Next three: Prevent sneakiness by redirecting if someone tries a direct link
    Has the side effect of redirecting to the list rather than crashing if an admin tries to hit a nonexistent id
        but that's okay, I think
    '''
    def change_view(self, request, object_id, form_url='', extra_context=None):
        if not self.queryset(request).filter(id=object_id).exists():
            return HttpResponseRedirect(reverse(self._ownerauth_redirect))

        return super(OwnerAuthModelAdmin, self).change_view(request, object_id, form_url=form_url, extra_context=extra_context)

    def delete_view(self, request, object_id, extra_context=None):
        if not self.queryset(request).filter(id=object_id).exists():
            return HttpResponseRedirect(reverse(self._ownerauth_redirect))

        return super(OwnerAuthModelAdmin, self).delete_view(request, object_id, extra_context=extra_context)

    def history_view(self, request, object_id, extra_context=None):
        if not self.queryset(request).filter(id=object_id).exists():
            return HttpResponseRedirect(reverse(self._ownerauth_redirect))

        return super(OwnerAuthModelAdmin, self).history_view(request, object_id, extra_context=extra_context)
