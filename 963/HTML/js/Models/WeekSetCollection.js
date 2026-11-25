/*globals ECALENDAR*/
/*globals Backbone*/
/*globals _*/
/*globals $ */

$(function() {
    "use strict";

    ECALENDAR.WeekSetCollection = Backbone.Collection.extend({
        model: ECALENDAR.WeekSetModel,


        initialize: function(options) {
            if (!options) {
                this.options = {};
            }
            //Initialization operation goes here.
            var weekSetModel = new ECALENDAR.WeekSetModel({ weekSetID: -1 });
            this.add(weekSetModel);
        },

        getDefaultWeekSet: function() {
            var defaults = this.where({ isDefault: true });
            if (defaults.length > 0) {
                return defaults[0];
            }
            return null;
        },

        getWeekSetModelFromID: function(id) {
            var i, weekSetModel;
            for (i = 0; i < this.models.length; i += 1) {
                weekSetModel = this.models[i];
                if (weekSetModel.get("weekSetID") === id) {
                    return weekSetModel;
                }
            }
            return null;
        },

        doesLabelExist: function(label, model) {
            var i, weekSetModel;
            model = model || new ECALENDAR.WeekSetModel();
            for (i = 0; i < this.models.length; i += 1) {
                weekSetModel = this.models[i];
                if (weekSetModel.get("label").toLowerCase() === label.toLowerCase()) {
                    if (model.isNew() || model.id !== weekSetModel.id) {
                        return true;
                    }
                }
            }
            return false;
        },

        doesIDExist: function(id) {
            var i, weekSetModel;
            for (i = 0; i < this.models.length; i += 1) {
                weekSetModel = this.models[i];
                if (weekSetModel.get("weekSetID") === id) {
                    return true;
                }
            }
            return false;
        },

        parse: function(resp, xhr) {
            var returnValue = null, weeksetCollection;
            if ((xhr !== null) && (xhr !== undefined)) {
                weeksetCollection = ECALENDAR.DataProvider.generateWeeksetCollectionFromXML(xhr.responseText, this.options.diaryGroup);
                if ((weeksetCollection !== null) && (weeksetCollection !== undefined)) {
                    returnValue = weeksetCollection.models;
                }
            }
            return returnValue;
        }
    });
});