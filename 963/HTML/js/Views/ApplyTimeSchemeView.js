/*globals ECALENDAR*/
/*globals Backbone*/
/*globals _*/
/*globals $ */

$(function () {
    "use strict";
    //todo: inject models instead of relying on the global variables.
    ECALENDAR.ApplyTimeSchemeView = Backbone.View.extend({
        template: _.template('<div><%= date %></div><div id="SpecialDayList"></div><div id="WeekSetList"></div>'),
        initialize: function (options) {

            this.options.timeSchemeSelection = this.options.timeSchemeSelection || ECALENDAR.TimeSchemeSelection;
          
        },
        render: function () {
            var weekSets = new Backbone.Collection(ECALENDAR.weekSetCollection.models);
            var defaultWeek = ECALENDAR.weekSetCollection.where({ isDefault: true });
            var date = this.model.get('startDate').toLocaleDateString();
            if (defaultWeek.length > 0) {
                weekSets.remove(defaultWeek);
            }
            if (weekSets.length === 0 && ECALENDAR.specialDayCollection.length === 0) {
                this._showCannotUseApplyTimeScheme();
                return;
            }

            if (this.model.get('startDate').getTime() !== this.model.get('endDate').getTime()) {
                date += " - " + this.model.get('endDate').toLocaleDateString();
            }

            this.$el.html(this.template({ date: date }));

            this.weeksetList = new ECALENDAR.TimeSchemeView({ selectDefault: false, title: ECALENDAR.ApplicationStrings.getResourceFromID('APPLY_TIMESCHEME_WEEKSETS'), el: this.$('#WeekSetList'), model: weekSets, timeSchemeSelection: this.options.timeSchemeSelection });
            this.specialDayList = new ECALENDAR.TimeSchemeView({ selectDefault: false, title: ECALENDAR.ApplicationStrings.getResourceFromID('APPLY_TIMESCHEME_SPECIALDAYS'), el: this.$("#SpecialDayList"), model: ECALENDAR.specialDayCollection, timeSchemeSelection: this.options.timeSchemeSelection });

            return this;
        },
        _showCannotUseApplyTimeScheme: function () {
            this.trigger('No timeschemes');
            this.global_dispatcher.trigger('info', ECALENDAR.ApplicationStrings.getResourceFromID('CANNOT_USE_APPLY_TIMESCHEME'));
        }

    });
});