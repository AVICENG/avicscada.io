/*globals ECALENDAR*/
/*globals Backbone*/
/*globals _*/
/*globals $ */

$(function () {
    "use strict";
    //todo: inject models instead of relying on the global variables.
    ECALENDAR.TimeSchemeContainerView = Backbone.View.extend({
        template: _.template('<form><div class="row-fluid"><div class="span8"><div id="TimeSchemeViewElement"></div><div id="NavUserSelectionTimeSchemeElement" class="row-fluid"></div></div>' +
                  '<div class="span4 timeSchemeTypeSelection" >' +
                  '<label class="radio"  for="DisplayWeekSets"><input type="radio"  name="timePeriodType" value="week" id="DisplayWeekSets" checked="checked" /><%= displayweeksets %></label>' +
                  '<label  class="radio" for="DisplaySpecialDays"><input type="radio" name="timePeriodType" value="day" id="DisplaySpecialDays" /><%= displayspecialdays %></label>' +
                  '<label for="DefaultTimeSchemeList"><%= default_time_text%></label><div id="DefaultTimeScheme"></div></div></div>' +
                  '<div class="row-fluid"><div class="span12"><div id="DisplayTimeSchemeViewElement" class="disabled"></div></div><div id="ChangeDefaultTimeScheme"></div>' +
                  '</div></form>',
                  {
                      default_time_text: ECALENDAR.ApplicationStrings.getResourceFromID('DEFAULT_TIME_SELECTION'),
                      displayweeksets: ECALENDAR.ApplicationStrings.getResourceFromID("DISPLAY_WEEK_SETS"),
                      displayspecialdays: ECALENDAR.ApplicationStrings.getResourceFromID("DISPLAY_SPECIAL_DAYS")
                  }),
        initialize: function (options) {

            this.options.timeSchemeSelection = this.options.timeSchemeSelection || ECALENDAR.TimeSchemeSelection;
            this.options.modelTypeSelection = this.options.modelTypeSelection || ECALENDAR.modelTypeSelection;



            function resetTimeSchemeView(model) {

                var type = 'week';
                if (model instanceof ECALENDAR.SpecialDayCollection) {
                    type = 'day';
                }
                if (type === this.options.modelTypeSelection.get('type')) {
                    this.timeSchemeView.model.reset(model.models);
                }
            }
            ECALENDAR.weekSetCollection.unbind('reset', resetTimeSchemeView, this);
            ECALENDAR.weekSetCollection.bind('reset', resetTimeSchemeView, this);

            ECALENDAR.specialDayCollection.unbind('reset', resetTimeSchemeView, this);
            ECALENDAR.specialDayCollection.bind('reset', resetTimeSchemeView, this);

            if (ECALENDAR.canConfigureActivationTimes === true && ECALENDAR.hasFullWebAccess === true) {
                $.contextMenu({
                    selector: '#DisplayTimeSchemeViewElement',
                    items: {
                        Edit: {
                            name: 'Edit',
                            callback: function (key, options) {
                                var editTimeScheme;
                                var data = options.$trigger.data('view');
                                if (data && data.model.get('timeScheme')) {
                                    editTimeScheme = new ECALENDAR.EditTimeSchemeView({
                                        model: data.model.get('timeScheme'),
                                        callback: function () { }
                                    });
                                }
                            }
                        }
                    }
                });
            }
            this.render();
        },
        events: {
            "change .radio input": "_updateViewType"
        },
        _updateViewType: function (event) {
            if (event.target.checked) {
                this.options.modelTypeSelection.set({ type: event.target.value });
                this.options.timeSchemeSelection.set('timeScheme', null);

                if (event.target.value == "day") {
                    this.timeSchemeView.model.reset(ECALENDAR.specialDayCollection.models);
                }
                else {
                    this.timeSchemeView.model.reset(ECALENDAR.weekSetCollection.models);
                }
            }
        },
        render: function () {

            this.$el.html(this.template);
            this.navUserSelectionTimeScheme = new ECALENDAR.NavUserSelectionTimeScheme({ el: this.$el.find("#NavUserSelectionTimeSchemeElement"), model: ECALENDAR.DiaryGroupSelection, modelTypeSelection: this.options.modelTypeSelection, timeSchemeSelection: this.options.timeSchemeSelection, template: this.options.navUserSelectionTemplate });
            this.timeSchemeView = new ECALENDAR.TimeSchemeView({ el: this.$el.find('#TimeSchemeViewElement'), model: new Backbone.Collection(), timeSchemeSelection: this.options.timeSchemeSelection });
            this.displayTimeSchemeView = new ECALENDAR.DisplayTimeSchemeView({ el: this.$el.find("#DisplayTimeSchemeViewElement"), model: this.options.timeSchemeSelection, diaryGroupSelection: ECALENDAR.DiaryGroupSelection });
            // keep a reference to the timescheme view for the context menu. Cannot use current context, because using menu within exception wizard (for example) can reference the wrong view instance.
            this.displayTimeSchemeView.$el.data('view', this.displayTimeSchemeView);

            var defaultTimeScheme = this.$('#DefaultTimeScheme');
            if (defaultTimeScheme.length > 0) {
                this.defaultTimeSchemeView = new ECALENDAR.DefaultTimeSchemeView({ el: defaultTimeScheme });
            }

            return this;
        }
    });

    ECALENDAR.ExceptionTimeSchemeView = ECALENDAR.TimeSchemeContainerView.extend({
        template: _.template('<form><div class="row-fluid"><div id="TimeSchemeViewElement" class="span6"></div><div id="NavUserSelectionTimeSchemeElement" class="span6 timeSchemeTypeSelection"><label class="radio"  for="Exception_DisplayWeekSets"><input type="radio"  name="timePeriodType" value="week" id="Exception_DisplayWeekSets"  /><%= displayweeksets %></label><label  class="radio" for="Exception_DisplaySpecialDays"><input type="radio" name="timePeriodType" value="day" id="Exception_DisplaySpecialDays" /><%= displayspecialdays %></label></div></div><div id="DisplayTimeSchemeViewElement" class="disabled"></div></form>', {
            displayweeksets: ECALENDAR.ApplicationStrings.getResourceFromID("DISPLAY_WEEK_SETS"),
            displayspecialdays: ECALENDAR.ApplicationStrings.getResourceFromID("DISPLAY_SPECIAL_DAYS")
        }),
        _updateViewType: function (event) {
            this.constructor.__super__._updateViewType.call(this, event);
            if (event.target.checked) {
                this.clearErrors();

            }

        },
        clearErrors: function () {
            this.$('.error').remove();
        },
        _showErrors: function (model, errors) {
            this.clearErrors();
            var controlgroup = $('<div class="error" ></div>');
            this.$el.prepend(controlgroup);
            _.each(errors, _.bind(function (error) {

                controlgroup.append('<span class="alert alert-error point-down"><button class="close" data-dismiss="alert">x</button>' + error.error + '</span>');

            }, this));
        },
        bindEvents: function () {
            this.model.bind('error', this._showErrors, this);
            this.clearErrors();
        },
        unbindEvents: function () {
            this.model.unbind('error', this._showErrors, this);
        },
        initialize: function (options) {
            if (!this.options.timeSchemeSelection) {
                this.options.timeSchemeSelection = new ECALENDAR.TimeSchemeSelectionModel();
                this.options.timeSchemeSelection.bind('change', function (model, o) {
                    if (model.get('timeScheme') === null) {
                        return;
                    }

                    var timeScheme = model.get('timeScheme'), attributes = {};
                    if (timeScheme !== null) {

                        attributes.timeschemelabel = timeScheme.get('label');

                        attributes.specialDayID = -1;
                        attributes.weeksetID = -1;
                        if (timeScheme instanceof ECALENDAR.SpecialDayModel) {
                            attributes.isWeekset = 0;
                            attributes.specialDayID = timeScheme.id || 0;
                        }
                        else {
                            attributes.isWeekset = 1;
                            attributes.weeksetID = timeScheme.id || 0;
                        }

                        if (this.model.length > 0) {
                            this.model.each(function (m) {

                                m.set(attributes, { silent: true });
                            });
                        } else {
                            this.model.add(new ECALENDAR.ExceptionModel(attributes), { silent: true });
                        }
                    }
                }, this);

            }

            options.modelTypeSelection = options.modelTypeSelection || new ECALENDAR.ModelTypeSelection({ type: "day" });


            var model = this.model.at(0), timeSchemeID, collectionToUse;
            if (!model.isNew()) {
                if ((model.get('specialDayID') > 0)) {
                    timeSchemeID = model.get('specialDayID');
                    collectionToUse = ECALENDAR.specialDayCollection;
                }

                else {
                    timeSchemeID = model.get('weeksetID');
                    collectionToUse = ECALENDAR.weekSetCollection;
                }
            }
            options.navUserSelectionTemplate = '<button id="newWeekSet" class="btn" disabled="disabled" ><%= name %></button><button id="editWeekSet" class="btn" disabled="disabled"><%= edit %></button>';

            this.constructor.__super__.initialize.call(this, options);
            // run the selection changed event handlers, there's not been a selection change but because its first load,
            // the change handlers need running to show current selection
            this.timeSchemeView.scrollIntoViewEnabled = true;

            if (collectionToUse) {
                var onReset = function () {

                    if (this.model.length > 0) {
                        this.model.unbind('reset', onReset, this);
                        this.setSelectedTimeSchemeById(timeSchemeID);
                    }
                };

                this.timeSchemeView.model.bind('reset', onReset, this.timeSchemeView);


                if (collectionToUse instanceof ECALENDAR.SpecialDayCollection) {
                    this._updateViewType({ target: this.$('#Exception_DisplaySpecialDays').attr("checked", true).get(0) });
                }
                else {
                    this._updateViewType({ target: this.$('#Exception_DisplayWeekSets').attr("checked", true).get(0) });
                }

            }
            else {
                this._updateViewType({ target: this.$('#Exception_DisplaySpecialDays').attr("checked", true).get(0) });
            }
            this.navUserSelectionTimeScheme.selectionChanged();
            this.bindEvents();
        }
    });


});