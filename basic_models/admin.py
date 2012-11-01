# Copyright 2011 Concentric Sky, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.contrib.admin import ModelAdmin
import datetime
from django.utils.translation import ugettext_lazy

__all__ = ['UserModelAdmin', 'DefaultModelAdmin', 'SlugModelAdmin', 'OneActiveAdmin']

class UserModelAdmin(ModelAdmin):
    """ModelAdmin subclass that will automatically update created_by and updated_by fields"""
    save_on_top = True
    readonly_fields = ('created_by', 'updated_by')
    
    def save_model(self, request, obj, form, change):
        instance = form.save(commit=False)
        self._update_instance(instance, request.user)
        instance.save()
        return instance

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            self._update_instance(instance, request.user)
            instance.save()
        formset.save_m2m()

    @staticmethod
    def _update_instance(instance, user):
        if not instance.pk:
            instance.created_by = user
        instance.updated_by = user


class DefaultModelAdmin(UserModelAdmin):
    """ModelAdmin subclass that will automatically update created_by or updated_by fields if they exist"""
    
    readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
    actions = UserModelAdmin.actions + [
        'activate_objects',
        'deactivate_objects',
    ]

    def activate_objects(self, request, queryset):
        """Admin action to set is_active=True on objects"""
        count = queryset.update(is_active=True)
        suffix = count == 1 and "1 object was" or "%s objects were" % count
        self.message_user(request, "%s marked as active." % suffix)
    activate_objects.short_description = "Mark selected objects as active"

    def deactivate_objects(self, request, queryset):
        """Admin action to set is_active=False on objects"""
        count = queryset.update(is_active=False)
        suffix = count == 1 and "1 object was" or "%s objects were" % count
        self.message_user(request, "%s marked as inactive." % suffix)
    deactivate_objects.short_description = "Mark selected objects as inactive"
    
    @staticmethod
    def _update_instance(instance, user):
        if not instance.pk:
            if hasattr(instance, 'created_by'):
                instance.created_by = user
        if hasattr(instance, 'updated_by'):
            instance.updated_by = user


class SlugModelAdmin(DefaultModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ('slug','name')


class OneActiveAdmin(ModelAdmin):
    save_on_top = True
    list_display = ('__unicode__', 'is_active')
    change_form_template = "admin/preview_change_form.html"
    actions = ['duplicate']

    def duplicate(self, request, queryset):
        for object in queryset:
            object.clone()
    duplicate.short_description = ugettext_lazy("Duplicate selected %(verbose_name_plural)s")
