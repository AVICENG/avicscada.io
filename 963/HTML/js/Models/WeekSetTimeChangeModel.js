/*! - v1.0
 * WeekSet Model 
 *
 * This model holds the postponed change weekset information of the time zone. 
 *
 * Date: Wed November 07, 2012
 * Copyright 2008-2012 Honeywell Technologies Sàrl, ECC Division. All rights reserved. Copyright 1995-2008 Trend Control Systems Ltd. 
 */

/*globals ECALENDAR*/
/*globals Backbone*/
/*globals $ */

$(function () {
    "use strict";


    ECALENDAR.WeekSetTimeChangeModel = Backbone.Model.extend({
        defaults: {
            //This should not be in the Diary model, put it here as long as we only have 1 model.
            groupId: -1,
            label: '',
            weekSetId: -1,
            date: null,
            isNew: true
        },
        isNew: function () {
            // bit lazy but for folders there won't be anything to use to say models from server are new, so set an isnew property when loading models into a collectin
            return this.get('isNew');
        }
    });


    ECALENDAR.WeekSetTimeChangeCollection = Backbone.Collection.extend({
        model: ECALENDAR.WeekSetTimeChangeModel,
        parse: function (resp, xhr) {
            var returnValue = null, collection;
            if ((xhr !== null) && (xhr !== undefined)) {
                returnValue = ECALENDAR.DataProvider.parseCalendarMarkersFromXML(xhr.responseText);
            }
            return returnValue;
        },
        fetch: function (options) {
            (options || (options = {})).model = 'WeeksetTimeChanges';
            return Backbone.Collection.prototype.fetch.call(this, options);
        }
    });
});

