/*! - v1.0
* Exception Data-structure.   
* This data structure holds the information about the expection for a diary group.
*
* Date: Wed March 28, 2012
* Copyright © 2008-2012 Honeywell Technologies Sàrl, ECC Division. All rights reserved. Copyright © 1995-2008 Trend Control Systems Ltd.
*/

/*globals Backbone*/
/*globals $ */
/*globals ECALENDAR*/
/*globals _ */

$(function () {
    "use strict";

    ECALENDAR.ExceptionModel = Backbone.Model.extend({
        defaults: {
            exceptionID: null,
            label: ECALENDAR.ApplicationStrings.getResourceFromID("New"),
            diaryGroupID: -1,
            startDate: new Date(),
            endDate: new Date(),
            sameEveryYear: false,
            specialDayID: -1,
            weeksetID: -1,
	    isWeekset: 0,
            timeschemelabel: '',
            colour: '#FFFFFF'

        },
        newException: true,
        initialize: function () {
        },
        idAttribute: 'exceptionID',
        isNew: function () {

            if (this.newException === false) {
                // if we have explicitly set the model to be an existing item, return false (its not a new exception)
                return false;
            }
            return this.constructor.__super__.isNew.call(this);
        },
        sameEveryYearText: function () {
            if (this.get('sameEveryYear') === true) {
                return ECALENDAR.ApplicationStrings.getResourceFromID('YES');
            }
            else {
                return ECALENDAR.ApplicationStrings.getResourceFromID('NO');
            }
        },
        validateLabel: function (attrs) {
            var errors = [];
            //Label validation rules.
            if ((attrs.label === null) || (attrs.label === undefined)) {
                errors.push({ name: 'label', error: ECALENDAR.ApplicationStrings.getResourceFromID('INTERNAL_ERROR') });
            } else if (attrs.label.length <= 0) {
                errors.push({ name: 'label', error: ECALENDAR.ApplicationStrings.getResourceFromID('LABEL_EMPTY') });
            } else if (attrs.label.length > 255) {
                errors.push({ name: 'label', error: ECALENDAR.ApplicationStrings.getResourceFromID('LABEL_TOO_LONG') });
            }
            return errors;
        },
        validateDates: function (attrs) {
            var currentDate, errors = [];

            currentDate = new Date();
            currentDate.setHours(0, 0, 0, 0);
            //Start Date validation rules.
            if ((attrs.startDate === null) || (attrs.startDate === undefined) || (!_.isDate(attrs.startDate))) {
                errors.push({ name: 'startDate', error: ECALENDAR.ApplicationStrings.getResourceFromID('EXCEPTION_DATE_NOT_SET') });
            } else if ((attrs.startDate < currentDate) && (attrs.exceptionID === this.defaults.exceptionID)) {
                //For the new exception, user can not set the date in past.
                errors.push({ name: 'startDate', error: ECALENDAR.ApplicationStrings.getResourceFromID('EXCEPTION_DATE_IN_PAST') });
            }

            //End Date validation rules.
            if (((attrs.startDate !== null) && (attrs.startDate !== undefined)) && ((attrs.endDate === null) || (attrs.endDate === undefined) || (!_.isDate(attrs.endDate)))) {
                errors.push({ name: 'endDate', error: ECALENDAR.ApplicationStrings.getResourceFromID('EXCEPTION_DATE_NOT_SET') });
            } else if (attrs.startDate > attrs.endDate) {
                errors.push({ name: 'endDate', error: ECALENDAR.ApplicationStrings.getResourceFromID('START_AND_END_DATE_VALIDATION') });
            }

            return errors;
        },
        validateTimeSchemeSelection: function (attrs) {
            var errors = [];

            //weeksetID and specialDayID validation rules.
            if ((attrs.specialDayID === null) || (attrs.specialDayID === undefined) || (!_.isNumber(attrs.specialDayID)) || (attrs.specialDayID < -1)) {
                errors.push({ name: 'specialDayID', error: ECALENDAR.ApplicationStrings.getResourceFromID('INTERNAL_ERROR') });
            }

            if ((attrs.weeksetID === null) || (attrs.weeksetID === undefined) || (!_.isNumber(attrs.weeksetID)) || (attrs.weeksetID < -1)) {
                errors.push({ name: 'weeksetID', error: ECALENDAR.ApplicationStrings.getResourceFromID('INTERNAL_ERROR') });
            }


            //A exception must be associated with either weekset or special day.
            if ((attrs.specialDayID !== null) && (attrs.specialDayID !== undefined) && (attrs.weeksetID !== null) && (attrs.weeksetID !== undefined)) {
                if ((attrs.weeksetID <= -1) && (attrs.specialDayID <= -1)) {
                    errors.push({ name: 'weeksetID', error: ECALENDAR.ApplicationStrings.getResourceFromID('EXCEPTION_MUST_BE_ASSOCIATED') });
                }
            }

            return errors;
        },
        validate: function (attrs) {
            var errors = [];
            //Exception ID validation rules.
            if ((attrs.exceptionID !== this.defaults.exceptionID) && ((attrs.exceptionID === undefined) || (!_.isNumber(attrs.exceptionID)) || (attrs.exceptionID < -1))) {
                errors.push({ name: 'exceptionID', error: ECALENDAR.ApplicationStrings.getResourceFromID('INTERNAL_ERROR') });
            }

            errors = errors.concat(this.validateLabel(attrs));

            //Diary group id validation rules.            
            if ((attrs.diaryGroupID === null) || (attrs.diaryGroupID === undefined) || (!_.isNumber(attrs.diaryGroupID)) || (attrs.diaryGroupID < -1)) {
                errors.push({ name: 'diaryGroupID', error: ECALENDAR.ApplicationStrings.getResourceFromID('INTERNAL_ERROR') });
            }

            errors = errors.concat(this.validateDates(attrs));


            //sameEveryYear validation rules.
            if ((attrs.sameEveryYear === null) || (attrs.sameEveryYear === undefined) || (!_.isBoolean(attrs.sameEveryYear))) {
                errors.push({ name: 'sameEveryYear', error: ECALENDAR.ApplicationStrings.getResourceFromID('INTERNAL_ERROR') });
            }

            errors = errors.concat(this.validateTimeSchemeSelection(attrs));

            //TODO: we have to write unit test which actually select the folder and these validation should only be applicable if folder is selected.
            //Time scheme label is necessary because on Server folder level common time schemes are currently identified by common name time scheme in all the children nodes.
            if ((attrs.timeschemelabel === null) || (attrs.timeschemelabel === undefined)) {
                errors.push({ name: 'timeschemelabel', error: ECALENDAR.ApplicationStrings.getResourceFromID('INTERNAL_ERROR') });
            } else if (ECALENDAR.DiaryGroupSelection) {
                if (ECALENDAR.DiaryGroupSelection.get("diaryGroup")) {
                    if (ECALENDAR.DiaryGroupSelection.get("diaryGroup").get("isFolder") === true) {
                        if (attrs.timeschemelabel.length <= 0) {
                            errors.push({ name: 'timeschemelabel', error: ECALENDAR.ApplicationStrings.getResourceFromID('LABEL_EMPTY') });
                        } else if (attrs.timeschemelabel.length > 255) {
                            errors.push({ name: 'timeschemelabel', error: ECALENDAR.ApplicationStrings.getResourceFromID('LABEL_TOO_LONG') });
                        }
                    }
                }
            }

            if (errors.length > 0) {
                return errors;
            }
        }
    });
});