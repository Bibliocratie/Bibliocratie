/**
 * Extension of: https://gist.github.com/compact/8118670
 * An AngularJS directive for Dropzone.js, http://www.dropzonejs.com/
 *
 * Usage:
 *
 * <div ng-app="app" ng-controller="SomeCtrl">
 *   <button dropzone ng-config="dropzoneConfig">
 *     Drag and drop files here or click to upload
 *   </button>
 * </div>
 *
 */
Dropzone.autoDiscover = false;
angular.module('dropzone', []).directive('dropzone', function () {
  return {
    scope: {
      ngConfig: '=ngConfig',
      ngCsrftokenname: '@?',
      ngCsrftoken: '=?',
    },
    link: function compile(scope, element, attrs, controller) {
      var dropzone;
      var once = scope.$watch('ngConfig', function(value) {
        if (typeof(value) == 'undefined' || typeof(value.options) == 'undefined') {
          console.error('Dropzone needs a config file with options & a URL to begin. Please refer to http://www.dropzonejs.com/ for details.');
          return;
        }

        var config = value;
        // create a Dropzone for the element with the given options
        dropzone = new Dropzone(element[0], config.options);

        // bind the given event handlers
        angular.forEach(config.eventHandlers, function (handler, event) {
          dropzone.on(event, handler);
        });
        dropzone.on('sending', function(file, xhr, formData) {
          if (typeof(scope.ngCsrftokenname)!='undefined') {
            formData.append(scope.ngCsrftokenname, scope.ngCsrftoken);
          }
        });
        dropzone.on('maxfilesexceeded', function(file) {
          dropzone.removeAllFiles();
          dropzone.addFile(file);
        });
        once();
      });
    }
  };
});
