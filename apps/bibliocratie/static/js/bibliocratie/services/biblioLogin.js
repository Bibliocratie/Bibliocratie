(function (angular, undefined) {
  'use strict';
  function noop() {
  }

  var biblio_login_module = angular.module('ng.biblio.loginctrl', []);

  biblio_login_module.service('LoginSrvc', function (djangoUrl) {
    var login_redirect_url = djangoUrl.reverse('home');

    this.getNextPage = function () {
      return login_redirect_url;
    };

    this.setNextPage = function (nextpage) {
      login_redirect_url=djangoUrl.reverse(nextpage);
    };
  })}(window.angular));
