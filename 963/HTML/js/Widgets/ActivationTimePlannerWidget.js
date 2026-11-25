/*!
* Activation time planner widget.   
* This is a custom JQuery UI widget to allows user to view and edit the activation period time scheme.
*
* Date: Wed March 28, 2012
* Copyright 2008-2012 Honeywell Technologies Sàrl, ECC Division. All rights reserved. Copyright 1995-2008 Trend Control Systems Ltd.
*/

/*jslint browser:true*/
/*globals ECALENDAR*/
/*globals alert*/
/*globals $ 
globals jQuery
globals document
*/


$(function () {
    "use strict";

    $.widget("ui.activationTimePlanner", {

        $timePlannerContainer: null,
        _getEventListeningObject: function () {
            return this.options.eventListeningObject || this.$timePlannerContainer.find('.activationTimePlannerContainer');
        },
        _setUpMouseLeave: function (callback) {
            return function (event) {
                var originalContext = this,
                mouseUpHandler = function (e) {
                    $(this).unbind('mouseup.timePlanner');
                    callback.call(originalContext, event);
                };
                $(document).unbind('mouseup.timeplanner').bind('mouseup.timeplanner', mouseUpHandler);
            };
        },
        _setUpMouseEnter: function () {
            $(document).unbind('mouseup.timeplanner');
        },

        //user interface options, used for internal purpose only.
        uiOptions: {
            minTimeSupported: 5,        //Minimum time rendering interval will be 5 minutes in the user interface.
            pxPerMinTimeBlock: 2,       //Default Time block is a minTimeSupported block means it supports 5 minutes. 2 pixels will be used to show 5 minutes in the user interface.
            pxPerQuarterTimeBlock: 6,   //When Ctrl key is pressed and moved the time period, movement of the time period must be based on 15 minute gap. 6 pixels reprensents 15 minutes.
            pxPerHalfTimeBlock: 12,     //If Shift key is pressed and time period is moved, movement of the time period must be based on the 30 minutes. 12 pixels represents 30 minutes.
            hourImageCount: 24,         //This variable represents the number of images we need to draw entire day structure. Actually we are drawing per hour one image so to display entire day we need 24 days.
            hourImageWidth: 24,         //Image hour width.
            resizeButtonWidth: 12,      //Resize button width.
            resizeButtonHeight: 12,     //Resize button height.
            dayHeight: 36,              //Height of a day in pixels
            dayMiddleGap: 10,           //Middle gap between two days
            timeBarHeight: 12,          //Time bar height (i.e. Height of the text 00:00, 02:00 title in the user interface.
            dayTitleContainerWidth: 48,  //Day title container width - which is prefixed area in the day.
            newTimePeriodContainerWidth: 36,    //Width of the new time planner div.
            timePeriodIDPrefix: 'daySelectionPeriod_',    //Prefix for the time period id.
            DELKeyCode: 46,
            activationPeriodColour: '#6464ff', //Background colour for activation periods
            activationPeriodClass: 'timePeriodStyle',
            containerClass: 'dayContainer'

        },

        options: {
            //TODO: In future we need to display the special day model as way.
            weekSetModelObject: new ECALENDAR.WeekSetModel(),
            containerID: 'activationTimePlannerContainer',
            isEditable: true,
            maxNumOfActivationPeriods: 10
        },
        _rtl: false,
        _cssProperty: 'left',
        _getDimensions: function () {
            var timeslots = this.$timePlannerContainer.find('.timeslot'),
            headers = this.$timePlannerContainer.find('.timeslot-header'),
            containerWidth = this.$timePlannerContainer.find('.' + this.uiOptions.containerClass).outerWidth(),
            timeslotWidth = timeslots.outerWidth(),
            perMinute = (timeslotWidth / 60), headerWidth = headers.outerWidth();

            var convertPixelsToPercent = function (px) {
                return ((px / containerWidth) * 100);
            };
            var convertPercentToPixels = function (value) {
                return ((value / 100) * containerWidth);
            };
            var convertPercentToString = function (value) {
                return value + "%";
            };

            var headerPercent = convertPixelsToPercent(headerWidth),
                minutePercent = convertPixelsToPercent(perMinute);

            var getPxValue = function (value) {
                if (typeof value === "string" && value.indexOf('%') > -1) {
                    var px = convertPercentToPixels(parseFloat(value, 10));
                    return parseFloat(px, 10);
                }
                return parseFloat(value, 10);
            };

            var getPercentValue = function (value) {
                if (typeof value === "string" && value.indexOf('%') == -1) {
                    return convertPixelsToPercent(parseFloat(value, 10));
                }
                return parseFloat(value, 10);
            };


            var getPositionForMinutes = function (minutes) {
                return ((perMinute * minutes) + headerWidth);
            };

            var getStartPixelsForObj, getEndPixelsForObj, getWidthPixelsForObj;

            getStartPixelsForObj = function (obj) {
                if (obj.getAttribute('startHour')) {
                    return getPositionForMinutes(((parseInt(obj.getAttribute('startHour'), 10) || 0) * 60) + (parseInt(obj.getAttribute('startMinute'), 10) || 0));
                }

                return getPxValue(obj.style.left);
            };
            getEndPixelsForObj = function (obj) {
                if (obj.getAttribute('endHour')) {

                    return getPositionForMinutes(((parseInt(obj.getAttribute('endHour'), 10) || 0) * 60) + (parseInt(obj.getAttribute('endMinute'), 10) || 0));
                }

                return getWidthPixelsForObj(obj) + getStartPixelsForObj(obj);
            };

            getWidthPixelsForObj = function (obj) {

                if (obj.getAttribute('endHour')) {
                    return getEndPixelsForObj(obj) - getStartPixelsForObj(obj);
                }

                return getPxValue(obj.style.width);
            };


            var getStartTime = function (obj) {
                var temp = new ECALENDAR.ActivationPeriodDataStructure();

                temp.setMinutes(Math.round(((getPercentValue(obj.style.left) - headerPercent) / minutePercent)));
                return temp;
            };

            var getEndTime = function (obj) {
                var temp = new ECALENDAR.ActivationPeriodDataStructure();
                temp.setMinutes(Math.round((getPercentValue(obj.style.width) / minutePercent)) + getStartTime(obj).getTotalMinutes());
                return temp;

            };

            var getStartTimeFromMoveArea = function (moveArea) {
                var temp = new ECALENDAR.ActivationPeriodDataStructure();

                temp.setMinutes(Math.round(((moveArea.left - headerWidth) / perMinute)));
                return temp;
            };
            var getEndTimeFromMoveArea = function (moveArea) {
                var temp = new ECALENDAR.ActivationPeriodDataStructure();
                temp.setMinutes(Math.round(((moveArea.right - moveArea.left) / perMinute)) + getStartTimeFromMoveArea(moveArea).getTotalMinutes());
                return temp;
            };

            return {
                convertPxToPercentString: function (value) {
                    return convertPercentToString(convertPixelsToPercent(value));
                },
                getEndPixelsForObj: getEndPixelsForObj,
                getStartPixelsForObj: getStartPixelsForObj,
                getWidthPixelsForObj: getWidthPixelsForObj,
                getPxValue: getPxValue,
                getStartTime: getStartTime,
                getEndTime: getEndTime,
                getStartTimeFromMoveArea: getStartTimeFromMoveArea,
                getEndTimeFromMoveArea: getEndTimeFromMoveArea,
                getPositionForMinutes: getPositionForMinutes
            };

        },



        _getParentArea: function () {
            return { left: this.dims.getPositionForMinutes(0), right: this.dims.getPositionForMinutes(this.uiOptions.hourImageCount * 60) };

        },
        _getRectangle: function (obj) {
            return {
                left: this.dims.getStartPixelsForObj(obj),
                right: this.dims.getEndPixelsForObj(obj)
            };
        },
        //Create custom HTML controls
        _create: function () {
            var dir = document.body.getAttribute('dir');
            if (dir && dir === "rtl") {
                this._rtl = true;
                this._cssProperty = "right";
            }


            //Generate the user interface and do event handling.
            this._createUI();

            //Disable the user text selection for the time planner control.
            this._disableSelection(this.$timePlannerContainer);
        },

        //Create user interface.
        _createUI: function () {

            //Show here current selection Divs for the given time period
            var count = 0, attrs = this.options.weekSetModelObject.attributes;
            for (count = 0; count < attrs.arrDay.length; count += 1) {
                if (attrs.arrDay[count].validate()) {
                    var containerDiv = this.element[0];
                    containerDiv.innerHTML = "<p>#@Input data-model is not valid. User interface can not be created.</p>";
                    return; //TODO: Put a message that no drawing possible because of invalid object of the arrDay.
                }
            }

            //timePlanner container element: To improve the performance.
            this.$timePlannerContainer = $(this.element[0]);

            //As we have all the data structure ready needed for rendering the control. Render them in the available area.
            this._renderControl();

            if (this.options.isEditable === true) {
                //All the event handling stuff should go here. User interaction is mainly considered in the event handling work.
                this._userInteraction();
            }
            this.dims = this._getDimensions();
        },

        //Apply here event handling techniques.
        _userInteraction: function () {

            //Event handling to resize the time period            
            this._handleTimePeriodResizeEvent();

            //Event handling to move the time period
            this._handleMoveTimePeriod();
            this._handleMoveNewPeriod();
        },

        //Reset the selection of the currently selected time period
        removeTimePeriodSelection: function () {

            this.$timePlannerContainer.attr("timePeriodSelID", '');
            this.$timePlannerContainer.attr("timePeriodSelParentID", '');
            //TODO: Might be in future we need to do other stuff as well here. 
        },

        //Remove the time period from the day container.
        removeTimePeriod: function ($timePeriod) {
            var self, $parent, $this;
            self = this;
            if (($timePeriod !== null) && ($timePeriod.length > 0)) {
                $parent = $timePeriod.parent();
                $timePeriod.remove();

                //Re-arrange the ids of the time period in the day container.
                $parent.find("." + this.uiOptions.activationPeriodClass).each(function (index) {
                    this.id = self.uiOptions.timePeriodIDPrefix.toString() + (index * 2).toString();
                });

                //re-enable newTimePeriod div for the day
                this._enableAddNewTimePeriod(this._getTimePeriodContainer($parent));
                
                this._trigger('timeperiod_removed', undefined, {
                    period: this.$timePlannerContainer.attr("timePeriodSelID"),
                    day: this.$timePlannerContainer.attr("timePeriodSelParentID")
                });
                //Now there is should not be anything selected by default
                this.removeTimePeriodSelection();
            }
        },
        _getTimePeriodContainer: function (target) {
            return target.closest('.' + this.uiOptions.containerClass);
        },
        isDayEmpty: function (day) {
            var container = this._getTimePeriodContainer(day);
            return (container.find('.' + this.uiOptions.activationPeriodClass).length == 0);
        },
        isWorkingWeekEmpty: function () {
            var isEmpty = true, self = this;
            this.$timePlannerContainer.find('.' + this.uiOptions.containerClass).each(function (i) {
                if (i === 5) {
                    return false;
                }
                var $this = $(this);
                var container = self._getTimePeriodContainer($this);
                if (container.find('.' + self.uiOptions.activationPeriodClass).length != 0) {
                    isEmpty = false;
                }
            });
            return isEmpty;
        },
        isWeekEmpty: function () {
            return (this.$timePlannerContainer.find('.' + this.uiOptions.activationPeriodClass).length == 0);
        },
        copyDay: function (day) {
            var container = this._getTimePeriodContainer(day);
            ECALENDAR.activationWidgetClipboard = container.find('.' + this.uiOptions.activationPeriodClass).clone().removeClass('focus');
        },
        cutDay: function (day) {
            var container = this._getTimePeriodContainer(day);
            ECALENDAR.activationWidgetClipboard = container.find('.' + this.uiOptions.activationPeriodClass).remove().removeClass('focus');
            this._enableAddNewTimePeriod(this._getTimePeriodContainer(container));
            this.removeTimePeriodSelection();
            this._trigger('timeperiod_removed', undefined);
        },
        canCopyOrCut: function (day) {
            if (day.hasClass(this.uiOptions.activationPeriodClass)) {
                return true;
            }
            return day.find('.' + this.uiOptions.activationPeriodClass).length > 0;
        },
        canPaste: function () {
            return ECALENDAR.hasOwnProperty('activationWidgetClipboard') && (ECALENDAR.activationWidgetClipboard.length <= this.options.maxNumOfActivationPeriods);
        },
        pasteDay: function (day) {
            if (!ECALENDAR.activationWidgetClipboard) {
                return;
            }
            var container = this._getTimePeriodContainer(day);

            this.offAllDay(container);
            container.append(ECALENDAR.activationWidgetClipboard.clone());

            if (ECALENDAR.activationWidgetClipboard.length === this.options.maxNumOfActivationPeriods) {
                this._disableAddNewTimePeriod(this._getTimePeriodContainer(container));
            }
            else {
                this._enableAddNewTimePeriod(this._getTimePeriodContainer(container));
            }

            this._handleMoveTimePeriod();
            this._handleTimePeriodResizeEvent();
        },
        pasteWorkingWeek: function () {
            var self = this;
            if (!ECALENDAR.activationWidgetClipboard) {
                return;
            }

            var disableActivation = ECALENDAR.activationWidgetClipboard.length === this.options.maxNumOfActivationPeriods;

            this.$timePlannerContainer.find('.' + this.uiOptions.containerClass).each(function (i) {
                if (i === 5) {
                    return false;
                }
                var $this = $(this);
                self.offAllDay($this);
                $this.append(ECALENDAR.activationWidgetClipboard.clone());
                if (disableActivation) {
                    self._disableAddNewTimePeriod(self._getTimePeriodContainer($this));
                }
                else {
                    self._enableAddNewTimePeriod(self._getTimePeriodContainer($this));
                }
            });

            this._handleMoveTimePeriod();
            this._handleTimePeriodResizeEvent();
        },
        pasteWeek: function () {
            if (!ECALENDAR.activationWidgetClipboard) {
                return;
            }
            this.offAllWeek();
            this.$timePlannerContainer.find('.' + this.uiOptions.containerClass).append(ECALENDAR.activationWidgetClipboard);
            if (ECALENDAR.activationWidgetClipboard.length === this.options.maxNumOfActivationPeriods) {
                this._disableAddNewTimePeriod(this.$timePlannerContainer.find('.' + this.uiOptions.containerClass));
            }
            else {
                this._enableAddNewTimePeriod(this.$timePlannerContainer.find('.' + this.uiOptions.containerClass));
            }
            this._handleMoveTimePeriod();
            this._handleTimePeriodResizeEvent();
        },
        offAllWeek: function () {
            this.$timePlannerContainer.find('.' + this.uiOptions.activationPeriodClass).remove();
            this._enableAddNewTimePeriod(this.$timePlannerContainer.find('.' + this.uiOptions.containerClass));
            this.removeTimePeriodSelection();
            this._trigger('timeperiod_removed', undefined);
        },
        offWorkingWeek: function () {
            var self = this;
            this.$timePlannerContainer.find('.' + this.uiOptions.containerClass).each(function (i) {
                if (i === 5) {
                    return false;
                }
                var $this = $(this);
                self.offAllDay($this);

            });

        },
        offAllDay: function (day) {
            var $day = this._getTimePeriodContainer(day);
            if ($day.find('.focus').length > 0) {
                this.removeTimePeriodSelection();
                this._trigger('timeperiod_removed', undefined);
            }
            $day.find('.' + this.uiOptions.activationPeriodClass).remove();
            this._enableAddNewTimePeriod($day);
        },
        onAllDay: function (day) {
            var selLeft, selRight, selSize, start, end, dayContainer, selectionDiv;
            dayContainer = this._getTimePeriodContainer(day);
            this.offAllDay(dayContainer);

            start = new ECALENDAR.ActivationPeriodDataStructure();
            end = new ECALENDAR.ActivationPeriodDataStructure();
            end.setTime(24, 0);
            selectionDiv = this.addDivToPlanner(start, end, 0, dayContainer);

            this._handleMoveTimePeriod();
            this._handleTimePeriodResizeEvent();
            //Select this time period.
            this._selectTimePeriod(selectionDiv.get(0));
            this._trigger('timeperiod_move_end', undefined, {
                period: this.$timePlannerContainer.attr("timeperiodselid"),
                day: this.$timePlannerContainer.attr("timeperiodselparentid"),
                start: this._getStartTime(selectionDiv),
                end: this._getEndTime(selectionDiv)
            });

        },
        onAllWeek: function () {
            var start, end, self = this;
            start = new ECALENDAR.ActivationPeriodDataStructure();
            end = new ECALENDAR.ActivationPeriodDataStructure();
            end.setTime(24, 0);
            this.offAllWeek();


            this.addDivToPlanner(start, end, 0, this.$timePlannerContainer.find('.' + this.uiOptions.containerClass));
            this._handleMoveTimePeriod();
            this._handleTimePeriodResizeEvent();

        },
        onWorkingWeek: function () {
            var start, end, self = this;
            start = new ECALENDAR.ActivationPeriodDataStructure();
            end = new ECALENDAR.ActivationPeriodDataStructure();
            end.setTime(24, 0);
            this.removeTimePeriodSelection();
            this.$timePlannerContainer.find('.' + this.uiOptions.containerClass).each(function (i, obj) {
                if (i === 5) {
                    return false;
                }
                self.offAllDay(this);
                self.addDivToPlanner(start, end, 0, $(this));
            });
            this._handleMoveTimePeriod();
            this._handleTimePeriodResizeEvent();
        },
        _generateActivationPeriodAttributes: function (start, end) {
            var atts = { "startHour": start.getHours(),
                "startMinute": start.getMinutes(),
                "endHour": end.getHours(),
                "endMinute": end.getMinutes(),
                "title": ECALENDAR.ApplicationStrings.getResourceFromID('STRING_FROM') + ' ' + start.timeAsString() +
				' ' + ECALENDAR.ApplicationStrings.getResourceFromID('STRING_TO') + ' ' + end.timeAsString()
            };
            return atts;
        },
        //This function will update the related information about the time periods available for the weekset.
        //It will update the title attribute of the time period.
        updateTimePeriodDetail: function (timePeriod, moveArea) {
            //Caller function did not pass the valid timePeriod, update all the timePeriod available.
            var selector = $(timePeriod), self = this;
            if (timePeriod === undefined || timePeriod === null) {
                selector = this.$timePlannerContainer.find('.' + this.uiOptions.activationPeriodClass);
            }


            //Update the title for the time period(s).
            selector.each(function (index) {
                var $this, startMinutes, tempActivationTimePeiod, endMinutes, tempActivationTimePeiod1, titleValue;
                $this = $(this);

                if (self.dims) {

                    if (moveArea && selector.length === 1) {

                        tempActivationTimePeiod = self.dims.getStartTimeFromMoveArea(moveArea);
                        tempActivationTimePeiod1 = self.dims.getEndTimeFromMoveArea(moveArea);
                    }
                    else {
                        //if you were to be looping through items, try and get detail from dimensions - which doesn't work so well with IE.
                        tempActivationTimePeiod = self.dims.getStartTime(this);
                        tempActivationTimePeiod1 = self.dims.getEndTime(this);
                    }
                } else {

                    //kp: happens on initial load.
                    //Start time.        
                    startMinutes = Math.round(((parseFloat(this.style.left, 10) - self.uiOptions.dayTitleContainerWidth) * self.uiOptions.minTimeSupported) / self.uiOptions.pxPerMinTimeBlock);
                    tempActivationTimePeiod = new ECALENDAR.ActivationPeriodDataStructure();
                    tempActivationTimePeiod.setMinutes(startMinutes);
                    //End time.
                    endMinutes = Math.round(((parseFloat(this.style.left, 10) + parseFloat(this.style.width, 10) - self.uiOptions.dayTitleContainerWidth) * self.uiOptions.minTimeSupported) / self.uiOptions.pxPerMinTimeBlock);
                    tempActivationTimePeiod1 = new ECALENDAR.ActivationPeriodDataStructure();
                    tempActivationTimePeiod1.setMinutes(endMinutes);

                }

                $this.attr(self._generateActivationPeriodAttributes(tempActivationTimePeiod, tempActivationTimePeiod1));

            });
        },
        _pad: function (n) {
            if (!n && n !== 0) {
                return;
            }
            if (n.toString().length === 1) {
                return '0' + n;
            }
            return n.toString();
        },
        _getStartTime: function (period) {
            var $period = (period instanceof jQuery) ? period : $(period);
            return { hour: this._pad($period.attr('startHour')), minute: this._pad($period.attr('startMinute')) };
        },
        _getEndTime: function (period) {
            var $period = (period instanceof jQuery) ? period : $(period);

            return { hour: this._pad($period.attr('endHour')), minute: this._pad($period.attr('endMinute')) };
        },
        updateEndTime: function (time, selId, parentId) {
            this.dims = this.dims || this._getDimensions();
            selId = selId || this.$timePlannerContainer.attr("timeperiodselid");
            parentId = parentId || this.$timePlannerContainer.attr("timeperiodselparentid");

            var $element = this.$timePlannerContainer.find('#' + parentId).find(' #' + selId);
            if ($element.length === 0) {
                return;
            }

            var moveArea, divParent, parentArea, css;
            var startTime = ((parseInt($element.attr('startHour'), 10) || 0) * 60) + (parseInt($element.attr('startMinute'), 10) || 0);


            moveArea = {
                left: this.dims.getPositionForMinutes(startTime),
                right: this.dims.getPositionForMinutes(time)
            };



            //Check the intersection of the user preferred are with its neighbour time period. If they are intersecting don't move the position of the control.
            divParent = $element.parent().get(0);
            if (this.isValidArea(moveArea)) {

                if (this.isIntersectNeighbourTimePeriod(selId, divParent, moveArea)) {
                    moveArea = this.getExtendedAreaFromAdjacentTimePeriod(selId, divParent, moveArea, false);
                }

                //Final check - identify whether it crosses the parent element's border. If it is not crossing parent border move the element.
                parentArea = this._getParentArea();

                //The mouse point must be inside the parent, than only allow the move the time period area.
                if (!ECALENDAR.AppUtilities.insideLine(parentArea, moveArea)) {
                    moveArea.right = parentArea.right;
                }
                css = { width: this.dims.convertPxToPercentString(moveArea.right - moveArea.left) };
                css[this._cssProperty] = this.dims.convertPxToPercentString(moveArea.left);

                $element.css(css);
                this.updateTimePeriodDetail($element.get(0), moveArea);
            }
            this._trigger('timeperiod_move', undefined, { period: selId, day: parentId, start: this._getStartTime($element), end: this._getEndTime($element) });


        },
        updateStartTime: function (time, selId, parentId) {
            if (!this.dims) {
                this.dims = this._getDimensions();
            }

            selId = selId || this.$timePlannerContainer.attr("timeperiodselid");
            parentId = parentId || this.$timePlannerContainer.attr("timeperiodselparentid");

            var $element = this.$timePlannerContainer.find('#' + parentId).find(' #' + selId);
            if ($element.length === 0) {
                return;
            }

            var moveArea, divParent, css;
            var endTime = ((parseInt($element.attr('endHour'), 10) || 0) * 60) + (parseInt($element.attr('endMinute'), 10) || 0);
            moveArea = {
                left: this.dims.getPositionForMinutes(time),
                right: this.dims.getPositionForMinutes(endTime)
            };


            //Check the intersection of the user preferred are with its neighbour time period. If they are intersecting don't move the position of the control.
            divParent = $element.parent().get(0);
            if (this.isValidArea(moveArea)) {

                if (this.isIntersectNeighbourTimePeriod(selId, divParent, moveArea)) {
                    moveArea = this.getExtendedAreaFromAdjacentTimePeriod(selId, divParent, moveArea, true);
                }

                css = { width: this.dims.convertPxToPercentString(moveArea.right - moveArea.left) };
                css[this._cssProperty] = this.dims.convertPxToPercentString(moveArea.left);
                $element.css(css);
                this.updateTimePeriodDetail($element.get(0), moveArea);

            }
            this._trigger('timeperiod_move', undefined, { period: selId, day: parentId, start: this._getStartTime($element), end: this._getEndTime($element) });
        },

        //Based on the event this function will identify minimum number of pixels one has to move.
        moveTimePeriodPixels: function (event) {
            //Move the element by considering the minimum time (i.e. 5 minutes by default here. 3 pixels are used to represent 5 minutes by default.)
            var pixelsMove = this.uiOptions.pxPerMinTimeBlock;                              //By default, movement must be based on the 5 minutes interval.
            if (event.shiftKey) {
                pixelsMove = this.uiOptions.pxPerHalfTimeBlock; //Movement must be based on the 30 minutes interval.
            } else if (event.ctrlKey) {
                pixelsMove = this.uiOptions.pxPerQuarterTimeBlock;
            }  //Movement must be based on the 15 minutes interval.

            return pixelsMove;
        },

        //Get element move area while performing the element move operation.
        getTimePeriodMoveArea: function (event, elementLeft, elementWidth, mouseDownEventPageX) {
            var moveArea, pixelsMove;

            //If any of the input variable value is null or undefined - we will assume 0 and proceed further
            if ((elementLeft === undefined) || (elementLeft === null)) {
                elementLeft = 0;
            }
            if ((elementWidth === undefined) || (elementWidth === null)) {
                elementWidth = 0;
            }
            if ((mouseDownEventPageX === undefined) || (mouseDownEventPageX === null)) {
                mouseDownEventPageX = 0;
            }

            //Identify the current area where user wants to move the time period.
            if (this._rtl === true) {
                moveArea = {
                    left: elementLeft + (mouseDownEventPageX - event.pageX),
                    right: (elementLeft + (mouseDownEventPageX - event.pageX)) + elementWidth
                };
            }
            else {
                moveArea = {
                    left: elementLeft - (mouseDownEventPageX - event.pageX),
                    right: (elementLeft - (mouseDownEventPageX - event.pageX)) + elementWidth
                };
            }

            pixelsMove = this.moveTimePeriodPixels(event);

            //We now need adjust the move area according to the movement constaint.
            moveArea.left = moveArea.left - (moveArea.left % pixelsMove);
            moveArea.right = moveArea.left + parseFloat(elementWidth, 10);

            return moveArea;
        },

        //During moving the time period, this function will handle the mousemove event, 
        //During the mouse move event it sets the new position /for the time period - Movement of the time period is allowed only within the parent div
        _handleTimePeriodMouseMoveEvent: function (event, elementLeft, elementWidth, mouseDownEventPageX) {
            var element, moveArea, pixelsMove, parentArea, width, movingLeft;
            element = event.currentTarget;

            moveArea = this.getTimePeriodMoveArea(event, elementLeft, elementWidth, mouseDownEventPageX);

            pixelsMove = this.moveTimePeriodPixels(event);

            movingLeft = (moveArea.left <= this.dims.getStartPixelsForObj(element));

            //Check - identify whether it crosses the parent element's border. If it is not crossing parent border move the element.
            parentArea = this._getParentArea();

            //The mouse point must be inside the parent, than only allow the move the time period area.
            if (!ECALENDAR.AppUtilities.insideLine(parentArea, moveArea)) {


                width = moveArea.right - moveArea.left;
                if (parentArea.left >= moveArea.left) {
                    moveArea.left = parentArea.left;
                } else if (parentArea.right <= moveArea.right) {
                    moveArea.left = (parentArea.right - (moveArea.right - moveArea.left));
                }
                moveArea.right = width + moveArea.left;
            }

            var initialLeft = moveArea.left;
            //Check the intersection of the user preferred are with its neighbour time period. If they are intersecting don't move the position of the control.
            if (this.isIntersectNeighbourTimePeriod(element.id, element.parentNode, moveArea)) {
                moveArea = this.getMovedAreaFromAdjacentTimePeriod(element.id, element.parentNode, moveArea, movingLeft);
            }
            var adjustment = (moveArea.left % pixelsMove);
            if (initialLeft !== moveArea.left) {
                adjustment = 0;
            }


            if ((ECALENDAR.AppUtilities.insideLine(parentArea, moveArea)) && (this.isValidArea(moveArea))) {
                element.style[this._cssProperty] = this.dims.convertPxToPercentString(moveArea.left - adjustment);
                this.updateTimePeriodDetail(element, { left: moveArea.left - adjustment, right: moveArea.right });          //Update the title of the div.
            }
          
        },

        //Move the time period user interface operation.
        _handleMoveTimePeriod: function () {
            var self = this;

            //Unbind the existing event handling binding.
            this.$timePlannerContainer.find('.' + this.uiOptions.activationPeriodClass).unbind('mousedown');

            //Mouse down event for the time period
            this.$timePlannerContainer.find('.' + this.uiOptions.activationPeriodClass).mousedown(function (event) {

                self.dims = self.dims || self._getDimensions();

                var element, $element, elementLeft, elementWidth, mouseDownEventPageX, moveTimePeriodMouseMoveHandler, $doc, moveTimePeriodMouseUpHandler;



                //It must be left button of the mouse. Mouse interaction is only allowed with them.
                if ((event.which === 1) || (event.button === 1)) {
                    element = event.currentTarget;
                    $element = $(element);

                    elementLeft = self.dims.getStartPixelsForObj(element);
                    elementWidth = self.dims.getWidthPixelsForObj(element);

                    mouseDownEventPageX = parseFloat(event.pageX, 10);

                    //Mouse move handler for setting the capture.
                    moveTimePeriodMouseMoveHandler = function (event) {
                        event.currentTarget = element;
                        self._handleTimePeriodMouseMoveEvent(event, elementLeft, elementWidth, mouseDownEventPageX);
                        self._trigger('timeperiod_move', undefined, { period: self.$timePlannerContainer.attr("timeperiodselid"), day: self.$timePlannerContainer.attr("timeperiodselparentid"), start: self._getStartTime(element), end: self._getEndTime(element) });

                        event.preventDefault();
                    };
                    $doc = self._getEventListeningObject();
                    //Mouse up handler for releasing the capture.
                    moveTimePeriodMouseUpHandler = function (event) {
                        var $doc = $(this);
                        //Un bind all the document events here.
                        $doc.unbind('mousemove.timeplanner');
                        $doc.unbind('mouseup.timeplanner');
                        $doc.unbind('mouseleave.timeplanner');
                        self._trigger('timeperiod_move_end', undefined, { period: self.$timePlannerContainer.attr("timeperiodselid"), day: self.$timePlannerContainer.attr("timeperiodselparentid"), start: self._getStartTime($element), end: self._getEndTime($element) });
                        event.preventDefault();
                    };

                    //Finally, associate the event handlers so that capture will be set to the element.
                    $doc.bind('mousemove.timeplanner', moveTimePeriodMouseMoveHandler);
                    $doc.bind('mouseup.timeplanner', moveTimePeriodMouseUpHandler);
                    $doc.bind("mouseleave.timeplanner", self._setUpMouseLeave(moveTimePeriodMouseUpHandler));
                    $doc.bind("mouseenter.timeplanner", self._setUpMouseEnter());


                    $doc.bind('blur.timeplanner', moveTimePeriodMouseUpHandler);

                    //break references
                    moveTimePeriodMouseMoveHandler = null;

                    $doc = null;
                }
                //Selection model.
                self._selectTimePeriod(event.currentTarget);

            });
        },

        //Get the first intersecting element
        //currentElement is time period element which we want to move.
        //parentElement is the day container element of the currentElement
        //moveRect is the area where we wish to move the currentElement.
        getIntersectFirstTimePeriod: function (currentElement, parentElement, moveRect) {
            var returnValue, self, $currentElement, $this, divRect;
            returnValue = null;
            self = this;
            //If null case for the input parameters.
            if ((currentElement === undefined) || (currentElement === null) ||
					(parentElement === undefined) || (parentElement === null)) {
                return returnValue;
            }

            //Now seach for the interesting element.
            $(parentElement).find("." + this.uiOptions.activationPeriodClass + ":not('#" + currentElement.id + "')").each(function (index) {
                $this = $(this);

                divRect = self._getRectangle(this);

                //Intersection for the avialable two rectangle.
                if (ECALENDAR.AppUtilities.intersectLine(divRect, moveRect)) {
                    returnValue = this;
                    return false;   //Now, moving out of the function using this return.
                }

            });

            return returnValue;
        },

        //Disable the selection in this control.
        _disableSelection: function (target) {
            if (typeof target[0].onselectstart !== "undefined") {
                target[0].onselectstart = function () {
                    return false;
                }; //IE route
            } else if (typeof target[0].style.MozUserSelect !== "undefined") { //Firefox route
                target[0].style.MozUserSelect = "none";
            }

            //only put this listener on the widget div not the document, because it breaks external widgets.
            //Stop the drgging functionality of the newTimePeriod image.
            this.$timePlannerContainer.find('.activationTimePlannerContainer').bind('dragstart', function (event) {
                event.preventDefault();
                event.stopImmediatePropagation();
                return true;
            });
        },

        //This will render the time bar information in the given left and the top position.
        _generateTimeBarHTML: function (leftPosition, topPosition, hour) {

            //If values are improper assume it as 0.
            if (topPosition == null) {
                topPosition = 0;
            }
            if (leftPosition == null) {
                leftPosition = 0;
            }

            //Default values.
            var htmlContent, preTitleHour;
            htmlContent = "";

            preTitleHour = hour.toString();
            if (preTitleHour.length === 1) {
                preTitleHour = '0' + preTitleHour;
            }
            htmlContent += '<span class="timebar-hour-label" >' + preTitleHour + ':00</span>';

            return htmlContent;
        },

        //Set option is widget factory method, override here the attributes and user interface behaviour.
        _setOption: function (key, value) {
            // In jQuery UI 1.8, you have to manually invoke the _setOption method from the base widget
            $.Widget.prototype._setOption.apply(this, arguments);
            // In jQuery UI 1.9 and above, you use the _super method instead
            //this._super("_setOption", key, value);

            //Post operation - now redraw the widget.
            switch (key) {
                case "weekSetModelObject":
                    this._reCreateUI();
                    break;
            }
        },


        //Set week set data model
        setWeeksetDataModel: function (newWeekSetDataModel) {
            this._setOption('weekSetModelObject', newWeekSetDataModel);
        },

        //Re-create the user interface, this will cleanup the existing user interface and create it back from the 
        _reCreateUI: function () {
            //TODO:Remove the existing DOM model.
            $(this.element[0]).empty();
            delete this.dims;
            //Update the user interface.
            this._createUI();
        },

        //Get week set data model.
        getWeeksetDataModel: function () {
            //Form here the weekset data model.
            var tempDataModel, cnt, addTimePeriodToModel;

            if (this.options.weekSetModelObject instanceof ECALENDAR.SpecialDayModel) {
                tempDataModel = new ECALENDAR.SpecialDayModel({ specialDayID: this.options.weekSetModelObject.id });
            }
            else {
                tempDataModel = new ECALENDAR.WeekSetModel({ weekSetID: this.options.weekSetModelObject.id });
            }



            addTimePeriodToModel = function (index) {
                var $this, startActivationTimePeriod, endActivationTimePeriod;
                $this = $(this);

                //Start activation time period
                startActivationTimePeriod = new ECALENDAR.ActivationPeriodDataStructure();
                startActivationTimePeriod.setTime(parseInt($this.attr('startHour'), 10), parseInt($this.attr('startMinute'), 10));
                startActivationTimePeriod.setValue(1);
                //End activation time period.
                endActivationTimePeriod = new ECALENDAR.ActivationPeriodDataStructure();
                endActivationTimePeriod.setTime(parseInt($this.attr('endHour'), 10), parseInt($this.attr('endMinute'), 10));
                endActivationTimePeriod.setValue(0);

                //Push them into the data-model
                tempDataModel.get('arrDay')[cnt].arrActivationPeriod.push(startActivationTimePeriod);
                tempDataModel.get('arrDay')[cnt].arrActivationPeriod.push(endActivationTimePeriod);
            };

            for (cnt = 0; cnt < this.options.weekSetModelObject.get('arrDay').length; cnt += 1) {
                //Copy very first existing number of days in the data-model.
                tempDataModel.get('arrDay')[cnt].setLabel(this.options.weekSetModelObject.get('arrDay')[cnt].getLabel());
                tempDataModel.get('arrDay')[cnt].setDayID(this.options.weekSetModelObject.get('arrDay')[cnt].getDayID());

                tempDataModel.get('arrDay')[cnt].arrActivationPeriod.length = 0;

                //Get all the time period in the day and add them into the data-model.
                this.$timePlannerContainer.find('#dayContainer_' + cnt).find('.' + this.uiOptions.activationPeriodClass).each(addTimePeriodToModel);

                if (tempDataModel.get('arrDay')[cnt].arrActivationPeriod.length === 0) {
                    tempDataModel.get('arrDay')[cnt].addOneEmptyActivationPeriod();
                }
            }

            //Finally return back the model.            
            return tempDataModel;
        },

        createDay: function (htmlContent, dayCount, dayPlannerWidth, singleImageWidth) {
            var imgCount;
            //create title of the day DIV
            htmlContent += '<div class="' + this.uiOptions.containerClass + '" id="dayContainer_' + dayCount + '">';

            //Display the back-ground image in it.
            htmlContent += '<div class="timeslot-header">' + this.options.weekSetModelObject.get('arrDay')[dayCount].getLabel() + '</div>';

            //create the planner control here.
            for (imgCount = 0; imgCount < (this.uiOptions.hourImageCount); imgCount += 1) {
                //Create here sequential IMG tag based upon the width and default height.
                htmlContent += '<div class="timeslot"></div>';
            }
            if (this.options.isEditable === true) {
                //Check if there is already maximum number of timezone period available - no point in putting the button here.                                        
                //Create the button to provide the functionality to add a new time period.                    
                htmlContent += '<div class="newtimeperiodcontainer"><div class="newtimeperiod"></div></div>';

            }
            //If there are still space for more time zone, make the create new time zone period control enabled.                                        
            htmlContent += "</div>";

            return htmlContent;
        },

        //Create the time planner control here.
        _renderControl: function () {

            //There must be at least one element, this control must be populated using the id selector of JQuery
            var containerDiv, htmlContent, dayPlannerWidth, singleImageWidth, numberOfDays, totalPlannerHeight, addtitleCount, titleCount, dayCount;
            containerDiv = this.element[0];

            //It has been assumed that we will take care such that division opeartion will return us integer number.        
            dayPlannerWidth = (this.uiOptions.hourImageCount * this.uiOptions.hourImageWidth) + this.uiOptions.newTimePeriodContainerWidth;
            singleImageWidth = this.uiOptions.hourImageWidth;
            numberOfDays = this.options.weekSetModelObject.get('arrDay').length;

            htmlContent = '<div class="activationTimePlannerContainer" >';

            //Show here the hours in text
            addtitleCount = 2;
            htmlContent += '<div class="timebar">';
            //create the timer hour control title here if the control needs timing information on the top.        
            for (titleCount = 0; titleCount <= this.uiOptions.hourImageCount; titleCount += addtitleCount) {
                htmlContent += this._generateTimeBarHTML(((singleImageWidth * titleCount) + this.uiOptions.dayTitleContainerWidth - 12), 0, titleCount);
            }
            htmlContent += '</div>';
            for (dayCount = 0; dayCount < numberOfDays; dayCount += 1) {
                htmlContent = this.createDay(htmlContent, dayCount, dayPlannerWidth, singleImageWidth);
            }

            htmlContent += '<div class="timebar">';

            //create the timer hour control title here if the control needs timing information on the bottom.
            for (titleCount = 0; titleCount <= this.uiOptions.hourImageCount; titleCount += addtitleCount) {
                htmlContent += this._generateTimeBarHTML(((singleImageWidth * titleCount) + this.uiOptions.dayTitleContainerWidth - 12),
					((this.uiOptions.dayHeight * numberOfDays) + this.uiOptions.timeBarHeight + ((numberOfDays - 1) * this.uiOptions.dayMiddleGap)), titleCount);
            }

            htmlContent += '</div></div>';
            $(containerDiv).append(htmlContent);

            //generate the current model time period information user interface.
            this._generateTimePeriodHTML();
        },
        addDivToPlanner: function (start, end, timePeriodSel, dayContainer) {
            var selectionDiv, timePeriodResizeHtml, atts, selSize, selLeft, selRight;

            atts = this._generateActivationPeriodAttributes(start, end);
            atts.id = this.uiOptions.timePeriodIDPrefix + timePeriodSel;

            if (this.options.isEditable === false) {
                timePeriodResizeHtml = "";
            } else {
                timePeriodResizeHtml = '<div class="timePeriodResize timePeriodResize-left-normal"  leftResize="1"/><div class="timePeriodResize timePeriodResize-right-normal"  leftResize="0"/>';
            }

            //Calculate here size of the time period and put a div inside the day planner container div.
            selLeft = ((start.getTotalMinutes() / this.uiOptions.minTimeSupported) * (this.uiOptions.pxPerMinTimeBlock) + this.uiOptions.dayTitleContainerWidth);
            selRight = ((end.getTotalMinutes() / this.uiOptions.minTimeSupported) * (this.uiOptions.pxPerMinTimeBlock) + this.uiOptions.dayTitleContainerWidth);

            selSize = {
                left: selLeft,
                width: selRight - selLeft
            };


            selectionDiv = $('<div class="' + this.uiOptions.activationPeriodClass + '" startHour="' + atts.startHour + '" startMinute="' + atts.startMinute + '" endHour="' + atts.endHour + '" endMinute="' + atts.endMinute + '" title="' + atts.title + '" id="' + atts.id + '" tabindex="100" style="' + this._cssProperty + ':' + selSize.left + 'px;width:' + selSize.width + 'px">' + timePeriodResizeHtml + '</div>');
            //append the child selection div.
            dayContainer.append(selectionDiv);
            return selectionDiv;
        },

        //Generate the time period HTML
        _generateTimePeriodHTML: function () {
            var dayArray, dayCount, localTimePeriodArr, timePeriodSel, dayContainer;

            dayArray = this.options.weekSetModelObject.get('arrDay');
            for (dayCount = 0; dayCount < dayArray.length; dayCount += 1) {
                dayContainer = $('#dayContainer_' + dayCount, this.$timePlannerContainer);

                localTimePeriodArr = dayArray[dayCount].arrActivationPeriod;
                //Here currently, we are assuming that arrActivationPeriod will have the even length. We will use them in the pair.
                for (timePeriodSel = 0; timePeriodSel < localTimePeriodArr.length; timePeriodSel += 2) {

                    //Calculate here size of the div (No validation has  put from the input XML whether time period selection is overriden or not).
                    //Assumed that time period selection are non overriding values.

                    if (localTimePeriodArr[timePeriodSel].timeAsString() !== localTimePeriodArr[timePeriodSel + 1].timeAsString()) { //Start and end time should not be equal.
                        this.addDivToPlanner(localTimePeriodArr[timePeriodSel], localTimePeriodArr[timePeriodSel + 1], timePeriodSel, dayContainer);
                    }
                }
                if (this.options.isEditable === true) {
                    // Disable the newTimePeriod button if the day has maximum periods already
                    if (localTimePeriodArr.length >= this.options.maxNumOfActivationPeriods) {
                        this._disableAddNewTimePeriod(dayContainer);
                    }
                }
            }
        },

        _disableAddNewTimePeriod: function (dayContainer) {
            dayContainer.find('.newtimeperiod').addClass('disabled');

        },
        _enableAddNewTimePeriod: function (dayContainer) {
            dayContainer.find('.newtimeperiod').removeClass('disabled');
        },

        //Name: _handleMoveNewPeriod
        //Comment: Sets up all UI event handlers for the .newtimeperiod elements
        _handleMoveNewPeriod: function () {
            var self = this;
            $(".newtimeperiod", this.$timePlannerContainer).mousedown(function (event) {
                self.dims = self.dims || self._getDimensions();

                var container, css, curPeriodCnt, selectionDiv, $selectionDiv, $leftResizeImg, $rightResizeImg, element, elementLeft,
					$element, $doc, moveNewTimePeriodHandler, mouseUpAndMouseOutHander, elementWidth, mouseDownEventPageX, maxPeriods;

                //It must be left button of the mouse. Mouse interaction is only allowed with them.
                if ((event.which === 1) || (event.button === 1)) {
                    container = self._getTimePeriodContainer($(event.currentTarget));


                    curPeriodCnt = container.find(" > ." + self.uiOptions.activationPeriodClass).length;

                    if (curPeriodCnt < self.options.maxNumOfActivationPeriods) {
                        // Disable newTimePeriod if no more can be created after this one
                        if (curPeriodCnt + 1 === self.options.maxNumOfActivationPeriods) {
                            self._disableAddNewTimePeriod(container);
                        }

                        elementLeft = self.dims.getPositionForMinutes(60 * self.uiOptions.hourImageCount);
                        elementWidth = 0;

                        // Create new time period
                        selectionDiv = document.createElement("div");
                        $selectionDiv = $(selectionDiv);
                        $selectionDiv.addClass(self.uiOptions.activationPeriodClass);
                        $selectionDiv.attr({ id: self.uiOptions.timePeriodIDPrefix + (curPeriodCnt * 2), tabindex: 100, startHour: 24, startMinute: 0, endHour: 24, endMinute: 0 });

                        css = { width: elementWidth };
                        css[self._cssProperty] = elementLeft;

                        $selectionDiv.css(css);

                        // Create left resize button
                        $leftResizeImg = $(document.createElement("div"));
                        $leftResizeImg.addClass("timePeriodResize timePeriodResize-left-normal");
                        $leftResizeImg.attr({ "leftResize": "1" });
                        // Create right resize button  
                        $rightResizeImg = $(document.createElement("div"));
                        $rightResizeImg.addClass("timePeriodResize timePeriodResize-right-normal").attr({ "leftResize": "0" });

                        // Add resize buttons to new time period and add new time period to day container
                        $selectionDiv.append($leftResizeImg);
                        $selectionDiv.append($rightResizeImg);

                        container.append(selectionDiv);

                        mouseDownEventPageX = parseFloat(event.pageX, 10);
                        $doc = self._getEventListeningObject();
                        moveNewTimePeriodHandler = function (event) {
                            event.currentTarget = $leftResizeImg.get(0);
                            self._handleTimePeriodLeftResize(event, elementLeft, elementWidth, mouseDownEventPageX);
                            event.preventDefault();
                        };

                        $doc.bind("mousemove.timeplanner", moveNewTimePeriodHandler);

                        mouseUpAndMouseOutHander = function (event) {
                            var $doc = $(this);
                            // Remove the new period if it is smaller than the minimum size, i.e. the resize button size
                            if ($selectionDiv.width() < self.uiOptions.resizeButtonWidth) {
                                $(selectionDiv).remove();

                                if (container.find("> ." + self.uiOptions.activationPeriodClass).length < self.options.maxNumOfActivationPeriods) {
                                    self._enableAddNewTimePeriod(container);
                                }
                            }
                            $doc.unbind('mousemove.timeplanner');
                            $doc.unbind('mouseup.timeplanner');
                            $doc.unbind('mouseleave.timeplanner');
                            self._trigger('timeperiod_move_end',
                             undefined, { period: self.$timePlannerContainer.attr("timeperiodselid"), day: self.$timePlannerContainer.attr("timeperiodselparentid"), start: self._getStartTime($selectionDiv), end: self._getEndTime($selectionDiv) });

                            event.preventDefault();
                        };

                        $doc.bind("mouseup.timeplanner", mouseUpAndMouseOutHander);
                        $doc.bind("mouseleave.timeplanner", self._setUpMouseLeave(mouseUpAndMouseOutHander));
                        $doc.bind("mouseenter.timeplanner", self._setUpMouseEnter());

                        //break references
                        moveNewTimePeriodHandler = null;
                        mouseUpAndMouseOutHander = null;
                        $doc = null;

                        self._handleMoveTimePeriod();
                        self._handleTimePeriodResizeEvent();
                        //Select this time period.
                        self._selectTimePeriod(selectionDiv);

                    } else {
                        self._disableAddNewTimePeriod(container);

                    }
                }
            });
        },

        //Returns true in case of given area intersect with the other time period available under the parent.
        //Returns false if area is not intersecting with any other time period element available under the parent.
        isIntersectNeighbourTimePeriod: function (currentElementID, parentElement, moveRect) {
            var returnVal = false, self = this;


            //If null case for the input parameters, we will assume that it says it does not intersect.
            if ((currentElementID === undefined) || (currentElementID === null) ||
					(parentElement === undefined) || (parentElement === null)) {
                return returnVal;
            }

            //Now seach for the interesting element.
            $('.' + self.uiOptions.activationPeriodClass + '[id!="' + currentElementID + '"]', $(parentElement)).each(function (index) {
                var divRect;

                divRect = self._getRectangle(this, false);

                if (ECALENDAR.AppUtilities.intersectLine(divRect, moveRect)) {
                    returnVal = true;   //Now, moving out of the function using this return.
                    return;
                }
            });
            return returnVal;
        },

        //Handle time period resize event. Click and drag resize left and right arrow task is performed here.
        _handleTimePeriodResizeEvent: function () {

            var self = this;

            //Hover effect for the time Period left and right arrow.
            $(".timePeriodResize", self.$timePlannerContainer).hover(function (event) {
                var currentNode = event.currentTarget;
                //Change the image to hovar state.
                if (currentNode.getAttribute("leftResize") === "1") {
                    $(currentNode).addClass('timePeriodResize-left-hover').removeClass('timePeriodResize-left-normal');
                } else {
                    $(currentNode).addClass('timePeriodResize-right-hover').removeClass('timePeriodResize-right-normal');
                }
            }, function (event) {
                var currentNode = event.currentTarget;
                //Change the image to normal state.
                if (currentNode.getAttribute("leftResize") === "1") {
                    $(currentNode).addClass('timePeriodResize-left-normal').removeClass('timePeriodResize-left-hover');
                } else {
                    $(currentNode).addClass('timePeriodResize-right-normal').removeClass('timePeriodResize-right-hover');
                }
            });

            $(".timePeriodResize", self.$timePlannerContainer).unbind('mousedown');
            //Mouse down event for the time period
            $(".timePeriodResize", self.$timePlannerContainer).mousedown(function (event) {
                var element, $element, elementLeft, elementWidth, mouseDownEventPageX, timePeriodResizeMouseMoveHandler, $doc, timePeriodResizeMouseUpHandler;


                //It must be left button of the mouse. Mouse interaction is only allowed with them.
                if ((event.which === 1) || (event.button === 1)) {
                    //We know this is current target for the event.    
                    element = event.currentTarget;
                    $element = $(element);

                    elementLeft = self.dims.getStartPixelsForObj(element.parentNode);
                    elementWidth = self.dims.getWidthPixelsForObj(element.parentNode);
                    mouseDownEventPageX = parseFloat(event.pageX, 10);



                    //Mouse move handler for setting the capture.
                    timePeriodResizeMouseMoveHandler = function (event) {
                        event.currentTarget = element;
                        //identify left or right border which needs resize of the time period.   
                        if (self._rtl === true) {
                            if (element.getAttribute("leftResize") === "1") {
                                self._handleTimePeriodRightResize(event, elementLeft, elementWidth, mouseDownEventPageX);
                            } else if (element.getAttribute("leftResize") === "0") {
                                self._handleTimePeriodLeftResize(event, elementLeft, elementWidth, mouseDownEventPageX);
                            }
                        }
                        else {
                            if (element.getAttribute("leftResize") === "1") {
                                self._handleTimePeriodLeftResize(event, elementLeft, elementWidth, mouseDownEventPageX);
                            } else if (element.getAttribute("leftResize") === "0") {
                                self._handleTimePeriodRightResize(event, elementLeft, elementWidth, mouseDownEventPageX);
                            }
                        }
                        self._trigger('timeperiod_resize',
                             undefined, { period: self.$timePlannerContainer.attr("timeperiodselid"), day: self.$timePlannerContainer.attr("timeperiodselparentid"), start: self._getStartTime(element.parentNode), end: self._getEndTime(element.parentNode) }
                            );
                        event.preventDefault();
                    };

                    $doc = self._getEventListeningObject();

                    //Mouse up handler for releasing the capture.
                    timePeriodResizeMouseUpHandler = function (event) {
                        var $doc = $(this);
                        //Un bind all the document events here.
                        $doc.unbind('mousemove.timeplanner');
                        $doc.unbind('mouseup.timeplanner');
                        $doc.unbind('mouseleave.timeplanner');
                        self._trigger('timeperiod_move_end',
                         undefined, { period: self.$timePlannerContainer.attr("timeperiodselid"), day: self.$timePlannerContainer.attr("timeperiodselparentid"), start: self._getStartTime(element.parentNode), end: self._getEndTime(element.parentNode) });

                        event.preventDefault();
                    };

                    //Finally, associate the event handlers so that capture will be set to the element.
                    $doc.bind('mousemove.timeplanner', timePeriodResizeMouseMoveHandler);
                    $doc.bind('mouseup.timeplanner', timePeriodResizeMouseUpHandler);
                    $doc.bind("mouseleave.timeplanner", self._setUpMouseLeave(timePeriodResizeMouseUpHandler));
                    $doc.bind("mouseenter.timeplanner", self._setUpMouseEnter());
                    $doc.bind('blur.timeplanner', timePeriodResizeMouseUpHandler);

                    //break references
                    timePeriodResizeMouseMoveHandler = null;
                    timePeriodResizeMouseUpHandler = null;
                    $doc = null;

                    //No point in further populating the event to the parent.
                    event.preventDefault();
                    event.stopImmediatePropagation();
                }

                //Select this time period.
                self._selectTimePeriod(element.parentNode);
            });
        },

        //Handle right arrow in the time period resize operation - it is actually a extension of mouse move event handling in a function.
        _handleTimePeriodRightResize: function (event, elementLeft, elementWidth, mouseDownEventPageX) {

            var self, element, moveArea, pixelsMove, divParent, parentArea, initialRight, adjustment;
            self = this;
            element = event.currentTarget;
            if (self._rtl === true) {
                moveArea = {
                    left: elementLeft,
                    right: ((elementLeft + (mouseDownEventPageX - event.pageX)) + parseFloat(elementWidth, 10))
                };
            } else {

                moveArea = {
                    left: elementLeft,
                    right: ((elementLeft - (mouseDownEventPageX - event.pageX)) + parseFloat(elementWidth, 10))
                };
            }
            pixelsMove = self.moveTimePeriodPixels(event);


            //Check the intersection of the user preferred are with its neighbour time period. If they are intersecting don't move the position of the control.
            divParent = element.parentNode.parentNode;

            if (self.isValidArea(moveArea)) {

                initialRight = moveArea.right;
                adjustment = (moveArea.right - moveArea.left) % pixelsMove;
                if (self.isIntersectNeighbourTimePeriod(element.parentNode.id, divParent, moveArea)) {
                    moveArea = self.getExtendedAreaFromAdjacentTimePeriod(element.parentNode.id, divParent, moveArea, false);
                }

                if (initialRight != moveArea.right) {
                    adjustment = 0;
                }

                //Final check - identify whether it crosses the parent element's border. If it is not crossing parent border move the element.
                parentArea = self._getParentArea();

                //The mouse point must be inside the parent, than only allow the move the time period area.
                if (!ECALENDAR.AppUtilities.insideLine(parentArea, moveArea)) {

                    moveArea.right = parentArea.right;
                    adjustment = 0;

                }

                //Move the element by considering the minimum time (i.e. 5 minutes by default here. 3 pixels are used to represent 5 minutes by default.)
                element.parentNode.style.width = self.dims.convertPxToPercentString((moveArea.right - moveArea.left) - adjustment); // - ((moveArea.right - moveArea.left) % pixelsMove) + adjustment)); // + 'px';

                //Update the title of the div.
                self.updateTimePeriodDetail(element.parentNode, { left: moveArea.left, right: moveArea.right - adjustment });

            }
        },

        //Get adjacent area for smoother navigation of the 
        getExtendedAreaFromAdjacentTimePeriod: function (currentElementID, parentElement, moveRect, isLeft) {
            var self, newArea, leftDiff, rightDiff;

            if ((currentElementID == null || parentElement == null || moveRect == null || isLeft == null) ||
					(moveRect.right == null || moveRect.left == null) || (isLeft !== true && isLeft !== false)) {
                return null;
            }

            self = this;
            newArea = { left: 0, right: 0 };
            leftDiff = 0;
            rightDiff = 0;
            //Get the time period div element and check area interaction - it's simple
            $(parentElement).find('.' + self.uiOptions.activationPeriodClass + '[id!="' + currentElementID + '"]').each(function () {
                //If not current element.                 
                //var divElement = childDivElements[cnt];
                var divRect = self._getRectangle(this, false);

                //Intersection for the available two rectangle.
                if (ECALENDAR.AppUtilities.intersectLine(divRect, moveRect)) {
                    if (isLeft === true) {
                        newArea.right = moveRect.right;
                        if (moveRect.right !== divRect.left) {
                            if ((leftDiff === 0) || (leftDiff > (moveRect.right - divRect.right))) {
                                newArea.left = divRect.right;
                                leftDiff = moveRect.right - divRect.right;
                            }
                        } else {
                            if (newArea.left === 0 || newArea.left < moveRect.left) {
                                newArea.left = moveRect.left;
                            }
                        }
                    } else { //Assumed it is right 
                        newArea.left = moveRect.left;
                        if (moveRect.left !== divRect.right) {
                            if ((rightDiff === 0) || (rightDiff > (divRect.left - moveRect.left))) {
                                newArea.right = divRect.left;
                                rightDiff = divRect.left - moveRect.left;
                            }
                        } else {
                            if (newArea.right === 0 || newArea.right > moveRect.right) {
                                newArea.right = moveRect.right;
                            }
                        }
                    }
                }

            });
            //No intersection element found.
            return newArea;
        },

        //Get adjacent area for smoother navigation of the 
        getMovedAreaFromAdjacentTimePeriod: function (currentElementID, parentElement, moveRect, isLeft) {
            var self, newArea, leftDiff, rightDiff, moveRectWidth, tempArea;

            if ((currentElementID == null || parentElement == null || moveRect == null || isLeft == null) ||
					(moveRect.right == null || moveRect.left == null) || (isLeft !== true && isLeft !== false)) {
                return null;
            }

            self = this;
            newArea = { left: 0, right: 0 };
            tempArea = { left: 0, right: 0 };
            leftDiff = 0;
            rightDiff = 0;
            moveRectWidth = moveRect.right - moveRect.left;
            //Get the time period div element and check area interaction - it's simple
            $('.' + self.uiOptions.activationPeriodClass + '[id!="' + currentElementID + '"]', $(parentElement)).each(function () {
                //If not current element.                 
                //var divElement = childDivElements[cnt];
                var divRect = self._getRectangle(this, false);

                //Intersection for the available two rectangle.
                if (ECALENDAR.AppUtilities.intersectLine(divRect, moveRect)) {
                    if (isLeft === true) {

                        if (moveRect.right !== divRect.left) {

                            if ((leftDiff === 0) || (leftDiff > (moveRect.right - divRect.right))) {

                                tempArea.left = divRect.right;
                                tempArea.right = tempArea.left + moveRectWidth;
                                if (!self.isIntersectNeighbourTimePeriod(currentElementID, parentElement, tempArea)) {

                                    newArea.left = tempArea.left;
                                    leftDiff = moveRect.right - divRect.right;
                                }
                            }
                        } else {

                            if (newArea.left === 0 || newArea.left < moveRect.left) {

                                tempArea.left = moveRect.left;
                                tempArea.right = tempArea.left + moveRectWidth;
                                if (!self.isIntersectNeighbourTimePeriod(currentElementID, parentElement, tempArea)) {
                                    newArea.left = tempArea.left;

                                }
                            }
                        }
                    } else { //Assumed it is right 

                        if (moveRect.left !== divRect.right) {

                            if ((rightDiff === 0) || (rightDiff > (divRect.left - moveRect.left))) {

                                tempArea.left = divRect.left - moveRectWidth;
                                tempArea.right = tempArea.left + moveRectWidth;
                                if (!self.isIntersectNeighbourTimePeriod(currentElementID, parentElement, tempArea)) {

                                    newArea.left = tempArea.left;
                                    rightDiff = divRect.left - moveRect.left;
                                }
                            }
                        } else {

                            if (newArea.left === 0 || newArea.left > moveRect.left) {

                                tempArea.left = moveRect.left;
                                tempArea.right = tempArea.left + moveRectWidth;
                                if (!self.isIntersectNeighbourTimePeriod(currentElementID, parentElement, tempArea)) {

                                    newArea.left = moveRect.left;
                                }
                            }
                        }
                    }
                }
            });
            newArea.right = newArea.left + moveRectWidth;
            return newArea;
        },

        //Returns true if given one dimension are is valid else returns false.
        isValidArea: function (area) {
            //By default if area is null - it would return false.
            if ((area === null) || (area === undefined) || (area.left === null) || (area.left === undefined) ||
					(area.right === null) || (area.right === undefined)) {
                return false;
            }

            if (parseFloat(area.left, 10) + this.uiOptions.resizeButtonWidth > parseFloat(area.right, 10)) {
                return false;
            }

            return true;
        },

        //Handle left arrow in the time period resize operation  - it is actually a extension of mouse move event handling in a function.
        _handleTimePeriodLeftResize: function (event, elementLeft, elementWidth, mouseDownEventPageX) {

            var self, element, moveArea, pixelsMove, divParent, parentArea, initialLeft, adjustment;
            self = this;
            element = event.currentTarget;
            if (self._rtl === true) {

                moveArea = {
                    left: elementLeft + (mouseDownEventPageX - event.pageX),
                    right: (elementLeft + self.dims.getPxValue(elementWidth))
                };
            }
            else {

                moveArea = {
                    left: elementLeft - (mouseDownEventPageX - event.pageX),
                    right: (elementLeft + self.dims.getPxValue(elementWidth))
                };
            }

            pixelsMove = this.moveTimePeriodPixels(event);

            //Check the intersection of the user perferred are with its neighbour time period. If they are intersecting don't move the position of the control.
            divParent = element.parentNode.parentNode;

            if (self.isValidArea(moveArea)) {

                initialLeft = moveArea.left;

                adjustment = (moveArea.left % pixelsMove);
                if (self.isIntersectNeighbourTimePeriod(element.parentNode.id, divParent, moveArea)) {
                    //Get here best suitable moveArea points.
                    moveArea = self.getExtendedAreaFromAdjacentTimePeriod(element.parentNode.id, divParent, moveArea, true);
                }


                if (initialLeft != moveArea.left) {
                    // an intersection has been found
                    adjustment = 0;

                }


                //Final check - identify whether it crosses the parent element's border. If it is not crossing parent border move the element.
                parentArea = self._getParentArea();

                //The mouse point must be inside the parent, than only allow the move the time period area.
                if (!ECALENDAR.AppUtilities.insideLine(parentArea, moveArea)) {
                    moveArea.left = parentArea.left;
                    adjustment = 0;

                }


                //Move the element by considering the minimum time (i.e. 5 minutes by default here. 3 pixels are used to represent 5 minutes by default.)
                element.parentNode.style[self._cssProperty] = self.dims.convertPxToPercentString(moveArea.left - adjustment);
                element.parentNode.style.width = self.dims.convertPxToPercentString(moveArea.right - (moveArea.left - adjustment));

                //Update the title of the div.
                self.updateTimePeriodDetail(element.parentNode, { left: moveArea.left - adjustment, right: moveArea.right });

            }
        },

        //Selection time period operation. 
        //This function is responsible for applying selection for the time period. Steps currently followed and used during implementation are
        //1. This function should be called on mouse left/right button down.
        //2. Deselect the earlier selected timePeriod - generate a event saying which element is deselected.
        //3. Select the asked time period - generate a event saying which element is selected.
        //4. Expected work here is: update the edit controls with the parameters about the attributes of the current time period.
        _selectTimePeriod: function (timePeriod) {
            var self, selID, selParentID, $timePeriod, $container, previousItem, previousDay, previousActivation;
            self = this;
            selID = timePeriod.id;
            selParentID = timePeriod.parentNode.id;
            $timePeriod = $(timePeriod);
            $container = $(timePeriod.parentNode);
            previousDay = this.$timePlannerContainer.attr("timePeriodSelParentID");
            previousActivation = this.$timePlannerContainer.attr("timePeriodSelID");

            this.$timePlannerContainer.attr("timePeriodSelID", selID);
            this.$timePlannerContainer.attr("timePeriodSelParentID", selParentID);
            if (previousDay !== "" && previousActivation !== "") {
                previousItem = this.$timePlannerContainer.find('#' + previousDay).find('#' + previousActivation);
            }
            else {
                previousItem = this.$timePlannerContainer.find('.focus'); // just to be sure.
            }

            if (previousItem.length > 0) {
                previousItem.removeClass('focus');
                this._trigger('timeperiod_deselected', undefined, { timeperiod: previousItem });
            }


            timePeriod.focus();
            $timePeriod.addClass('focus');


            $timePeriod.keyup(function (event) {
                //Check for the DEL key press.

                var code = (event.keyCode || event.which);
                if (code === self.uiOptions.DELKeyCode) {/*Delete code*/
                    //remove current selected element.

                    self.removeTimePeriod($timePeriod);
                    
                }
            });




            var startTime, endTime;
            startTime = this._getStartTime($timePeriod);
            endTime = this._getEndTime($timePeriod);

            if (startTime.hour != endTime.hour && startTime.minute != endTime.minute) {

                this._trigger('timeperiod_selected',
             undefined, { period: selID, day: selParentID, start: startTime, end: endTime }
           );

                this._trigger('timeperiod_move_start',
             undefined, { period: selID, day: selParentID, start: startTime, end: endTime }
             );
            }
        },

        // Use the destroy method to clean up any modifications your widget has made to the DOM
        destroy: function () {
            var count;

            for (count = 0; count < this.element.length; count += 1) {

                //Break the event binding as well here.
                $(this.element[count]).unbind().removeClass("timePeriodStyle dayContainer timeslot-header timeslot newtimeperiod").empty();

            }
            // In jQuery UI 1.8, you must invoke the destroy method from the base widget
            $.Widget.prototype.destroy.call(this);
            // In jQuery UI 1.9 and above, you would define _destroy instead of destroy and not call the base method.
        }

    });
});