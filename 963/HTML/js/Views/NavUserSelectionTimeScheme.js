/*! - v1.0
*/

/*globals ECALENDAR*/
/*globals Backbone*/
/*globals _*/
/*globals $ */

$(function () {
    "use strict";
    ECALENDAR.NavUserSelectionTimeScheme = Backbone.View.extend({

        events: {
            "click #newWeekSet": "newWeeksetForEdit",
            "click #editWeekSet": "editWeekset",
            "click #deleteWeekSet": "deleteWeekset",
            "click #importweekset": "_importWeeksetDialog",
            "click #whereused": "showWhereUsed"
        },
        template: '<span class="btn-group-container"><button id="newWeekSet" class="btn" disabled="disabled" ><%= name %></button><button id="editWeekSet" class="btn" disabled="disabled"><%= edit %></button><button id="deleteWeekSet" class="btn" disabled="disabled"><%= delete_text %></button></span><span class="btn-group-container"><button class="btn" id="importweekset" disabled="disabled"><%= import_timescheme %></button><button id="whereused" disabled="disabled" class="btn"><%= where_used %></button></span>',
        weeksetButton: $(),
        editWeeksetButton: $(),
        deleteWeeksetButton: $(),
        importWeeksetButton: $(),
        whereUsedButton: $(),
        initialize: function (options) {
            if (!options.el) {
                this.$el = $('#NavUserSelectionTimeSchemeElement');
                this.el = this.$el.get(0);
            }

            this.options.modelTypeSelection = this.options.modelTypeSelection || ECALENDAR.modelTypeSelection;

            if (!this.options.timeSchemeSelection) {
                this.options.timeSchemeSelection = ECALENDAR.TimeSchemeSelection;
            }

            this.$el.append(_.template((this.options.template || this.template),
            {
                name: ECALENDAR.ApplicationStrings.getResourceFromID("New"),
                edit: ECALENDAR.ApplicationStrings.getResourceFromID("Edit"),
                delete_text: ECALENDAR.ApplicationStrings.getResourceFromID("Delete"),
                import_timescheme: ECALENDAR.ApplicationStrings.getResourceFromID("IMPORT_TIME_SCHEME"),
                where_used: ECALENDAR.ApplicationStrings.getResourceFromID("WHERE_TIMES_USED")
            }));
            this.weeksetButton = this.$('#newWeekSet');
            this.editWeeksetButton = this.$('#editWeekSet');
            this.deleteWeeksetButton = this.$('#deleteWeekSet');
            this.importWeeksetButton = this.$('#importweekset');
            this.whereUsedButton = this.$('#whereused');
           // this.model.bind('change', this.selectionChanged, this); // this is ECALENDAR.DiaryGroupSelection
            this.options.timeSchemeSelection.bind('change', this.selectionChanged, this);

            if (this.global_dispatcher) {
                this.global_dispatcher.bind('sending_data_complete:weekSetCollection:fetch', this.selectionChanged, this);
                this.global_dispatcher.bind('sending_data:weekSetCollection:fetch', this.disableButtons, this);
            }

        },
        disableButtons: function () {
            this.weeksetButton.attr("disabled", true);
            this.editWeeksetButton.attr("disabled", true);
            this.deleteWeeksetButton.attr("disabled", true);
            this.importWeeksetButton.attr("disabled", true);
            this.weeksetButton.attr("disabled", true);
            this.whereUsedButton.attr("disabled", true);
        },
        newWeeksetForEdit: function () {
            var weekset, editTimeScheme;
            weekset = new ECALENDAR[(this.options.modelTypeSelection.get('type') === 'day') ? "SpecialDayModel" : "WeekSetModel"]();
            editTimeScheme = new ECALENDAR.EditTimeSchemeView({ model: weekset, callback: _.bind(this.HandleChildNotification, this) });
            this.weeksetButton.attr("disabled", true);
            return false;
        },
        editWeekset: function () {
            var editTimeScheme, self = this;
            // you should clone the model here, but backbone doesn't deep clone. i.e. activation array is defaults not set values.            
            if (this.options.timeSchemeSelection.get('timeScheme')) {
                if (this.options.timeSchemeSelection.get('timeScheme').isUsedInException()) {
                    //Warning message to the user: time scheme is already used for exception, do the user still want to show the message box.
                    var options = { title: ECALENDAR.ApplicationStrings.getResourceFromID('TITLE_PLEASE_CONFIRM') };
                    var buttons = {};
                    buttons[ECALENDAR.ApplicationStrings.getResourceFromID('YES')] = function (event) {
                        $(this).dialog("close");
                        editTimeScheme = new ECALENDAR.EditTimeSchemeView({
                            model: self.options.timeSchemeSelection.get('timeScheme'),
                            callback: function () { }
                        });
                    };
                    buttons[ECALENDAR.ApplicationStrings.getResourceFromID('NO')] = function () {
                        $(this).dialog("close");
                    };
                    options.buttons = buttons;
                    this.global_dispatcher.trigger('warning', ECALENDAR.ApplicationStrings.getResourceFromID('EDIT_TIMESCHEME_ARE_YOU_SURE'), options);
                }
                else {
                    editTimeScheme = new ECALENDAR.EditTimeSchemeView({
                        model: self.options.timeSchemeSelection.get('timeScheme'),
                        callback: function () { }
                    });
                }
            }
            return false;
        },
        destroyWeekset: function () {
            var self = this;
            this.global_dispatcher.trigger('sending_data');
            this.options.timeSchemeSelection.get('timeScheme').destroy({
                success: function (model, resp) {
                    model.set('timeScheme', null);
                    self.global_dispatcher.trigger('sending_data_complete', model);
                    self.global_dispatcher.trigger('view_messaging:timeSchemeUpdated', model);
                },
                error: function (model, resp) {
                    if (self.global_dispatcher != null) {

                        //In case if some error appears at server, it is being sent in XML as <Error> error-description </Error>
                        //If there is no error message as response - it means server has succeesully completed the request.
                        var xmlDoc, $xmlDoc, errorMsg = null;
                        if (resp != null) {
                            if (resp.responseText != null && resp.responseText !== "") {
                                xmlDoc = $.parseXML(resp.responseText);
                                $xmlDoc = $(xmlDoc);
                                errorMsg = $xmlDoc.find("Error").text();
                            }
                        }
                        if (errorMsg === null || errorMsg.length === 0) {
                            //It seems a communication error or might be server not available error.
                            self.global_dispatcher.trigger('user_messaging', [ECALENDAR.ApplicationStrings.getResourceFromID("SEND_DATA_ERROR")]);
                        } else {
                            self.global_dispatcher.trigger('user_messaging', [errorMsg]);
                            self.global_dispatcher.trigger('view_messaging:timeSchemeUpdated', model);
                        }
                        self.global_dispatcher.trigger('sending_data_complete', model);
                    }
                }
            });
        },
        deleteWeekset: function () {
            var options = { title: ECALENDAR.ApplicationStrings.getResourceFromID('TITLE_PLEASE_CONFIRM') };
            var buttons = {}, self = this;
            buttons[ECALENDAR.ApplicationStrings.getResourceFromID('YES')] = function (event) {
                var filter = {}, whereused = [], isDefault = false, onlyWeekset = false;
                $(this).dialog("close");
                if (self.options.timeSchemeSelection.get('timeScheme')) {
                    if (self.options.timeSchemeSelection.get('timeScheme') instanceof ECALENDAR.SpecialDayModel) {
                        filter.specialDayID = self.options.timeSchemeSelection.get('timeScheme').id;
                    }
                    else {
                        filter.weeksetID = self.options.timeSchemeSelection.get('timeScheme').id;
                        onlyWeekset = (ECALENDAR.weekSetCollection.length == 1) ? true : false;
                        isDefault = self.options.timeSchemeSelection.get('timeScheme').get('isDefault');
                    }
                    whereused = ECALENDAR.exceptionCollection.where(filter);
                    if (whereused.length > 0) {
                        self.global_dispatcher.trigger('view_messaging:timeSchemeUpdated');
                        self.global_dispatcher.trigger('user_messaging', ECALENDAR.ApplicationStrings.getResourceFromID('EXCEPTION_USED'));
                    } else if (onlyWeekset === true) {
                        self.global_dispatcher.trigger('view_messaging:timeSchemeUpdated');
                        self.global_dispatcher.trigger('user_messaging', ECALENDAR.ApplicationStrings.getResourceFromID('ONLY_SINGLE_DEFAULT_WEEKSET_DELETE'));
                    }
                    else if (isDefault === true) { //Currently, we are trying to delete the default weekset of the diary group, please take the details of the new default weekset from the user.
                        var changeTimeSchemeOptions = { title: ECALENDAR.ApplicationStrings.getResourceFromID('TITLE_PLEASE_CONFIRM') };
                        var changeTimeSchemeButtons = {};
                        changeTimeSchemeButtons[ECALENDAR.ApplicationStrings.getResourceFromID('YES')] = function (event) {
                            $(this).dialog('close');
                            var view = new ECALENDAR.ChangeDefaultTimeSchemeView({ model: self.options.timeSchemeSelection.get('timeScheme') });
                        };
                        changeTimeSchemeButtons[ECALENDAR.ApplicationStrings.getResourceFromID('NO')] = function (event) {
                            $(this).dialog('close');
                        };
                        changeTimeSchemeOptions.buttons = changeTimeSchemeButtons;
                        self.global_dispatcher.trigger('warning', ECALENDAR.ApplicationStrings.getResourceFromID('DEFAULT_WEEKSET_DELETE'), changeTimeSchemeOptions);
                    }
                    else {
                        self.destroyWeekset();
                    }
                }
            };
            buttons[ECALENDAR.ApplicationStrings.getResourceFromID('NO')] = function () {

                $(this).dialog("close");
            };
            options.buttons = buttons;
            this.global_dispatcher.trigger('warning', ECALENDAR.ApplicationStrings.getResourceFromID('ARE_YOU_SURE'), options);
            return false;
        },
        //Handle the Cancel button responces
        HandleChildNotification: function () {
            this.weeksetButton.removeAttr("disabled");
        },

        selectionChanged: function () {
            var diaryGroup = ECALENDAR.DiaryGroupSelection.get("diaryGroup"),
           timeScheme = this.options.timeSchemeSelection.get('timeScheme') || null;

            this.disableButtons();
            if (timeScheme && diaryGroup && diaryGroup.get('isFolder') === false) {
                this.whereUsedButton.removeAttr('disabled');
            }

            if (ECALENDAR.canConfigureActivationTimes && ECALENDAR.hasFullWebAccess) {

                if (diaryGroup !== null) {
                    this.importWeeksetButton.removeAttr('disabled');
                    if (diaryGroup.attributes.isFolder !== true) {
                        this.weeksetButton.removeAttr("disabled");
                        if (timeScheme) {
                            this.editWeeksetButton.removeAttr("disabled");
                            this.deleteWeeksetButton.removeAttr("disabled");
                        }
                    }
                }
            }
        },
        _importWeeksetDialog: function (event) {
            var importView = new ECALENDAR.ImportTimeSchemeView();
            return false;
        },
        showWhereUsed: function () {
            var self = this;

            function showWhereUsedDialog() {
                ECALENDAR.exceptionCollection.global_dispatcher.unbind('sending_data_complete:exceptionCollection:fetch', showWhereUsedDialog, this);
                var view = new ECALENDAR.ExceptionListView({ model: self.options.timeSchemeSelection.get('timeScheme') });
                view.dialog();
            }


            ECALENDAR.exceptionCollection.global_dispatcher.bind('sending_data_complete:exceptionCollection:fetch', showWhereUsedDialog, this);
            ECALENDAR.ExceptionListView.prototype.reloadExceptions(ECALENDAR.DiaryGroupSelection.get('diaryGroup').get('diaryID'));


            return false;
        }
    });
});