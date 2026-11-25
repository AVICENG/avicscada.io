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

    ECALENDAR.DiaryGroupSelectionModel = Backbone.Model.extend({
        defaults: {
            //It holds the pointer of the diary group, which is currently selected.           
            diaryGroup: null

        },
        initialize: function () {

        },
        validate: function (attrs) {
            if (attrs.hasOwnProperty('diaryGroup') && attrs.diaryGroup === undefined) {
                return 'Attribute diary group must exist.';
            }
        }
    });

    //Create a global diary group selection model here.
    ECALENDAR.DiaryGroupSelection = new ECALENDAR.DiaryGroupSelectionModel();
});