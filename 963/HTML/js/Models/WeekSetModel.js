/*! - v1.0
 * WeekSet Model 
 *
 * This model holds the weekset information of the time zone. 
 * It should be ideally holds seven days activation time period information but architecturally it should support variable numbers of days collection as well.
 *
 * Date: Wed March 28, 2012
 * Copyright 2008-2012 Honeywell Technologies Sàrl, ECC Division. All rights reserved. Copyright 1995-2008 Trend Control Systems Ltd. 
 */

/*globals ECALENDAR*/
/*globals Backbone*/
/*globals $ */

$(function () {
    "use strict";


    ECALENDAR.SpecialDayModel = Backbone.Model.extend({
        defaults: {
            //This should not be in the Diary model, put it here as long as we only have 1 model.
            groupId: -1,
            //Default colour value is set according to the 963 default value in hexa-decimal format, this should be move valuable.
            colour: '#FFFFFF',
            label: ECALENDAR.ApplicationStrings.getResourceFromID('New'),
            specialDayID: null,
            arrDay: [],
            isDefault: false
        },
        idAttribute: "specialDayID",
        initialize: function () {
            if (this.get('arrDay').length === 0) {
                this.set('arrDay', this.getDefaultDayArray());
            }
        },
        isUsedInException: function () {
            return (ECALENDAR.exceptionCollection.where({ specialDayID: this.attributes.specialDayID }).length > 0 ? true : false);
        },
        getDefaultDayArray: function () {
            //TODO: Replace these string literal in the sub task 21.
            var day = new ECALENDAR.DayStructure();

            day.setLabel("&#160;");
            day.setDefaultActivationPeriod();
            //Monday.
            return [day];

        },
        validate: function (attrs) {
            var count, validationReturn, errors = [], validColourRegExp = /#[0-9A-Fa-f]{6,6}$/i;
            //Colour validation.
            if ((attrs.colour === null) || (attrs.colour === undefined)) {
                errors.push({ name: 'colour', error: ECALENDAR.ApplicationStrings.getResourceFromID('INTERNAL_ERROR') });
            }
            else if (validColourRegExp.test(attrs.colour) === false) {
                errors.push({ name: 'colour', error: ECALENDAR.ApplicationStrings.getResourceFromID('COLOUR_INVALID') });
            }

            //Label validation.
            if ((attrs.label === null) || (attrs.label === undefined)) {
                errors.push({ name: 'label', error: ECALENDAR.ApplicationStrings.getResourceFromID('INTERNAL_ERROR') });
            }
            else if (attrs.label.length <= 0) {
                errors.push({ name: 'label', error: ECALENDAR.ApplicationStrings.getResourceFromID('LABEL_EMPTY') });
            }
            else if (attrs.label.length > 255) {
                errors.push({ name: 'label', error: ECALENDAR.ApplicationStrings.getResourceFromID('LABEL_TOO_LONG') });
            }

            //Special Day ID validation.
            if ((attrs.specialDayID === undefined)) {
                errors.push({ name: 'specialDayID', error: ECALENDAR.ApplicationStrings.getResourceFromID('INTERNAL_ERROR') });
            }
            else if (attrs.weekSetID < -1) {
                errors.push({ name: 'specialDayID', error: ECALENDAR.ApplicationStrings.getResourceFromID('INTERNAL_ERROR') });
            }

            // Array of days validation.
            if (attrs.arrDay === null) {
                errors.push({ name: 'days', error: ECALENDAR.ApplicationStrings.getResourceFromID('INTERNAL_ERROR') });
            }
            else if (attrs.arrDay.length !== 1) {
                errors.push({ name: 'days', error: ECALENDAR.ApplicationStrings.getResourceFromID('INTERNAL_ERROR') });
            }
            else {
                validationReturn = attrs.arrDay[0].validate();
                if (validationReturn) {
                    errors.push({ name: 'days', error: validationReturn });

                }

            }

            if (errors.length > 0) {
                return errors;
            }
        }
    }
    );


    ECALENDAR.WeekSetModel = Backbone.Model.extend({

        defaults: {
            //This should not be in the Diary model, put it here as long as we only have 1 model.
            groupId: -1,
            //Default colour value is set according to the 963 default value in hexa-decimal format, this should be move valuable.
            colour: '#FFFFFF',
            label: ECALENDAR.ApplicationStrings.getResourceFromID('New'),
            weekSetID: null,
            arrDay: []
        },
        idAttribute: "weekSetID",
        initialize: function () {
            //Set the weekset as collection of the days.
            this.attributes.arrDay = this.getDefaultDayArray();
        },
        isUsedInException: function() {            
            return (ECALENDAR.exceptionCollection.where({weeksetID:this.attributes.weekSetID}).length > 0 ? true: false);
        },
        validate: function (attrs) {
            var count, validationReturn, errors = [], validColourRegExp = /#[0-9A-Fa-f]{6,6}$/i;
            //Colour validation.
            if ((attrs.colour === null) || (attrs.colour === undefined)) {
                errors.push({ name: 'colour', error: ECALENDAR.ApplicationStrings.getResourceFromID('INTERNAL_ERROR') });
            }
            else if (validColourRegExp.test(attrs.colour) === false) {
                errors.push({ name: 'colour', error: ECALENDAR.ApplicationStrings.getResourceFromID('COLOUR_INVALID') });
            }

            //Label validation.
            if ((attrs.label === null) || (attrs.label === undefined)) {
                errors.push({ name: 'label', error: ECALENDAR.ApplicationStrings.getResourceFromID('INTERNAL_ERROR') });
            }
            else if (attrs.label.length <= 0) {
                errors.push({ name: 'label', error: ECALENDAR.ApplicationStrings.getResourceFromID('LABEL_EMPTY') });
            }
            else if (attrs.label.length > 255) {
                errors.push({ name: 'label', error: ECALENDAR.ApplicationStrings.getResourceFromID('LABEL_TOO_LONG') });
            }
            //Weekset ID validation.
            if ((attrs.weekSetID === undefined)) {
                errors.push({ name: 'weeksetID', error: ECALENDAR.ApplicationStrings.getResourceFromID('INTERNAL_ERROR') });
            }
            else if (attrs.weekSetID < -1) {
                errors.push({ name: 'weeksetID', error: ECALENDAR.ApplicationStrings.getResourceFromID('INTERNAL_ERROR') });
            }


            // Array of days validation.
            if (attrs.arrDay === null) {
                errors.push({ name: 'days', error: ECALENDAR.ApplicationStrings.getResourceFromID('INTERNAL_ERROR') });
            }
            else if (attrs.arrDay.length !== 7) {
                errors.push({ name: 'days', error: ECALENDAR.ApplicationStrings.getResourceFromID('INTERNAL_ERROR') });
            }
            else {
                //Validate the array, it must be correct
                for (count = 0; count < attrs.arrDay.length; count += 1) {
                    validationReturn = attrs.arrDay[count].validate();
                    if (validationReturn) {
                        errors.push({ name: 'days', error: validationReturn });
                        break;
                    }
                }
            }

            if (errors.length > 0) {
                return errors;
            }
        },

        getDefaultDayArray: function () {
            //TODO: Replace these string literal in the sub task 21.
            var dayArray, day;
            dayArray = [];

            //Monday.
            day = new ECALENDAR.DayStructure();
            day.setLabel(ECALENDAR.ApplicationStrings.getResourceFromID('MONDAY_SHORT'));
            day.setDefaultActivationPeriod();
            dayArray.push(day);

            //Tuesday
            day = new ECALENDAR.DayStructure();
            day.setLabel(ECALENDAR.ApplicationStrings.getResourceFromID('TUESDAY_SHORT'));
            day.setDefaultActivationPeriod();
            dayArray.push(day);

            //Wednesday.
            day = new ECALENDAR.DayStructure();
            day.setLabel(ECALENDAR.ApplicationStrings.getResourceFromID('WEDNESDAY_SHORT'));
            day.setDefaultActivationPeriod();
            dayArray.push(day);

            //Thursday
            day = new ECALENDAR.DayStructure();
            day.setLabel(ECALENDAR.ApplicationStrings.getResourceFromID('THURSDAY_SHORT'));
            day.setDefaultActivationPeriod();
            dayArray.push(day);

            //Friday
            day = new ECALENDAR.DayStructure();
            day.setLabel(ECALENDAR.ApplicationStrings.getResourceFromID('FRIDAY_SHORT'));
            day.setDefaultActivationPeriod();
            dayArray.push(day);

            //Saturday
            day = new ECALENDAR.DayStructure();
            day.addOneEmptyActivationPeriod();
            day.setLabel(ECALENDAR.ApplicationStrings.getResourceFromID('SATURDAY_SHORT'));
            dayArray.push(day);

            day = new ECALENDAR.DayStructure();
            day.addOneEmptyActivationPeriod();
            day.setLabel(ECALENDAR.ApplicationStrings.getResourceFromID('SUNDAY_SHORT'));
            dayArray.push(day);

            return dayArray;
        }
    });
});