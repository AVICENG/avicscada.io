/*! - v1.0
* Exception Collection Data-structure.   
* This data structure holds the collection of the the ECALENDAR.ExceptionModel model.
*
* Date: Mon August 27, 2012
* Copyright © 2008-2012 Honeywell Technologies Sàrl, ECC Division. All rights reserved. Copyright © 1995-2008 Trend Control Systems Ltd.
*/

/*globals Backbone*/
/*globals $ */
/*globals ECALENDAR*/

$(function () {
    "use strict";
    ECALENDAR.ExceptionCollection = Backbone.Collection.extend({
        model: ECALENDAR.ExceptionModel,
		originalForEdit: null,

        initialize: function () {
        },

        save: function (options) {
            if (this.length === 1 && !this.at(0).isNew()) {
                Backbone.sync("update", this, options);
            }
            else {
                Backbone.sync("create", this, options);
            }


        },

        destroy: function (options) {
            Backbone.sync("delete", this, options);
        },

        parse: function (resp, xhr) {
            var returnValue = null, exceptionCollection;
            if ((xhr !== null) && (xhr !== undefined)) {
                exceptionCollection = ECALENDAR.DataProvider.generateExceptionCollectionFromXML(xhr.responseText);
                if ((exceptionCollection !== null) && (exceptionCollection !== undefined)) {
                    returnValue = exceptionCollection.models;
                }
            }
            return returnValue;
        },
        filterForModelsInsideDateRange: function (start, end, includeYearly) {

            function compareDates(dateStart, dateEnd) {
                return (start >= dateStart) && (dateEnd >= end);
            }
            function compareYearlyDates(year, ex) {
                var dateStart, dateEnd;
                //set the start year the same year as the date range selection is taking place
                dateStart = new Date(year, ex.get('startDate').getMonth(), ex.get('startDate').getDate());
                // set the end year the same year as the date range selection is taking place, adding exception year difference (in case it spanned multiple years)
                dateEnd = new Date(year + (ex.get('endDate').getFullYear() - ex.get('startDate').getFullYear()), ex.get('endDate').getMonth(), ex.get('endDate').getDate());

                return compareDates(dateStart, dateEnd);
            }

            return this.filter(
                function (ex) {
                    var exists = compareDates(ex.get('startDate'), ex.get('endDate'));
                    if (exists !== true && includeYearly === true && ex.get('sameEveryYear') === true) {
                        exists = compareYearlyDates(start.getFullYear(), ex);
                        if (!exists && end.getFullYear() > start.getFullYear()) {
                            exists = compareYearlyDates(end.getFullYear(), ex);
                        }
                    }
                    return exists;
                }
            );
        },

        filterModelsThatStartOrEndInRange: function (start, end, includeYearly) {
            function compareDates(dateStart, dateEnd) {
                return ((start <= dateEnd) && (dateStart <= end));
            }
            function compareYearlyDates(year, ex) {
                var dateStart, dateEnd;
                //set the start year the same year as the date range selection is taking place
                dateStart = new Date(year, ex.get('startDate').getMonth(), ex.get('startDate').getDate());
                // set the end year the same year as the date range selection is taking place, adding exception year difference (in case it spanned multiple years)
                dateEnd = new Date(year + (ex.get('endDate').getFullYear() - ex.get('startDate').getFullYear()), ex.get('endDate').getMonth(), ex.get('endDate').getDate());

                return compareDates(dateStart, dateEnd);
            }

            return this.filter(
                function (ex) {
                    var exists = compareDates(ex.get('startDate'), ex.get('endDate'));
                    if (exists !== true && includeYearly === true && ex.get('sameEveryYear') === true && start > ex.get('endDate')) {

                        exists = compareYearlyDates(start.getFullYear(), ex);

                        if (!exists && end.getFullYear() > start.getFullYear()) {
                            exists = compareYearlyDates(end.getFullYear(), ex);
                        }
                    }
                    return exists;
                }
            );
        }



    });
});