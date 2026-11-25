/*globals ECALENDAR*/
/*globals Backbone*/
/*globals $*/

$(function() {
    "use strict";

    ECALENDAR.DisplayTimeSchemeView = Backbone.View.extend({

        initialize: function(options) {

            if (options && !options.el) {
                this.$el = $("#DisplayTimeSchemeViewElement");
                this.el = this.$el.get(0);
            }

            this.model.bind('change', function(m, o) {
                return function() {
                    m.apply(o, Array.prototype.slice.call(arguments));
                };
            } (this.selectionChanged, this));
            this.$el.activationTimePlanner({ isEditable: false });
            if (options.diaryGroupSelection) {
                options.diaryGroupSelection.bind('change', $.proxy(function() {
                    this.$el.addClass('loading');
                }, this));
            }
        },


        selectionChanged: function() {

            this.$el.removeClass('loading');
            var timeScheme = this.model.get('timeScheme');

            if ((timeScheme !== null) && (ECALENDAR.DiaryGroupSelection.get("diaryGroup").get("isFolder") === false)) {
                this.$el.removeClass('disabled').activationTimePlanner('setWeeksetDataModel', this.model.get('timeScheme'));
            }
            else {
                this.$el.addClass('disabled');
            }
        }
    });
});