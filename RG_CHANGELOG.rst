[Lilac Release] - 2021-06-17
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

[Fix] 2021-09-28
~~~~~~~~~~~~~~~~
* Incorrect logo path in email templates

[Fix] 2021-09-10
~~~~~~~~~~~~~~~~
* course discovery search error on devstack related to incorrect elasticsearch host in settings
* course discovery search error related to visibility filters
  * fixes 6d9f9352
* course discovery search sidebar filters
  * relates to update to elasticsearch7
  * bug cause: now elasticsearch returns `aggs` in the search results instead of `facets`

[Koa Release]
~~~~~~~~~~~~~

[Fix] 2021-06-15
~~~~~~~~~~~~~~~~
* pass required context to bulk enrollment emails

  * logo_url
  * homepage_url
  * dashboard_url

* add additional context for enrollment emails

  * contact_email
  * platform_name

[Feature] 2021-05-20
~~~~~~~~~~~~~~~~
‘enable_programs’ command is added.

[Fix] 2021-04-26
~~~~~~~~~~~~~~~~
‘Linked accounts’ tab is hidden if there are no SSO provider are installed

[Documentation|Enhancement] - 2021-02-24
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* RG_CHANGELOG is added!
* gitlab base RG-LMS MergeRequest template is added.

* For the upcoming logs please use the following tags:
   * Feature
   * Enhancement
   * Fix
   * Documentation
