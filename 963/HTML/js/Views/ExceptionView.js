/*globals ECALENDAR*/
/*globals Backbone*/
/*globals _*/
/*globals $, setTimeout, document */

$(function () {
    "use strict";
    //todo: inject models instead of relying on the global variables.
    ECALENDAR.ExceptionView = Backbone.View.extend({
        initialize: function () {

            this.render();
            this.postponeDefaultTimeoutID = -1;
            var self = this;
            ECALENDAR.DiaryGroupSelection.bind('change', function (model) {
                if (ECALENDAR.canConfigureActivationTimes === true && ECALENDAR.hasFullWebAccess === true) {
                    this._enableButton(this._newExceptionButton);
                }

            }, this);

            ECALENDAR.weeksetTimeChanges.bind('reset', function () {
                self._addPostponedChanges.call(self.calendar, { dpDiv: self.calendar.$el });               
            });


            if ((ECALENDAR.canConfigureActivationTimes === true && ECALENDAR.hasFullWebAccess === true)) {
                $.contextMenu({
                    selector: '.exceptionMenu',
                    html5: true,
                    callback: function (key, options) {
                        switch (key) {
                            case "edit":
                                self._showEditExceptionWizard();
                                break;
                            case "deleteException":
                                self._deleteExceptions();
                                break;
                            case "apply":
                                self._showApplyTimeScheme();
                                break;
                        }
                    },
                    build: function ($trigger, e) {
                        return self._buildContextMenu();
                    }
                });

                $.contextMenu({
                    selector: '#Exceptions .datepicker-indicator',
                    items: {
                        deleteTooltip: {
                            name: ECALENDAR.ApplicationStrings.getResourceFromID('Delete'),
                            callback: function ($trigger, options) {
                                var id = options.$trigger.data('id');

                                function doDelete() {
                                    $(this).dialog('close');

                                    ECALENDAR.weeksetTimeChanges.global_dispatcher.trigger('sending_data');

                                    ECALENDAR.weeksetTimeChanges.getByCid(id).destroy(
                                    {
                                        success: function (model, resp) {
                                            var triggerComplete = function (model) {
                                                model.global_dispatcher.trigger('sending_data_complete');
                                            };

                                            ECALENDAR.weeksetTimeChanges.reset();
                                            ECALENDAR.weeksetTimeChanges.fetch({ diaryId: ECALENDAR.DiaryGroupSelection.get("diaryGroup").get("diaryID"),
                                                success: triggerComplete, error: triggerComplete
                                            });


                                        },
                                        error: function (model, resp) {

                                            if (model.global_dispatcher != null) {
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
                                                    model.global_dispatcher.trigger('user_messaging', [ECALENDAR.ApplicationStrings.getResourceFromID("SEND_DATA_ERROR")]);
                                                } else {
                                                    model.global_dispatcher.trigger('user_messaging', [errorMsg]);

                                                }
                                                model.global_dispatcher.trigger('sending_data_complete');
                                            }

                                        },
                                        wait: true
                                    }
                                );
                                }

                                var dialogOptions = {
                                    title: ECALENDAR.ApplicationStrings.getResourceFromID('ARE_YOU_SURE'),
                                    width: 400,
                                    buttons: [
                                    { text: ECALENDAR.ApplicationStrings.getResourceFromID('YES'),
                                        click: doDelete
                                    },
                                    {
                                        text: ECALENDAR.ApplicationStrings.getResourceFromID('NO'),
                                        click: function () {
                                            $(this).dialog('close');
                                        }
                                    }
                                ]
                                };

                                self.global_dispatcher.trigger('warning', ECALENDAR.ApplicationStrings.getResourceFromID('POSTPONE_DELETE_CHOICE'), dialogOptions);

                            }
                        }
                    }
                });

            }

        },
        _buildContextMenu: function ($trigger, e) {
            return {
                items: {
                    "apply": { name: ECALENDAR.ApplicationStrings.getResourceFromID('BTN_APPLY_TIMESCHEME'), disabled: !this._canApplyTimeScheme() },
                    "edit": { name: ECALENDAR.ApplicationStrings.getResourceFromID('Edit'), disabled: ((this.exceptionDates.length !== 1)) },
                    "deleteException": { name: ECALENDAR.ApplicationStrings.getResourceFromID('Delete'), disabled: (this.exceptionDates.length === 0) }
                }
            };
        },
        _canApplyTimeScheme: function () {
            var today = new Date().setHours(0, 0, 0, 0);
            return ((this.exceptionDates.length === 0 || this.selectionStartsOrEndsOnNormalTimes) && this.calendar.model.get('endDate').getTime() >= today && this.calendar.model.get('startDate').getTime() >= today);
        },
        render: function () {
            var exceptionsDisplay;
            this.$el.html(_.template('<div id="Exceptions"></div><div class="btn-row" ><button disabled="disabled" id="ApplyTimeScheme" class="btn"><%= btn_apply_timescheme %></button><button disabled="disabled" id="NewException" class="btn"><%= btn_new_exception %></button><button disabled="disabled" id="EditException" class="btn"><%= btn_edit_exception %></button><button disabled="disabled" id="DeleteException" class="btn"><%= btn_delete_exception %></button></div><div class="exceptionMenu"></div>',
            {
                btn_new_exception: ECALENDAR.ApplicationStrings.getResourceFromID("BTN_NEW_EXCEPTION"),
                btn_delete_exception: ECALENDAR.ApplicationStrings.getResourceFromID("BTN_DELETE_EXCEPTION"),
                btn_edit_exception: ECALENDAR.ApplicationStrings.getResourceFromID("BTN_EDIT_EXCEPTION"),
                btn_apply_timescheme: ECALENDAR.ApplicationStrings.getResourceFromID("BTN_APPLY_TIMESCHEME")
            }));
            this._deleteButton = this.$('#DeleteException');
            this._editButton = this.$('#EditException');
            this._newExceptionButton = this.$('#NewException');
            this._applyTimeSchemeButton = this.$('#ApplyTimeScheme');

            this._contextMenu = this.$('.exceptionMenu');
            this.calendar = new ECALENDAR.ExceptionCalendarView({ el: this.$('#Exceptions') });
            this.calendar.bind('daterange_selected', this._handleDateSelected, this);
            this.calendar.bind('calendar_generated', this._addPostponedChanges);



            this.global_dispatcher.bind('sending_data:exceptionCollection:fetch',
            function () {
                this._disableButton(this._deleteButton);
                this._disableButton(this._editButton);
                this._disableButton(this._applyTimeSchemeButton);
                this.calendar.unbindMouseEvents();
            }, this);
            this.global_dispatcher.bind('sending_data_complete:exceptionCollection:fetch',
            function () {
                this.calendar.bindMouseEvents();
            }, this);
            return this;
        },
        events: {
            "click #NewException": "_showNewExceptionWizard",
            "click #EditException": "_showEditExceptionWizard",
            "click #DeleteException": "_deleteExceptions",
            "click #ApplyTimeScheme": "_showApplyTimeScheme"
        },
        concatDates: function (m) {
            if (m.get('startDate').toString() === m.get('endDate').toString()) {
                return '<li>' + m.get('startDate').toLocaleDateString() + '</li>';
            }
            return '<li>' + m.get('startDate').toLocaleDateString() + ' - ' + m.get('endDate').toLocaleDateString() + '</li>';
        },
        _showIndicatorTooltip: function (event) {
            var $el = $(event.target).closest('.datepicker-indicator');
            var tooltip = new ECALENDAR.PostponedWeeksetChangeTooltipView(
                {
                    model: ECALENDAR.weeksetTimeChanges.getByCid($el.data('id')),
                    animate: true,
                    el: $el
                });
            event.preventDefault();

        },

        _addPostponedChanges: function (inst) {
            if (!inst.dpDiv || !ECALENDAR.weeksetTimeChanges) {
                return;
            }
            var calendar = this; // the event comes from the calendar view therefore context is the calendar
            var appends = [];

            inst.dpDiv.find('.datepicker-indicator').remove();
            if (self.postponeDefaultTimeoutID !== -1) {
                clearTimeout(self.postponeDefaultTimeoutID);
                self.postponeDefaultTimeoutID = -1;
            }

            ECALENDAR.weeksetTimeChanges.each(function (m) {
                appends.push(function (id, indicator) {
                    return function () {
                        $(id, inst.dpDiv).find("span:first").append('<span class="datepicker-indicator" data-id="' + indicator + '"><span></span></span>');
                    };
                } (calendar.getID(m.get('date')), m.cid));

            });

            if (appends.length > 0) {                
                self.postponeDefaultTimeoutID = setTimeout(function () {
                    inst.dpDiv.css('visibility', 'hidden');
                    _.each(appends, function (f) {
                        f();
                    });
                    inst.dpDiv.css('visibility', 'visible');
                    self.postponeDefaultTimeoutID = -1;
                }, 0);
            }

        },
        _deleteButton: $(),
        _editButton: $(),
        _newExceptionButton: $(),
        _applyTimeSchemeButton: $(),
        _toggleButton: function (button, enable) {

            if (enable === true && ECALENDAR.canConfigureActivationTimes === true && ECALENDAR.hasFullWebAccess === true) {
                this._enableButton(button);
            }
            else {
                this._disableButton(button);
            }
        },
        _enableButton: function (button) {
            button.removeAttr('disabled');
        },
        _disableButton: function (button) {
            button.attr('disabled', true);
        },
        _deleteExceptions: function (e) {
            var datesToDelete, buttons, self = this;
            if (this.exceptionDates && this.exceptionDates.length > 0) {

                buttons = {};
                buttons[ECALENDAR.ApplicationStrings.getResourceFromID("YES")] = function () {

                    $(this).dialog("close");

                    function commitToServer() {
                        if (self.global_dispatcher != null) {
                            self.global_dispatcher.trigger('sending_data');
                        }


                        self.exceptionDates.destroy({
                            success: function () {
                                self._reloadExceptions(ECALENDAR.DiaryGroupSelection.get('diaryGroup').get('diaryID'));
                                self._disableButton(self._deleteButton);
                                self.global_dispatcher.trigger('sending_data_complete');
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
                                        self.global_dispatcher.trigger('view_messaging:timeSchemeUpdated', [model]);
                                    }
                                    self.global_dispatcher.trigger('sending_data_complete');
                                }
                            }
                        });
                    }
                    // is it diary group or exception diarygroup that isAssociatedWithTimeZones should be checked?

                    if (self.global_dispatcher && ECALENDAR.DiaryGroupSelection.get("diaryGroup").get("isAssociatedWithTimeZones")) {
                        self.global_dispatcher.trigger('download', commitToServer);

                    } else {
                        commitToServer();
                    }


                };
                buttons[ECALENDAR.ApplicationStrings.getResourceFromID("NO")] = function () {

                    $(this).dialog("close");
                };

                this.global_dispatcher.trigger('warning', ECALENDAR.ApplicationStrings.getResourceFromID('CONFIRM_DELETE_EXCEPTIONS'), {
                    title: ECALENDAR.ApplicationStrings.getResourceFromID('TITLE_PLEASE_CONFIRM'),
                    buttons: buttons,
                    close:
                    function () {
                        $(this).dialog("destroy").remove();
                    }
                });
                return;
            }
            // no date was found so disable the button again (?)
            $(e.currentTarget).attr('disabled', true);
        },
        _eventIsFromIndicator: function (event) {
            return (event.target.className === "datepicker-indicator" || event.target.parentNode.className === "datepicker-indicator");
        },
        _handleDateSelected: function (view, event) {
            var start, end, tooltip, exception, models, tooltipoptions;

            if (ECALENDAR.DiaryGroupSelection.get('diaryGroup')) {

                start = view.model.get('startDate');
                end = view.model.get('endDate');


                this.exceptionDates = new ECALENDAR.ExceptionCollection(ECALENDAR.exceptionCollection.filterModelsThatStartOrEndInRange(view.model.get('startDate'), view.model.get('endDate'), true));
                this.selectionStartsOrEndsOnNormalTimes = (this.exceptionDates.filterModelsThatStartOrEndInRange(start, start, true).length === 0) || (this.exceptionDates.filterModelsThatStartOrEndInRange(end, end, true).length === 0);

                this._toggleButton(this._deleteButton, (this.exceptionDates.length > 0));
                this._toggleButton(this._editButton, (this.exceptionDates.length === 1));

                this._toggleButton(this._applyTimeSchemeButton, this._canApplyTimeScheme());

                //create tooltip:
                if (event && event.originalEvent && ECALENDAR.DiaryGroupSelection.get('diaryGroup') !== null) {

                    if (event.originalEvent.button < 2) {

                        if (this._eventIsFromIndicator(event)) {

                            this._showIndicatorTooltip(event);
                        }
                        else {


                            var el = view.getDay($(event.target));
                            if (el.length === 0) {
                                el = $(view.getID(end));
                            }
                            if (el.length > 0) {
                                tooltipoptions = { animate: true, model: view.model, collection: this.exceptionDates, el: el };

                                if (ECALENDAR.DiaryGroupSelection.get('diaryGroup').get('isFolder') === false) {
                                    tooltip = new ECALENDAR.TimeSchemeTooltipView(tooltipoptions);
                                }
                                else {
                                    tooltip = new ECALENDAR.FolderTimeSchemeTooltipView(tooltipoptions);
                                }
                            }
                        }
                    }
                    else {
                        if (!this._eventIsFromIndicator(event)) {
                            this._contextMenu.contextMenu({ x: event.pageX, y: event.pageY });
                        }

                    }
                }
            }
        },
        _reloadExceptions: function (diaryId) {

            ECALENDAR.exceptionCollection.global_dispatcher.trigger('sending_data:exceptionCollection:fetch');
            // Get the up-to-dates exception collection from server
            ECALENDAR.exceptionCollection.fetch({
                success: $.proxy(function () { // success callback for fetch
                    if (this.global_dispatcher) {
                        this.global_dispatcher.trigger('sending_data_complete:exceptionCollection:fetch');
                    }
                }, this),
                error: $.proxy(function (collection, xhr, fetch) { // error callback for fetch
                    if (this.global_dispatcher) {
                        this.global_dispatcher.trigger('sending_data_complete:exceptionCollection:fetch');
                    }
                    if (xhr.statusText === "abort") {
                        return;
                    }
                    if (this.global_dispatcher) {
                        this.global_dispatcher.trigger('user_messaging', [ECALENDAR.ApplicationStrings.getResourceFromID("GET_EXCEPTION_ERROR")]);
                    }
                }, ECALENDAR.exceptionCollection),
                model: "Exceptions",
                diaryId: diaryId
            });
        },
        _saveException: function (model) {

            var self = this, commitToServer, saveExceptions;
            commitToServer = function () {
                self.global_dispatcher.trigger('sending_data');
                if (ECALENDAR.deletedDates && ECALENDAR.deletedDates.length > 0) {
                    // Delete the conflicted dates from server
                    ECALENDAR.deletedDates.destroy({
                        success: function () { // success callback for destroy
                            // Create new exceptions on server
                            saveExceptions();
                        },
                        error: function (jqXHR) { // error callback for destroy
                            var xmlDoc, $xmlDoc, errorMsg = null;
                            if ((jqXHR != null) && (jqXHR !== undefined)) {
                                if (jqXHR.responseText != null && jqXHR.responseText !== "") {
                                    xmlDoc = $.parseXML(jqXHR.responseText);
                                    $xmlDoc = $(xmlDoc);
                                    errorMsg = $xmlDoc.find("Error").text();
                                }
                            }
                            if (errorMsg === null || errorMsg.length === 0) {
                                //It seems a communication error or might be server not available error.
                                self.global_dispatcher.trigger('user_messaging', [ECALENDAR.ApplicationStrings.getResourceFromID("SEND_DATA_ERROR")]);
                            } else {
                                self.global_dispatcher.trigger('user_messaging', [errorMsg]);
                            }
                            self.global_dispatcher.trigger('sending_data_complete');
                        }
                    });
                }
                else {
                    // just save the exceptions if nothing to delete - saves a server request.
                    saveExceptions();
                }
            };
            saveExceptions = function () {

                model.save({
                    success: function () { // success callback for save
                        model.trigger('model_saved');
                        // clear deleted dates 
                        if (ECALENDAR.deletedDates) {
                            ECALENDAR.deletedDates.reset();
                        }
                        self.global_dispatcher.trigger('sending_data_complete');
                        self._reloadExceptions(model.at(0).get('diaryGroupID'));
                    },
                    error: function (jqXHR) { // error callback for save
                        if (self.global_dispatcher != null) {
                            //In case if some error appears at server, it is being sent in XML as <Error> error-description </Error>
                            //If there is no error message as response - it means server has succeesully completed the request.
                            var xmlDoc, $xmlDoc, errorMsg = null, conflictDetected = false, buttons = {}, msg;
                            if ((jqXHR !== null) && (jqXHR !== undefined)) {
                                if (jqXHR.responseText != null && jqXHR.responseText !== "") {
                                    xmlDoc = $.parseXML(jqXHR.responseText);
                                    $xmlDoc = $(xmlDoc);
                                    if ($xmlDoc.find("ConflictExceptionCollection").length !== 0) {
                                        conflictDetected = true;
                                        ECALENDAR.deletedDates = ECALENDAR.DataProvider.generateExceptionCollectionFromXML(jqXHR.responseText);
                                        if (ECALENDAR.deletedDates.length > 0) {
                                            // Construct user message to ask if user wants to delete conflicted exceptions
                                            buttons[ECALENDAR.ApplicationStrings.getResourceFromID("YES")] = function () {
                                                commitToServer(); // recursive call

                                                model.trigger('delete_conflicts');
                                                $(this).dialog("close");
                                            };
                                            buttons[ECALENDAR.ApplicationStrings.getResourceFromID("NO")] = function () {
                                                ECALENDAR.deletedDates.reset();
                                                model.trigger('keep_conflicts');
                                                $(this).dialog("close");
                                            };

                                            msg = _.template('<p><%= msg %></p><p><%= details %></p><ul class="unstyled"><%= dates %></ul>',
                                            {
                                                msg: ECALENDAR.ApplicationStrings.getResourceFromID('DATE_CLASH_HAS_BEEN_DETECTED'),
                                                details: ECALENDAR.ApplicationStrings.getResourceFromID('EXCEPTION_CLASH_DETAILS'),
                                                dates: ECALENDAR.deletedDates.map(self.concatDates).join('')
                                            });

                                            self.global_dispatcher.trigger('warning', msg, {
                                                buttons: buttons,
                                                close: function () {
                                                    $(this).dialog("destroy").remove();
                                                }
                                            });

                                        } else {
                                            self.global_dispatcher.trigger('warning', [ECALENDAR.ApplicationStrings.getResourceFromID("PARSE_CONFLICTED_EXCEPTION_ERROR")]);
                                        }
                                    } else {
                                        errorMsg = $xmlDoc.find("Error").text();
                                        if ($xmlDoc.find("MaxExceptionsHit").length !== 0) {
                                            self._reloadExceptions(model.at(0).get('diaryGroupID'));
                                            model.trigger('max_exceptions_hit');

                                        }
                                    }
                                } else {
                                    self.global_dispatcher.trigger('user_messaging', [ECALENDAR.ApplicationStrings.getResourceFromID("SEND_DATA_ERROR")]);
                                }
                            }
                            if (conflictDetected === false) {
                                if (errorMsg === null || errorMsg.length === 0) {
                                    //It seems a communication error or might be server not available error.
                                    self.global_dispatcher.trigger('user_messaging', [ECALENDAR.ApplicationStrings.getResourceFromID("SEND_DATA_ERROR")]);
                                } else {
                                    self.global_dispatcher.trigger('user_messaging', [errorMsg]);
                                }
                            }
                            self.global_dispatcher.trigger('sending_data_complete');
                        }
                    }
                });
            };

            if (this.global_dispatcher && ECALENDAR.DiaryGroupSelection.get("diaryGroup").get("isAssociatedWithTimeZones")) {
                this.global_dispatcher.trigger('download', commitToServer);
            } else {
                commitToServer();
            }


        },
        _showApplyTimeScheme: function () {

            var view, self = this, timeSchemeSelection, model, buttons;
            if (!this.calendar.model) {
                // in order to run  apply time scheme, a date selection must have been made on the calendar, 
                // which assigns the model property with an exception model.
                // without this model the apply time scheme selection cannot be made.
                return;
            }

            self = this;
            timeSchemeSelection = new ECALENDAR.TimeSchemeSelectionModel();
            model = this.calendar.model.clone();


            timeSchemeSelection.bind('change', function (m) {

                this.unbind('change');
                var attributes, collection, timeScheme;
                timeScheme = m.get('timeScheme');
                attributes = { timeschemelabel: timeScheme.get('label'), label: ECALENDAR.ApplicationStrings.getResourceFromID("EXCEPTION_TEXT"), diaryGroupID: ECALENDAR.DiaryGroupSelection.get('diaryGroup').get('diaryID') };
                if (timeScheme instanceof ECALENDAR.SpecialDayModel) {
                    attributes.isWeekset = 0;
                    attributes.specialDayID = (timeScheme.id > 0) ? timeScheme.id : 0;
                }
                else {
                    attributes.isWeekset = 1;
                    attributes.weeksetID = (timeScheme.id > 0) ? timeScheme.id : 0;
                }


                model.set(attributes);
                collection = new ECALENDAR.ExceptionCollection(model);

                view.$el.dialog('close');

                self._saveException(collection);


            });

            view = new ECALENDAR.ApplyTimeSchemeView({ timeSchemeSelection: timeSchemeSelection, model: model });
            view.bind('No timeschemes', function () { this.$el.dialog('close'); });


            buttons = {};
            buttons[ECALENDAR.ApplicationStrings.getResourceFromID('BTN_CANCEL')] = function () {
                $(this).dialog('close');
            };
            view.$el.dialog({
                height: 450,
                width: 350,
                resizable: false,
                draggable: true,
                modal: true,
                title: ECALENDAR.ApplicationStrings.getResourceFromID('APPLY_TIMESCHEME_TITLE'),
                buttons: buttons,
                close: function () {

                    $(this).dialog("destroy").remove();
                }
            });

            view.render();

        },
        _showNewExceptionWizard: function () {
            this._showExceptionWizard();
        },
        _showEditExceptionWizard: function () {
            this._showExceptionWizard(this.exceptionDates.at(0).clone());
        },
        _showExceptionWizard: function (exception) {
            var exceptionCollection, nextButtonClickHandler, validateLabel, validateTimeScheme, wizard, self, defaultDate;
            self = this;

            exceptionCollection = new ECALENDAR.ExceptionCollection();
            exception = exception || new ECALENDAR.ExceptionModel({ diaryGroupID: ECALENDAR.DiaryGroupSelection.get('diaryGroup').get('diaryID') });

            defaultDate = new Date(exception.get('startDate'));
            if (exception.get('specialDayID') === 0 || exception.get('weeksetID') === 0) {
                // exception is an existing exception for a folder. so set new Exception property to false;
                exception.newException = false;
            }

            if (!exception.isNew()) {
                exceptionCollection.originalForEdit = exception.clone();
                defaultDate.setMonth(defaultDate.getMonth() - 1);
            }
            exceptionCollection.add(exception);
            validateLabel = function () {
                var modelToValidate, errors = [];
                modelToValidate = this.model.at(0);
                if (modelToValidate) {
                    errors = modelToValidate.validateLabel(modelToValidate.attributes);
                    if (errors.length > 0) {
                        modelToValidate.trigger('error', modelToValidate, errors);
                        return false;
                    }
                }
                return true;
            };
            validateTimeScheme = function () {
                var modelToValidate, errors = [];
                modelToValidate = this.model.at(0);
                if (modelToValidate) {
                    errors = modelToValidate.validateTimeSchemeSelection(modelToValidate.attributes);
                    if (errors.length > 0) {
                        modelToValidate.trigger('error', modelToValidate, errors);
                        return false;
                    }
                }
                return true;
            };
            wizard = new ECALENDAR.WizardView({
                title: ECALENDAR.ApplicationStrings.getResourceFromID("WIZARD_TITLE_CONFIGURE_EXCEPTION"),
                model: new ECALENDAR.TabCollection([
                    new ECALENDAR.TabModel({ tabText: ECALENDAR.ApplicationStrings.getResourceFromID("WIZARD_TITLE_EXCEPTION_LABEL"), view: ECALENDAR.ExceptionLabelView, viewparams: { model: exceptionCollection, onSubmit: validateLabel} }),
                    new ECALENDAR.TabModel({ tabText: ECALENDAR.ApplicationStrings.getResourceFromID("WIZARD_TITLE_EDIT_TIMES"), view: ECALENDAR.ExceptionTimeSchemeView, viewparams: { model: exceptionCollection, onSubmit: validateTimeScheme} }),
                    new ECALENDAR.TabModel({ tabText: ECALENDAR.ApplicationStrings.getResourceFromID("WIZARD_TITLE_EDIT_DATES"), view: ECALENDAR.SelectionCalendarView, viewparams: { rows: 1, columns: 3, model: exceptionCollection, defaultDate: defaultDate, onSubmit:
                    function () {
                        this.clearErrors();
                        if (!this.copyDatesToModel()) {
                            this.model.at(0).set({ startDate: null, endDate: null });
                            return false;
                        }
                        return true;
                    }
                    }
                    }),
                    new ECALENDAR.TabModel({ tabText: ECALENDAR.ApplicationStrings.getResourceFromID("WIZARD_TITLE_END"), view: ECALENDAR.ExceptionWizardSummaryView, viewparams: { model: exceptionCollection} })
                ])
            });

            wizard.bind('back_click',
            function (view) {
                if (view instanceof ECALENDAR.SelectionCalendarView) {
                    view.copyDatesToModel();
                }
            });


            wizard.bind('finish_click', function (view) {

                function closeDialog() {
                    //model has been done with so unbind events
                    this.unbind('model_saved');
                    this.unbind('keep_conflicts');
                    this.unbind('max_exceptions_hit');
                    wizard.$el.dialog('close');
                }

                view.model.bind('model_saved', closeDialog);
                view.model.bind('keep_conflicts', closeDialog);
                view.model.bind('max_exceptions_hit', closeDialog);

                self._saveException(view.model);

            });
            wizard.$el.bind('dialogclose',
            function () {

                if (ECALENDAR.deletedDates) {
                    ECALENDAR.deletedDates.reset();
                }

            }
            );
            wizard.render();
        }
    });
});