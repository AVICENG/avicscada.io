/*globals ECALENDAR*/
/*globals Backbone*/
/*globals $ */

$(function() {
    "use strict";

    ECALENDAR.ConflictDiaryGroupModel = Backbone.Model.extend({
        defaults: {
            groupId: -1,
            replace: -1
        },
        isNew: function() {
            return this.get('replace') === this.defaults.replace;
        }
    });

    ECALENDAR.ConflictDiaryGroupCollection = Backbone.Collection.extend({
        model: ECALENDAR.ConflictDiaryGroupModel,
        getNewConflicts: function() {
            return this.where({ replace: ECALENDAR.ConflictDiaryGroupModel.prototype.defaults.replace });
        }
    });

    ECALENDAR.ImportTimeSchemeModel = Backbone.Model.extend({
        defaults: {
            //This should not be in the Diary model, put it here as long as we only have 1 model.
            groupId: -1,
            timeSchemeId: null,
            isWeekset: 1,
            yesToAll: 0,
            noToAll: 0,
            replaceList: null
        },
        initialize: function(options) {
            if (this.get('replaceList') === this.defaults.replaceList) {
                this.set('replaceList', new ECALENDAR.ConflictDiaryGroupCollection());
            }
        }
    });
});