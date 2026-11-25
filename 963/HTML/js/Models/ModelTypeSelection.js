/*! - v1.0
* User selection Model 
*
* This model holds the information of the selection model in the current user interface. 
*
* Date: Wed May 16, 2012
* Copyright 2008-2012 Honeywell Technologies Sàrl, ECC Division. All rights reserved. Copyright 1995-2008 Trend Control Systems Ltd. 
*/

/*globals ECALENDAR*/
/*globals Backbone*/
/*globals $*/

$(function () {

    "use strict";

    ECALENDAR.ModelTypeSelection = Backbone.Model.extend({
        defaults: {
            //It holds the pointer of the diary group, which is currently selected.           
            type: "week"

        },
        initialize: function () {

        }
    });

    //Create a global diary group selection model here.
    ECALENDAR.modelTypeSelection = new ECALENDAR.ModelTypeSelection();
});