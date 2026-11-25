/*! - v1.0
*/

/*globals ECALENDAR*/
/*globals Backbone*/
/*globals _*/
/*globals $ */
/*globals Modernizr*/

$(function () {
    "use strict";
    ECALENDAR.ExceptionWizardSummaryView = Backbone.View.extend({
        template: _.template(
        '<p><%= HTML_TEXT_EXCEPTION_SUMMARY %></p>' +
        '<div class="row-fluid"><div class="span4"><%=HTML_LABEL_NAME %>:</div><div class="span8 pre" id="ExceptionLabel"></div></div>' +
        '<div class="row-fluid"><div class="span4"><%=HTML_LABEL_REPETITION %>:</div><div class="span8"><%= CONVERTED_SAMEEVERYYEAR %></div></div>' +
        '<div class="row-fluid"><div class="span4"><%=HTML_LABEL_OPERATING_TIMES %>:</div><div class="span8 pre" id="operatingTime"></div></div>' +
        '<div id="exceptionDates" class="row-fluid"><div class="span4"><%=HTML_LABEL_DATES_COVERED %>:</div><div class="span8"><ul class="unstyled exception-date-list"><%= CONVERTED_DATES %></ul></div></div>'),
        exceptionDeletionTemplate: _.template('<div id="deletedDates" class="row-fluid"><div class="span4"><%=HTML_LABEL_DATES_TO_DELETE %>:</div><div class="span8"><ul class="unstyled exception-date-list"><%= CONVERTED_DATES %></ul></div></div>'),
        initialize: function () {
            this.model.bind('change', this.render, this);
            this.model.bind('add', this.render, this);
            this.model.bind('reset', this.render, this);

            // Expectation is that deleted dates does exist - created by previous wizard view, 
            // but if it doesn't initialise it so that listeners can be added in one place instead 
            // of continually looking to see if the collection has been created

            ECALENDAR.deletedDates = ECALENDAR.deletedDates || new ECALENDAR.ExceptionCollection();
            ECALENDAR.deletedDates.bind('add', this.updateDeletions, this);
            ECALENDAR.deletedDates.bind('remove', this.updateDeletions, this);

            this.render();
        },
        updateDeletions: function () {
       
            var deletions = this.$('#deletedDates'), tempDeletions;
            if (ECALENDAR.deletedDates.length === 0) {
                if (deletions.length > 0) {
                    deletions.remove();
                    
                }
            }
            else {
                var dates = ECALENDAR.deletedDates.map(this.concatDates).join('');

                tempDeletions = this.exceptionDeletionTemplate({ CONVERTED_DATES: dates, HTML_LABEL_DATES_TO_DELETE: ECALENDAR.ApplicationStrings.getResourceFromID('LABEL_DATES_TO_DELETE') });

                if (deletions.length > 0) {
                    deletions.replaceWith(tempDeletions);
                 
                }
                else {
                    this.$el.append(tempDeletions);
                 
                }

            }
        },
        concatDates: function (m) {
            if (m.get('startDate').toString() === m.get('endDate').toString()) {
                return '<li>' + m.get('startDate').toLocaleDateString() + '</li>';
            }
            return '<li>' + m.get('startDate').toLocaleDateString() + ' - ' + m.get('endDate').toLocaleDateString() + '</li>';
        },
        render: function () {
            function getResource(id) {
                return ECALENDAR.ApplicationStrings.getResourceFromID(id);
            }


            var dates = this.model.map(this.concatDates).join('');


            this.$el.html(this.template(_.extend(this.model.at(0).toJSON(),
            { HTML_LABEL_NAME: getResource('LABEL_NAME'),
                HTML_LABEL_REPETITION: getResource('LABEL_EXCEPTION_REPEAT_YEARLY'),
                CONVERTED_SAMEEVERYYEAR: (this.model.at(0).get('sameEveryYear') === true) ? getResource('YES') : getResource('NO'),
                HTML_LABEL_OPERATING_TIMES: getResource('LABEL_OPERATION_TIMES'),
                HTML_LABEL_DATES_COVERED: getResource('LABEL_DATES_COVERED'),
                CONVERTED_DATES: dates,
                HTML_TEXT_EXCEPTION_SUMMARY: getResource('TEXT_EXCEPTION_SUMMARY')
            })));

            this.$('#ExceptionLabel').text(this.model.at(0).get('label'));
            this.$('#operatingTime').html(this.model.at(0).get('timeschemelabel'));
            if (ECALENDAR.deletedDates && ECALENDAR.deletedDates.length > 0) {
                this.updateDeletions();
            }

        }



    });

});