""" Django admin pages for student app """
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import ugettext_lazy as _
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from ratelimitbackend import admin
from xmodule.modulestore.django import modulestore

from config_models.admin import ConfigurationModelAdmin
from student.models import (
    UserProfile, UserTestGroup, CourseEnrollmentAllowed, DashboardConfiguration, CourseEnrollment, Registration,
    PendingNameChange, CourseAccessRole, LinkedInAddToProfileConfiguration, UserAttribute, LogoutViewConfiguration,
    RegistrationCookieConfiguration
)
from student.roles import REGISTERED_ACCESS_ROLES

from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
User = get_user_model()  # pylint:disable=invalid-name


class CourseAccessRoleForm(forms.ModelForm):
    """Form for adding new Course Access Roles view the Django Admin Panel."""

    class Meta(object):
        model = CourseAccessRole
        fields = '__all__'

    email = forms.EmailField(required=True)
    COURSE_ACCESS_ROLES = [(role_name, role_name) for role_name in REGISTERED_ACCESS_ROLES.keys()]
    role = forms.ChoiceField(choices=COURSE_ACCESS_ROLES)

    def clean_course_id(self):
        """
        Checking course-id format and course exists in module store.
        This field can be null.
        """
        if self.cleaned_data['course_id']:
            course_id = self.cleaned_data['course_id']

            try:
                course_key = CourseKey.from_string(course_id)
            except InvalidKeyError:
                raise forms.ValidationError(u"Invalid CourseID. Please check the format and re-try.")

            if not modulestore().has_course(course_key):
                raise forms.ValidationError(u"Cannot find course with id {} in the modulestore".format(course_id))

            return course_key

        return None

    def clean_org(self):
        """If org and course-id exists then Check organization name
        against the given course.
        """
        if self.cleaned_data.get('course_id') and self.cleaned_data['org']:
            org = self.cleaned_data['org']
            org_name = self.cleaned_data.get('course_id').org
            if org.lower() != org_name.lower():
                raise forms.ValidationError(
                    u"Org name {} is not valid. Valid name is {}.".format(
                        org, org_name
                    )
                )

        return self.cleaned_data['org']

    def clean_email(self):
        """
        Checking user object against given email id.
        """
        email = self.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
        except Exception:
            raise forms.ValidationError(
                u"Email does not exist. Could not find {email}. Please re-enter email address".format(
                    email=email
                )
            )

        return user

    def clean(self):
        """
        Checking the course already exists in db.
        """
        cleaned_data = super(CourseAccessRoleForm, self).clean()
        if not self.errors:
            if CourseAccessRole.objects.filter(
                    user=cleaned_data.get("email"),
                    org=cleaned_data.get("org"),
                    course_id=cleaned_data.get("course_id"),
                    role=cleaned_data.get("role")
            ).exists():
                raise forms.ValidationError("Duplicate Record.")

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super(CourseAccessRoleForm, self).__init__(*args, **kwargs)
        if self.instance.user_id:
            self.fields['email'].initial = self.instance.user.email


@admin.register(CourseAccessRole)
class CourseAccessRoleAdmin(admin.ModelAdmin):
    """Admin panel for the Course Access Role. """
    form = CourseAccessRoleForm
    raw_id_fields = ("user",)
    exclude = ("user",)

    fieldsets = (
        (None, {
            'fields': ('email', 'course_id', 'org', 'role',)
        }),
    )

    list_display = (
        'id', 'user', 'org', 'course_id', 'role',
    )
    search_fields = (
        'id', 'user__username', 'user__email', 'org', 'course_id', 'role',
    )

    def save_model(self, request, obj, form, change):
        obj.user = form.cleaned_data['email']
        super(CourseAccessRoleAdmin, self).save_model(request, obj, form, change)


