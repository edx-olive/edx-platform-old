"""Utils for async files downloading."""

import csv
import logging
import os

from django.conf import settings


log = logging.getLogger('edx.celery.task')


# TODO add docstrings everywhere (all modules)


def get_latest_user_file(user_id, dir_path, extension="csv"):
    """Get latest file in a dir provided a user id in a file name."""

    latest_file = None
    dirpath = os.path.join(dir_path)
    user_files_paths = [
        os.path.join(dirpath, f)
        for f in os.listdir(dirpath)
        if os.path.isfile(os.path.join(dirpath, f))
        and int(get_filename_user_id(f)) == int(user_id)
        and os.path.join(dirpath, f).split(".")[-1] == extension
    ]
    if user_files_paths:
        latest_file = max(user_files_paths, key=os.path.getctime)
    return latest_file


def fetch_csv_data(filepath):
    with open(filepath, "r+") as csv_file:
        csv_file.seek(0)
        data = csv_file.read()
        # csv_file.seek(0)
        # csv_file.truncate()
        yield data


def create_empty_file(filename, header):
    """Create a file with header but without any data."""

    filepath = os.path.join(settings.POLL_SURVEY_SUBMISSIONS_DIR, filename + ".tmp")
    with open(filepath, "a+") as csv_file:
        writer = csv.writer(csv_file, dialect='excel', quotechar='"',
                            quoting=csv.QUOTE_ALL)
        writer.writerow(header)


def store_rows(
        filename,
        data,
        header,
        datum_processor=None,
        datum_processor_kwargs=None,
        store_header=True):

    if not (datum_processor_kwargs and datum_processor):
        raise ValueError("Datum processor requires kwargs.")

    if store_header and not header:
        raise ValueError("Header is required.")

    filepath = os.path.join(settings.POLL_SURVEY_SUBMISSIONS_DIR, filename + ".tmp")

    with open(filepath, "a+") as csv_file:
        writer = csv.writer(csv_file, dialect='excel', quotechar='"',
                            quoting=csv.QUOTE_ALL)
        if store_header:
            writer.writerow(header)
        for datum in data:
            if datum_processor:
                datum = datum_processor(datum, **datum_processor_kwargs)
            # log.debug("datum: {!s}".format(datum))
            writer.writerow(datum)


def cleanup_directory_files(dir_path, user_id):
    """Cleanup directory files by user id."""

    for the_file in os.listdir(dir_path):
        file_path = os.path.join(dir_path, the_file)
        try:
            file_user_id = get_filename_user_id(the_file)
            if int(file_user_id) == user_id:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
        except Exception as e:
            log.error(str(e))


def get_filename_user_id(filename):
    """
    Fetch user id from the file name.

    Examples of a `filename`:
     `poll_survey_submissions_1569269158_11.csv`
     `poll_survey_submissions_1569269158_11.csv.tmp`
    """

    return filename.split("_")[-1].split(".")[0]
