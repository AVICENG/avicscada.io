/*!
*/

/*globals ECALENDAR*/
/*globals Backbone*/
/*globals $ */
/*globals _*/

$(function () {
	"use strict";

    ECALENDAR.DiaryModel = Backbone.Model.extend({
        defaults: function () {
            return {
                label: "New diary group",
				diaryID: -1,
                //, defaultWeekdaySetID: -1,
                isFolder: true,
                childrenArray: [],
                weekSets: null,
				maxPeriods: 0,
				isAssociatedWithTimeZones: false,
				timeZones: []
            };
        },

        validate: function (attrs) {

            if (attrs.hasOwnProperty('label')) {
                if (attrs.label === null) {
					return 'Diary label must not be null';
				}
                if (attrs.label.length <= 0) {
                    return 'Diary label must not be empty string.';
                }
                if (attrs.label.length > 255) {
                    return 'Maximum length of the diary label must be 255 characters.';
                }
            }

            if (attrs.hasOwnProperty('diaryID') && !_.isNumber(attrs.diaryID)) {
                return 'Diary ID must be a numeric value.';
            }

            if (attrs.hasOwnProperty('maxPeriods') && ((!_.isNumber(attrs.maxPeriods)) || (attrs.maxPeriods < 0))) {
				return 'Max periods must be a number equals to or greater than zero.';
            }

            //            if (attrs.hasOwnProperty('defaultWeekdaySetID') && !_.isNumber(attrs.defaultWeekdaySetID)) {
            //                return 'Default weekday set ID must be a numeric value.';
            //            }

            if (attrs.hasOwnProperty('isFolder') && attrs.hasOwnProperty('childrenArray') && !attrs.isFolder && !_.isEmpty(attrs.childrenArray)) {
                return 'A diary group must not have children.';
            }

//TODO: We need to uncomment following code once the weekSet XML will be available from the server.This is just a temporary work.
//            if (attrs.hasOwnProperty('isFolder') && attrs.hasOwnProperty('weekSets') && !attrs.isFolder && _.isNull(attrs.weekSets)) {
//                return 'A diary group must have at least one week set.';
//            }

            if (attrs.hasOwnProperty('isFolder') && attrs.hasOwnProperty('weekSets') && attrs.isFolder && !_.isNull(attrs.weekSets)) {
                return 'A folder must not have any week set.';
            }
        }
    });
});