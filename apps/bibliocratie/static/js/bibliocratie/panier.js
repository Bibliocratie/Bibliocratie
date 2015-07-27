angular.module('bibliocratie_app')
    .controller("PanierCtrl", ['$scope','$rootScope','$window', 'djangoRMI', 'djangoUrl', 'LoginSrvc','djangoForm','$timeout', '$http','packeryService', 'biblioUserWebsocket', function ($scope, $rootScope, $window, djangoRMI, djangoUrl, LoginSrvc, djangoForm, $timeout, $http, packeryService, biblioUserWebsocket) {
        $scope.panier = {
            souscription_set: [],
            discount_set: [],
            shipping: 0,
            shipping_country:'France',
            prix:0,
            nbArticles:0,
        };

        $scope.init = function () {
            $scope.basketAddLivre(-1);
        }


        $scope.basketAddLivre = function (livre_id, quantite) {
            var in_data = { livre_id: livre_id, quantite:quantite };
            djangoRMI.panierjsonview.addLivre(in_data)
                .success(function (out_data) {
                    $scope.panier=out_data.panier;
                    if (out_data.message!="") swal(out_data.message);
                    if (livre_id!=-1){
                        $('#basket-dropdown').dropdown('toggle');
                        $timeout(function() {
                            if (document.getElementById('basket-dropdown').attributes['aria-expanded'].value=="true"){
                                $('#basket-dropdown').dropdown('toggle');
                            }
                        },5000);
                    }
                })
                .error(function(data, status, headers, config) {
                   swal("Erreur de connexion reseau. Le serveur est injoignable.");
                });
        },

        $scope.basketRemoveLivre = function (livre_id) {
            var in_data = { livre_id: livre_id };
            djangoRMI.panierjsonview.removeLivre(in_data)
                .success(function (out_data) {
                    $scope.panier=out_data.panier;
                })
                .error(function(data, status, headers, config) {
                   if (data){swal(data.detail);} else {swal("Erreur de connexion reseau. Le serveur est injoignable.");}
                });
        },

        $scope.basketRemoveItem = function (souscription_id) {
            var in_data = { souscription_id: souscription_id };
            djangoRMI.panierjsonview.removeSouscriptions(in_data)
                .success(function (out_data) {
                    $scope.panier=out_data.panier;
                })
                .error(function(data, status, headers, config) {
                   swal("Erreur de connexion reseau. Le serveur est injoignable.");
                });
        },

        $scope.basketRemoveDiscount = function (discount_id) {
            var in_data = { discount_id: discount_id };
            djangoRMI.panierjsonview.removeDiscount(in_data)
                .success(function (out_data) {
                    $scope.panier=out_data.panier;
                })
                .error(function(data, status, headers, config) {
                   swal("Erreur de connexion reseau. Le serveur est injoignable.");
                });
        },

        $scope.onSouscription = function (panier) {
            $scope.panier=panier;
        }

        $scope.packery = function(){
            var promise = packeryService.Packery();
            promise.then(function (object) {
                object.layout();
                $timeout(function() {object.layout();},500)
                $timeout(function() {object.layout();},1000)
                $timeout(function() {object.layout();},2000)
            });
        }

        biblioUserWebsocket.connect($scope, 'onSouscription', 'PANIER');

        $scope.init();

        $scope.toggleMenu = function(){
            if (!$('#chat-bar').hasClass('chat-active')) {
                $('#nav,.navbar-header').addClass('nav-xs');
            }
        }

        $scope.toggleChat = function(){
            if ($('#nav').hasClass('nav-xs')) {
                $('#chat-bar,#subContent').removeClass('chat-active');
            }
        }

        $scope.toggleSearch = function(){
            $('#globalSearch').addClass('active');
            $timeout(function() {
                document.getElementById('searchInput').focus();
            },100);
        }

        Dropzone.autoDiscover = false;

        $scope.images = {
            config: {
                'options': {
                    'url': djangoUrl.reverse('paylineretour'),
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

        $rootScope.csrftoken = getCookie('csrftoken');
        $rootScope.csrfmiddlewaretoken = getCookie('csrfmiddlewaretoken');

        $scope.retourPaylineSubmit = function () {
            if ($scope.biblio_userbiolieu_data) {
                $http.defaults.headers.post['X-CSRFToken'] = getCookie('csrftoken');
                $http.post(djangoUrl.reverse('paylineretour'), $scope.biblio_userbiolieu_data).success(function (out_data) {
                    if (!djangoForm.setErrors($scope.biblio_userbiolieu_form, out_data.errors)) {
                        $window.location.href=out_data.successurl;
                    }
                }).error(function () {
                    swal("Erreur de connexion reseau. Le serveur est injoignable.");
                });
            } else {
                swal("Si vous ne voulez pas rentrer votre biographie, rentrez au moins un lieu")
            }
            return false;
        }

        $scope.couponSubmit = function () {
            if ($scope.coupon_data) {
                $http.post(djangoUrl.reverse('panier'), $scope.coupon_data).success(function (out_data) {
                    if (!djangoForm.setErrors($scope.coupon_form, out_data.errors)) {
                        $scope.basketRefresh(out_data);
                    }
                }).error(function(data, status, headers, config) {
                   swal("Erreur de connexion reseau. Le serveur est injoignable.");
                });
            }
        };
        $scope.goToOrderSubmit = function () {
            var in_data = { rien: "rien" };
            djangoRMI.panierjsonview.goToOrder(in_data)
                .success(function (out_data) {
                    if (out_data.is_authenticated) {
                        $window.location.href = out_data.success_url + '?nocache=' + (new Date()).getTime();
                    } else {
                        LoginSrvc.setNextPage('checkout')
                        swal({  title: "Vous devez être authentifié pour valider votre commande",
                                text: "Avez-vous déjà un compte Bibliocratie?",
                                type: "",
                                showCancelButton: true,
                                confirmButtonColor: "#DD6B55",
                                confirmButtonText: "S'authentifier",
                                cancelButtonText: "Créer un compte",
                                closeOnConfirm: true,
                                closeOnCancel: true,
                                allowEscapeKey:true,
                                allowOutsideClick:true
                            }, function (isConfirm) {
                                if (isConfirm) {
                                    $('#modalLogin').modal('show');
                                } else {
                                    $('#modalSignup').modal('show');
                                }
                            }
                        );
                    }
                });
        }

        $scope.lancerMonProjet = function () {
            var in_data = { rien: "rien" };
            djangoRMI.panierjsonview.lancerMonProjet(in_data)
                .success(function (out_data) {
                    if (out_data.is_authenticated) {
                        $window.location.href = out_data.success_url + '?nocache=' + (new Date()).getTime();
                    } else {
                        LoginSrvc.setNextPage('checkout')
                        swal({  title: "Vous devez être authentifié pour lancer votre projet",
                                text: "Avez-vous déjà un compte Bibliocratie?",
                                type: "",
                                showCancelButton: true,
                                confirmButtonColor: "#DD6B55",
                                confirmButtonText: "S'authentifier",
                                cancelButtonText: "Créer un compte",
                                closeOnConfirm: true,
                                closeOnCancel: true,
                                allowEscapeKey:true,
                                allowOutsideClick:true
                            }, function (isConfirm) {
                                if (isConfirm) {
                                    $('#modalLogin').modal('show');
                                } else {
                                    $('#modalSignup').modal('show');
                                }
                            }
                        );
                    }
                });
        }
    }]);


$('body').on('click', function (e) {
    if (!$('#panier-dropdown').parent().is(e.target) && $('#panier-dropdown').parent().has(e.target).length === 0 && $('.open').has(e.target).length === 0 && e.target.className != "icon-close" && !e.target.classList.contains("lnk-panier")) {
        $('#menuUtilisateurContenu li').removeClass('open');
    }
    if (e.target.classList.contains("lnk-panier") || ($('#panier-dropdown').parent().has(e.target).length != 0)) {
        $('#menuUtilisateurContenu li').addClass('open');
    }
    if ($('#continuer_achat').is(e.target)) {
        $('#menuUtilisateurContenu li').removeClass('open');
    }

});
