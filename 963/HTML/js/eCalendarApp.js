/*! - v1.0
*/

/*globals NavUserSelectionTimeScheme*/
/*globals ECALENDAR*/
/*globals $*/
/*globals Backbone*/
/*globals _*/
/*globals document*/
$(function () {
    "use strict";

    var displayDiaryView, errorDisplayView, tabbedPanelView;
	
    ECALENDAR.AppUtilities.setRightToLeft();
    ECALENDAR.AppUtilities.setPageTitle(ECALENDAR.ApplicationStrings.getResourceFromID('DIARY_PAGE_TITLE'));
    ECALENDAR.AppUtilities.createSessionApplet();
    function requestUserInformationSuccess(data, textStatus, jqXHR) {
        //Retrive user information.        
        if (jqXHR !== null) {
            var xmlDoc, $xmlDoc;
            xmlDoc = $.parseXML(jqXHR.responseText);
            $xmlDoc = $(xmlDoc);
            if ($xmlDoc.find("CanConfigDiaryTimes").text() === "1") {
                ECALENDAR.canConfigureActivationTimes = true;
            }
            if ($xmlDoc.find("HasFullWebAccess").text() === "1") {
                ECALENDAR.hasFullWebAccess = true;
            }
        }


        //Create user interface now as we have sufficient information to proceed.
        displayDiaryView = new ECALENDAR.DisplayDiaryView({});

        ECALENDAR.specialDayCollection = new ECALENDAR.SpecialDayCollection();
        ECALENDAR.weekSetCollection = new ECALENDAR.WeekSetCollection();
        ECALENDAR.exceptionCollection = new ECALENDAR.ExceptionCollection();
        ECALENDAR.weeksetTimeChanges = new ECALENDAR.WeekSetTimeChangeCollection();

        tabbedPanelView = new ECALENDAR.TabbedView({ el: $('#TabbedPanel'), id: "MainTabView",
            model: new ECALENDAR.TabCollection([
                new ECALENDAR.TabModel({ tabText: ECALENDAR.ApplicationStrings.getResourceFromID("TAB_EXCEPTIONS"), view: ECALENDAR.ExceptionView }),
                new ECALENDAR.TabModel({ tabText: ECALENDAR.ApplicationStrings.getResourceFromID("TAB_IQ_ZONES"), view: ECALENDAR.BrowseIQZoneView }),
                new ECALENDAR.TabModel({ tabText: ECALENDAR.ApplicationStrings.getResourceFromID("TAB_TIMESCHEMES"), view: ECALENDAR.TimeSchemeContainerView })
            ])
        });

        function abortExistingRequests() {
            if (ECALENDAR.objTimeSchemeDataRequest && ECALENDAR.objTimeSchemeDataRequest.readyState !== 4) {
                ECALENDAR.objTimeSchemeDataRequest.abort();
            }
            if (ECALENDAR.objSpecialDayDataRequest && ECALENDAR.objSpecialDayDataRequest.readyState !== 4) {
                ECALENDAR.objSpecialDayDataRequest.abort();
            }
            if (ECALENDAR.objExceptionDataRequest && ECALENDAR.objExceptionDataRequest.readyState !== 4) {
                ECALENDAR.objExceptionDataRequest.abort();
            }
            if (ECALENDAR.objTimeChangeDataRequest && ECALENDAR.objTimeChangeDataRequest.readyState != 4) {
                ECALENDAR.objTimeChangeDataRequest.abort();
            }
        }



        function getWeeksetChangeData() {

            var diaryGroup = this.get("diaryGroup"), requestsCompleted = 0, expectedRequests = 2;
            var checkRequests = function () {
                requestsCompleted += 1;
                if (requestsCompleted === expectedRequests) {
                    this.global_dispatcher.trigger('sending_data_complete:weekSetData:fetch');
                }

            }, callbacks = {
                success: function (model, response) {
                    checkRequests.call(model);
                },
                error: function (model, xhr, fetch) {
                    checkRequests.call(model);

                    if (xhr.statusText === "abort") {
                        return;
                    }
                    if (model.global_dispatcher != null) {
                        model.global_dispatcher.trigger('user_messaging', [ECALENDAR.ApplicationStrings.getResourceFromID("GET_TIMESCHEME_ERROR")]);
                    }
                }
            };

            this.global_dispatcher.trigger('sending_data:weekSetData:fetch');

            ECALENDAR.weekSetCollection.reset();
            ECALENDAR.objTimeSchemeDataRequest = ECALENDAR.weekSetCollection.fetch(_.extend({}, callbacks,
            {
                model: "Weeksets",
                diaryId: diaryGroup.attributes.diaryID
            })
            );

            ECALENDAR.weeksetTimeChanges.reset();
            ECALENDAR.objTimeChangeDataRequest = ECALENDAR.weeksetTimeChanges.fetch(_.extend({}, callbacks,
            {
                model: "WeeksetTimeChanges",
                diaryId: diaryGroup.attributes.diaryID
            }));
        }


        function refreshData(model, changes) {

            var diaryGroup = this.get("diaryGroup"), fetchCompletionCount = 0,
            fetchDone = function () {
                fetchCompletionCount = fetchCompletionCount + 1;
                if (fetchCompletionCount === 3) {
                    if (this.global_dispatcher != null) {
                        this.global_dispatcher.trigger('sending_data_complete:DiaryGroupSelection:refreshData');
                    }
                }
            },
            createSuccessCallback = function () {
                return _.bind(function () {
                    if (this.global_dispatcher != null) {
                        this.global_dispatcher.trigger('sending_data_complete:weekSetCollection:fetch');
                    }
                    fetchDone.call(ECALENDAR.DiaryGroupSelection);
                }, this);
            },
            createErrorCallback = function () {
                return _.bind(function (collection, xhr, fetch) {
                    if (this.global_dispatcher != null) {
                        this.global_dispatcher.trigger('sending_data_complete:weekSetCollection:fetch');
                    }
                    fetchDone.call(ECALENDAR.DiaryGroupSelection);
                    if (xhr.statusText === "abort") {
                        return;
                    }
                    if (this.global_dispatcher != null) {
                        this.global_dispatcher.trigger('user_messaging', [ECALENDAR.ApplicationStrings.getResourceFromID("GET_TIMESCHEME_ERROR")]);
                    }
                }, this);
            };


            abortExistingRequests();

            ECALENDAR.exceptionCollection.reset();

            if (this.global_dispatcher != null) {
                this.global_dispatcher.trigger('sending_data:DiaryGroupSelection:refreshData');
                this.global_dispatcher.trigger('sending_data:weekSetCollection:fetch');
                this.global_dispatcher.unbind('sending_data_complete:weekSetData:fetch');
                this.global_dispatcher.bind('sending_data_complete:weekSetData:fetch', function () {
                    this.unbind('sending_data_complete:weekSetData:fetch');
                    fetchDone.call(ECALENDAR.DiaryGroupSelection);
                });
            }
            getWeeksetChangeData.call(this);

            ECALENDAR.specialDayCollection.reset();
            ECALENDAR.objSpecialDayDataRequest = ECALENDAR.specialDayCollection.fetch({
                success: createSuccessCallback.call(this),
                error: createErrorCallback.call(this),
                model: "SpecialDays",
                diaryId: diaryGroup.attributes.diaryID
            });

            if (this.global_dispatcher != null) {
                this.global_dispatcher.trigger('sending_data:exceptionCollection:fetch');
            }

            ECALENDAR.objExceptionDataRequest = ECALENDAR.exceptionCollection.fetch({
                success: $.proxy(function () {
                    if (this.global_dispatcher != null) {
                        this.global_dispatcher.trigger('sending_data_complete:exceptionCollection:fetch');
                    }
                    fetchDone.call(ECALENDAR.DiaryGroupSelection);
                }, this),
                error: $.proxy(function (collection, xhr, fetch) {
                    if (this.global_dispatcher != null) {
                        this.global_dispatcher.trigger('sending_data_complete:exceptionCollection:fetch');
                    }
                    fetchDone.call(ECALENDAR.DiaryGroupSelection);
                    if (xhr.statusText === "abort") {
                        return;
                    }
                    if (this.global_dispatcher != null) {
                        this.global_dispatcher.trigger('user_messaging', [ECALENDAR.ApplicationStrings.getResourceFromID("GET_EXCEPTION_ERROR")]);
                    }
                }, this),
                model: "Exceptions",
                diaryId: diaryGroup.attributes.diaryID
            });
        }

        ECALENDAR.DiaryGroupSelection.global_dispatcher.bind('view_messaging:timeSchemeUpdated', function () { refreshData.call(this, this, {}); }, ECALENDAR.DiaryGroupSelection);
        ECALENDAR.DiaryGroupSelection.bind('change', function (model, change) { ECALENDAR.TimeSchemeSelection.set('timeScheme', null); refreshData.call(this, model, change); }, ECALENDAR.DiaryGroupSelection);

        ECALENDAR.DiaryGroupSelection.global_dispatcher.bind('view_messaging:defaultTimeChangeUpdated', getWeeksetChangeData, ECALENDAR.DiaryGroupSelection);

    }

    function requestUserInformationError() {
        //TODO: Display error message.
        $("body").empty();
        errorDisplayView.global_dispatcher.trigger('user_messaging', [ECALENDAR.ApplicationStrings.getResourceFromID("USER_INFORMATION_NOT_AVAILABLE")]);
    }
    errorDisplayView = new ECALENDAR.DialogDisplayView();

    //Request user information from the Server, it is mandatory information to proceed for the client application.
    ECALENDAR.Communication.requestUserInformation(requestUserInformationSuccess, requestUserInformationError);
	
	var viewportErrorTimeout;
	function displayViewportSizeError() {
		if($(window).width() < ECALENDAR.viewportMinWidth ||  $(window).height() < ECALENDAR.viewportMinHeight ) {
			if($(".viewport-size-error").length == 0) {
				var html = '<span class="error"><span class="alert alert-error viewport-size-error"><button class="close" data-dismiss="alert">x</button>' + ECALENDAR.ApplicationStrings.getResourceFromID("VIEWPORT_SIZE_ERROR") + '</span></span>';
				$("body").prepend(html);
			}
			window.clearTimeout(viewportErrorTimeout);
			viewportErrorTimeout = window.setTimeout(function(){$(".viewport-size-error").remove()}, 15000);
		} else if ($(window).width() > ECALENDAR.viewportMinWidth &&  $(window).height() > ECALENDAR.viewportMinHeight){
			$(".viewport-size-error").remove();
		}		
	}

	$(window).resize(displayViewportSizeError);
	$(window).load(displayViewportSizeError);

    $(document).live('click', function (e) {
        var target = $(e.target);
        if (target.hasClass('close') && target.data('dismiss')) {
            target.closest('.' + target.data('dismiss')).remove();
        }
    });
});