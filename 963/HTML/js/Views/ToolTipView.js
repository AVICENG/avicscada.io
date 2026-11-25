/*globals $
Modernizr
window
setTimeout
clearTimeout
document
_
Backbone
ECALENDAR
*/

$(function () {
    "use strict";
    //todo: inject models instead of relying on the global variables.
    ECALENDAR.TooltipView = Backbone.View.extend({
        template: _.template('<div class="tooltip bottom"><div class="tooltip-arrow"></div><div class="tooltip-inner"><%= content %></div></div>'),
        initialize: function () {

            if (this.$el && this.$el.length > 0) {
                this.offset = this.$el.offset();
            }
        },
        offset: { top: 0, left: 0 },
        render: function () {
            this.remove();
            ECALENDAR.tooltip = $(this.template({ content: this.options.content })).appendTo('body');
            if (this.options.animate) {
                ECALENDAR.tooltip.addClass('fade');
            }

            this.show();
            return this;
        },
        show: function () {
            if (!ECALENDAR.tooltip) {
                return;
            }

            if (!this.offset) {
                // if there isn't an offset to position the tooltip, don't show the tooltip
                return;
            }

            ECALENDAR.tooltip.addClass('in');

            var css = { top: this.offset.top + this.$el.outerHeight(), left: this.offset.left - (ECALENDAR.tooltip.width() / 2) + (this.$el.outerWidth() / 2) };
            var viewport = $(document.body), className;
            if ((css.top + ECALENDAR.tooltip.height()) > viewport.height()) {
                delete css.top;
                css.bottom = viewport.height() - this.offset.top;
                className = 'top';

                if (css.bottom + ECALENDAR.tooltip.height() > viewport.height()) {
                    css.left = this.offset.left - ECALENDAR.tooltip.width();
                    delete css.bottom;
                    css.top = 0;
                    className = 'left';
                    ECALENDAR.tooltip.find('.tooltip-arrow').css({ top: this.offset.top + (this.$el.outerHeight() / 2) });
                }
                ECALENDAR.tooltip.removeClass('bottom').addClass(className);

            }
            if (css.left + ECALENDAR.tooltip.width() > viewport.width()) {
                delete css.left;
                css.right = 0;
            }
            ECALENDAR.tooltip.css(css);
            if (className !== 'left') {
                ECALENDAR.tooltip.find('.tooltip-arrow').css({ left: this.offset.left - ECALENDAR.tooltip.offset().left + (this.$el.outerWidth() / 2) });
            }
            var hideOnUIEvents = _.bind(function () {
                $(window).unbind('resize.tooltip');
                $(document).unbind('mousedown.tooltip');
                this.remove();
            }, this);

            $(window).bind('resize.tooltip', hideOnUIEvents);
            $(document).bind('mousedown.tooltip', hideOnUIEvents);
            hideOnUIEvents = null;
            ECALENDAR.timer = setTimeout(_.bind(this.hide, this), this.options.delay || 3000);
        },
        hide: function () {
            $(window).unbind('resize.tooltip');
            $(document).unbind('mousedown.tooltip');
            if (ECALENDAR.timer) {
                //remove the timer if hide is called explicitly
                clearTimeout(ECALENDAR.timer);
                delete ECALENDAR.timer;
            }
            if (ECALENDAR.tooltip) {
                ECALENDAR.tooltip.removeClass('in');
                //ideally make use of transition timeout events (modernizr check needed)
                if (Modernizr.csstransitions && this.options.animate) {

                    ECALENDAR.tooltip.bind("webkitTransitionEnd transitionend oTransitionEnd", _.bind(function (event) {
                        if (ECALENDAR.tooltip) {
                            ECALENDAR.tooltip.unbind("webkitTransitionEnd transitionend oTransitionEnd");
                            this.remove();
                        }

                    }, this));
                }
                else {
                    this.remove();
                }

            }
        },
        remove: function () {

            if (ECALENDAR.timer) {
                clearTimeout(ECALENDAR.timer);
            }
            if (ECALENDAR.tooltip) {
                ECALENDAR.tooltip.remove();
                delete ECALENDAR.tooltip;
            }
        }


    });



    ECALENDAR.TimeSchemeTooltipView = ECALENDAR.TooltipView.extend({
        base: ECALENDAR.TooltipView.prototype,
        initialize: function () {
            this.options.content = this.createContent();
            this.base.initialize.call(this, this.options);
            this.render();
        },
        createContent: function () {
            var html = [];
            function append(value) {
                html.push(value);
            }

            function appendActivations(day, label) {
                var l, i;
                l = day.arrActivationPeriod.length;
                if (l > 0) {

                    append(label);

                    for (i = 0; i < l; i += 2) {
                        append(day.arrActivationPeriod[i].timeAsString() + " - " + day.arrActivationPeriod[i + 1].timeAsString() + " ");
                    }
                    append("<br />");
                } else {
                    append(label + "24:00 - 24:00<br />");
                }
            }

            function logDay(m, defaultTimes) {
                var day, days, k, timeScheme, start, numberOfDays;
                if (defaultTimes === true) {

                    timeScheme = ECALENDAR.weekSetCollection.at(0);
                    append(timeScheme.get('label') + "<br />");
                }
                else {


                    if (m.get('specialDayID') > -1) {
                        timeScheme = ECALENDAR.specialDayCollection.get(m.get('specialDayID'));
                    }
                    else {
                        timeScheme = ECALENDAR.weekSetCollection.get(m.get('weeksetID'));
                    }
                    append('<div class="pre">' + m.get('label'));

                    if (timeScheme && timeScheme.get('label')) {
                        append(" (" + timeScheme.get('label') + ")");
                    }
                    append("</div>");


                    append('<div class="tooltip-nowrap">' + m.get('startDate').toLocaleDateString());
                    if (m.get('startDate') != m.get('endDate')) {
                        append(" - " + m.get('endDate').toLocaleDateString());
                    }
                    append("</div>");
                    append(ECALENDAR.ApplicationStrings.getResourceFromID('SAME_EVERY_YEAR') + ": " + m.sameEveryYearText() + "<br />");
                }

                if (timeScheme) {

                    if (timeScheme instanceof ECALENDAR.SpecialDayModel) {
                        day = timeScheme.get('arrDay')[0];
                        appendActivations(day, "");
                    }
                    else {

                        var checkStartDate = (m && (m.get('startDate') > this.model.get('startDate'))) ? m.get('startDate') : this.model.get('startDate');
                        var checkEndDate = (m && (m.get('endDate') < this.model.get('endDate'))) ? m.get('endDate') : this.model.get('endDate');
                        var startDay = checkStartDate.getDay() - 1,
                    endDay = checkEndDate.getDay() - 1;

                        if (startDay == -1) {
                            startDay = 6;
                        }
                        if (endDay == -1) {
                            endDay = 6;
                        }

                        numberOfDays = ((checkEndDate - checkStartDate) / (24 * 3600 * 1000)) + 1;

                        if (numberOfDays > 7) {
                            numberOfDays = 7;
                        }
                        //list the days as day of week as an array to sort selection Monday - Sunday
                        days = [];
                        start = startDay;
                        for (k = 0; k < numberOfDays; k += 1) {

                            days.push(start);
                            start += 1;
                            if (start == 7) {
                                start = 0;
                            }
                        }

                        days = days.sort();

                        //generate html for days of week.
                        for (k = 0; k < numberOfDays; k += 1) {
                            start = days[k];
                            day = timeScheme.get('arrDay')[start];
                            appendActivations(day, day.getLabel() + ": ");
                        }
                    }
                }
            }


            if (this.collection.length > 0) {

                if (this.collection.length > 1 && this.model.get('startDate').getTime() == this.model.get('endDate').getTime()) {
                    html.push('<strong>' + ECALENDAR.ApplicationStrings.getResourceFromID('WARNING_OVERLAID_EXCEPTIONS') + '</strong><br />');
                }
                this.collection.each(logDay, this);
            }
            else {

                logDay.call(this, null, true);
            }
            return html.join('');
        }
    });

    ECALENDAR.FolderTimeSchemeTooltipView = ECALENDAR.TimeSchemeTooltipView.extend({
        createContent: function () {
            if (this.collection.length === 0) {
                return ECALENDAR.ApplicationStrings.getResourceFromID('SELECT_GROUP_FIRST');
            }
            else {
                var m = this.collection.at(0);
                return (m.get('label') + "(" + m.get('timeschemelabel') + ")<br />" +
                 '<div class="tooltip-nowrap">' + m.get('startDate').toLocaleDateString() +
                  ((m.get('startDate') != m.get('endDate')) ? " - " + m.get('endDate').toLocaleDateString() : '') + '</div>' +
                 ECALENDAR.ApplicationStrings.getResourceFromID('SAME_EVERY_YEAR') + ": " + m.sameEveryYearText());
            }
        }

    });


    ECALENDAR.PostponedWeeksetChangeTooltipView = ECALENDAR.TooltipView.extend({
        base: ECALENDAR.TooltipView.prototype,
        initialize: function () {
            this.options.content = this.createContent();
            this.base.initialize.call(this, this.options);

            this.render();
        },
        createContent: function () {

            var tooltip = "<strong>" + ECALENDAR.ApplicationStrings.getResourceFromID('POSTPONED_DAY') + "</strong>";
            if ((this.model !== null) && (this.model !== undefined)) {
                tooltip += "<div>" + this.model.get('tooltip') + "</div>";
            }
            return tooltip;
        }


    });


});