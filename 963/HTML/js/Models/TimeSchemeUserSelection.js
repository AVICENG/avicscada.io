/*! - v1.0
* Time Scheme User selection Model 
*
* This model holds the information of the time scheme selection model in the current user interface. 
*
* Date: Tue July 10, 2012
* Copyright 2008-2012 Honeywell Technologies Sàrl, ECC Division. All rights reserved. Copyright 1995-2008 Trend Control Systems Ltd. 
*/

/*globals ECALENDAR*/
/*globals Backbone*/
/*globals $*/

$(function () {

    "use strict";

    ECALENDAR.TimeSchemeSelectionModel = Backbone.Model.extend({
        defaults: {
            //It holds the pointer of the time scheme, which is currently selected.           
            timeScheme: null

        },
        initialize: function () {

        },
        validate: function (attrs) {
            if (attrs.hasOwnProperty('timeScheme') && attrs.timeScheme === undefined) {
                return 'Attribute time scheme must exist.';
            }
        }
    });

    //Create a global time scheme selection model here.
    ECALENDAR.TimeSchemeSelection = new ECALENDAR.TimeSchemeSelectionModel();
});