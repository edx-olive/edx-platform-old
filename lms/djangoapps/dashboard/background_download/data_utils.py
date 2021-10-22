"""
Data preparation for file storage.
"""
import logging

from lms.djangoapps.certificates.models import CertificateWhitelist, GeneratedCertificate, certificate_info_for_user
from lms.djangoapps.grades.api import CourseGradeFactory
from lms.djangoapps.instructor_task.tasks_helper.grades import _CourseGradeReportContext
from lms.djangoapps.verify_student.services import IDVerificationService
from common.djangoapps.student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore

log = logging.getLogger('edx.celery.task')


def fetch_course_grades(course):
    """
    Prepare grades report for a particular course.
    Mimicked Grade Report, see `upload_grades_csv`.
    Returns:
        course grades for all enrollees and modules (generator)
    """
    certificate_whitelist = CertificateWhitelist.objects.filter(course_id=course.id, whitelist=True)
    whitelisted_user_ids = [entry.user_id for entry in certificate_whitelist]
    context = _CourseGradeReportContext(None, None, course.id, None, None)
    graded_assignments = context.graded_assignments
    enrolled_students = CourseEnrollment.objects.users_enrolled_in(course.id)

    for student, course_grade, err_msg in CourseGradeFactory().iter(enrolled_students, course):

        if not course_grade:
            log.info(f"Couldn't fetch a grade for a sysadmin grades report: {err_msg}")
            # We don't collect errors, unlike standard grade reports
            continue

        enrollment_mode = CourseEnrollment.enrollment_mode_for_user(student, course.id)[0]
        verification_status = IDVerificationService.verification_status_for_user(student, enrollment_mode)
        try:
            generated_certificate = GeneratedCertificate.objects.get(user=student, course_id=course.id)
        except GeneratedCertificate.DoesNotExist:
            generated_certificate = None
        certificate_info = certificate_info_for_user(
            student,
            course.id,
            course_grade.letter_grade,
            student.id in whitelisted_user_ids,
            generated_certificate,
        )

        for assignment_type, assignment_info in graded_assignments.items():

            assignment_average = '-'
            if assignment_info['separate_subsection_avg_headers']:
                assignment_average = course_grade.summary['grade_breakdown'].get(assignment_type, {}).get('percent')
                if assignment_average:
                    assignment_average = round(assignment_average, 2)

            for i, subsection_location in enumerate(assignment_info['subsection_headers']):

                try:
                    subsection_grade = course_grade.graded_subsections_by_format[assignment_type][
                        subsection_location]
                except KeyError:
                    score = 'Not Available'
                else:
                    if subsection_grade.graded_total.first_attempted:
                        score = round(subsection_grade.graded_total.earned / subsection_grade.graded_total.possible, 2)
                    else:
                        score = 'Not Attempted'

                datum = [
                    course.id,
                    student.id,
                    student.email,
                    student.username,
                    course_grade.percent,
                    list(assignment_info['subsection_headers'].values())[i],
                    score,
                    assignment_average,
                    enrollment_mode,
                    verification_status,
                ]
                datum.extend(certificate_info)
                yield datum


def get_courses():
    """
    Return all courses from modulestore.
    """
    return modulestore().get_courses()
