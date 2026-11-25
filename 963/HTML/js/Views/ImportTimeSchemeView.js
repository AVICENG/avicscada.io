/*globals ECALENDAR*/
/*globals Backbone*/
/*globals _*/
/*globals $ */
/*globals Modernizr*/



$(function () {
    "use strict";
    ECALENDAR.ImportTimeSchemeView = Backbone.View.extend({

        className: 'wizard',
        template: _.template('<div class="row-fluid" id="importWeeksetView">' +
        '<div class="span6"><div id="diaryExplorer"><div id="treeView" class="filetree"></div></div></div>' +
        '<div class="span6"><form class="form-inline">' +
        '<label class="radio span6"  for="importWeekSets"><input type="radio"  name="importType" value="week" id="importWeekSets" /><%= displayweeksets %></label>' +
        '<label  class="radio span6" for="importSpecialDays"><input type="radio" name="importType" value="day" id="importSpecialDays" /><%= displayspecialdays %></label>' +
        '</form><div id="weeksets"></div></div>' +
        '</div>' +
        '<div class="btn-row wizard-buttons"><button class="btn btn-primary btn-finish" disabled="disabled"><%= ok_text %></button><button class="btn btn-cancel"><%= cancel_text %></button></div>'),
        viewType: "week",
        groupId: -1,
        specialDays: null,
        weekSets: null,
        events: {
            'click .btn-row': '_buttonClickHandler',
            'change input[name=importType]': '_updateViewType'
        },
        render: function () {
            // create the wizard html that will contain the views.
            var diaryCollection = new ECALENDAR.DiaryCollection(ECALENDAR.diaryCollectionObject.models);

            this.$el.html(this.template({
                ok_text: ECALENDAR.ApplicationStrings.getResourceFromID("OK"),
                cancel_text: ECALENDAR.ApplicationStrings.getResourceFromID("BTN_CANCEL"),
                displayweeksets: ECALENDAR.ApplicationStrings.getResourceFromID("DISPLAY_WEEK_SETS"),
                displayspecialdays: ECALENDAR.ApplicationStrings.getResourceFromID("DISPLAY_SPECIAL_DAYS")
            }));

            this.$('input[value="' + this.viewType + '"]').attr('checked', true);

            if (!this._importingOnFolder()) {
                diaryCollection.remove(ECALENDAR.DiaryGroupSelection.get('diaryGroup'));
            }

            this.diaryView = new ECALENDAR.DisplayDiaryView({
                el: this.$('#diaryExplorer'),
                model: diaryCollection,
                diaryGroupSelection: new ECALENDAR.DiaryGroupSelectionModel()
            });

            this.diaryView.options.diaryGroupSelection.bind('change', this._diaryUpdated, this);

            this.timeSchemeView = new ECALENDAR.TimeSchemeView({
                selectDefault: false,
                el: this.$('#weeksets'),
                model: new Backbone.Collection(),
                timeSchemeSelection: new ECALENDAR.TimeSchemeSelectionModel()
            });

            this.timeSchemeView.options.timeSchemeSelection.bind('change', this._timeSchemeUpdated, this);

            this.$el.dialog({
                height: 540,
                width: 700,
                resizable: false,
                draggable: true,
                modal: true,
                title: ECALENDAR.ApplicationStrings.getResourceFromID('IMPORT_WEEKSET')
            });

            this.$el.bind("dialogclose", _.bind(function () {
                this.$el.unbind('dialogclose');
                this._destroyView();
            }, this));
        },
        initialize: function () {
            if (ECALENDAR.modelTypeSelection) {
                this.viewType = ECALENDAR.modelTypeSelection.get('type') || "week";
            }
            this.render();
            this.specialDays = new ECALENDAR.SpecialDayCollection();
            this.weekSets = new ECALENDAR.WeekSetCollection();

            this.specialDays.bind('reset', this._resetTimeSchemeView, this);
            this.weekSets.bind('reset', this._resetTimeSchemeView, this);

        },
        _destroyView: function () {
            this.$el.dialog('destroy').remove();
        },
        _closeDialog: function () {
            $(this).dialog('close');
        },
        _diaryUpdated: function (model) {
            this.groupId = model.get('diaryGroup').get('diaryID');
            this._abortExistingRequest();
            this.weekSets.reset();
            this.weekSets.options.diaryGroup = model.get('diaryGroup');
            this.specialDays.reset();
            this.specialDays.options.diaryGroup = model.get('diaryGroup');
            this._clearTimeScheme();

            if (model.get('diaryGroup').get('isFolder') !== true) {
                this._updateViewType({ target: this.$(':checked').get(0) });
            }

        },

        _clearTimeScheme: function () {
            this.timeSchemeView.options.timeSchemeSelection.set('timeScheme', null);
        },
        _resetTimeSchemeView: function (model, resp) {
            this.timeSchemeView.model.reset(model.models);
        },
        _timeSchemeUpdated: function (model) {
            if (model.get('timeScheme') === null) {
                this._disableView();
            }
            else {
                this._enableView();
            }
        },
        _enableView: function () {
            this.$('.btn-finish').removeAttr('disabled');
        },
        _disableView: function () {
            this.$('.btn-finish').attr('disabled', 'disabled');
        },
        _abortExistingRequest: function () {
            if (this.request && this.request.readyState !== 4) {
                this.request.abort();
            }
        },
        _updateViewType: function (event) {
            this._clearTimeScheme();
            var triggerComplete = function () {
                this.timeSchemeView.hideLoading();
            }, sendingData = function () {
                this.timeSchemeView.showLoading();
            };
            if (event.target.checked) {
                this._abortExistingRequest();
                this.viewType = event.target.value;

                if (this.diaryView.options.diaryGroupSelection.get('diaryGroup') === null || this.diaryView.options.diaryGroupSelection.get('diaryGroup').get('isFolder') === true) {
                    //nothing selected, don't do anything.
                    // Folder selected, timeschemes are empty already (diarygroup change event) don't fill it with a fetch
                    return;
                }

                if (event.target.value == "day") {
                    this.$el.dialog('option', 'title', ECALENDAR.ApplicationStrings.getResourceFromID('IMPORT_SPECIAL_DAY'));
                    if (this.specialDays.length === 0) {
                        this._resetTimeSchemeView({ models: [] }, null);

                        sendingData.call(this);
                        this.request = this.specialDays.fetch({ model: 'SpecialDays', diaryId: this.groupId, success: _.bind(triggerComplete, this), error: _.bind(triggerComplete, this) });

                    }
                    else {
                        this._resetTimeSchemeView(this.specialDays, null);
                    }
                }
                else {
                    this.$el.dialog('option', 'title', ECALENDAR.ApplicationStrings.getResourceFromID('IMPORT_WEEKSET'));
                    if (this.weekSets.length === 0) {
                        this._resetTimeSchemeView({ models: [] }, null);

                        sendingData.call(this);
                        this.request = this.weekSets.fetch({ model: 'Weeksets', diaryId: this.groupId, success: _.bind(triggerComplete, this), error: _.bind(triggerComplete, this) });

                    }
                    else {
                        this._resetTimeSchemeView(this.weekSets, null);
                    }
                }
            }
        },
        _buttonClickHandler: function (e) {
            var $e;

            $e = $(e.target).closest('button');

            if ($e.length === 0) {
                return;
            }
            if ($e.hasClass('btn-cancel')) {
                this.$el.dialog('close');
                return;
            }

            if ($e.hasClass('btn-finish')) {
                this._confirmUserWantsToImportSelection();
            }


        },
        _confirmUserWantsToImportSelection: function () {
            var self = this;
            this._closeDialog.call(this.el);

            var continueImportingSelection = function (event) {
                self._closeDialog.call(this);
                self._checkAssociatedZones();
            };

            var buttons = [{
                text: ECALENDAR.ApplicationStrings.getResourceFromID('YES'),
                id: 'btnYes',
                click: continueImportingSelection
            }, {
                text: ECALENDAR.ApplicationStrings.getResourceFromID('NO'),
                id: 'btnNo',
                click: this._closeDialog
            }
            ];

            this.global_dispatcher.trigger('warning',
            ECALENDAR.ApplicationStrings.getResourceFromID('IMPORT_TIMESCHEME') + this._timeSchemeSelection().get('label'),
            {
                title: ECALENDAR.ApplicationStrings.getResourceFromID('ARE_YOU_SURE'),
                buttons: buttons
            });

        },
        _timeSchemeSelection: function () {
            return this.timeSchemeView.options.timeSchemeSelection.get('timeScheme');
        },
        _askUserToOverwriteTimescheme: function (conflicts, index) {
            //model = iterator (should be individual replace confliect element)
            //self = this = the view context
            // therefore self.model = the full import model
            var self, buttons, title, yesButton, noButton, yesAllButton, noAllButton, cancelButton;

            if (index === conflicts.length) {
                this._importTimeScheme();
                return;
            }

            self = this;

            yesButton = {
                text: ECALENDAR.ApplicationStrings.getResourceFromID('YES'),
                click: function () {
                    conflicts[index].set({ replace: 1 });
                    self._closeDialog.call(this);
                    self._askUserToOverwriteTimescheme(conflicts, index += 1);
                }
            };
            noButton = { text: ECALENDAR.ApplicationStrings.getResourceFromID('NO'),
                click: function () {
                    conflicts[index].set({ replace: 0 });
                    self._closeDialog.call(this);
                    self._askUserToOverwriteTimescheme(conflicts, index += 1);
                }
            };
            yesAllButton = {
                text: ECALENDAR.ApplicationStrings.getResourceFromID('YES_TO_ALL'),
                click: function () {
                    self.model.set({ yesToAll: 1, noToAll: 0 });
                    self._closeDialog.call(this);
                    self._importTimeScheme();

                }
            };
            noAllButton = {
                text: ECALENDAR.ApplicationStrings.getResourceFromID('NO_TO_ALL'),
                click: function () {
                    self.model.set({ yesToAll: 0, noToAll: 1 });
                    self._closeDialog.call(this);
                    self._importTimeScheme();
                }
            };
            cancelButton = {
                text: ECALENDAR.ApplicationStrings.getResourceFromID('BTN_CANCEL'),
                click: function () {
                    self.model = null;
                    self._closeDialog.call(this);
                }
            };


            buttons = [yesButton, yesAllButton, noButton, noAllButton, cancelButton];

            title = ECALENDAR.ApplicationStrings.getResourceFromID('DIARY_CONTAINS_TIMESCHEME').replace('%1', '"' + ECALENDAR.diaryCollectionObject.getModelFromId(conflicts[index].get('groupId')).get('label') + '"').replace('%2', '"' + this.timeSchemeView.options.timeSchemeSelection.get('timeScheme').get('label') + '"');
            title += "<br />";
            title += ECALENDAR.ApplicationStrings.getResourceFromID('DIARY_REPLACE_EXISTING');

            this.global_dispatcher.trigger('warning', title, {
                title: ECALENDAR.ApplicationStrings.getResourceFromID('CONFIRM_TIMESCHEME_REPLACE'),
                buttons: buttons,
                width: 400
            });

        },
        _checkGrouphasLabelAlready: function () {
            if (this._groupHasTimeschemeLabel()) {
                this._askUserToOverwriteTimescheme(this._timeSchemeSelection());
            }
            else {
                this._checkAssociatedZones();
            }
        },
        _checkAssociatedZones: function () {
            if (ECALENDAR.DiaryGroupSelection.get('diaryGroup').get('isAssociatedWithTimeZones')) {
                this.global_dispatcher.trigger('download', _.bind(this._importTimeScheme, this));
            }
            else {
                this._importTimeScheme();
            }
        },
        _groupHasTimeschemeLabel: function () {
            if (this._importingOnFolder()) {
                // let the server find the clashes.
                return false;
            }
            if (this._isSpecialDay()) {
                return (ECALENDAR.specialDayCollection.where({ label: this._timeSchemeSelection().get('label') }).length > 0);
            }
            else {
                return (ECALENDAR.weekSetCollection.where({ label: this._timeSchemeSelection().get('label') }).length > 0);
            }
        },
        _isSpecialDay: function () {
            return this.viewType === "day";
        },
        _importingOnFolder: function () {
            return (ECALENDAR.DiaryGroupSelection.get('diaryGroup').get('isFolder') === true);
        },
        _importTimeScheme: function () {
            var self = this,
            sendingComplete = function () {
                this.global_dispatcher.trigger('sending_data_complete');
            },
            callbacks = {
                success: function (model, response) {
                    sendingComplete.call(model);
                    model.global_dispatcher.trigger('view_messaging:timeSchemeUpdated');
                },
                error: function (model, response) {


                    //In case if some error appears at server, it is being sent in XML as <Error> error-description </Error>
                    //If there is no error message as response - it means server has succeesully completed the request.
                    var xmlDoc, $xmlDoc, errorMsg = null, conflicts;
                    if ((response !== null) && (response !== undefined)) {
                        if (response.responseText != null && response.responseText !== "") {
                            xmlDoc = $.parseXML(response.responseText);
                            $xmlDoc = $(xmlDoc);
                            if ($xmlDoc.find("ConflictDiaryGroupCollection").length !== 0) {

                                model.get('replaceList').reset(ECALENDAR.DataProvider.parseGroupReplaceConflictFromXml($xmlDoc.find("ConflictDiaryGroupCollection")));
                                conflicts = model.get('replaceList').getNewConflicts();

                                if (conflicts.length > 0) {
                                    self._askUserToOverwriteTimescheme(conflicts, 0);
                                    return;
                                }
                            }
                            else {
                                errorMsg = $xmlDoc.find("Error").text();
                            }
                        }
                    }
                    sendingComplete.call(model);
                    if (errorMsg === null || errorMsg.length === 0) {
                        //It seems a communication error or might be server not available error.
                        self.global_dispatcher.trigger('user_messaging', [ECALENDAR.ApplicationStrings.getResourceFromID("SEND_DATA_ERROR")]);
                    } else {
                        self.global_dispatcher.trigger('user_messaging', [errorMsg]);
                    }

                }
            },
            selection = this._timeSchemeSelection();
            if (selection) {
                (this.model || (this.model = new ECALENDAR.ImportTimeSchemeModel({
                    timeSchemeId: selection.id,
                    groupId: selection.get('groupId'),
                    isWeekset: ((selection instanceof ECALENDAR.SpecialDayModel) ? 0 : 1)
                })
                )).save(null, _.extend({ groupId: ECALENDAR.DiaryGroupSelection.get('diaryGroup').get('diaryID') }, callbacks));
            }
        }
    });
});