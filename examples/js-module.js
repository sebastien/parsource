// FROM: https://github.com/sebastien/select.js/blob/master/src/select.js#L405
// @module select

// @function Filters all the nodes that match the given selector. This is a wrapper
// around `select.filter`.
//
// @param(selector,String) -- the selector string to use as filter
// @param(nodes,[Node]) -- the node set to filter
//
// @returns(Node) the subset of the array with matching nodes
var filter = function(selector, nodes) {
    var result = [];
    for (var i = 0; i < nodes.length; i++) {
        var node = nodes[i];
        if (match(selector, node)) {
            result.push(node);
        }
    }
    return result;
};

// @class Wraps an array of node resulting from the selection of the given
// selector in the given scope.
//
// Note that in any case, the *selection will only contain element nodes*.
//
// @arg(selector,String|Node|Selection) -- the selector to look from nodes from the base
// @arg(scope,String|Node|Selection) -- set of nodes to use as the base for the selection
var Selection = function(selector, scope) {
    // @attribute(isSelection,bool) -- helper attribute to denote that the
    // object is a selection.
    this.isSelection = true;
    // […]
};

// @parent(Selection,Array)
Selection.prototype = new Array();

// @classmethod Tells if the value is a selection
// @returns(bool)
// @example select.Selection.Is(new Selection ()) === true
Selection.Is = function(s) {
    return s && s.__class__ === Selection;
};
