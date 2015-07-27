

function getParameterByName(name) {
    name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results === null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
};

var successurl;

angular.module('bibliocratie_app')
.controller('LoginCtrl', ['$scope', '$rootScope','$http', '$window', 'djangoForm', 'djangoUrl', 'djangoAuth','LoginSrvc', function ($scope, $rootScope, $http, $window, djangoForm, djangoUrl, djangoAuth, LoginSrvc) {
    $scope.login = {};
    $scope.loginSubmit = function () {
        if ($scope.login_data) {
            $scope.login_data.action='login';
            $scope.login_data.next=getParameterByName('next');
            if ($scope.login_data.next==""){
                $scope.login_data.next=LoginSrvc.getNextPage();
            }
            if ($scope.login_data.next==""){
                $scope.login_data.next=document.URL;
            }
            $http.post(djangoUrl.reverse('home'), $scope.login_data).success(function (out_data) {
                if (!djangoForm.setErrors($scope.login_form, out_data.errors)) {
                    // on successful post, redirect onto success page
                    successurl = out_data.success_url;

                    if ($window.location.href!=successurl){
                        $window.location.href = successurl;
                    } else {
                        window.location.reload()
                    }
                }
            }).error(function () {
                console.error('An error occured during submission');
            });
        }
        return false;
    };

    $scope.signup_phase = 0;

    $scope.setPhase = function(){
        $scope.signup_phase = 1;
    }


    $scope.checkphase = function (phase) {
        if ($scope.signup_phase==phase){
            return true;
        }
        return false;
    }

    function getCookie(name) {
      var cookieValue = null;
      if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
          var cookie = jQuery.trim(cookies[i]);
          // Does this cookie string begin with the name we want?
          if (cookie.substring(0, name.length + 1) == (name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    }

    $scope.signup_data = {};
    $scope.signupSubmit = function () {
        if ($scope.signup_data) {
            $scope.signup_data.action='signup';
            $scope.signup_data.next=getParameterByName('next');
            if ($scope.signup_data.next==""){
                $scope.signup_data.next=LoginSrvc.getNextPage();
            }
            if ($scope.signup_data.next==""){
                $scope.signup_data.next=document.URL;
            }

            if ($scope.signup_data.next.indexOf('checkout')>0){
                $scope.signup_data['need_more_info']=true;
            }

            $http.post(djangoUrl.reverse('home'), $scope.signup_data).success(function (out_data) {
                if (!djangoForm.setErrors($scope.signup_form, out_data.errors)) {
                    //$('#modalLogin').modal({backdrop: 'static'})

                    // save success page
                    successurl = out_data.success_url;
                    if ($scope.signup_data.hasOwnProperty('need_more_info') && $scope.signup_data['need_more_info']==true){
                        $window.location.href=successurl;
                        return;
                    }
                    $rootScope.csrftoken = getCookie('csrftoken');
                    $rootScope.csrfmiddlewaretoken = getCookie('csrfmiddlewaretoken');

                    $scope.signup_phase = 1;
                }
            }).error(function () {
                swal("Erreur de connexion reseau. Le serveur est injoignable.");
            });
        }
        return false;
    };

    $scope.biolieuSubmit = function () {
        if ($scope.biblio_user_data) {
            $scope.biblio_user_data.action='biolieu';
            $scope.biblio_user_data.next=getParameterByName('next');
            if ($scope.biblio_user_data.next==""){
                $scope.biblio_user_data.next=LoginSrvc.getNextPage();
            }
            if ($scope.biblio_user_data.next==""){
                $scope.biblio_user_data.next=document.URL;
            }

            $http.post(djangoUrl.reverse('home'), $scope.biblio_user_data).success(function (out_data) {
                if (!djangoForm.setErrors($scope.biblio_user_form, out_data.errors)) {
                    if ($scope.signup_phase==2 ){
                        if ($scope.signup_data.next && $scope.signup_data.next.indexOf("lancement") > 0) {
                            $scope.signup_phase=3;
                        } else {
                            $window.location.href=successurl;
                        }
                    } else {
                        $scope.signup_phase = 2;
                    }

                }
            }).error(function () {
                swal("Erreur de connexion reseau. Le serveur est injoignable.");
            });
        } else {
            swal("Si vous ne voulez pas rentrer votre biographie, rentrez au moins un lieu")
        }
        return false;
    }


    $scope.adresseSubmit = function () {
        if ($scope.adresse_data) {
            $scope.adresse_data.action='adresse';
            $scope.adresse_data.next=getParameterByName('next');
            if ($scope.adresse_data.next==""){
                $scope.adresse_data.next=LoginSrvc.getNextPage();
            }
            if ($scope.adresse_data.next==""){
                $scope.adresse_data.next=document.URL;
            }
            $http.defaults.headers.post['X-CSRFToken'] = getCookie('csrftoken');
            $http.post(djangoUrl.reverse('home'), $scope.adresse_data).success(function (out_data) {
                if (!djangoForm.setErrors($scope.adresse_form, out_data.errors)) {
                    $window.location.href=successurl;
                }
            }).error(function () {
                swal("Erreur de connexion reseau. Le serveur est injoignable.");
            });
        } else {
            swal("Si vous ne voulez pas rentrer votre biographie, rentrez au moins un lieu")
        }
        return false;
    }


    Dropzone.autoDiscover = false;

    $scope.images = {
        config: {
            'options': {
                'url': djangoUrl.reverse('home'),
                parallelUploads: 3,
                maxFiles:1,
                maxFileSize: 30,
                paramName:"avatar",
                autoDiscover : false,
                acceptedFiles : '.jpg',
                dictInvalidFileType : "Seuls les fichiers de type .jpg sont acceptés",
                previewsContainer : '#uploaded_avatar',
                previewTemplate : '<div class="dz-preview dz-file-preview">\
                              <div class="dz-details text-center">\
                                <div class="dz-filename ng-hide"><span data-dz-name></span></div>\
                                <div class="dz-size ng-hide" data-dz-size></div>\
                                <img data-dz-thumbnail class="img-circle img-full" style="max-height:120px; max-width:120px;" />\
                              </div>\
                              <div class="dz-progress"><span class="dz-upload" data-dz-uploadprogress></span></div>\
                              <div class="dz-success-mark ng-hide"><span>✔</span></div>\
                              <div class="dz-error-mark ng-hide"><span>✘</span></div>\
                              <div class="dz-error-message"><span data-dz-errormessage></span></div>\
                            </div>',
            },
            'eventHandlers': {
                'error': function(file, response, xhr) {
                },
                'complete': function() {
                },
                'sending': function (file, xhr, formData) {
                },
                'success': function (file, response) {
                },
            },
        }
    };


    $scope.recoverSubmit = function () {
        $scope.recover_data.action='recover';
        if ($scope.recover_data) {
            $http.post(djangoUrl.reverse('home'), $scope.recover_data).success(function (out_data) {
                if (!djangoForm.setErrors($scope.recover_form, out_data.errors)) {
                    // on successful post, redirect onto success page
                    $('#modalRecover').modal('toggle');
                    swal("Un mail de confirmation vient de vous être envoyé.");
                }
            }).error(function () {
                swal("Erreur de connexion reseau. Le serveur est injoignable.");
            });
        }
        return false;
    };

    $('#modalSignup').on('hide.bs.modal', function (e) {
        if ($scope.signup_phase!=0)
        {
            e.preventDefault();
            e.stopImmediatePropagation();
            return false;
        }


    });

    //$('#modalSignup').on('hidden.bs.modal', function (e) {
    //    djangoAuth.authenticationStatus(true).then(function(result) {
    //        $window.location.href=successurl
    //    }, function(err) {
    //        console.log(err); // Error: "Ça a foiré"
    //    });
    //});

}]);


angular.module('bibliocratie_app').directive('match', function () {
    return {
        require: 'ngModel',
        restrict: 'A',
        scope: {
            match: '='
        },
        link: function (scope, elem, attrs, ctrl) {
            scope.$watch(function () {
                var modelValue = ctrl.$modelValue || ctrl.$$invalidModelValue;
                return (ctrl.$pristine && angular.isUndefined(modelValue)) || scope.match === modelValue;
            }, function (currentValue) {
                ctrl.$setValidity('match', currentValue);
            });
        }
    };
});