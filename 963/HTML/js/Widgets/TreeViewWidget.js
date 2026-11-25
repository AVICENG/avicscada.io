/*! - v1.0
* TreeView widget.   
* This is a custom JQuery UI widget to populate the tree veiw control
*
* Date: Wed April 2, 2012
* Copyright © 2008-2012 Honeywell Technologies Sàrl, ECC Division. All rights reserved. Copyright © 1995-2008 Trend Control Systems Ltd.
*
*  Version 1.0.0
*/

/*globals jQuery*/
/*globals $*/

(function ($) {
    "use strict";

    $.widget("ui.TreeView", {
        // These options will be used as defaults
        options: {
            //Input DataCollection information. 
            //Current control will parse the information and generates HTML content.
            diaryCollectionInputData: null
        },

        // Set up the widget
        _create: function () {

            this._renderTreeView();
        },

        //Create the tree view contol here.
        _renderControl: function () {
            var htmlContent, nodeContent, parentID, nodeCount, nodeID, $containerDiv;
            $containerDiv = $(this.element[0]);
            parentID = -1;
            htmlContent = '';
            nodeContent = '';
            htmlContent = '<ul>';

            if (this.options.diaryCollectionInputData !== null) {
                //Initially add only Parent node (Global) and its immediate children
                for (nodeCount = 0; nodeCount < this.options.diaryCollectionInputData.length; nodeCount += 1) {
                    nodeID = this.options.diaryCollectionInputData.at(nodeCount).get('diaryID');
                    parentID = this.__getPatentID(nodeID);
                    if (parentID <= 0) {

                        nodeContent = '<li class="open"' + ' databaseindex="' + this.options.diaryCollectionInputData.at(nodeCount).get('diaryID');

                        if (nodeID !== -1) {
                            if (this.options.diaryCollectionInputData.at(nodeCount).get('isFolder')) {
                                nodeContent += '"><a class="folder pre">';
                            } else {
                                nodeContent += '"><a class="timezone pre">';
                            }
                        }

                        // This will be the top most parent (Global)
                        if (nodeID === -1) {
                            nodeContent += '"><a class="global pre">';
                            nodeContent += $('<div/>').text(this.options.diaryCollectionInputData.at(nodeCount).get('label')).html() + '</a><ul>';
                        } else {//These will the immediate children of the top most node.
                            nodeContent += $('<div/>').text(this.options.diaryCollectionInputData.at(nodeCount).get('label')).html() + '</a></li>';
                        }
                        htmlContent += nodeContent;
                    }
                }

                htmlContent += '</ul></li></ul>';
                $containerDiv.append(htmlContent);

                // Now add the remaining children to the nodes.
                for (nodeCount = 1; nodeCount < this.options.diaryCollectionInputData.length; nodeCount += 1) {
                    parentID = this.__getPatentID(this.options.diaryCollectionInputData.at(nodeCount).get('diaryID'));
                    if (parentID > 0) {
                        nodeContent = '<li class="open"' + ' databaseindex="' + this.options.diaryCollectionInputData.at(nodeCount).get('diaryID');
                        if (this.options.diaryCollectionInputData.at(nodeCount).get('isFolder')) {
                            nodeContent += '"><a class="folder pre">';
                        } else {
                            nodeContent += '"><a class="timezone pre">';
                        }
                        nodeContent += $('<div/>').text(this.options.diaryCollectionInputData.at(nodeCount).get('label')).html() + '</a></li>';

                        if ($("li", $containerDiv).filter('[databaseindex=' + parentID + ']').find('ul').length === 0) {
                            //If the parent does't have any child node
                            nodeContent = '<ul>' + nodeContent + '</ul>';
                            $("li", $containerDiv).filter('[databaseindex=' + parentID + ']').append(nodeContent);
                        } else {//If the parent already have a child node
                            $('li [databaseindex=' + parentID + '] ul:first', $containerDiv).append(nodeContent);
                        }
                    }
                }
            }
        },

        //Traverse all the childrenArray and if the child ID is present in the array then return that nodeID
        __getPatentID: function (nodeID) {
            var parentID, nCount, id;

            parentID = -1;
            for (nCount = 0; nCount < this.options.diaryCollectionInputData.length; nCount += 1) {
                if (this.options.diaryCollectionInputData.at(nCount).attributes.childrenArray.length >= 0) {
                    for (id = 0; id < this.options.diaryCollectionInputData.at(nCount).attributes.childrenArray.length; id += 1) {
                        if (this.options.diaryCollectionInputData.at(nCount).attributes.childrenArray[id] === nodeID) {
                            parentID = this.options.diaryCollectionInputData.at(nCount).get('diaryID');
                        }
                    }
                }
            }
            return parentID;
        },

        //Display the tree view contol here.
        _renderTreeView: function () {
            //As we have all the data structure ready needed for rendering the control. Render them in the available area.
            this._renderControl();
            var $containerDiv = $(this.element[0]);

            $containerDiv.jstree({
                "ui": { "select_limit": 1 },
                "plugins": ["html_data", "ui"]
            }).bind("loaded.jstree", function () {        //Open the tree control by default.
                $containerDiv.jstree("open_all");
            }).bind('select_node.jstree', $.proxy(function () {   //Bind the node selection event in the tree view.               
                var groupIndex, selectedNode = $containerDiv.jstree('get_selected', $containerDiv);

                //Ensure something is selected in the diaryGroup.                
                if ((selectedNode !== undefined) && (selectedNode !== null) && (selectedNode.length > 0)) {
                    //Find out the id of the element.
                    //Please note: In IE 7 & FF 13, attr() or prop() is causing problem - To avoid those problems we have used getAttribute() method which is basic javascript DOM methods (not jquery).
                    groupIndex = parseInt(selectedNode[0].getAttribute("databaseindex"), 10);
                    this._trigger('itemSelected', undefined, { id: groupIndex });


                }
            }, this)).delegate("a", "click", function (event) {
                event.preventDefault();
            }); //Now prevent the default behaviour of the anchor tag.
        },
        get_selected: function () {
            var $containerDiv = $(this.element[0]);
            return $containerDiv.jstree('get_selected', $containerDiv);
        }
    });
} (jQuery));