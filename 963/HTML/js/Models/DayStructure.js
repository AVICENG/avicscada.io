/*! - v1.0
* Day Data-structure.   
* This data structure holds the information about a day of a weekset of a IQ controller or 963.
*
* Date: Wed March 28, 2012
* Copyright © 2008-2012 Honeywell Technologies Sàrl, ECC Division. All rights reserved. Copyright © 1995-2008 Trend Control Systems Ltd.
*/

/*globals ECALENDAR*/
/*globals $ */

$(function () {
	"use strict";

    ECALENDAR.DayStructure = function () {
        this.label = ECALENDAR.ApplicationStrings.getResourceFromID('DAY_SHORT');
        this.dayID = -1;

        //Activation period array, programmer should take care to assign the value to this field.
        this.arrActivationPeriod = [];

        var self = this;


        //Add one empty activation period in the structure.
        //Empty activation period starts with 24:00 and ends at 24:00 with start and end value as 0.
        this.addOneEmptyActivationPeriod = function () {

            //Start activation time per
            var startPeriod, endPeriod;
			startPeriod = new ECALENDAR.ActivationPeriodDataStructure();
            startPeriod.setTime(24, 0);
            startPeriod.setValue(0);
            this.arrActivationPeriod.push(startPeriod);

            endPeriod = new ECALENDAR.ActivationPeriodDataStructure();
            endPeriod.setTime(24, 0);
            endPeriod.setValue(0);
            this.arrActivationPeriod.push(endPeriod);
        };

        //Default activation period is 08:00AM to 05:30PM. This method removes all activation period and adds one activation period only as specified.
        this.setDefaultActivationPeriod = function () {
            //Empty the array first.
            if ((self.arrActivationPeriod !== null) ||
					(self.arrActivationPeriod.toString() !== 'undefined')) {
                self.arrActivationPeriod.length = 0;
            } else {
                self.arrActivationPeriod = [];
            }

            //Now add the default item in the - On at 8:00 AM
            var activationPeriod = new ECALENDAR.ActivationPeriodDataStructure();
            activationPeriod.setTime(8, 0);
            activationPeriod.setValue(1);
            self.arrActivationPeriod.push(activationPeriod);

            activationPeriod = new ECALENDAR.ActivationPeriodDataStructure();
            activationPeriod.setTime(17, 30);
            activationPeriod.setValue(0);
            self.arrActivationPeriod.push(activationPeriod);
        };

        //Get the label.
        this.getLabel = function () {
            return self.label;
        };

        //Set the label of the day.
        this.setLabel = function (newLabel) {
            self.label = newLabel;
        };

        //Set day ID
        this.setDayID = function (newDayID) {
            self.dayID = newDayID;
        };

        //Get day ID
        this.getDayID = function () {
            return self.dayID;
        };

        //For me it's okay not to put the getter and setter method for the arrActivationPeriod variable.
        //It is an array and should be accessed directly to avoid any problem.

        //Validation of the current object.
        this.validate = function () {
            if (self.hasOwnProperty('label')) {
                if (self.label === null) {
                    return 'DayStructure::Label must not be null';
                }
                if (self.label.length <= 0) {
                    return 'DayStructure::Label must not be empty string.';
                }
                if (self.label.length > 255) {
                    return 'DayStructure::Maximum length of the label must be 255 characters.';
                }
            }

            if (self.hasOwnProperty('dayID')) {
                if (self.dayID < -1) {
                    return "DayStructure::dayID must be positive number";
                }
            }

            //Length of the activation period must be even. The user interface will read in pair
            //If the Length is 2, it indicates that there is one activation period slot will be available. 
            if ((self.arrActivationPeriod === null) || (self.arrActivationPeriod === undefined)) {
                return "DayStructure::Activation period array must not be null or undefined";
            }

            if ((self.arrActivationPeriod.length) % 2 !== 0) {
                return "DayStructure::Length of the activation period must be even number.";
            }

            return false;
        };
    };
});