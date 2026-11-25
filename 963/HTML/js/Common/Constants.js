/*globals ECALENDAR*/
/*globals $ */
/*globals jQuery */

(function ($) {
	"use strict";

	var AppConstants;
	AppConstants = function () {

		this.weekDays = {
			MONDAY: '1',
			TUESDAY: '2',
			WEDNESDAY: '3',
			THURSDAY: '4',
			FRIDAY: '5',
			SATURDAY: '6',
			SUNDAY: '7'
		};

		this.downloadOptions = {
			NEVER: 'never',
			NOW: 'now',
			LATER: 'later'
		};
	};

	ECALENDAR.ApplicationConstants = new AppConstants();
} (jQuery));