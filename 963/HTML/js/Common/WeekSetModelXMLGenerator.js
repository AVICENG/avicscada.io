/*
* WeekSetModelXMLGenerator
*
* This will generate the xml for DiaryModel.
*
* Date: Thu April 12, 2012
* Copyright 2008-2012 Honeywell Technologies Sarl, ECC Division. All rights reserved. Copyright 1995-2008 Trend Control Systems Ltd. 
*/

/*globals ECALENDAR*/
/*globals _*/
/*globals $*/

$(function () {
    "use strict";

    var XMLGenerator;
    XMLGenerator = function () {
        this.XML_METADATA = "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>";

        //Delete weekset XML for Weekset object 
        this.generateDeleteWeekSetXML = function (weeksetObject, newDefaultWeekSet) {
            var retXML = '', defaultXML = '';
            if ((weeksetObject !== null) && (weeksetObject !== undefined)) {
                retXML = this.createElement('weeksetID', weeksetObject.get('weekSetID'));
                retXML += this.createElement('groupId', weeksetObject.get('groupId'));
                retXML = this.createElement('WeekSetModel', retXML);
            }
            if ((newDefaultWeekSet !== null) && (newDefaultWeekSet !== undefined)) {
                defaultXML = this.createElement('weeksetID', newDefaultWeekSet.get("weekSetId"));
                defaultXML += this.createElement('groupId', weeksetObject.get('groupId'));
                defaultXML = this.createElement('NewDefaultWeekSet', defaultXML);
                retXML += defaultXML;
            }
            if (retXML.length > 0) {
                retXML = this.createElement('DeleteWeekSet', retXML);
            }
            return retXML;
        };

        //This function creates XML from the Exception model.
        this.generateExceptionModelXML = function (exceptionObject) {
            var retXML = '', xmlContent = '';
            if ((exceptionObject !== null) && (exceptionObject !== undefined)) {
                xmlContent = this.generateExceptionContentXML(exceptionObject);
                retXML = this.createElement('Exception', xmlContent);
            }
            return retXML;
        };

        this.generateOrigExceptionForEditModelXML = function (exceptionObject) {
            var retXML = '', xmlContent = '';
            if ((exceptionObject !== null) && (exceptionObject !== undefined)) {
                xmlContent = this.generateExceptionContentXML(exceptionObject);
                retXML = this.createElement('OrigExceptionForEdit', xmlContent);
            }
            return retXML;
        };

        this.generateExceptionContentXML = function (exceptionObject) {
            var temp, xmlContent = '', sameEveryYearValue = 0;

            if ((exceptionObject !== null) && (exceptionObject !== undefined)) {
                temp = new Date();
                xmlContent = this.createElement('exceptionID', exceptionObject.get("exceptionID") || -1);
                xmlContent += this.createElement('label', '<![CDATA[' + exceptionObject.get("label") + ']]>');
                xmlContent += this.createElement('diaryGroupID', exceptionObject.get("diaryGroupID"));

                xmlContent += this.createElement('startDate', this.generateDateXML(exceptionObject.get("startDate")));
                xmlContent += this.createElement('endDate', this.generateDateXML(exceptionObject.get("endDate")));
                if (exceptionObject.get("sameEveryYear") === true) {
                    sameEveryYearValue = 1;
                }
                xmlContent += this.createElement('sameEveryYear', sameEveryYearValue);
                xmlContent += this.createElement('specialDayID', exceptionObject.get("specialDayID"));
                xmlContent += this.createElement('weeksetID', exceptionObject.get("weeksetID"));
                xmlContent += this.createElement('isWeekset', exceptionObject.get("isWeekset"));

                xmlContent += this.createElement('timeschemelabel', '<![CDATA[' + $('<div />').html(exceptionObject.get("timeschemelabel")).text() + ']]>');
            }
            return xmlContent;
        };

        //This function will generate the XML from the date object.
        this.generateDateXML = function (dateObject) {
            var xml = "";
            if ((dateObject !== null) && (dateObject !== undefined) && (_.isDate(dateObject))) {
                xml = this.createElement('year', dateObject.getFullYear());
                xml += this.createElement('month', (dateObject.getMonth() + 1));
                xml += this.createElement('day', dateObject.getDate());
            }
            return xml;
        };

        //This function will generate the XML from the date object.
        this.generateDeleteDateXML = function (dateObject) {
            var xml = "<date>";
            if ((dateObject !== null) && (dateObject !== undefined) && (_.isDate(dateObject))) {
                xml += this.createElement('year', dateObject.getFullYear());
                xml += this.createElement('month', (dateObject.getMonth() + 1));
                xml += this.createElement('day', dateObject.getDate());
            }
            xml += "</date>";
            return xml;
        };

        this.generateDeleteExceptionModelXML = function (exceptionObject) {
            var retXML = '', xmlContent = '', sameEveryYearValue = 0;
            if ((exceptionObject !== null) && (exceptionObject !== undefined)) {
                xmlContent = this.createElement('exceptionID', exceptionObject.get("exceptionID") || -1);
                xmlContent += this.createElement('startDate', this.generateDateXML(exceptionObject.get("startDate")));
                xmlContent += this.createElement('endDate', this.generateDateXML(exceptionObject.get("endDate")));
                if (exceptionObject.get("sameEveryYear") === true) {
                    sameEveryYearValue = 1;
                }
                xmlContent += this.createElement('sameEveryYear', sameEveryYearValue);
                xmlContent += this.createElement('label', exceptionObject.get("label"));
                xmlContent += this.createElement('diaryGroupID', exceptionObject.get("diaryGroupID"));
                retXML = this.createElement('Exception', xmlContent);
            }
            return retXML;
        };

        //This function creates XML from the exception collection.
        this.generateGenericExceptionCollectionXML = function (exceptionCollectionObject, collectionForDeletion) {
            var i, modelXml = "", xmlContent = "";

            if ((exceptionCollectionObject !== null) && (exceptionCollectionObject !== undefined) && collectionForDeletion != null) {
                for (i = 0; i < exceptionCollectionObject.models.length; i += 1) {
                    if (collectionForDeletion) {
                        modelXml = modelXml + this.generateDeleteExceptionModelXML(exceptionCollectionObject.models[i]);
                    } else {
                        modelXml = modelXml + this.generateExceptionModelXML(exceptionCollectionObject.models[i]);

                        if (exceptionCollectionObject != null && exceptionCollectionObject.originalForEdit != null) {
                            modelXml = modelXml + this.generateOrigExceptionForEditModelXML(exceptionCollectionObject.originalForEdit);
                        }
                    }
                }
                xmlContent = this.createElement("ExceptionCollection", modelXml);
            }
            return xmlContent;
        };

        this.generateExceptionCollectionXML = function (exceptionCollectionObject) {
            return this.generateGenericExceptionCollectionXML(exceptionCollectionObject, false);
        };

        this.generateDeleteExceptionCollectionXML = function (exceptionCollectionObject) {
            return this.generateGenericExceptionCollectionXML(exceptionCollectionObject, true);
        };

        this.generateWeeksetXML = function (dataObject) {
            var retXML, xmlContent, dayStruct, arrDayXML;
            retXML = '';
            xmlContent = '';

            xmlContent += this.createElement('groupId', dataObject.get("groupId"));

            xmlContent += this.createElement('colour', dataObject.get("colour"));
            xmlContent += this.createElement('label', '<![CDATA[' + dataObject.get("label") + ']]>');
            xmlContent += this.createElement('weeksetID', dataObject.get("weekSetID"));

            // Now generate the xml content for day structure
            dayStruct = dataObject.get("arrDay");
            arrDayXML = this.createDayStructureXML(dataObject.get("arrDay"));

            xmlContent += arrDayXML;

            retXML += this.createElement('WeekSetModel', xmlContent);
            return retXML;
        };


        this.generateSpecialDayXML = function (dataObject) {
            var retXML, xmlContent, dayStruct, arrDayXML;
            retXML = '';
            xmlContent = '';

            xmlContent += this.createElement('GroupID', dataObject.get("groupId"));

            xmlContent += this.createElement('Colour', dataObject.get("colour"));
            xmlContent += this.createElement('Label', '<![CDATA[' + dataObject.get("label") + ']]>');
            xmlContent += this.createElement('Index', dataObject.id);

            // Now generate the xml content for day structure
            dayStruct = dataObject.get("arrDay");
            arrDayXML = this.createSpecialDayStructureXML(dataObject.get("arrDay"));

            xmlContent += arrDayXML;

            retXML += this.createElement('SpecialDayModel', xmlContent);
            return retXML;
        };

        //This function will create the xml for spcial days DayStructure
        this.createSpecialDayStructureXML = function (dayStructure) {
            var retDayXML, dayXML, nIndex, dayContent, arrActivationPeriod, arrActivationPeriodXML;
            retDayXML = '';
            dayXML = '';
            dayContent = '';
            if (dayStructure.length !== 0) {
                for (nIndex = 0; nIndex < dayStructure.length; nIndex += 1) {
                    // Now generate the xml content for Activation Period
                    arrActivationPeriod = dayStructure[nIndex].arrActivationPeriod;
                    dayContent += this.createSpecialDayActivationPeriodXML(arrActivationPeriod);
                }
            }

            retDayXML = this.createElement('ActivationTimePeriods', dayContent);

            return retDayXML;
        };


        this.createElement = function (elementName, value) {
            return '<' + elementName + '>' + value + '</' + elementName + '>';
        };

        //This function will create the xml for DayStructure
        this.createDayStructureXML = function (dayStructure) {
            var retDayXML, dayXML, nIndex, dayContent, arrActivationPeriod, arrActivationPeriodXML;
            retDayXML = '';
            dayXML = '';
            if (dayStructure.length !== 0) {
                for (nIndex = 0; nIndex < dayStructure.length; nIndex += 1) {
                    dayContent = '';
                    dayContent += this.createElement('dayName', dayStructure[nIndex].getLabel());

                    // Now generate the xml content for Activation Period
                    arrActivationPeriod = dayStructure[nIndex].arrActivationPeriod;
                    arrActivationPeriodXML = this.createActivationPeriodXML(arrActivationPeriod);

                    if (arrActivationPeriodXML !== '') {
                        dayContent += arrActivationPeriodXML;
                    }

                    dayXML += this.createElement('day', dayContent);
                }
            }

            retDayXML = this.createElement('arrDay', dayXML);

            return retDayXML;
        };

        //This function will create the xml for Activation Period
        this.createActivationPeriodXML = function (arrActivationPeriod) {
            var actPeriodContent, actPeriodXML, timePeriod, nValue;

            actPeriodContent = '';
            actPeriodXML = '';
            timePeriod = '';

            if (arrActivationPeriod.length !== 0) {
                for (nValue = 0; nValue < arrActivationPeriod.length; nValue = nValue + 2) {
                    actPeriodContent = '';
                    actPeriodContent += this.createElement('startTime', arrActivationPeriod[nValue].timeAsString());
                    actPeriodContent += this.createElement('startValue', arrActivationPeriod[nValue].getValue());
                    actPeriodContent += this.createElement('endTime', arrActivationPeriod[nValue + 1].timeAsString());
                    actPeriodContent += this.createElement('endValue', arrActivationPeriod[nValue + 1].getValue());
                    timePeriod += this.createElement('timePeriod', actPeriodContent);
                }
            }

            if (timePeriod !== '') {
                actPeriodXML = this.createElement('arrActivationPeriod', timePeriod);
            }

            return actPeriodXML;
        };

        //This function will create the xml for Activation Period
        this.createSpecialDayActivationPeriodXML = function (arrActivationPeriod) {
            var actPeriodContent, timePeriod, nValue;

            actPeriodContent = '';
            timePeriod = '';

            if (arrActivationPeriod.length !== 0) {
                for (nValue = 0; nValue < arrActivationPeriod.length; nValue = nValue + 2) {
                    actPeriodContent = '';
                    actPeriodContent += this.createElement('StartTime', arrActivationPeriod[nValue].timeAsString());
                    actPeriodContent += this.createElement('StartValue', arrActivationPeriod[nValue].getValue());
                    actPeriodContent += this.createElement('EndTime', arrActivationPeriod[nValue + 1].timeAsString());
                    actPeriodContent += this.createElement('EndValue', arrActivationPeriod[nValue + 1].getValue());
                    timePeriod += this.createElement('ActivationTimePeriod', actPeriodContent);
                }
            }

            return timePeriod;
        };

        this.generateWeekSetTimeChangeXML = function (model) {
            var retXML, xmlContent, dayStruct, arrDayXML;
            retXML = '';
            xmlContent = '';


            xmlContent += this.createElement('label', '<![CDATA[' + model.get("label") + ']]>');
            xmlContent += this.createElement('weeksetID', model.get("weekSetId"));
            if (model.get('date') !== null) {
                xmlContent += this.createElement('date', this.generateDateXML(model.get("date")));
            }


            retXML += this.createElement('NewDefaultWeekSet', xmlContent);
            return retXML;
        };

        this.generateImportTimeSchemeXML = function (model) {
            var xmlContent = [];

            function createUserChoice(choice) {
                var xmlContent = '';
                xmlContent += this.createElement('diaryGroupID', choice.get('groupId'));
                xmlContent += this.createElement('Replace', choice.get('replace'));
                return this.createElement('UserChoice', xmlContent);
            }
            xmlContent.push(this.createElement('TimeSchemeID', model.get('timeSchemeId')));
            xmlContent.push(this.createElement('diaryGroupID', model.get('groupId')));
            xmlContent.push(this.createElement('isWeekset', model.get('isWeekset')));
            xmlContent.push(this.createElement('yesToAll', model.get('yesToAll')));
            xmlContent.push(this.createElement('noToAll', model.get('noToAll')));
            if (model.get('replaceList').length > 0) {
                xmlContent.push(this.createElement('ConflictDiaryGroupCollection', model.get('replaceList').map(createUserChoice, this).join('')));
            }
            return this.createElement('ImportTimeScheme', xmlContent.join(''));
        };


    };

    ECALENDAR.WeekSetModelXMLGenerator = new XMLGenerator();
});
