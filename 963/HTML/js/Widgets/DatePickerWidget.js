/*jslint browser:true*/
/*
globals window 
globals jQuery
*/
(function ($) {
    $.extend($.datepicker, {

        /* OVERRIDE */
        /* Generate the HTML for the current state of the date picker. */
        _generateHTML: function (inst) {
            // I don't know why I have to do this
            var dpuuid = new Date().getTime();
            window['DP_jQuery_' + dpuuid] = $;
            var today = new Date();
            today = this._daylightSavingAdjust(
			new Date(today.getFullYear(), today.getMonth(), today.getDate())); // clear time
            var isRTL = this._get(inst, 'isRTL');
            var showButtonPanel = this._get(inst, 'showButtonPanel');
            var hideIfNoPrevNext = this._get(inst, 'hideIfNoPrevNext');
            var navigationAsDateFormat = this._get(inst, 'navigationAsDateFormat');
            var numMonths = this._getNumberOfMonths(inst);
            var showCurrentAtPos = this._get(inst, 'showCurrentAtPos');
            var stepMonths = this._get(inst, 'stepMonths');
            var isMultiMonth = (numMonths[0] != 1 || numMonths[1] != 1);
            var currentDate = this._daylightSavingAdjust((!inst.currentDay ? new Date(9999, 9, 9) :
			new Date(inst.currentYear, inst.currentMonth, inst.currentDay)));
            var minDate = this._getMinMaxDate(inst, 'min');
            var maxDate = this._getMinMaxDate(inst, 'max');
            var drawMonth = inst.drawMonth - showCurrentAtPos;
            var drawYear = inst.drawYear;
            if (drawMonth < 0) {
                drawMonth += 12;
                drawYear--;
            }
            if (maxDate) {
                var maxDraw = this._daylightSavingAdjust(new Date(maxDate.getFullYear(),
				maxDate.getMonth() - (numMonths[0] * numMonths[1]) + 1, maxDate.getDate()));
                maxDraw = (minDate && maxDraw < minDate ? minDate : maxDraw);
                while (this._daylightSavingAdjust(new Date(drawYear, drawMonth, 1)) > maxDraw) {
                    drawMonth--;
                    if (drawMonth < 0) {
                        drawMonth = 11;
                        drawYear--;
                    }
                }
            }
            inst.drawMonth = drawMonth;
            inst.drawYear = drawYear;
            var prevText = this._get(inst, 'prevText');
            prevText = (!navigationAsDateFormat ? prevText : this.formatDate(prevText,
			this._daylightSavingAdjust(new Date(drawYear, drawMonth - stepMonths, 1)),
			this._getFormatConfig(inst)));

            var biggerStep = numMonths[0] * numMonths[1], prev, prevYear, nextText, next, nextYear;

            prev = (this._canAdjustMonth(inst, -1, drawYear, drawMonth) ?
			'<a class="ui-datepicker-prev datepicker-prev-month ui-corner-all" onclick="DP_jQuery_' + dpuuid +
			'.datepicker._adjustDate(\'#' + inst.id + '\', -' + stepMonths + ', \'M\');"' +
			' title="' + prevText + '"><span class="ui-icon ui-icon-arrowthick-1-' + (isRTL ? 'e' : 'w') + '">' + prevText + '</span></a>' :
			(hideIfNoPrevNext ? '' : '<a class="ui-datepicker-prev datepicker-prev-month ui-corner-all ui-state-disabled" title="' + prevText + '"><span class="ui-icon ui-icon-arrowthick-1-' + (isRTL ? 'e' : 'w') + '">' + prevText + '</span></a>'));

            nextText = this._get(inst, 'nextText');
            nextText = (!navigationAsDateFormat ? nextText : this.formatDate(nextText,
			this._daylightSavingAdjust(new Date(drawYear, drawMonth + stepMonths, 1)),
			this._getFormatConfig(inst)));

            next = (this._canAdjustMonth(inst, +1, drawYear, drawMonth) ?
			'<a class="ui-datepicker-next datepicker-next-month ui-corner-all" onclick="DP_jQuery_' + dpuuid +
			'.datepicker._adjustDate(\'#' + inst.id + '\', +' + stepMonths + ', \'M\');"' +
			' title="' + nextText + '"><span class="ui-icon ui-icon-arrowthick-1-' + (isRTL ? 'w' : 'e') + '">' + nextText + '</span></a>' :
			(hideIfNoPrevNext ? '' : '<a class="ui-datepicker-next datepicker-next-month ui-corner-all ui-state-disabled" title="' + nextText + '"><span class="ui-icon ui-icon-arrowthick-1-' + (isRTL ? 'w' : 'e') + '">' + nextText + '</span></a>'));

            if (biggerStep > 1) {

                prevYear = (this._canAdjustMonth(inst, -biggerStep, drawYear, drawMonth) ?
			'<a class="ui-datepicker-prev ui-corner-all" onclick="DP_jQuery_' + dpuuid +
			'.datepicker._adjustDate(\'#' + inst.id + '\', -' + biggerStep + ', \'M\');"' +
			' title="' + prevText + ' ' + biggerStep + '"><span class="ui-icon ui-icon-arrowthickstop-1-' + (isRTL ? 'e' : 'w') + '">' + prevText + ' ' + biggerStep + '</span></a>' :
			(hideIfNoPrevNext ? '' : '<a class="ui-datepicker-prev ui-corner-all ui-state-disabled" title="' + prevText + ' ' + biggerStep + '"><span class="ui-icon ui-icon-arrowthickstop-1-' + (isRTL ? 'e' : 'w') + '">' + prevText + ' ' + biggerStep + '</span></a>'));

                nextYear = (this._canAdjustMonth(inst, +biggerStep, drawYear, drawMonth) ?
			'<a class="ui-datepicker-next ui-corner-all" onclick="DP_jQuery_' + dpuuid +
			'.datepicker._adjustDate(\'#' + inst.id + '\', +' + biggerStep + ', \'M\');"' +
			' title="' + nextText + ' ' + biggerStep + '"><span class="ui-icon ui-icon-arrowthickstop-1-' + (isRTL ? 'w' : 'e') + '">' + nextText + ' ' + biggerStep + '</span></a>' :
			(hideIfNoPrevNext ? '' : '<a class="ui-datepicker-next ui-corner-all ui-state-disabled" title="' + nextText + ' ' + biggerStep + '"><span class="ui-icon ui-icon-arrowthickstop-1-' + (isRTL ? 'w' : 'e') + '">' + nextText + ' ' + biggerStep + '</span></a>'));

            }

            var currentText = this._get(inst, 'currentText');
            var gotoDate = (this._get(inst, 'gotoCurrent') && inst.currentDay ? currentDate : today);
            currentText = (!navigationAsDateFormat ? currentText :
			this.formatDate(currentText, gotoDate, this._getFormatConfig(inst)));
            var controls = (!inst.inline ? '<button type="button" class="ui-datepicker-close ui-state-default ui-priority-primary ui-corner-all" onclick="DP_jQuery_' + dpuuid +
			'.datepicker._hideDatepicker();">' + this._get(inst, 'closeText') + '</button>' : '');
            var buttonPanel = (showButtonPanel) ? '<div class="ui-datepicker-buttonpane ui-widget-content">' + (isRTL ? controls : '') +
			(this._isInRange(inst, gotoDate) ? '<button type="button" class="ui-datepicker-current ui-state-default ui-priority-secondary ui-corner-all" onclick="DP_jQuery_' + dpuuid +
			'.datepicker._gotoToday(\'#' + inst.id + '\');"' +
			'>' + currentText + '</button>' : '') + (isRTL ? '' : controls) + '</div>' : '';
            var firstDay = parseInt(this._get(inst, 'firstDay'), 10);
            firstDay = (isNaN(firstDay) ? 0 : firstDay);
            var showWeek = this._get(inst, 'showWeek');
            var dayNames = this._get(inst, 'dayNames');
            var dayNamesShort = this._get(inst, 'dayNamesShort');
            var dayNamesMin = this._get(inst, 'dayNamesMin');
            var monthNames = this._get(inst, 'monthNames');
            var monthNamesShort = this._get(inst, 'monthNamesShort');
            var beforeShowDay = this._get(inst, 'beforeShowDay');
            var showOtherMonths = this._get(inst, 'showOtherMonths');
            var selectOtherMonths = this._get(inst, 'selectOtherMonths');
            var calculateWeek = this._get(inst, 'calculateWeek') || this.iso8601Week;
            var defaultDate = this._getDefaultDate(inst);
            var html = '';
            var group, selectedDate, cornerClass, calender, thead, dow;


            for (var row = 0; row < numMonths[0]; row++) {
                group = '';
                this.maxRows = 4;
                for (var col = 0; col < numMonths[1]; col++) {
                    selectedDate = this._daylightSavingAdjust(new Date(drawYear, drawMonth, inst.selectedDay));
                    cornerClass = ' ui-corner-all';
                    calender = '';
                    if (isMultiMonth) {
                        calender += '<div class="ui-datepicker-group';
                        if (numMonths[1] > 1) {
                            switch (col) {
                                case 0:
                                    calender += ' ui-datepicker-group-first';
                                    cornerClass = ' ui-corner-' + (isRTL ? 'right' : 'left');
                                    break;
                                case numMonths[1] - 1:
                                    calender += ' ui-datepicker-group-last';
                                    cornerClass = ' ui-corner-' + (isRTL ? 'left' : 'right');
                                    break;
                                default:
                                    calender += ' ui-datepicker-group-middle';
                                    cornerClass = '';
                                    break;
                            }
                        }
                        calender += '">';
                    }
                    calender += '<div class="ui-datepicker-header ui-widget-header ui-helper-clearfix' + cornerClass + '">' +
                    (/all|left/.test(cornerClass) && row === 0 ? (isRTL ? nextYear : prevYear) : '') +
					(/all|left/.test(cornerClass) && row === 0 ? (isRTL ? next : prev) : '') +
				    (/all|right/.test(cornerClass) && row === 0 ? (isRTL ? prevYear : nextYear) : '') +
					(/all|right/.test(cornerClass) && row === 0 ? (isRTL ? prev : next) : '') +
					this._generateMonthYearHeader(inst, drawMonth, drawYear, minDate, maxDate,
					row > 0 || col > 0, monthNames, monthNamesShort) + // draw month headers
					'</div><table class="ui-datepicker-calendar"><thead>' +
					'<tr>';
                    thead = (showWeek ? '<th class="ui-datepicker-week-col">' + this._get(inst, 'weekHeader') + '</th>' : '');

                    for (dow = 0; dow < 7; dow++) { // days of the week
                        var day = (dow + firstDay) % 7;
                        thead += '<th' + ((dow + firstDay + 6) % 7 >= 5 ? ' class="ui-datepicker-week-end"' : '') + '>' +
						'<span title="' + dayNames[day] + '">' + dayNamesMin[day] + '</span></th>';
                    }
                    calender += thead + '</tr></thead><tbody>';
                    var daysInMonth = this._getDaysInMonth(drawYear, drawMonth);
                    if (drawYear == inst.selectedYear && drawMonth == inst.selectedMonth) {
                        inst.selectedDay = Math.min(inst.selectedDay, daysInMonth);
                    }
                    var leadDays = (this._getFirstDayOfMonth(drawYear, drawMonth) - firstDay + 7) % 7;
                    var curRows = Math.ceil((leadDays + daysInMonth) / 7); // calculate the number of rows to generate
                    var numRows = (isMultiMonth ? this.maxRows > curRows ? this.maxRows : curRows : curRows); //If multiple months, use the higher number of rows (see #7043)
                    this.maxRows = numRows;
                    var printDate = this._daylightSavingAdjust(new Date(drawYear, drawMonth, 1 - leadDays));
                    var realMonth = printDate.getMonth() + 1;

                    var createDateClass = function (dow, otherMonth, unselectable, daySettings) {
                        var classes = [];
                        if ((dow + firstDay + 6) % 7 >= 5) {
                            classes.push('ui-datepicker-week-end');
                        } // highlight weekend
                        if (otherMonth) {
                            classes.push('ui-datepicker-other-month');
                        } // highlight days from other months
                        if ((printDate.getTime() == selectedDate.getTime() && drawMonth == inst.selectedMonth && inst._keyEvent) || // user pressed key
							(defaultDate.getTime() == printDate.getTime() && defaultDate.getTime() == selectedDate.getTime())) // or defaultDate is current printedDate and defaultDate is selectedDate
                        {
                            classes.push(this._dayOverClass); // highlight selected day
                        }
                        if (unselectable) {
                            classes.push(this._unselectableClass + ' ui-state-disabled');
                        }   // highlight unselectable days
                        if (!(otherMonth && !showOtherMonths)) {
                            classes.push(daySettings[1]);
                        } // highlight custom dates
                        if (printDate.getTime() == currentDate.getTime()) {
                            classes.push(this._currentClass);
                        }
                        if (printDate.getTime() == today.getTime()) {
                            classes.push('ui-datepicker-today');
                        }
                        if (classes.length > 0) {
                            return ' class="' + classes.join(' ') + '"';
                        }
                        return "";
                    };

                    var createPickerDayContent = function (otherMonth, unselectable, daySettings) {
                        var classes = ['ui-state-default'];
                        if (otherMonth && !showOtherMonths) {
                            return '&#160;';
                        }
                        if (!unselectable) {
                            if (printDate.getTime() == today.getTime()) {
                                classes.push('ui-state-highlight');
                            }
                            if (printDate.getTime() == currentDate.getTime()) {
                                classes.push('ui-state-active');
                            }
                            if (otherMonth) {
                                classes.push('ui-priority-secondary');
                            }

                        }
                        return '<span unselectable="on" class="' + classes.join(' ') + '" style="' + daySettings[3] + '">' + printDate.getDate() + '</span>';

                    };

                    var createPickerDay = function (dow) {
                        var daySettings, otherMonth, unselectable;
                        daySettings = (beforeShowDay ? beforeShowDay.apply((inst.input ? inst.input[0] : null), [printDate]) : [true, '', '', '']);
                        otherMonth = (printDate.getMonth() != drawMonth);
                        unselectable = (otherMonth && !selectOtherMonths) || !daySettings[0] || (minDate && printDate < minDate) || (maxDate && printDate > maxDate);

                        return '<td' + (unselectable ? ' unselectable="on"' : ' id="dp' + printDate.getTime() + '"') // use date as id
                            + createDateClass(dow, otherMonth, unselectable, daySettings) + // highlight today (if different)
							((!otherMonth || showOtherMonths) && daySettings[2] ? ' title="' + daySettings[2] + '"' : '') + // cell title
                            '>' + // actions
							createPickerDayContent(otherMonth, unselectable, daySettings) +
							'</td>'; // display selectable date
                    };


                    for (var dRow = 0; dRow < numRows; dRow++) { // create date picker rows
                        calender += '<tr>';
                        var tbody = (!showWeek ? '' : '<td class="ui-datepicker-week-col">' + this._get(inst, 'calculateWeek')(printDate) + '</td>');

                        for (dow = 0; dow < 7; dow++) { // create date picker days
                            tbody += createPickerDay(dow);
                            printDate.setDate(printDate.getDate() + 1);
                            printDate = this._daylightSavingAdjust(printDate);
                            realMonth = printDate.getMonth() + 1;
                        }
                        calender += tbody + '</tr>';
                    }
                    drawMonth++;
                    if (drawMonth > 11) {
                        drawMonth = 0;
                        drawYear++;
                    }
                    calender += '</tbody></table>' + (isMultiMonth ? '</div>' +
							((numMonths[0] > 0 && col == numMonths[1] - 1) ? '<div class="ui-datepicker-row-break"></div>' : '') : '');
                    group += calender;
                }
                html += group;
            }
            html += buttonPanel + ($.browser.msie && parseInt($.browser.version, 10) < 7 && !inst.inline ?
			'<iframe src="javascript:false;" class="ui-datepicker-cover" frameborder="0"></iframe>' : '');
            inst._keyEvent = false;

            //var element = document.createE('img');


            var onChange = this._get(inst, 'onHtmlGenerated');
            if (onChange) {
                onChange.apply((inst.input ? inst.input[0] : null), [inst]);
            }

            return html;
        }


    });

})(jQuery);