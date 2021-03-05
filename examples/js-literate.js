// FROM: https://github.com/jashkenas/underscore/blob/master/underscore.js

// @module Underscore.js @version(1.10.2)
// @url    https://underscorejs.org
// @copyright
//  (c) 2009-2020 Jeremy Ashkenas, DocumentCloud and Investigative Reporters & Editors
//  Underscore may be freely distributed under the MIT license.

// @section Baseline setup

// @p Establish the root object, `window` (`self`) in the browser, `global`
// on the server, or `this` in some virtual machines. We use `self`
// instead of `window` for `WebWorker` support.
var root =
    (typeof self == "object" && self.self === self && self) ||
    (typeof global == "object" && global.global === global && global) ||
    Function("return this")() ||
    {};

// @p Save bytes in the minified (but not gzipped) version:
var ArrayProto = Array.prototype,
    ObjProto = Object.prototype;
var SymbolProto = typeof Symbol !== "undefined" ? Symbol.prototype : null;

// @p Create quick reference variables for speed access to core prototypes.
var push = ArrayProto.push,
    slice = ArrayProto.slice,
    toString = ObjProto.toString,
    hasOwnProperty = ObjProto.hasOwnProperty;
