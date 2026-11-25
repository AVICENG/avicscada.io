/*globals jQuery*/
/*globals ECALENDAR*/
/*globals $*/
/*globals Modernizr*/
/*globals document*/
(function($, m, d) {
    "use strict";

    $.widget("ui.TimeInput", {

        options: { step: "300", shiftStep: "1800", ctrlStep: "900", showHourAs24: true },
        disableControl: function() {
            if (!this.element.get(0).disabled) {
                this.element.val('').attr('disabled', true);
                if (this._plus) {
                    this._plus.attr('disabled', true);
                    this._minus.attr('disabled', true);
                }
            }

        },
        enableControl: function() {
            if (this.element.get(0).disabled) {
                this.element.removeAttr('disabled');
                if (this._plus) {
                    this._plus.removeAttr('disabled');
                    this._minus.removeAttr('disabled');
                }
            }
        },
        _create: function() {
            this._time = new Date(0);

            this._supportsTime = m.inputtypes.time;


            if (!this._supportsTime) {
                // Modernizr doesn't detect time support correctly in safari 6 (yet??)
                var tempInput = d.createElement('input');
                tempInput.setAttribute('type', 'time');
                this._supportsTime = (tempInput.type !== 'text');
            }

            if (this._supportsTime && !this.options.showHourAs24) {
                var tempElement = this.element.clone(true).attr('type', 'time')
                this.element.replaceWith(tempElement);
                this.element = tempElement;
                tempElement = null;
            }

            this.element.attr('step', this.options.step);
            $(d).bind('keydown.timeinput', $.proxy(function(e) {

                if (e.shiftKey) {
                    this.element.attr('step', this.options.shiftStep);
                }
                if (e.ctrlKey) {
                    this.element.attr('step', this.options.ctrlStep);
                }

                if (e.shiftKey || e.ctrlKey) {
                    $(d).bind('keyup.timeinput', $.proxy(function(e) {
                        if (!e.shiftKey && !e.ctrlKey) {

                            this.element.attr('step', this.options.step); $(e.delegateTarget).unbind('keyup.timeinput');
                        }
                    }, this));
                }

            }, this));


            if (!this._supportsTime || this.options.showHourAs24) {

                var container = $('<div class="timeinput-container form-inline"></div>');
                var disabled = "";
                if (this.element.get(0).disabled) {
                    disabled = 'disabled="disabled"';
                }

                this._plus = $('<button tabindex="1" class="btn timeinput-plus" ' + disabled + '>+</button>');
                this._minus = $('<button  tabindex="1" class="btn timeinput-minus" ' + disabled + '>-</button>');
                var buttongroup = $('<div class="btn-group"></div>');
                buttongroup.append(this._plus);
                buttongroup.append(this._minus);

                this.element.wrap(container);
                this.element.after(buttongroup);

                this._plus.bind('click', $.proxy(this._increment, this));
                this._minus.bind('click', $.proxy(this._decrement, this));

                this.element.bind('focus', $.proxy(function(e) {
                    this.element.bind('keyup.timeinput', $.proxy(function(e) {
                        if (e.keyCode === $.ui.keyCode.UP) { this._increment(e); e.preventDefault(); }
                        if (e.keyCode === $.ui.keyCode.DOWN) { this._decrement(e); e.preventDefault(); }

                    }, this));

                }, this));
                this.element.bind('keydown.timeinput', $.proxy(
                    function(e) {
                        if (e.keyCode === $.ui.keyCode.ENTER) {
                            this.element.blur();
                            e.preventDefault();
                            return false;
                        }
                    }, this));

                this.element.bind('blur', function(e) { $(this).unbind('keyup.timeinput'); });


            }

            this.element.bind('change.timeinput input.timeinput', $.proxy(function(e) {

                var tempDate, isValidDate = function(date) {
                    if (Object.prototype.toString.call(date) === '[object Date]' && !isNaN(date.getTime())) {
                        return true;
                    }
                };
                if (this._supportsTime && e.type != 'change') {
                    tempDate = e.target.valueAsDate;


                    if (isValidDate(tempDate)) {
                        tempDate.setSeconds(0);

                        if (!this._time.toLocaleTimeString() !== tempDate.toLocaleTimeString()) {
                            this._time = tempDate;
                            this._raiseTimeChangedEvent(e);
                        }
                        return;
                    }


                }
                if (e.type === 'change') {
                    tempDate = new Date(0);

                    var values = e.target.value.split(":");
                    var hours, minutes;


                    if (values[0].length < 3 && values[0].length > 0) {
                        hours = values[0];

                    }
                    if (values.length > 1 && values[1].length < 3 && values[1].length > 0) {
                        minutes = values[1];
                    }
                    tempDate.setHours(Math.abs(hours || 0), Math.abs(minutes || 0), 0);

                    if (isValidDate(tempDate)) {

                        if (!this._time.toLocaleTimeString() !== tempDate.toLocaleTimeString()) {
                            this._time = tempDate;
                            this._raiseTimeChangedEvent(e);
                        }
                        return;
                    }
                    this._setValue();
                }
            }, this));



        },
        setTime: function(hours, minutes) {
            if (!hours && !minutes) { return; }
            this._time = new Date(0);
            this._time.setHours(Math.abs(hours || 0), Math.abs(minutes || 0));
            this._setValue();

          
        },
        _pad: function pad(n) {
            if (!n && n !== 0) { return; }
            if (n.toString().length === 1) { return '0' + n; }
            return n.toString();
        },
        _setValue: function() {


            var time = [this._pad(this._time.getHours()), this._pad(this._time.getMinutes())];

            if (this.options.showHourAs24) {
                if (this._time.getHours() === 0) {
                    if (this._time.getDate() > new Date(0).getDate()) {
                        time[0] = 24;
                    }
                }

            }

            this.element.val(time.join(':'));
        },
        _decrement: function(e) {
            var seconds = this._time.getTime();
            seconds -= (parseInt(this.element.attr('step'), 10) * 1000);
            this._time.setTime(seconds);
            this._setValue();
            this._raiseTimeChangedEvent(e);
        },
        _increment: function(e) {

            var seconds = this._time.getTime();
            seconds += (parseInt(this.element.attr('step'), 10) * 1000);
            this._time.setTime(seconds);
            this._setValue();
            this._raiseTimeChangedEvent(e);
        },
        _raiseTimeChangedEvent: function(e) {
            this._trigger('timechanged', e, { time: this._time });
        },
        _setOption: function(key, value) {

            switch (key) {

            }
            $.Widget.prototype._setOption.apply(this, arguments);
        },
        destroy: function() {
            // Use the destroy method to reverse everything your plugin has applied
            $.Widget.prototype.destroy.call(this);
        }

    });

} (jQuery, Modernizr, document));