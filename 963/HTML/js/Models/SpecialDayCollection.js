/*globals ECALENDAR*/
/*globals Backbone*/
/*globals _*/
/*globals $ */

$(function () {
    "use strict";

    ECALENDAR.SpecialDayCollection = Backbone.Collection.extend({
        model: ECALENDAR.SpecialDayModel,
        initialize: function (options) {
            if (!options) {
                this.options = {};
            }
        },
        doesLabelExist: function (label) {
            var i, weekSetModel;
            for (i = 0; i < this.models.length; i += 1) {
                weekSetModel = this.models[i];
                if (weekSetModel.get("label").toLowerCase() === label.toLowerCase()) {
                    return true;
                }
            }
            return false;
        },

        doesIDExist: function (id) {
            return this.get(id) !== undefined;

        },

        parse: function (resp, xhr) {
            var returnValue = null, collection;
            if ((xhr !== null) && (xhr !== undefined)) {
                returnValue = ECALENDAR.DataProvider.parseSpecialDayCollectionFromXML(xhr.responseText, this.options.diaryGroup);
            }
            return returnValue;
        }
    });
});