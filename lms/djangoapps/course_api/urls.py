"""
Course API URLs
"""


from django.conf import settings
from django.conf.urls import include, url

from custom_views.views import AppliedXCourseListView

from .views import CourseDetailView, CourseIdListView, CourseListView

urlpatterns = [
    url(r'^v1/courses/$', CourseListView.as_view(), name="course-list"),
    url(fr'^v1/courses/{settings.COURSE_KEY_PATTERN}', CourseDetailView.as_view(), name="course-detail"),
    url(r'^v1/course_ids/$', CourseIdListView.as_view(), name="course-id-list"),
    url(r'', include('lms.djangoapps.course_api.blocks.urls'))
]

if settings.FEATURES.get("ENABLE_AMAT_EXTENSIONS", False):
    urlpatterns.append(
        url(r"^v1/appliedx_courses/$",
            AppliedXCourseListView.as_view(),
            name="appliedx-course-list",
            )
        )
