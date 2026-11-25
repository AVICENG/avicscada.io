/*! - v1.0
* ModelGenerator.js
*
* This will generate the model from the input XML data.
*
* Date: Thu May 10, 2012
* Copyright 2008-2012 Honeywell Technologies Sàrl, ECC Division. All rights reserved. 
* Copyright 1995-2008 Trend Control Systems Ltd.
*/

/*globals ECALENDAR*/
/*globals $, jQuery, _
*/

$(function () {
    "use strict";

    var ModelGenerator = function () {

        var self = this;
        this.parseDate = function ($xml) {
            return new Date(parseInt($xml.find('year').text(), 10), parseInt($xml.find('month').text(), 10) - 1, parseInt($xml.find('day').text(), 10));
        };

        //This method is created to generate a new DiaryCollection model from the given input XML.
        //NOTE: It is assumed that provided input XML is validated before feeding into this function. If this function will fail to parse the XML, it will return the null value.
        this.generateDiaryCollectionFromXML = function (diaryCollectionXML) {

            var xmlDoc, $xmlDoc, rootXMLNode, collection = null;

            //Generate the XML DOM from the provided input.
            if ((diaryCollectionXML !== undefined) && (diaryCollectionXML !== null)) {
                xmlDoc = $.parseXML(diaryCollectionXML);
                $xmlDoc = $(xmlDoc);

                //Create an empty DiaryCollection object.
                collection = new ECALENDAR.DiaryCollection();

                //Perform the parsing here to generate the Diary Model and feed them into the DiaryCollection.
                rootXMLNode = $xmlDoc.find('Diary');

                //Find out the n level groups and folders, n would increase recursively for the folders only
                self.appendDiaryModel(collection, collection.getModelFromId(-1), rootXMLNode);
            }

            return collection;
        };

        //This function parses the input XML and sets the list of children for the given DiaryModel object. 
        //These children are also be added into the diary collection.         
        this.appendDiaryModel = function (diaryCollection, parentDiaryModel, xmlNode) {

            //All the input must be valid - else it will not change the parentDiaryModel, diaryCollection.
            if ((diaryCollection !== null) && (diaryCollection !== undefined) && (parentDiaryModel !== null) && (parentDiaryModel !== undefined) && (xmlNode !== null) && (xmlNode !== undefined)) {
                var newDiaryModel, folder, childArray, folderArray, folderXML, folderCount;
                childArray = [];
                folderArray = [];
                folderXML = [];
                xmlNode.children().each(function () {

                    //Only proceed if children is Folder or Group tag.
                    if ((this.nodeName === 'Folder') || (this.nodeName === 'Group')) {

                        var $this = $(this), timeZoneCollection;

                        //Create a new diary Model
                        newDiaryModel = new ECALENDAR.DiaryModel();
                        timeZoneCollection = new ECALENDAR.TimeZoneCollection();
                        folder = (this.nodeName === 'Folder');

                        newDiaryModel.set({ label: $this.find("Label:first").text() });
                        newDiaryModel.set({ diaryID: parseInt($this.find("Index:first").text(), 10) });
                        newDiaryModel.set({ isFolder: folder });

                        if (!folder) {


                            newDiaryModel.set({ maxPeriods: parseInt($this.find("MaxPeriods:first").text(), 10) });
                        }

                        timeZoneCollection = new ECALENDAR.TimeZoneCollection(self.parseTimeZoneFromXml($this.find("Timezones")));

                        newDiaryModel.set({ 'timeZones': timeZoneCollection });
                        newDiaryModel.set({ isAssociatedWithTimeZones: timeZoneCollection.length > 0 });

                        //Now store it's index and push it to the collection.
                        childArray.push(parseInt($this.find("Index:first").text(), 10));
                        if (folder) {
                            folderArray.push(diaryCollection.length);
                            folderXML.push($this);
                        }

                        diaryCollection.push(newDiaryModel);
                    }
                });

                //Update the children list to the parentDiaryModel.
                parentDiaryModel.set({ childrenArray: childArray });

                //Finally call recuirsively for the Folder nodes to update their children.
                for (folderCount = 0; folderCount < folderArray.length; folderCount += 1) {
                    self.appendDiaryModel(diaryCollection, diaryCollection.at(folderArray[folderCount]), folderXML[folderCount]);
                }
            }
        };

        //Input the Weeksets XML and this function will return the ECALENDAR.WeekSetCollection object
        //In case if the input parameters is null or undefined this function will return the null.
        this.generateWeeksetCollectionFromXML = function (weeksetCollectionXML, diaryGroup) {

            var xmlDoc, $xmlDoc, weeksetCollection = null;
            diaryGroup = diaryGroup || ECALENDAR.DiaryGroupSelection.get('diaryGroup');

            if ((weeksetCollectionXML !== undefined) && (weeksetCollectionXML !== null)) {

                //Assumed that XML always comes in the correct format.
                xmlDoc = $.parseXML(weeksetCollectionXML);
                $xmlDoc = $(xmlDoc);

                weeksetCollection = new ECALENDAR.WeekSetCollection();

                if (diaryGroup.get('isFolder')) {
                    weeksetCollection.reset();
                    $xmlDoc.find("Weekset").each(function () {
                        var $this, weeksetModel, label, isDefault;

                        $this = $(this);
                        label = $('<div />').text($this.find("Label:first").text()).html();
                        isDefault = !!parseInt($this.find("IsDefault:first").text(), 10);
                        weeksetModel = new ECALENDAR.WeekSetModel();

                        weeksetModel.set({ label: label }, { silent: true });
                        weeksetModel.set({ weekSetID: null }, { silent: true });
                        weeksetModel.set({ isDefault: isDefault }, { silent: true });

                        weeksetCollection.add(weeksetModel);
                    });
                } else {
                    $xmlDoc.find("Weekset").each(function () {
                        var $this, isDefault, index, label, colour, weeksetModel, arrDays;

                        $this = $(this);
                        isDefault = !!parseInt($this.find("IsDefault:first").text(), 10);
                        index = parseInt($this.find("Index:first").text(), 10);
                        label = $('<div />').text($this.find("Label:first").text()).html();

                        colour = $this.find("Colour:first").text();

                        if (isDefault) {
                            //We already have a default weekset associated with the collection, make use of it.
                            weeksetModel = weeksetCollection.at(0);
                        } else {
                            weeksetModel = new ECALENDAR.WeekSetModel();
                        }

                        //For each weekset, arrDay is associated and now we need to fill the information about it.
                        arrDays = self.generateDayArrayFromXML($this.find("Days:first"));

                        weeksetModel.set({
                            groupId: diaryGroup.get('diaryID'),
                            colour: colour,
                            label: label,
                            weekSetID: index,
                            arrDay: arrDays,
                            isDefault: isDefault
                        }, { silent: true });


                        if (!isDefault) {
                            weeksetCollection.add(weeksetModel);
                        }

                    });
                }
            }

            return weeksetCollection;
        };


        this.parseSpecialDayCollectionFromXML = function (data, diaryGroup) {
            var xmlDoc, $xmlDoc, collection = [];
            diaryGroup = diaryGroup || ECALENDAR.DiaryGroupSelection.get('diaryGroup');
            if ((data !== undefined) && (data !== null)) {

                //Assumed that XML always comes in the correct format.
                xmlDoc = $.parseXML(data);
                $xmlDoc = $(xmlDoc);


                $xmlDoc.find("Specialday").each(function () {

                    var $this = $(this);
                    var dayStructure = new ECALENDAR.DayStructure();
                    dayStructure.setLabel("&#160;");
                    dayStructure.arrActivationPeriod = self.generateActivationPeriodArrayFromXML($this.find("ActivationTimePeriods:first"));

                    collection.push({
                        groupId: diaryGroup.get('diaryID'),
                        colour: $this.find("Colour:first").text(),
                        label: $('<div />').text($this.find("Label:first").text()).html(),
                        specialDayID: parseInt($this.find("Index:first").text(), 10) || null,
                        arrDay: [dayStructure]
                    });
                });
            }

            return collection;
        };

        this.parseCalendarMarkersFromXML = function (data) {
            var xmlDoc, $xmlDoc, collection = [];
            if ((data !== undefined) && (data !== null)) {
                xmlDoc = $.parseXML(data);
                $xmlDoc = $(xmlDoc);
                $xmlDoc.find('Marker').each(function () {
                    var $this = $(this);

                    var date = self.parseDate($this.find('date:first'));
                    var tooltip = $this.find('ToolTip:first').text();

                    collection.push({
                        date: date,
                        tooltip: tooltip,
                        isNew: false,
                        groupId: ECALENDAR.DiaryGroupSelection.get('diaryGroup').get('diaryID')
                    });
                });

            }
            return collection;


        };

        this.parseTimeZoneFromXml = function (xml) {
            var collection = [], $xml;
            $xml = (xml instanceof jQuery) ? xml : $($.parseXML(xml));
            $xml.find('Timezone').each(function () {
                var $this = $(this);
                collection.push(
                {
                    siteName: $this.find('SiteName').text(),
                    lanName: $this.find('LANName').text(),
                    osName: $this.find('OSname').text(),
                    zoneLabel: $this.find('ZoneLabel').text(),
                    item: $this.find('Item').text(),
                    deviceType: $this.find('DeviceType').text()
                }
                );
            });
            return collection;
        };


        this.parseGroupReplaceConflictFromXml = function (xml) {
            var collection = [], $xml;
            $xml = (xml instanceof jQuery) ? xml : $($.parseXML(xml));
            $xml.find('UserChoice').each(function () {
                var $this = $(this);
                collection.push(
                {
                    groupId: parseInt($this.find('diaryGroupID').text(), 10),
                    replace: parseInt(($this.find('Replace').text() || -1), 10) 
                }
                );
            });
            return collection;
        };


        //Input the Days XML and this function will return the array of ECALENDAR.DayStructure data-structure. It returns empty array in case of input daysXML is null or undefined.        
        //Day XML structure: <Days><Day><Index>1</Index><Label>Monday</Label><Colour>#FFFFFF</Colour><ActivationTimePeriods><ActivationTimePeriod><Time>08:00</Time><Value>1.000000</Value></ActivationTimePeriod><ActivationTimePeriod><Time>17:30</Time><Value>0.000000</Value></ActivationTimePeriod><ActivationTimePeriod><Time>24:00</Time><Value>0.000000</Value></ActivationTimePeriod><ActivationTimePeriod><Time>24:00</Time><Value>0.000000</Value></ActivationTimePeriod><ActivationTimePeriod><Time>24:00</Time><Value>0.000000</Value></ActivationTimePeriod><ActivationTimePeriod><Time>24:00</Time><Value>0.000000</Value></ActivationTimePeriod></ActivationTimePeriods></Day></Days>
        this.generateDayArrayFromXML = function (daysXMLNode) {

            var $xmlDoc, arrDay = [];

            if ((daysXMLNode !== null) && (daysXMLNode !== undefined)) {
                $xmlDoc = $(daysXMLNode);

                $xmlDoc.find("Day").each(function () {
                    var $this, dayStructure, label;
                    $this = $(this);

                    dayStructure = new ECALENDAR.DayStructure();
                    dayStructure.dayID = $this.find("Index:first").text();
                    label = $this.find("Label:first").text();
                    switch (label) {
                        case ECALENDAR.ApplicationConstants.weekDays.MONDAY:
                            dayStructure.setLabel(ECALENDAR.ApplicationStrings.getResourceFromID('MONDAY_SHORT'));
                            break;
                        case ECALENDAR.ApplicationConstants.weekDays.TUESDAY:
                            dayStructure.setLabel(ECALENDAR.ApplicationStrings.getResourceFromID('TUESDAY_SHORT'));
                            break;
                        case ECALENDAR.ApplicationConstants.weekDays.WEDNESDAY:
                            dayStructure.setLabel(ECALENDAR.ApplicationStrings.getResourceFromID('WEDNESDAY_SHORT'));
                            break;
                        case ECALENDAR.ApplicationConstants.weekDays.THURSDAY:
                            dayStructure.setLabel(ECALENDAR.ApplicationStrings.getResourceFromID('THURSDAY_SHORT'));
                            break;
                        case ECALENDAR.ApplicationConstants.weekDays.FRIDAY:
                            dayStructure.setLabel(ECALENDAR.ApplicationStrings.getResourceFromID('FRIDAY_SHORT'));
                            break;
                        case ECALENDAR.ApplicationConstants.weekDays.SATURDAY:
                            dayStructure.setLabel(ECALENDAR.ApplicationStrings.getResourceFromID('SATURDAY_SHORT'));
                            break;
                        case ECALENDAR.ApplicationConstants.weekDays.SUNDAY:
                            dayStructure.setLabel(ECALENDAR.ApplicationStrings.getResourceFromID('SUNDAY_SHORT'));
                            break;
                    }
                    dayStructure.arrActivationPeriod = self.generateActivationPeriodArrayFromXML($this.find("ActivationTimePeriods:first"));
                    arrDay.push(dayStructure);
                });
            }
            return arrDay;
        };


        //This function will generate the activation period array from input XML
        //Input XML format: <ActivationTimePeriods><ActivationTimePeriod><Time>08:00</Time><Value>1.000000</Value></ActivationTimePeriod><ActivationTimePeriod><Time>17:30</Time><Value>0.000000</Value></ActivationTimePeriod><ActivationTimePeriod><Time>24:00</Time><Value>0.000000</Value></ActivationTimePeriod><ActivationTimePeriod><Time>24:00</Time><Value>0.000000</Value></ActivationTimePeriod><ActivationTimePeriod><Time>24:00</Time><Value>0.000000</Value></ActivationTimePeriod><ActivationTimePeriod><Time>24:00</Time><Value>0.000000</Value></ActivationTimePeriod></ActivationTimePeriods>
        this.generateActivationPeriodArrayFromXML = function (activationPeriodsXMLNode) {
            var $xmlDoc, arrActivationperiods = [];
            if ((activationPeriodsXMLNode !== undefined) && (activationPeriodsXMLNode !== null)) {
                $xmlDoc = $(activationPeriodsXMLNode);
                $xmlDoc.find("ActivationTimePeriod").each(function () {
                    var activationPeriod, $this;

                    $this = $(this);
                    activationPeriod = new ECALENDAR.ActivationPeriodDataStructure();
                    activationPeriod.setStringTime($this.find("Time:first").text());
                    activationPeriod.setValue(parseInt($this.find("Value:first").text(), 10));

                    arrActivationperiods.push(activationPeriod);
                });
            }
            return arrActivationperiods;
        };

        //Input the Exceptions XML and this function will return the ECALENDAR.ExceptionCollection object
        //In case if the input parameters is null or undefined this function will return null.
        this.generateExceptionCollectionFromXML = function (exceptionCollectionXML) {
            var xmlDoc, $xmlDoc, exceptionCollection = null;
            if ((exceptionCollectionXML !== undefined) && (exceptionCollectionXML !== null)) {

                //Assumed that XML always comes in the correct format.
                xmlDoc = $.parseXML(exceptionCollectionXML);
                $xmlDoc = $(xmlDoc);

                exceptionCollection = new ECALENDAR.ExceptionCollection();

                $xmlDoc.find("exception").each(function () {
                    var $this, index, label, specialDayID, weeksetID, timeSchemeLabel, sameEveryYear, exceptionModel, startDate, endDate, colour, diaryId;

                    $this = $(this);
                    index = parseInt($this.find("exceptionID:first").text(), 10);
                    if (index === -1) {
                        index = null;
                    }
                    label = $('<div />').text($this.find("label:first").text()).html();
                    specialDayID = parseInt($this.find("specialDayID:first").text(), 10);
                    weeksetID = parseInt($this.find("weeksetID:first").text(), 10);
                    timeSchemeLabel = $this.find("timeschemelabel:first").text();
                    sameEveryYear = (parseInt($this.find("sameEveryYear:first").text(), 10) === 1);
                    startDate = new Date();
                    startDate.setFullYear(parseInt($this.find("startDate:first > year").text(), 10), parseInt($this.find("startDate:first > month").text(), 10) - 1, parseInt($this.find("startDate:first > day").text(), 10));
                    startDate.setHours(0, 0, 0, 0);
                    endDate = new Date();
                    endDate.setFullYear(parseInt($this.find("endDate:first > year").text(), 10), parseInt($this.find("endDate:first > month").text(), 10) - 1, parseInt($this.find("endDate:first > day").text(), 10));
                    endDate.setHours(0, 0, 0, 0);
                    colour = $this.find("timeschemecolour:first").text();
                    diaryId = parseInt($this.find("diaryGroupID:first").text(), 10);

                    exceptionModel = new ECALENDAR.ExceptionModel();

                    if (_.isNumber(diaryId) && !_.isNaN(diaryId)) {
                        exceptionModel.set({ diaryGroupID: diaryId }, { silent: true });
                    } else {
                        exceptionModel.set({ diaryGroupID: ECALENDAR.DiaryGroupSelection.get('diaryGroup').get('diaryID') }, { silent: true });
                    }

                    exceptionModel.set({ exceptionID: index }, { silent: true });
                    exceptionModel.set({ label: label }, { silent: true });
                    exceptionModel.set({ weeksetID: weeksetID }, { silent: true });
                    exceptionModel.set({ specialDayID: specialDayID }, { silent: true });
                    exceptionModel.set({ sameEveryYear: sameEveryYear }, { silent: true });
                    exceptionModel.set({ startDate: startDate }, { silent: true });
                    exceptionModel.set({ endDate: endDate }, { silent: true });
                    exceptionModel.set({ colour: colour }, { silent: true });
                    exceptionModel.set({ timeschemelabel: timeSchemeLabel }, { silent: true });

                    exceptionCollection.add(exceptionModel);
                });
            }
            return exceptionCollection;
        };
    };

    ECALENDAR.DataProvider = new ModelGenerator();
});