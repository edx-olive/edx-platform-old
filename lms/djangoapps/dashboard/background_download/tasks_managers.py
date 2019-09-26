"""
Logic for async tasks running.

Ref.: https://github.com/open-craft/xblock-poll/blob/c7ebcc471153c860e1f8f4035f4f162c72b3f778/poll/poll.py
"""


class AsyncTaskManager(object):
    """Celery tasks manager."""

    def __init__(self, task):
        self.task = task
        self.task_id = None
        self.last_result = None

    def run(self, **kwargs):
        """
        Asynchronously run `self.task`.

        Make sure we nail down our state before sending off an asynchronous task.

        The logic is for subclasses to decide.
        """
        raise NotImplementedError

    def _process_result(self, async_result):
        if not async_result.ready():
            self.task_id = async_result.id
        else:
            self._get_result(async_result)

        return self._get_status()

    def _get_result(self, task_result):
        """Given an AsyncResult or EagerResult, get it."""
        self.task_id = ''
        if task_result.successful():
            if isinstance(task_result.result, dict) and not task_result.result.get('error'):
                self.last_result = task_result.result
            else:
                self.last_result = {'error': u'Unexpected result: {}'.format(repr(task_result.result))}
        else:
            self.last_result = {'error': unicode(task_result.result)}

    def _get_status(self):
        """Get the export status."""
        self._check_pending_result()
        return {
            'pending': bool(self.task_id),
            'last_result': self.last_result
        }

    def _check_pending_result(self):
        """If we're waiting for an export, see if it has finished, and if so, get the result."""
        if self.task_id:
            async_result = self.task.AsyncResult(self.task_id)
            if async_result.ready():
                self._get_result(async_result)


class PollsMigrationTaskManager(AsyncTaskManager):

    def run(self, **kwargs):
        """Asynchronously run `self.task`."""
        # Make sure we nail down our state before sending off an asynchronous task.
        async_result = self.task.apply_async(kwargs=dict(
            user_id=kwargs.get("user_id"),
            courses_ids=kwargs.get("courses_ids")
        ))
        return self._process_result(async_result)
