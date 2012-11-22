# ownerauth

A simple Django app that restricts non-superusers from editing objects created by other users.

# Usage

    #models.py
    from django.db import models
    import ownerauth

    class MyModel(ownerauth.models.OwnerAuthModel):
        myField = models.CharField(max_length=100)

    class MyModelAdmin(ownerauth.models.OwnerAuthModelAdmin):
        pass


    #admin.py
    from django.db import admin
    from myapp.models import MyModel, MyModelAdmin

    admin.site.register(MyModel, MyModelAdmin)

That's all there is to it!

# How it works

The app defines an abstract model OwnerAuthModel, which has one field: `owner`, a `ForeignKey` to `django.contrib.auth.models.User`. This field is hidden in the Django admin when logged on as a non-superuser, and has a few other safeguards on it to make sure it really can't be accessed. It is set automatically to the editing user on first save.

`OwnerAuthModelAdmin` provides the other half of the magic by overriding `queryset(self, request)` to only show items whose `owner` field matches the currently logged in user, unless logged in as a superuser.

The final result: when you look at the list of objects for any given model, you'll only see the ones you created - unless you're a superuser, in which case you can see all of them, and even reassign them.

# Licensing

Take your pick - MIT, GPL, LGPL, FreeBSD, whatever best serves your purposes.