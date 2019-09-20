"""
Management commands of the `poll_survey` app.

First of all, dedicated to persist historical polls and surveys
to the `poll_survey` tables.

Ignoring `module_type`'s other than "poll" and "survey" (e.g. "open_ended_survey"),
as they've been introduced together with the "poll_survey" app
i.e. there's no historical data for other module types.
"""
