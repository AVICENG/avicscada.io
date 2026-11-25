/*!
*/

/*globals ECALENDAR*/
/*globals Backbone*/
/*globals $ */
/*globals _*/

$(function() {
    "use strict";

    ECALENDAR.TimeZoneModel = Backbone.Model.extend({
        defaults: {
            siteName: "",
            lanName: "",
            osName: "",
            zoneLabel: "",
            item: "",
            deviceType: ""
        }
    });

    ECALENDAR.TimeZoneCollection = Backbone.Collection.extend(
        {
            model: ECALENDAR.TimeZoneModel
        }

     );
});