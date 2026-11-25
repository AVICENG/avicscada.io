/*! - v1.0
* ActivationPeriod Data-structure.   
* This data structure holds the information about the activation period.  
*
* Date: Wed March 28, 2012
* Copyright © 2008-2012 Honeywell Technologies Sàrl, ECC Division. All rights reserved. Copyright © 1995-2008 Trend Control Systems Ltd.
*/

/*globals ECALENDAR*/
/*globals $ */

$(function () {
    "use strict";

    ECALENDAR.ActivationPeriodDataStructure = function () {
        //time is represented in the minutes from the start of the day.
        //For example: 
        //1. 08:30 would be represented as 510 ((8*60)+30)        
        //2. 18:30 would be represented as 1110((18*60)+30)

        //Default value is set to 0, normally ActivationPeriodStructure would be operated in a pair in a day data-structure.
        //So, if pair contains both the ActionPeriodDataStructure with default value - don't consider it as a valid activation detail.
        this.time = 0;
        this.value = 0;

        var self = this;

        //Set the new value
        this.setValue = function (newValue) {
            self.value = newValue;
        };

        //Get the value.
        this.getValue = function () {
            return self.value;
        };

        //Set the time, as a parameter one has to pass the newHour and newMinute.
        this.setTime = function (newHour, newMinute) {
            if ((newHour >= 0) && (newMinute >= 0)) {
                self.time = (newHour * 60) + newMinute;
            }
        };

        //Get the hours
        this.getHours = function () {
            return ((self.time - (self.time % 60)) / 60);
        };

        //Get the minutes
        this.getMinutes = function () {
            return (self.time % 60);
        };

        //Set the minutes (since last mid-night), if value is null or undefined - it will set the 0.
        this.setMinutes = function (value) {
            if ((value === null) || (value === undefined)) {
                self.time = 0;
            } else {
                self.time = value;
            }
        };

        //Returns the time in the minutes format, for example: 08:30 would be returned as 510.
        this.getTotalMinutes = function () {
            return self.time;
        };

        //Get the time as string (as an example: 08:00)
        this.timeAsString = function () {
            //TODO: Take care of the string literal while implementing item 21.
            var Hours, Minutes;
            Hours = self.getHours().toString();
            if (Hours.length === 1) {
                Hours = '0' + Hours;
            }
            Minutes = self.getMinutes().toString();
            if (Minutes.length === 1) {
                Minutes = '0' + Minutes;
            }
            return (Hours + ":" + Minutes);
        };

        //This function sets the time input in the string form, the expected input form is "08:00"
        this.setStringTime = function (timeAsString) {
            if ((timeAsString !== null) && (timeAsString !== undefined)) {
                //Split the string based on : delimeter
                var hourMinute = timeAsString.split(":");
                self.setMinutes((parseInt(hourMinute[0], 10) * 60) + parseInt(hourMinute[1], 10));
            }
        };

        //Validation of the current object.
        this.validate = function () {
            if (self.hasOwnProperty('time')) {
                if ((self.time < 0) && (self.time > 1440)) {
                    return "ActivationPeriodDataStructure::Time range must be from 0 to 1440.";
                }
                if (self.time === null) {
                    return "ActivationPeriodDataStructure::Time value should not be null";
                }
            }

            //For the moment, it is assumed that value could be any thing, but it should not empty string.
            if (self.hasOwnProperty('value')) {
                if ((self.value.toString()).length <= 0) {
                    return "ActivationPeriodDataStructure::Value must not be empty string or number.";
                }
                if (self.value === null) {
                    return "ActivationPeriodDataStructure:: value must not be null.";
                }
            }
        };
    };
});