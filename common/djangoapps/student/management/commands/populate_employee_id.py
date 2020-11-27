"""
Populate 'employee_id' field for `UserProfile` entries.
"""
from datetime import datetime
from optparse import make_option

from django.db import IntegrityError
from django.core.management.base import BaseCommand
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist

from student.models import UserProfile


class Command(BaseCommand):
    """
    Command to populate `UserProfile` entries' `employee_id`.

    `employee_id` is a `userid` from PingSSO stored in `social_django.models.UserSocialAuth`.

    Examples:
    ```
    ./manage.py lms --settings=devstack populate_employee_id
    ```
    """
    help = "Populate employee_id values in legacy users profiles."

    CHUNK_SIZE = 2000
    FROM_PK = 1L

    option_list = BaseCommand.option_list + (
        make_option("--from_pk",
                    dest="from_pk",
                    default=FROM_PK,
                    type="long",
                    help="PK of a user profile entry to start from."),
        make_option("--chunk_size",
                    dest="chunk_size",
                    type="int",
                    default=CHUNK_SIZE,
                    help="Number of entries in a chunk to process."),
    )

    def handle(self, *args, **options):
        """
        Save employee_id for users' profiles.
        """
        from_pk = options.get("from_pk")
        chunk_size = options.get("chunk_size")

        qs = UserProfile.objects.filter(
            # To filter by employee_id, use no slicing when iterating over profiles
            # Q(employee_id="") | Q(employee_id=None),
            pk__gte=from_pk,
        )

        found_entries_n = qs.count()
        print("============= Found {!s} UserProfile entries without employee_id. =============\n".format(found_entries_n))

        if not found_entries_n:
            return

        processed_entries_n = 0
        # The sum of these two counters should be the number of processed `UserProfile` entries
        entries_with_empl_id = 0
        entries_without_empl_id = 0

        start = datetime.now()

        for offset in range(0, found_entries_n, chunk_size):
            print("offset " + str(offset))

            profiles = qs[offset:chunk_size+offset]

            for user_profile in profiles:

                processed_entries_n += 1
                # Incrementing here to not place incrementation under every warning.
                entries_without_empl_id += 1

                user = user_profile.user
                print(
                    "-------- User : {!s}, id {!s}. "
                    "Entries count: {!s}/{!s}. --------".format(
                        user,
                        user.id,
                        processed_entries_n,
                        found_entries_n,
                    ))

                try:
                    social_user = user.social_auth.get(provider='tpa-saml')
                except MultipleObjectsReturned:
                    print("WARNING #1. Multiple social auth entries exist for the user {!s} #{!s}.".format(
                        user,
                        user.id,
                    ))
                    continue
                except ObjectDoesNotExist:
                    print("WARNING #2. No social auth entry found for a user {!s} #{!s}.".format(
                        user,
                        user.id,
                    ))
                    continue

                try:
                    employee_id = social_user.uid.split(':')[1] if social_user.uid else None
                except (TypeError, IndexError):
                    print(
                        "WARNING #3. Social auth uid can't be parsed for a user {!s} id # {!s}. "
                        "It should be in the 'pingsso:employee_id_goes_here' format.".format(
                            user,
                            user.id,
                        )
                    )
                    continue

                if employee_id:
                    user_profile.employee_id = employee_id
                    try:
                        user_profile.save()
                        entries_with_empl_id += 1
                        entries_without_empl_id -= 1
                        print("SUCCESS. Saved employee_id {!s} for a user {!s} #{!s}".format(
                            employee_id,
                            user,
                            user.id,
                        ))
                    except IntegrityError:
                        print("WARNING #4. Such employee id is already stored in edX: " + employee_id)
                else:
                    print("WARNING #5. No employee id found in the social auth entry #{!s} for a user {!s} #{!s}.".format(
                        social_user.id,
                        user,
                        user.id,
                    ))

        finish = datetime.now()
        duration = (finish - start).microseconds

        print("\n============= Processed {!s} UserProfile entries out of {!s}. =============".format(processed_entries_n, found_entries_n))
        print("============= It took {!s} microseconds to process selected profiles. =============\n".format(duration))

        print("============= Saved employee id for {!s} UserProfile entries. =============".format(entries_with_empl_id))
        print("============= {!s} UserProfile entries still don't have employee id. =============\n".format(entries_without_empl_id))

        print("============= CONGRATULATIONS :) =============")
