/*globals ECALENDAR*/
/*globals Backbone*/
/*globals $ */

$(function() {
    "use strict";
    ECALENDAR.TabModel = Backbone.Model.extend({
        defaults: {
            tabText: '',
            view: '',
            viewparams: {}

        }
    });

    ECALENDAR.TabCollection = Backbone.Collection.extend({
        model: ECALENDAR.TabModel
    });
});