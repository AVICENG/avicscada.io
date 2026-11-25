/*globals ECALENDAR*/
/*globals Backbone*/
/*globals $*/

$(function () {
    "use strict";
    ECALENDAR.DiaryCollection = Backbone.Collection.extend({
        model: ECALENDAR.DiaryModel,

        initialize: function () {
            this.add([
				{ label: "Global", diaryID: -1, isFolder: true, childrenArray: [] }
			]);
        },

        getModelFromId: function (id) {
            var i, diaryModel;
            for (i = 0; i < this.models.length; i += 1) {
                diaryModel = this.models[i];
                if (diaryModel.get("diaryID") === id) {
                    return diaryModel;
                }
            }
            return null;
        },

        validateAllChildren: function () {
            var folderId, diaryModel, childArray, child, childID;
            for (folderId = 0; folderId < this.models.length; folderId += 1) {
                diaryModel = this.models[folderId];
                childArray = diaryModel.get("childrenArray");

                for (child = 0; child < childArray.length; child += 1) {
                    childID = childArray[child];
                    if (this.getModelFromId(childID) === null) {
                        return "Folder " + diaryModel.get("label") + " has an child (id=" + childID + ") which does not exist in the collection";
                    }
                }
            }
        },

        //Parse and build the data-model based on the input XML.
        parse: function (resp, xhr) {
            //Return the array of new models. They will automatically added in the collection.
            var returnValue = null, diaryCollection;
            if ((xhr !== null) && (xhr !== undefined)) {
                diaryCollection = ECALENDAR.DataProvider.generateDiaryCollectionFromXML(xhr.responseText);
                if ((diaryCollection !== null) && (diaryCollection !== undefined)) {
                    returnValue = diaryCollection.models;
                }
            }
            return returnValue;
        }
    });
});
