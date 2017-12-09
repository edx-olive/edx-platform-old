(function(define) {
    'use strict';
    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'edx-ui-toolkit/js/utils/html-utils'
        ],
        function(Backbone, $, _, gettext, HtmlUtils) {
            return Backbone.View.extend({
                el: '#unenroll-entitlement-modal',

                triggerSelector: '.js-action-unenroll-entitlement',

                submitButtonSelector: '#unenroll-entitlement-submit',

                trackInfoSelector: '#entitlement-track-info',

                refundInfoSelector: '#entitlement-refund-info',

                errorInfoSelector: '#unenroll-entitlement-error',

                closeButtonSelector: '#unenroll-entitlement-modal .close-entitlement-modal',

                mainPageSelector: '#dashboard-main',

                initialize: function(options) {
                    var _this = this;
                    this.dashboardUrl = options.dashboardUrl;

                    this.$submitButton = $(this.submitButtonSelector);
                    this.$trackInfo = $(this.trackInfoSelector);
                    this.$refundInfo = $(this.refundInfoSelector);
                    this.$errorInfo = $(this.errorInfoSelector);

                    this.$submitButton.on('click', this.handleSubmit.bind(this));

                    $(this.triggerSelector).each(function(index) {
                        var $trigger = $(this);

                        $trigger.on('click', _this.handleTrigger.bind(_this));

                        if (window.accessible_modal) {
                            window.accessible_modal(
                                '#' + $trigger.attr('id'),
                                _this.closeButtonSelector,
                                '#' + _this.$el.attr('id'),
                                _this.mainPageSelector
                            );
                        }
                    });
                },

                handleTrigger: function(event) {
                    var $trigger = $(event.target),
                        courseName = $trigger.data('courseName'),
                        courseNumber = $trigger.data('courseNumber'),
                        isRefundable = $trigger.data('entitlementIsRefundable'),
                        apiEndpoint = $trigger.data('entitlementApiEndpoint');

                    this.resetModal();
                    this.setTrackInfo(courseName, courseNumber);
                    this.setRefundInfo(isRefundable);
                    this.setSubmitData(apiEndpoint, isRefundable);

                    if (window.edx && window.edx.dashboard && window.edx.dashboard.dropdown) {
                        window.edx.dashboard.dropdown.toggleCourseActionsDropdownMenu(event);
                        this.$el.css('position', 'fixed');
                    }
                },

                handleSubmit: function(event) {
                    var apiEndpoint = this.$submitButton.data('entitlementApiEndpoint'),
                        isRefundable = this.$submitButton.data('entitlementIsRefundable');

                    if (apiEndpoint === undefined || isRefundable === undefined) {
                        this.setError(gettext('Error: cannot process unenrollment request.'));
                        return;
                    }

                    $.ajax({
                        url: apiEndpoint,
                        method: 'DELETE',
                        complete: this.onComplete.bind(this)
                    });
                },

                resetModal: function() {
                    this.$submitButton.removeData();
                    this.$submitButton.prop('disabled', false);
                    this.$trackInfo.empty();
                    this.$refundInfo.empty();
                    this.$errorInfo.css('display', 'none');
                    this.$errorInfo.empty();
                },

                setError: function(message) {
                    this.$submitButton.prop('disabled', true);
                    this.$errorInfo.empty();
                    HtmlUtils.setHtml(
                        this.$errorInfo,
                        message
                    )
                    this.$errorInfo.css('display', 'block');
                },

                setTrackInfo: function(courseName, courseNumber) {
                    this.$trackInfo.empty();
                    HtmlUtils.setHtml(
                        this.$trackInfo,
                        HtmlUtils.interpolateHtml(
                            gettext('Are you sure you want to unenroll from {courseName} ({courseNumber})?'),
                            {
                                courseName: HtmlUtils.joinHtml(
                                    HtmlUtils.HTML('<span id="entitlement-unenrollment-course-name">'),
                                    courseName,
                                    HtmlUtils.HTML('</span>')
                                ),
                                courseNumber: HtmlUtils.joinHtml(
                                    HtmlUtils.HTML('<span id="entitlement-unenrollment-course-number">'),
                                    courseNumber,
                                    HtmlUtils.HTML('</span>')
                                )
                            }
                        )
                    );
                },

                setRefundInfo: function(isRefundable) {
                    var message = null;

                    if (isRefundable) {
                        message = gettext('You will be refunded the amount you paid.');
                    } else {
                        message = gettext('You will not be refunded the amount you paid.');
                    }

                    this.$refundInfo.empty();
                    HtmlUtils.setHtml(this.$refundInfo, message);
                },

                setSubmitData: function(apiEndpoint, isRefundable) {
                    this.$submitButton.removeData();
                    this.$submitButton.data('entitlementApiEndpoint', apiEndpoint);
                    this.$submitButton.data('entitlementIsRefundable', isRefundable);
                },

                onComplete: function(xhr, textStatus) {
                    if (xhr.status === 204) {
                        window.location.href = this.dashboardUrl
                    } else {
                        this.setError(gettext('Error: something went wrong while processing your request.'))
                    }
                }
            });
        }
    );

}).call(this, define || RequireJS.define);
