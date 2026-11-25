/*! - v1.0
*/

/*globals Backbone*/
/*globals _*/
/*globals ECALENDAR*/
/*globals $ */

$(function () {
    "use strict";


    ECALENDAR.CalendarView = Backbone.View.extend({
        bindEvents: function () {
            if (this.collection) {
                this.collection.bind('reset', this.refreshCalendar, this);
            }
        },
        unbindEvents: function () {
            if (this.collection) {
                this.collection.unbind('reset', this.refreshCalendar, this);
            }
        },
        initialize: function () {
            this.collection = this.collection || ECALENDAR.exceptionCollection;
            this.start = null;
            this.end = null;
            this.highlighted = $();
            this.bindEvents();
            this.render();
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

        render: function () {
            var self = this;
            if (this.$el.datepicker) {
                this.$el.datepicker('destroy');
            }
            this.$el.empty();
            this.$el.datepicker({ firstDay: (this.options.firstDay || 1), numberOfMonths: [(this.options.rows || 3), (this.options.columns || 4)],
                beforeShowDay: _.bind(this.beforeShowDay, this),
                defaultDate: this.options.defaultDate || null,
                onHtmlGenerated: function (inst) {
                    self.trigger('calendar_generated', inst);
                }
            });

            this.$el.bind('mousedown.calendar', _.bind(function (event) {

                var $target = this.getDay(event.target), day, currentDate, $days;
                if ($target.length === 0) {
                    return;
                }

                event.preventDefault();
                day = this.getDay(event.target);
                currentDate = this.getDate(day);

                this.clearSelectedDates();

                // set start and end date with current date
                this.start = currentDate;
                this.end = currentDate;

                this.$el.bind('mouseup.calendar', _.bind(function (event) {
                    this.$el.unbind('mouseup.calendar');
                    event.preventDefault();
                    this.trigger('singledate_selected', this, event);
                }, this));

                // re-select current cell
                this.highlight(day);

            }, this));

        },
        refreshCalendar: function () {
            if (this.collection.length > 0) {
                this.$el.datepicker('refresh');
            }
            else {
                this.$('td[id^=dp]').removeClass(this.readOnlyClassName).find(':first-child').removeAttr('style');
            }
        },
        beforeShowDay: function (date) {

            var currentDate, classname = [], selectable = true, style = '', matchCount = 0;

            if (this.collection) {
                this.collection.each(function (e) {

                    //Repeat every year exception should get displayed when the year changes in the calendar.                    
                    currentDate = new Date(date.getTime());
                    if (currentDate > e.get('endDate')) {
                        currentDate.setFullYear(e.get('startDate').getFullYear());
                    }

                    if ((date >= e.get('startDate') && date <= e.get('endDate')) || ((e.get('sameEveryYear') === true) && (currentDate >= e.get('startDate')) && (currentDate <= e.get('endDate')))) {
                        matchCount += 1;
                        classname.push(this.readOnlyClassName);
                        style = "background-color:" + e.get('colour') + ";color:" + ECALENDAR.AppUtilities.getContrastColour(e.get('colour'));
                    }


                }, this);
                if (matchCount > 1) {
                    classname.push(this.overlappedClassName);
                }
                if (date < new Date().setHours(0, 0, 0, 0)) {
                    selectable = false;
                }

                if (this.start !== null && this.start === this.end) {
                    if (date.getTime() === this.start.getTime()) {
                        classname.push(this.className);
                    }
                }
            }
            return [selectable, classname.join(' '), '', style];
        },

        getDate: function (obj) {
            return this.createDateObject(this.getDay(obj).attr('id'));
        },
        getDay: function (obj) {
            return (obj.closest ? obj : $(obj)).closest('td[id^="dp"]');
        },
        getID: function (date) {
            return '#dp' + date.getTime();
        },
        highlight: function (obj) {
            if (obj.length > 0) {
                if (obj.get(0).tagName === 'TD') {
                    this.highlighted = this.highlighted.add(obj.addClass(this.className));
                }
                else {
                    this.highlighted = this.highlighted.add(obj.find('td[id^="dp"]').addClass(this.className));
                }
            }
        },
        highlightDates: function (startday, endday) {

            var startMonth = this.getMonth(startday),
            endMonth = this.getMonth(endday),
            startWeek = this.getWeek(startday),
            endWeek = this.getWeek(endday),
            highlightUntil = function (start, end) {
                this.highlight(start.nextUntil(end));
            },
            highlightAfter = function (obj) {
                this.highlight(obj.nextAll());
            },
            highlightBefore = function (obj) {
                this.highlight(obj.prevAll());
            };

            this.highlight(startday);

            if (startMonth[0] !== endMonth[0]) {
                // start and end date are not in the same month
                highlightAfter.call(this, startday);
                highlightAfter.call(this, startWeek);
                highlightUntil.call(this, startMonth, endMonth);
                highlightBefore.call(this, endWeek);
                highlightBefore.call(this, endday);
            }
            else {

                // start and end date are in the same month
                if (startWeek[0] !== endWeek[0]) {

                    // start and end date are not in the same week
                    highlightAfter.call(this, startday);
                    highlightUntil.call(this, startWeek, endWeek);
                    highlightBefore.call(this, endday);

                }
                else {
                    if (startday[0] !== endday[0]) {

                        // start and end date are in the same week
                        highlightUntil.call(this, startday, endday);
                    }

                }
            }
            this.highlight(endday);
        },
        clearSelectedDates: function () {
            this.$('.' + this.className).removeClass(this.className);
        },
        clearHighlighted: function () {
            var highlighted = this.highlighted;
            if (highlighted.length > 0) {
                highlighted.removeClass(this.className);
                highlighted = $();
                return;
            }


        },
        resetSelections: function () {
            this.$('.' + this.className).removeClass(this.className);

            var start, end;
            if (this.model) {
                start = this.model.get('startDate');
                end = this.model.get('endDate');
            }

            if (start === end) {
                this.highlight(this.$(this.getID(start)));
            }
            else {
                this.highlightDates(this.$(this.getID(start)), this.$(this.getID(end)));
            }
            this.highlighted = $();

        },
        getMonth: function (day) {
            return day.closest('.ui-datepicker-group');
        },
        getWeek: function (day) {
            return day.closest('tr');
        },
        createDateObject: function (dateString) {
            return new Date(parseInt(dateString.replace('dp', ''), 10));
        },
        setDate: function (property, obj) {
            this[property] = this.getDate(obj);
        },
        concatDates: function (m) {
            if (m.get('startDate').toString() === m.get('endDate').toString()) {
                return '<li>' + m.get('startDate').toLocaleDateString() + '</li>';
            }
            return '<li>' + m.get('startDate').toLocaleDateString() + ' - ' + m.get('endDate').toLocaleDateString() + '</li>';
        },
        className: 'datepicker-active',
        readOnlyClassName: 'datepicker-readonly',
        selectableClassName: 'datepicker-selectable',
        overlappedClassName: 'datepicker-overlap'


    });

    ECALENDAR.ExceptionCalendarView = ECALENDAR.CalendarView.extend({
        beforeShowDay: function (date) {
            var classname = [], selectable, daySettingsArray = this.constructor.__super__.beforeShowDay.call(this, date);

            if (daySettingsArray[1] !== '') {
                classname.push(daySettingsArray[1]);
            }
            if (date >= this.model.get('startDate') && date <= this.model.get('endDate')) {
                classname.push(this.className);
            }
            classname.push(this.selectableClassName);
            return [true, classname.join(' '), daySettingsArray[2], daySettingsArray[3]];
        },
        bindMouseEvents: function () {
            this.$el.unbind('mousedown.calendar');
            this.$el.bind('mousedown.picker', _.bind(function (event) {

                var $target = this.getDay(event.target), day, currentDate, $days;
                if ($target.length === 0) {
                    return;
                }

                event.preventDefault();

                $days = this.$('td[id^=dp]', '.date-picker-group');
                day = this.getDay(event.target);
                currentDate = this.getDate(day);

                this.resetSelections();

                // set start and end date with current date
                this.start = currentDate;
                this.end = currentDate;

                this.$el.bind('mouseup.picker', _.bind(function (event) {

                    $days.unbind('mouseenter.picker');
                    this.$el.unbind('mouseup.picker');
                    event.preventDefault();

                    this.addDateToModel();
                    this.trigger('daterange_selected', this, event);
                }, this));

                $days.bind('mouseenter.picker', _.bind(function (event) {
                    var startDay, endDay;
                    // Clear all UI selections
                    this.clearHighlighted();
                    this.end = this.getDate(event.target);

                    if (this.start > this.end) {
                        startDay = this.$(this.getID(this.end));
                        endDay = this.$(this.getID(this.start));
                    }
                    else {
                        endDay = this.$(this.getID(this.end));
                        startDay = this.$(this.getID(this.start));
                    }

                    // re-select every cell between current and start
                    this.highlightDates(startDay, endDay);

                }, this));

                // re-select current cell
                this.highlight(day);

            }, this));

        },
        unbindMouseEvents: function () {
            this.clearSelectedDates();
            this.highlighted = $();
            this.model.set({ startDate: new Date(0), endDate: new Date(0) }, { silent: true });
            this.$el.unbind('mousedown.picker');
        },
        initialize: function (options) {
            var today = new Date().setHours(0, 0, 0, 0);
            this.model = this.model || new ECALENDAR.ExceptionModel();
            this.start = null;
            this.end = null;
            this.highlighted = $();

            this.constructor.__super__.initialize.call(this, options);

            this.bindMouseEvents();


        },
        addDateToModel: function () {
            if (this.start > this.end) {
                this.model.set({ endDate: this.start, startDate: this.end }, { silent: true });
            } else {
                this.model.set({ startDate: this.start, endDate: this.end }, { silent: true });
            }


            this.highlighted = $();
            this.resetSelections();

        }

    });

    ECALENDAR.SelectionCalendarView = ECALENDAR.CalendarView.extend({
        beforeShowDay: function (date) {
            var classname = [], selectable, daySettingsArray = this.constructor.__super__.beforeShowDay.call(this, date);
            if (daySettingsArray[1] !== '') {
                classname.push(daySettingsArray[1]);
            }
            selectable = daySettingsArray[0];

            if (!this.model.at(0).isNew()) {
                // if editing a selection allow all existing exceptions to be selectable
                selectable = true;
            }

            if (this.tempCollection && selectable === true) {
                this.tempCollection.each(function (e) {
                    if (date >= e.get('startDate') && date <= e.get('endDate')) {
                        classname.push(this.className);
                    }

                }, this);

                if (date < new Date().setHours(0, 0, 0, 0)) {
                    selectable = false;
                }
                else {
                    classname.push(this.selectableClassName);
                }
            }

            return [selectable, classname.join(' '), daySettingsArray[2], daySettingsArray[3]];
        },
        bindEvents: function () {
            this.constructor.__super__.bindEvents.call(this);
            this.tempCollection.bind('add', this.clearErrors, this);
            this.model.bind('error', this._showErrors, this);
            this.clearErrors();
        },
        unbindEvents: function () {
            this.constructor.__super__.unbindEvents.call(this);
            this.tempCollection.unbind('add', this._clearErrors, this);
            this.model.unbind('error', this._showErrors, this);
        },
        initialize: function (options) {
            var today = new Date().setHours(0, 0, 0, 0);
            this.collection = new ECALENDAR.ExceptionCollection(ECALENDAR.exceptionCollection.filter(
            function (m) {
                return (m.get('endDate') > today || m.get('sameEveryYear') === true);
            }));

            ECALENDAR.deletedDates = new ECALENDAR.ExceptionCollection();
            this.tempCollection = new ECALENDAR.ExceptionCollection();

            if (!this.model.at(0).isNew()) {
                this.tempCollection.add(this.model.at(0));
                this.collection.remove(this.model.at(0));
            }

            this.start = null;
            this.end = null;
            this.highlighted = $();

            this.constructor.__super__.initialize.call(this, options);

            this.$el.unbind('mousedown.calendar');
            this.$el.bind('mousedown.picker', _.bind(function (event) {

                var $target = this.getDay(event.target), day, currentDate, $days, isActive;
                if ($target.length === 0) {
                    return;
                }

                event.preventDefault();

                $days = this.$('td[id^=dp]', '.date-picker-group');
                day = this.getDay(event.target);
                currentDate = this.getDate(day);
                isActive = $target.hasClass(this.className);

                if ($target.hasClass(this.readOnlyClassName) && !isActive && this.model.at(0).isNew()) {
                    return;
                }
                this.resetSelections();

                // set start and end date with current date
                this.start = currentDate;
                this.end = currentDate;

                this.$el.bind('mouseup.picker', _.bind(function (event) {
                    var dates, newDeletedArray, removedDeletedArray, buttons = {}, view = this, msg;
                    $days.unbind('mouseenter.picker');
                    this.$el.unbind('mouseup.picker');
                    event.preventDefault();


                    if (isActive) {
                        //signifies that this should delete a timeset
                        dates = this.tempCollection.filterModelsThatStartOrEndInRange(this.start, this.end);

                        if (dates.length > 0) {
                            view.tempCollection.remove(dates);
                            view.resetSelections();


                            //Get dates from deleted dates that no longer clash with date that is being de-selected
                            newDeletedArray = ECALENDAR.deletedDates.filterModelsThatStartOrEndInRange(dates[0].get('startDate'), dates[0].get('endDate'), true);

                            var datesThatCanBeRescued = [];
                            //loop through array to find which of the deleted dates don't clash with any new exceptions and therefore can be rescued.
                            _.each(newDeletedArray,
                                function (m) {
                                    var dates = this.tempCollection.filterModelsThatStartOrEndInRange(m.get('startDate'), m.get('endDate'), true);
                                    if (dates.length === 0) {
                                        //not clashing with temp collection, so add it to the rescue list.
                                        datesThatCanBeRescued.push(m);
                                    }
                                }, this);

                            if (datesThatCanBeRescued.length > 0) {
                                this.triggerDateClashAvoidance(datesThatCanBeRescued);

                            }
                            return;
                        }
                    }

                    if (this.tempCollection.length < 50) {
                        this.addDateToCollection();
                    } else {
                        view.resetSelections();
                        this.global_dispatcher.trigger('warning', [ECALENDAR.ApplicationStrings.getResourceFromID("NEW_EXCEPTION_NUM_EXCEED_50_ERROR")]);
                    }

                }, this));

                $days.bind('mouseenter.picker', _.bind(function (event) {
                    var startDay, endDay;
                    // Clear all UI selections
                    this.clearHighlighted();
                    this.end = this.getDate(event.target);

                    if (this.start > this.end) {
                        startDay = this.$(this.getID(this.end));
                        endDay = this.$(this.getID(this.start));
                    }
                    else {
                        endDay = this.$(this.getID(this.end));
                        startDay = this.$(this.getID(this.start));
                    }

                    // re-select every cell between current and start
                    this.highlightDates(startDay, endDay);

                }, this));

                // re-select current cell
                this.highlight(day);

            }, this));


        },
        triggerDateClashAvoidance: function (dates) {
            var buttons = {}, view = this, msg;
            buttons[ECALENDAR.ApplicationStrings.getResourceFromID("YES")] = function () {
                ECALENDAR.deletedDates.remove(dates);
                view.collection.add(dates);
                // update the calendar

                _.each(dates,
                function (exception) {
                    this.showException(exception);
                }, view);
                $(this).dialog("close");
            };
            buttons[ECALENDAR.ApplicationStrings.getResourceFromID("NO")] = function () {
                $(this).dialog("close");
            };
            // display user message to ask if removedDeletedArray should be put back
            msg = _.template('<p><%= msg %></p><p><%= details %></p><ul class="unstyled"><%= dates %></ul>',
            {
                msg: ECALENDAR.ApplicationStrings.getResourceFromID('DATE_CLASH_HAS_BEEN_AVOIDED'),
                details: ECALENDAR.ApplicationStrings.getResourceFromID('EXCEPTION_RECOVER_DETAILS'),
                dates: _.map(dates, this.concatDates).join('')
            });

            this.global_dispatcher.trigger('warning', msg, {
                buttons: buttons,
                close: function () {
                    $(this).dialog("destroy").remove();
                }
            });
        },
        addDateToCollection: function () {
            var view = this,
            clone, originalStartDate, originalEndDate, newStartDate, newEndDate;


            function resetDisplay() {
                this.highlighted = $();
                this.resetSelections();
            }

            function updateExceptionDates() {

                if (!clone) {
                    clone = new ECALENDAR.ExceptionModel();
                }
                clone.set({ startDate: newStartDate, endDate: newEndDate }, { silent: true });
            }

            function addClone() {

                updateExceptionDates.call(this);

                var overlapCollection;
                // Merge clone into tempCollection without overlaps
                overlapCollection = this.tempCollection.filterForModelsInsideDateRange(clone.get("endDate"), clone.get("startDate"));
                // current date ranges overlap);

                if (overlapCollection.length > 0) {

                    var overlapIterator = function (exception) {
                        if (clone.get("startDate") > exception.get("startDate")) {
                            clone.set({ startDate: exception.get("startDate") }, { silent: true });
                        }
                        if (clone.get("endDate") < exception.get("endDate")) {
                            clone.set({ endDate: exception.get("endDate") }, { silent: true });
                        }
                        this.tempCollection.remove(exception);

                    };

                    _.each(overlapCollection, overlapIterator, this);

                }
                this.tempCollection.add(clone);

                this.highlighted = $();

            }


            function checkForItemsToRecover(startDate, endDate) {
                if (clone.isNew()) {
                    // only need to check when editing an existing exception.
                    return;
                }
                var temp, tempStartDate, tempEndDate, dates;
                dates = ECALENDAR.deletedDates.filterModelsThatStartOrEndInRange(startDate, endDate);

                if (dates.length > 0) {
                    temp = new ECALENDAR.ExceptionCollection(dates);


                    if (this.start > this.end) {
                        tempStartDate = this.end;
                        tempEndDate = this.start;
                    }
                    else {
                        tempStartDate = this.start;
                        tempEndDate = this.end;
                    }

                    temp.remove(temp.filterModelsThatStartOrEndInRange(tempStartDate, tempEndDate));

                    if (temp.length > 0) {

                        this.triggerDateClashAvoidance(temp.models);
                    }
                }
            }

            function checkForExistingExceptionsThatNeedDeleting() {
                var existingDatesWithCurrentEdit, existingDates, anySameEveryYear, buttons = {}, msg;
                var comparer = function (exception) {
                    return (exception.get("startDate").getTime() !== view.model.originalForEdit.get("startDate").getTime()) && (exception.get("endDate").getTime() !== view.model.originalForEdit.get("endDate").getTime());
                };
                var anySameEveryYearIterator = function (model) {
                    return (model.get('sameEveryYear') === true);
                };

                // check for existing exception dates.
                existingDatesWithCurrentEdit = this.collection.filterModelsThatStartOrEndInRange(newStartDate, newEndDate, true);

                // remove originalForEdit if we have one.
                if (this.model.originalForEdit != null) {
                    existingDates = _.filter(existingDatesWithCurrentEdit, comparer);
                } else {
                    existingDates = existingDatesWithCurrentEdit;
                }


                if (existingDates.length > 0) {
                    anySameEveryYear = _.any(existingDates, anySameEveryYearIterator);

                    if (anySameEveryYear) {
                        // Some of existing dates are repeated yearly
                        // Display warning message to stop user from overlapping with existing repeated exceptions
                        resetDisplay.call(view);
                        this.global_dispatcher.trigger('warning', [ECALENDAR.ApplicationStrings.getResourceFromID("OVERLAP_WITH_REPEATED_EXCEPTION_ERROR")]);
                    } else {

                        //there is an exception already. Ask the user if they want to delete the existing exception.
                        buttons[ECALENDAR.ApplicationStrings.getResourceFromID("YES")] = function () {
                            var hideException = function (exception) {
                                this.hideException(exception);
                            };


                            ECALENDAR.deletedDates.add(existingDates);
                            view.collection.remove(existingDates);

                            _.each(existingDates, hideException, view);
                            addClone.call(view);
                            checkForItemsToRecover.call(view, originalStartDate, originalEndDate);
                            $(this).dialog("close");

                        };
                        buttons[ECALENDAR.ApplicationStrings.getResourceFromID("NO")] = function () {
                            $(this).dialog("close");
                        };

                        msg = _.template('<p><%= msg %></p><p><%= details %></p><ul class="unstyled"><%= dates %></ul>',
                        {
                            msg: ECALENDAR.ApplicationStrings.getResourceFromID('DATE_CLASH_HAS_BEEN_DETECTED'),
                            details: ECALENDAR.ApplicationStrings.getResourceFromID('EXCEPTION_CLASH_DETAILS'),
                            dates: _.map(existingDates, this.concatDates).join('')
                        });

                        var closeDialog = function () {
                            resetDisplay.call(view);
                            $(this).dialog("destroy").remove();
                        };

                        this.global_dispatcher.trigger('warning', msg, { buttons: buttons, close: closeDialog });
                    }

                } else {

                    addClone.call(this);
                    checkForItemsToRecover.call(view, originalStartDate, originalEndDate);
                    resetDisplay.call(this);
                }
            }

            if (this.start > this.end) {
                newStartDate = this.end;
                newEndDate = this.start;
            }
            else {
                newStartDate = this.start;
                newEndDate = this.end;
            }

            if (this.model && this.model.length > 0) {
                if (this.model.at(0).isNew()) {
                    clone = this.model.at(0).clone();
                }
                else {
                    clone = this.model.at(0);

                    originalStartDate = clone.get('startDate');
                    originalEndDate = clone.get('endDate');
                }

            }

            checkForExistingExceptionsThatNeedDeleting.call(this);

        },
        clearSelectedDates: function () {
            this.$('.' + this.className).removeClass(this.className);
            this.tempCollection.reset();
        },
        hideException: function (exception) {


            var start = exception.get('startDate'), end = exception.get('endDate');
            var date = new Date(start.getTime()), ids = [];
            while (date.getTime() <= end.getTime()) {
                ids.push(this.getID(date));
                date.setHours(24);
            }
            this.$(ids.join(',')).removeClass(this.readOnlyClassName).find(':first-child').removeAttr('style');

        },
        showException: function (exception) {

            var start = exception.get('startDate'), end = exception.get('endDate');
            // set font colour to black if background colour is too light
            var cssattributes = { backgroundColor: exception.get('colour'), color: ECALENDAR.AppUtilities.getContrastColour(exception.get('colour')) };

            var date = new Date(start.getTime()), ids = [];
            while (date.getTime() <= end.getTime()) {
                ids.push(this.getID(date));
                date.setHours(24);
            }
            this.$(ids.join(',')).addClass(this.readOnlyClassName).find(':first-child').css(cssattributes);

        },
        resetSelections: function () {
            this.$('.' + this.className).removeClass(this.className);

            if (this.tempCollection.length > 0) {

                this.tempCollection.each(_.bind(function (e) {
                    var start, end;
                    start = e.get('startDate');
                    end = e.get('endDate');
                    if (start === end) {
                        this.highlight(this.$(this.getID(start)));
                    }
                    else {
                        this.highlightDates(this.$(this.getID(start)), this.$(this.getID(end)));
                    }

                }, this));

                this.highlighted = $();
            }
        },
        copyDatesToModel: function () {
            if (this.tempCollection.length > 0) {
                this.model.reset(this.tempCollection.models);
                return true;
            }
            return false;
        }

    });


});