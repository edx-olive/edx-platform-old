(function(define) {
    'use strict';

    define([
        'js/learner_dashboard/views/entitlement_unenroll_view'
    ],
    function(EntitlementUnenrollView) {
        return function(options) {
            return new EntitlementUnenrollView(options);
        };
    });
}).call(this, define || RequireJS.define);