@admin.register(LinkedInAddToProfileConfiguration)
class LinkedInAddToProfileConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for the LinkedIn Add to Profile configuration. """

    class Meta(object):
        model = LinkedInAddToProfileConfiguration

    # Exclude deprecated fields
    exclude = ('dashboard_tracking_code',)


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    """ Admin interface for the CourseEnrollment model. """
    list_display = ('id', 'course_id', 'mode', 'user', 'is_active',)
    list_filter = ('mode', 'is_active',)
    raw_id_fields = ('user',)
    search_fields = ('course_id', 'mode', 'user__username',)

    def queryset(self, request):
        return super(CourseEnrollmentAdmin, self).queryset(request).select_related('user')

    class Meta(object):
        model = CourseEnrollment


class UserProfileInline(admin.StackedInline):
    """ Inline admin interface for UserProfile model. """
    model = UserProfile
    can_delete = False
    verbose_name_plural = _('User profile')

    def get_readonly_fields(self, request, obj=None):
        django_readonly = super(UserProfileInline, self).get_readonly_fields(request, obj)
        if obj and obj.profile.employee_id:
            return django_readonly + ('employee_id',)
        return django_readonly


def validate_unique_email(value, user_id=None):
    if User.objects.filter(email=value).exclude(id=user_id).exists():
        raise ValidationError(
            _('Email "%(value)s" is already taken.'),
            params={'value': value}
        )


class UserCreationFormExtended(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(UserCreationFormExtended, self).__init__(*args, **kwargs)
        self.fields['email'] = forms.EmailField(
            label=_("E-mail"),
            max_length=75,
            validators=[validate_email, validate_unique_email]
        )


class UserChangeFormExtended(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super(UserChangeFormExtended, self).__init__(*args, **kwargs)
        self.fields['email'] = forms.EmailField(
            label=_("E-mail"),
            max_length=75,
            validators=[validate_email]
        )

    def clean_email(self):
        value = self.cleaned_data['email']
        validate_unique_email(value, user_id=self.instance.id)
        return value

class UserAdmin(BaseUserAdmin):
    """ Admin interface for the User model. """
    inlines = (UserProfileInline,)
    list_display = ('username', 'email',  'employee_id', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'profile__employee_id')

    def employee_id(self, obj):
        return obj.profile.employee_id

    def get_readonly_fields(self, request, obj=None):
        """
        Allows editing the users while skipping the username check, so we can have Unicode username with no problems.
        The username is marked read-only regardless of `ENABLE_UNICODE_USERNAME`, to simplify the bokchoy tests.
        """
        django_readonly = super(UserAdmin, self).get_readonly_fields(request, obj)
        if obj:
            return django_readonly + ('username',)
        return django_readonly


@admin.register(UserAttribute)
class UserAttributeAdmin(admin.ModelAdmin):
    """ Admin interface for the UserAttribute model. """
    list_display = ('user', 'name', 'value',)
    list_filter = ('name',)
    raw_id_fields = ('user',)
    search_fields = ('name', 'value', 'user__username',)

    class Meta(object):
        model = UserAttribute


UserAdmin.add_form = UserCreationFormExtended
UserAdmin.add_fieldsets = (
    (None, {
        'classes': ('wide',),
        'fields': ('email', 'username', 'password1', 'password2',)
    }),
)


UserAdmin.form = UserChangeFormExtended
UserAdmin.fieldsets = (
    (None, {'fields': ('email', 'username', 'password')}),
    (_('Personal info'), {'fields': ('first_name', 'last_name')}),
    (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                   'groups', 'user_permissions')}),
    (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
)


admin.site.register(UserTestGroup)
admin.site.register(CourseEnrollmentAllowed)
admin.site.register(Registration)
admin.site.register(PendingNameChange)
admin.site.register(DashboardConfiguration, ConfigurationModelAdmin)
admin.site.register(LogoutViewConfiguration, ConfigurationModelAdmin)
admin.site.register(RegistrationCookieConfiguration, ConfigurationModelAdmin)


# We must first un-register the User model since it may also be registered by the auth app.
admin.site.register(User, UserAdmin)
