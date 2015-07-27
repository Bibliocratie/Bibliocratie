angular.module('bibliocratie_app')
.controller("ProfileCtrl", ['$scope', '$rootScope','$http', '$interval','$timeout','djangoUrl', 'djangoRMI', 'djangoForm', 'biblioBroadcastWebsocket','$parse', function($scope, $rootScope, $http, $interval, $timeout, djangoUrl, djangoRMI, djangoForm, biblioBroadcastWebsocket, $parse) {
    $scope.timeline = [];
    $scope.userprofile = {
        'mes_livres' : [],
    };
    $scope.biblio_user_data={};
    $scope.commandes = {};
    $scope.isFirstPage=true;
    $scope.isLastPage=true;
    $scope.type_follow='non';
    var page = 1;

    $scope.gPlace;

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

    Dropzone.autoDiscover = false;

    $scope.images = {
        config: {
            'options': {
                'url': '.',
                parallelUploads: 3,
                maxFiles:1,
                maxFileSize: 30,
                paramName:"avatar",
                autoDiscover : false,
                previewsContainer : '#uploaded_avatar',
                previewTemplate : '<div class="dz-preview dz-file-preview ng-hide">\
                              <div class="dz-details text-center">\
                                <div class="dz-filename ng-hide"><span data-dz-name></span></div>\
                                <div class="dz-size ng-hide" data-dz-size></div>\
                                <img data-dz-thumbnail />\
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
                'sending': function (file, formData, xhr) {
                },
                'success': function (file, response) {
                    $scope.getUserDetail();
                }
            },
        }
    };

    $scope.loadingmore=false;
    $scope.nextPage = function(){
        if (!$scope.isLastPage){
            $scope.loadingmore=true;
            page+=1;
            $scope.getTimeLine();
        }
    };

    $scope.previousPage = function(){
        if (!$scope.isFirstPage){
            page-=1;
            $scope.getTimeLine();
        }
    };

    $scope.ShowSettingsProfil = function(){
        $('#prefTab a[href="#settings_profil"]').tab('show');
    };

    $scope.ShowSettingsPreference = function(){
        $('#prefTab a[href="#settings_preferences"]').tab('show');
    };

    $scope.ShowSettingsCommandes = function(){
        $('#prefTab a[href="#settings_commandes"]').tab('show');
    }


    $scope.profilSubmit = function(button){
        if ($scope.biblio_user_data) {
            var in_data = {'biblio_user_data':$scope.biblio_user_data}
            $http.post(djangoUrl.reverse('profil_detail',{'slug':$scope.user_slug}), in_data).success(function (out_data) {
                if (out_data.refresh){
                    window.location.assign(out_data.new_url);
                }
                if (!djangoForm.setErrors($scope.biblio_user_form, out_data.biblio_user_errors))
                {}
                $scope.buttons[button].value=1;
            }).error(function() {
                swal("Erreur de connexion reseau. Le serveur est injoignable.");
                $scope.buttons[button].value=0;
            });
        }
        return false;
    }

    $scope.preferenceSubmit = function(button){
        if ($scope.preference_data || $scope.facturation_data ) {
            var in_data = {'preference_data':$scope.preference_data,
                           'facturation_data':$scope.facturation_data,
            }
            $http.post(djangoUrl.reverse('profil_detail',{'slug':$scope.userprofile.slug}), in_data).success(function (out_data) {
                if (!djangoForm.setErrors($scope.preference_form, out_data.preference_errors))
                {}
                if (!djangoForm.setErrors($scope.facturation_form, out_data.facturation_errors))
                {}
                $scope.buttons[button].value=1;
            }).error(function() {
                swal("Erreur de connexion reseau. Le serveur est injoignable.");
                $scope.buttons[button].value=0;
            });
        }
        return false;
    }

    $scope.TimeLineInit = function(user_id, slug) {
        $scope.user_id=user_id;
        $scope.user_slug=slug;
        $scope.getTimeLine();
        $scope.getUserDetail();
        $scope.follow(user_id, -1,"?");
    };

    $scope.checkboxes = ['pref_actu','pref_adol','pref_art','pref_bd','pref_beau','pref_cuisine','pref_dict','pref_droit',
                         'pref_entreprise','pref_erotisme','pref_esoterisme','pref_etude','pref_famille','pref_fantaisie',
                         'pref_histoire','pref_humour','pref_informatique','pref_litterature','pref_sentiment','pref_enfant',
                         'pref_loisirs','pref_manga','pref_nature','pref_policier','pref_religion','pref_sciencefi','pref_sciencehu',
                         'pref_sciencete','pref_scolaire','pref_sport','pref_tourisme','pref_photo'];

    $scope.$watchCollection('biblio_user_data', function(newNames, oldNames) {
        var compteur = 0;
        var lastkey = '';
        for (var key in newNames){
            if ($scope.checkboxes.indexOf(key)!=-1){
                if (newNames[key]==true) {
                    compteur+=1;
                    if (oldNames[key]!=newNames[key]){
                        lastkey=key;
                    }
                };
            }
        };
        if (compteur>5) {
            $scope.biblio_user_data[lastkey]=false;
        };
    });

    $scope.firstload = false;
    $scope.getTimeLine = function(){
        $http({
            url: djangoUrl.reverse("api-timeline-list"),
            method: "GET",
            params: {
                'user_id':$scope.user_id,
                'page':page,
                'page_size': 6,
                'nocache': new Date().getTime()
            }
        }).success(function(out_data){
            for (var i=0;i<out_data.results.length;i++){
                timeline_event=out_data.results[i];
                var trouve = false;
                for (var j=0;j<$scope.timeline.length;j++) {
                    if ($scope.timeline[j].id == timeline_event.id) {
                        trouve = true;
                        break;
                    }
                }
                if (trouve){
                    $scope.timeline[j]=timeline_event;
                }
                else {
                    $scope.timeline.push(timeline_event);
                }
            }
            $scope.firstload = true;
            $scope.loadingmore = false;
            out_data.next===null?$scope.isLastPage=true:$scope.isLastPage=false;
            out_data.previous===null?$scope.isFirstPage=true:$scope.isFirstPage=false;
        }).error(function(){
            swal("Erreur de connexion reseau. Le serveur est injoignable.");
        });
    }

    $scope.getUserDetail = function () {
        var urlapi=djangoUrl.reverse('api-user-detail', {"pk":$scope.user_id});
        $http({
            cache: false,
            url: urlapi,
            method: 'GET',
            params: {
                'nocache': new Date().getTime()
            }}).success(function(out_data){
            $scope.userprofile=out_data;
        }).error(function(){
            swal("Erreur de connexion reseau. Le serveur est injoignable.");
        });
    }

    $scope.follow = function(user, event_id,question){
        in_data  = {"userid":user,"question":question}
        djangoRMI.profiljsonview.follow(in_data)
              .success(function (out_data) {
                if (out_data.success){
                    if (event_id==-1){
                        $scope.css_follow=out_data.css_follow;
                        $scope.txt_follow=out_data.txt_follow;
                    } else {
                        for (var i=0;i<$scope.timeline.length;i++){
                            if ($scope.timeline[i].id==event_id){
                                $scope.timeline[i].css_follow=out_data.css_follow;
                                $scope.timeline[i].txt_follow=out_data.txt_follow;
                            }
                        }
                    }
                    $scope.getUserDetail();
                } else {
                    swal(out_data.message);
                }

              }).error(function(){
                    swal("Erreur de connexion reseau. Le serveur est injoignable.");
              });
    }

    $scope.comment = function(event_id,commentaire){
        in_data  = {"timelineid":event_id,"commentaire":commentaire}
        djangoRMI.profiljsonview.comment(in_data)
            .success(function (out_data) {
                if (out_data.success){
                    for (var i=0;i<$scope.timeline.length;i++){
                        if ($scope.timeline[i].id==out_data.timeline.id){
                            $scope.timeline[i]=out_data.timeline;
                            break;
                        }
                    }

                } else {
                    swal(out_data.message);
                }
            }).error(function(){
                swal("Erreur de connexion reseau. Le serveur est injoignable.");
            });
    }

    $scope.getCommandes = function(userId){
        in_data = {'user_id':userId};
        djangoRMI.profiljsonview.getCommandes(in_data)
            .success(function (out_data) {
                if (out_data.success){
                   $scope.commandes=out_data.commandes;
                   $scope.commandes.sort(function(a, b) {
                        return a.date_creation < b.date_creation;
                   });

                } else {
                    swal(out_data.message);
                }
            }).error(function(){
                swal("Erreur de connexion reseau. Le serveur est injoignable.");
            });;

    }

    $scope.passRecover = function(){
        djangoRMI.profiljsonview.passRecover({})
            .success(function (out_data) {
                swal(out_data.message);
            }).error(function(){
                swal("Erreur de connexion reseau. Le serveur est injoignable.");
            });

    }

    $scope.buttons = [
            { value: 0.0 },
            { value: 0.0 },
        ]

    $scope.simulateProgress = function(buttonIndex, callback) {
            if($scope.buttons[buttonIndex].simulating) return

            $scope.buttons[buttonIndex].simulating = true;
            $scope.buttons[buttonIndex].value = 0.1;

            var seconds=1;

            var interval = $interval(function() {
                if($scope.buttons[buttonIndex].value == 0){
                    $interval.cancel(interval);
                    $scope.buttons[buttonIndex].simulating = false;
                    return;
                }
                if($scope.buttons[buttonIndex].value < 0.9){
                    $scope.buttons[buttonIndex].value += 0.1;
                } else {
                    if($scope.buttons[buttonIndex].value == 1){
                        $interval.cancel(interval);
                        if(typeof callback === 'function') callback();
                        $timeout(function(){
                            $scope.buttons[buttonIndex].simulating = false;
                            $scope.buttons[buttonIndex].value = 0;
                        },2000)
                    }
                }
            }, (seconds / 5) * 1000)
        }

    $scope.onTimeline = function(message){
        if ($scope.user_slug!=message.user.slug){
            var trouve=false;
            for (var i=0;i<message.partage.length;i++){
                if (message.partage[i].slug==$scope.user_slug){
                    trouve=true;
                    break;
                }
            }
            if (!trouve){
                return;
            }
        }
        var trouve=false;
        for (var i=0;i<$scope.timeline.length;i++){
            if ($scope.timeline[i].id==message.id){
                trouve=true;
                $scope.timeline[i]=message;
            }
        }
        if (!trouve)
            $scope.timeline.unshift(message);
    };


    biblioBroadcastWebsocket.connect($scope, 'onTimeline', 'TIMELINE');

    $scope.onLivre = function(message){
        $scope.livre=message;
        for (var i=0; i< $scope.userprofile.mes_livres.length;i++){
            if ($scope.userprofile.mes_livres[i].id==message.id){
               $scope.userprofile.mes_livres[i]=message;
               break;
            }
        }
    };

    biblioBroadcastWebsocket.connect($scope, 'onLivre', 'LIVRE');

}])
.directive('timelineElem', ['$sce', function($sce) {
  return {
    restrict: 'E',
    link: function(scope, element, attrs) {
            switch (scope.event.action){
                case "GETMONEY":
                    scope.contentUrl = 'template/timeline-livre.html';
                    scope.event.content_object.resume_html=$sce.trustAsHtml(scope.event.content_object.resume);
                    break;
                case "FEEDBACK":
                    scope.contentUrl = 'template/timeline-feedback.html';
                    break;
                case "SUCCES-LIVRE":
                    scope.contentUrl = 'template/timeline-succes-livre.html';
                    break;
                case 'SUCCES-SOUSCRIPTION':
                    scope.contentUrl = 'template/timeline-succes-souscription.html';
                    break
                case "ECHEC-LIVRE":
                    scope.contentUrl = 'template/timeline-echec-livre.html';
                    break;
                case "ECHEC-SOUSCRIPTION":
                    scope.contentUrl = 'template/timeline-echec-souscription.html';
                    break;
                case "AMI":
                    scope.contentUrl = 'template/timeline-ami.html';
                    break;
                case "ENN":
                    scope.contentUrl = 'template/timeline-ennemi.html';
                    break;
                case "ACHAT":
                    scope.contentUrl = 'template/timeline-achat.html';
                    break;
                case "PROPOSITION":
                    scope.contentUrl = 'template/timeline-proposition.html';
                    if (scope.event.content_object.type=='BIO' || scope.event.content_object.type=='EXTRA'){
                        if (!scope.event.content_object.hasOwnProperty('thumbnail_260x260')){
                            scope.event.content_object.valeur_html=$sce.trustAsHtml(scope.event.content_object.valeur);
                        }
                    }
                    break;
                case "COMMENTAIRE":
                    scope.contentUrl = 'template/timeline-commentaire.html';
                    break;
                case "VOTE":
                    scope.contentUrl = 'template/timeline-vote.html';
                    if (scope.event.content_object.proposition.type=='BIO' || scope.event.content_object.proposition.type=='EXTRA'){
                        if (!scope.event.content_object.proposition.hasOwnProperty('thumbnail_260x260')){
                            scope.event.content_object.proposition.valeur_html=$sce.trustAsHtml(scope.event.content_object.proposition.valeur);
                        }
                    }
                    break;
                case "SUGGESTION_LIVRE":
                    scope.contentUrl = 'template/timeline-suggestion-livre.html';
                    scope.event.content_object.resume_html=$sce.trustAsHtml(scope.event.content_object.resume);
                    break;
                case "SUGGESTION_USER":
                    scope.contentUrl = 'template/timeline-suggestion-user.html';
                    scope.event.content_object.biographie_html=$sce.trustAsHtml(scope.event.content_object.biographie);
                    scope.follow(scope.event.content_object.id,scope.event.id,'?');
                    break;
            }
       },
    template: '<div ng-include="contentUrl"></div>'

  };
}]);
