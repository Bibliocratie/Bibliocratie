angular.module('bibliocratie_app')
.controller("LivreCtrl", ['$scope', '$http', '$sce', '$timeout', '$interval', '$window', 'djangoForm', 'djangoRMI', 'djangoUrl', 'biblioBroadcastWebsocket','$location',function($scope, $http, $sce, $timeout, $interval, $window, djangoForm, djangoRMI, djangoUrl, biblioBroadcastWebsocket,$location) {
    $scope.livre = {};
    $scope.sondages = {};
    $scope.quantite=1;
    $scope.comment_data = {};
    $scope.comment_form = {};
    $scope.livre_data = {

    };
    $scope.type_extrait_propose=true;

    $scope.propositionsubmiting = {
        'BIO':false,
        'TITRE':false,
        'PRIX' : false
    };

    //Les booleans suivants stockent l'etat du bouton EDIT de chaque champ
    $scope.zone_editable = {
        biographie: false,
        extrait1: false,
        extrait2: false,
        extrait3: false,
        extrait4: false,
        pourquoi: false,
        resume: false,
        titre: false,
        extraits: false,
        prix: false,
        couverture: false,
        phrase_cle: false,
        annonces: false
    }

    $scope.show_extraits_title = function() {
        if ($scope.zone_editable.extrait1 || $scope.zone_editable.extrait2 || $scope.zone_editable.extrait3 || $scope.zone_editable.extrait4){
            return false;
        }
        return true;
    }

    //Les booleans suivants stockent l'etat du bouton EDIT-SONDAGES de chaque champ
    $scope.zone_sondageable = {
        biographie: false,
        extrait1: false,
        extrait2: false,
        extrait3: false,
        extrait4: false,
        pourquoi: false,
        resume: false,
        titre: false,
        extraits: false,
        prix: false,
        couverture: false
    }


    $scope.$watch('zone_editable', function(newValue, oldValue) {
        if (newValue.biographie) {$scope.livre_data.type_biographies="NEVER_OPENED";$scope.zone_sondageable.biographie=false;}
        if (newValue.pourquoi) $scope.zone_sondageable.pourquoi=false;
        if (newValue.titre) {$scope.livre_data.type_titres="NEVER_OPENED";$scope.zone_sondageable.titre=false;}
        if (newValue.prix) {$scope.livre_data.type_prix="NEVER_OPENED";$scope.zone_sondageable.prix=false;}
        if (newValue.extraits) {$scope.livre_data.type_extraits="NEVER_OPENED";$scope.zone_sondageable.extraits=false;}
        if (newValue.couverture) {$scope.livre_data.type_couvertures="NEVER_OPENED";$scope.zone_sondageable.couverture=false;}
        if (newValue.extrait1 || newValue.extrait2 || newValue.extrait3 || newValue.extrait1){
            $('#carousel-extraits').carousel("pause");
        } else {
            $('#carousel-extraits').carousel();
        }
    },true);

    //Appele au chargement de la page avec les donnees serveur contenues dans la form
    $scope.$watch('livre_data.type_titres', function(newValue, oldValue) {
        if (newValue=="NEVER_OPENED") {
            $scope.zone_sondageable.titre=false;
        } else {
            $scope.zone_sondageable.titre=true;
            $scope.zone_editable.titre=false;
        }
    },true);

    $scope.$watch('livre_data.type_extraits', function(newValue, oldValue) {
        if (newValue=="NEVER_OPENED") {
            $scope.zone_sondageable.extraits=false;
        } else {
            $scope.zone_sondageable.extraits=true;
            $scope.zone_editable.extraits=false;
        }
    },true);

    $scope.$watch('livre_data.type_biographies', function(newValue, oldValue) {
        if (newValue=="NEVER_OPENED") {
            $scope.zone_sondageable.biographie=false;
        } else {
            $scope.zone_sondageable.biographie=true;
            $scope.zone_editable.biographie=false;
        }
    },true);

    $scope.$watch('livre_data.type_prix', function(newValue, oldValue) {
        if (newValue=="NEVER_OPENED") {
            $scope.zone_sondageable.prix=false;
        } else {
            $scope.zone_sondageable.prix=true;
            $scope.zone_editable.prix=false;
        }
    },true);

    $scope.$watch('livre_data.type_couvertures', function(newValue, oldValue) {
        if (newValue=="NEVER_OPENED") {
            $scope.zone_sondageable.couverture=false;
        } else {
            $scope.zone_sondageable.couverture=true;
            $scope.zone_editable.couverture=false;
        }
    },true);


    $scope.switchSondages = function(value){
        switch (value) {
            case "type_titres":
                if ($scope.livre_data.type_titres=='NEVER_OPENED') {
                    $scope.livre_data.type_titres='OPEN';

                } else {
                    $scope.livre_data.type_titres='NEVER_OPENED';
                }
                break;
            case "type_extraits":
                if ($scope.livre_data.type_extraits=='NEVER_OPENED') {
                    $scope.livre_data.type_extraits='READ_ONLY';

                } else {
                    $scope.livre_data.type_extraits='NEVER_OPENED';
                }
                break;
            case "type_biographies":
                if ($scope.livre_data.type_biographies=='NEVER_OPENED') {
                    $scope.livre_data.type_biographies='OPEN';

                } else {
                    $scope.livre_data.type_biographies='NEVER_OPENED';
                }
                break;
            case "type_prix":
                if ($scope.livre_data.type_prix=='NEVER_OPENED') {
                    $scope.livre_data.type_prix='OPEN';

                } else {
                    $scope.livre_data.type_prix='NEVER_OPENED';
                }
                break;
            case "type_couvertures":
                if ($scope.livre_data.type_couvertures=='NEVER_OPENED') {
                    $scope.livre_data.type_couvertures='OPEN';

                } else {
                    $scope.livre_data.type_couvertures='NEVER_OPENED';
                }
                break;
        }
    }

    $scope.switchProposition = function(value){
        switch (value) {
            case "type_titres":
                if ($scope.livre_data.type_titres=='OPEN') {
                    $scope.livre_data.type_titres='READ_ONLY';
                } else {
                    $scope.livre_data.type_titres='OPEN';
                }
                break;
            case "type_biographies":
                if ($scope.livre_data.type_biographies=='OPEN') {
                    $scope.livre_data.type_biographies='READ_ONLY';
                } else {
                    $scope.livre_data.type_biographies='OPEN';
                }
                break;
            case "type_prix":
                if ($scope.livre_data.type_prix=='OPEN') {
                    $scope.livre_data.type_prix='READ_ONLY';
                } else {
                    $scope.livre_data.type_prix='OPEN';
                }
                break;
            case "type_couvertures":
                if ($scope.livre_data.type_couvertures=='OPEN') {
                    $scope.livre_data.type_couvertures='READ_ONLY';
                } else {
                    $scope.livre_data.type_couvertures='OPEN';
                }
                break;
        }
    }

    $scope.switchExtrait = function(value){
        switch (value) {
            case "extrait1_type":
                switch ($scope.livre_data.extrait1_type) {
                    case "I":$scope.livre_data.extrait1_type='T';break;
                    case "T":$scope.livre_data.extrait1_type='I';break;
                }
                break;
        }
        switch (value) {
            case "extrait2_type":
                switch ($scope.livre_data.extrait2_type) {
                    case "I":$scope.livre_data.extrait2_type='T';break;
                    case "T":$scope.livre_data.extrait2_type='I';break;
                }
                break;
        }
        switch (value) {
            case "extrait3_type":
                switch ($scope.livre_data.extrait3_type) {
                    case "I":$scope.livre_data.extrait3_type='T';break;
                    case "T":$scope.livre_data.extrait3_type='I';break;
                }
                break;
        }
        switch (value) {
            case "extrait4_type":
                switch ($scope.livre_data.extrait4_type) {
                    case "I":$scope.livre_data.extrait4_type='T';break;
                    case "T":$scope.livre_data.extrait4_type='I';break;
                }
                break;
        }
    }




    $scope.timerRunning = true;
    $scope.$broadcast('timer-start');
    $scope.maincommentaire = {commentAllowed : true};

    Dropzone.autoDiscover = false;

    $scope.dzExtrait1 = {
        config: {
            'options' : {
                parallelUploads: 3,
                maxFileSize: 30,
                paramName:"extrait1_img",
                autoDiscover : false,
                previewsContainer : '#uploaded_extrait1',
                acceptedFiles : '.jpg',
                dictInvalidFileType : "Seuls les fichiers de type .jpg sont acceptés",
                previewTemplate : '<div class="dz-preview dz-file-preview">\
                                      <div class="dz-details ng-hide">\
                                        <div class="dz-filename"><span data-dz-name></span></div>\
                                        <div class="dz-size" data-dz-size></div>\
                                        <img data-dz-thumbnail />\
                                      </div>\
                                      <div class="dz-progress"><span class="dz-upload" data-dz-uploadprogress></span></div>\
                                      <div class="dz-success-mark ng-hide"><span>✔</span></div>\
                                      <div class="dz-error-mark ng-hide"><span>✘</span></div>\
                                      <div class="dz-error-message"><span data-dz-errormessage></span></div>\
                                    </div>'
            },
            'eventHandlers': {
                 'success': function (file, response) {
                    $scope.livreRefresh();
                 }
            }
        }
    };

    $scope.dzExtrait2 = {
        config: {
            'options' : {
                parallelUploads: 3,
                maxFileSize: 30,
                paramName:"extrait2_img",
                autoDiscover : false,
                previewsContainer : '#uploaded_extrait2',
                acceptedFiles : '.jpg',
                dictInvalidFileType : "Seuls les fichiers de type .jpg sont acceptés",
                previewTemplate : '<div class="dz-preview dz-file-preview">\
                                      <div class="dz-details ng-hide">\
                                        <div class="dz-filename"><span data-dz-name></span></div>\
                                        <div class="dz-size" data-dz-size></div>\
                                        <img data-dz-thumbnail />\
                                      </div>\
                                      <div class="dz-progress"><span class="dz-upload" data-dz-uploadprogress></span></div>\
                                      <div class="dz-success-mark ng-hide"><span>✔</span></div>\
                                      <div class="dz-error-mark ng-hide"><span>✘</span></div>\
                                      <div class="dz-error-message"><span data-dz-errormessage></span></div>\
                                    </div>'
            },
            'eventHandlers': {
                 'success': function (file, response) {
                    $scope.livreRefresh();
                 }
            }
        }
    };

    $scope.dzExtrait3 = {
        config: {
            'options' : {
                parallelUploads: 3,
                maxFileSize: 30,
                paramName:"extrait3_img",
                autoDiscover : false,
                previewsContainer : '#uploaded_extrait3',
                acceptedFiles : '.jpg',
                dictInvalidFileType : "Seuls les fichiers de type .jpg sont acceptés",
                previewTemplate : '<div class="dz-preview dz-file-preview">\
                                      <div class="dz-details ng-hide">\
                                        <div class="dz-filename"><span data-dz-name></span></div>\
                                        <div class="dz-size" data-dz-size></div>\
                                        <img data-dz-thumbnail />\
                                      </div>\
                                      <div class="dz-progress"><span class="dz-upload" data-dz-uploadprogress></span></div>\
                                      <div class="dz-success-mark ng-hide"><span>✔</span></div>\
                                      <div class="dz-error-mark ng-hide"><span>✘</span></div>\
                                      <div class="dz-error-message"><span data-dz-errormessage></span></div>\
                                    </div>'
            },
            'eventHandlers': {
                 'success': function (file, response) {
                    $scope.livreRefresh();
                 }
            }
        }
    };

    $scope.dzExtrait4 = {
        config: {
            'options' : {
                parallelUploads: 3,
                maxFileSize: 30,
                paramName:"extrait4_img",
                autoDiscover : false,
                previewsContainer : '#uploaded_extrait4',
                acceptedFiles : '.jpg',
                dictInvalidFileType : "Seuls les fichiers de type .jpg sont acceptés",
                previewTemplate : '<div class="dz-preview dz-file-preview">\
                                      <div class="dz-details ng-hide">\
                                        <div class="dz-filename"><span data-dz-name></span></div>\
                                        <div class="dz-size" data-dz-size></div>\
                                        <img data-dz-thumbnail />\
                                      </div>\
                                      <div class="dz-progress"><span class="dz-upload" data-dz-uploadprogress></span></div>\
                                      <div class="dz-success-mark ng-hide"><span>✔</span></div>\
                                      <div class="dz-error-mark ng-hide"><span>✘</span></div>\
                                      <div class="dz-error-message"><span data-dz-errormessage></span></div>\
                                    </div>'
            },
            'eventHandlers': {
                 'success': function (file, response) {
                    $scope.livreRefresh();
                 }
            }
        }
    };

    $scope.dzExtrait = {
        config:{
            'options':{
                parallelUploads: 3,
                maxFileSize: 30,
                paramName:"valeur",
                autoDiscover : false,
                previewsContainer : '#uploaded_extrait',
                acceptedFiles : '.jpg',
                dictInvalidFileType : "Seuls les fichiers de type .jpg sont acceptés",
                previewTemplate : '<div class="dz-preview dz-file-preview">\
                                      <div class="dz-details ng-hide">\
                                        <div class="dz-filename"><span data-dz-name></span></div>\
                                        <div class="dz-size" data-dz-size></div>\
                                        <img data-dz-thumbnail />\
                                      </div>\
                                      <div class="dz-progress"><span class="dz-upload" data-dz-uploadprogress></span></div>\
                                      <div class="dz-success-mark ng-hide"><span>✔</span></div>\
                                      <div class="dz-error-mark ng-hide"><span>✘</span></div>\
                                      <div class="dz-error-message"><span data-dz-errormessage></span></div>\
                                    </div>'
                },
                'eventHandlers': {
                 'success': function (file, response) {
                    $scope.livreRefresh();
                 }
            }
        }
    };

    $scope.dzImageProposition = {
        config : {
            'options' : {
                parallelUploads: 3,
                maxFileSize: 30,
                paramName:"valeur",
                autoDiscover : false,
                previewsContainer : '#uploaded_proposition',
                acceptedFiles : '.jpg',
                dictInvalidFileType : "Seuls les fichiers de type .jpg sont acceptés",
                maxFilesize : 6 ,//maxFilesize in MB
                dictFileTooBig : "Fichier trop lourd ({{filesize}} Mo). Taille maximum: {{maxFilesize}} Mo.",
                previewTemplate : '<div class="dz-preview dz-file-preview">\
                                      <div class="dz-details ng-hide">\
                                        <div class="dz-filename"><span data-dz-name></span></div>\
                                        <div class="dz-size" data-dz-size></div>\
                                        <img data-dz-thumbnail />\
                                      </div>\
                                      <div class="dz-progress"><span class="dz-upload" data-dz-uploadprogress></span></div>\
                                      <div class="dz-success-mark ng-hide"><span>✔</span></div>\
                                      <div class="dz-error-mark ng-hide"><span>✘</span></div>\
                                      <div class="dz-error-message"><span data-dz-errormessage></span></div>\
                                    </div>'
            },
            'eventHandlers': {
                'success': function (file, response) {
                    $scope.sondagesRefresh();
                }
            }
        }
    };

    $scope.dzImage = {
        config : {
            'options' : {
                parallelUploads: 3,
                maxFileSize: 30,
                paramName:"image_couverture",
                previewsContainer : '#uploaded_image',
                acceptedFiles : '.ai,.indd,.psd,.jpg,.zip',
                dictInvalidFileType : "Seuls les fichiers de type .ai / .indd / .psd / .jpg / .zip sont acceptés",
                previewTemplate : '<div class="dz-preview dz-file-preview">\
                                      <div class="dz-details ng-hide">\
                                        <div class="dz-filename"><span data-dz-name></span></div>\
                                        <div class="dz-size" data-dz-size></div>\
                                        <img data-dz-thumbnail />\
                                      </div>\
                                      <div class="dz-progress"><span class="dz-upload" data-dz-uploadprogress></span></div>\
                                      <div class="dz-success-mark ng-hide"><span>✔</span></div>\
                                      <div class="dz-error-mark ng-hide"><span>✘</span></div>\
                                      <div class="dz-error-message"><span data-dz-errormessage></span></div>\
                                    </div>'
            },
            'eventHandlers': {
                'success': function (file, response) {
                    $scope.livreRefresh();
                }
            }
        }
    };


    $scope.baisseQuantite = function(){
        if ($scope.quantite>1){$scope.quantite-=1;}
    };

    $scope.livreInit = function(livre_id) {
        $scope.livre.id=livre_id;
        $scope.livreRefresh();
    };

    $scope.livreRefresh = function() {
        livre_id = $scope.livre.id;
        if (livre_id){
            var in_data = { livre_id: livre_id };
            djangoRMI.livrejsonview.getLivre(in_data)
               .success(function(out_data) {
                    if (out_data.livre.contenu_explicite && ! out_data.je_suis_lauteur){
                        swal({
                                title: "Contenu sexuellement explicite.",
                                text: "Vous devez être majeur pour continuer.",
                                // type: "warning",
                                customClass: "majeur_livre",
                                imageUrl: "/static/images/exclamation-triangle.png",
                                showCancelButton: true,
                                confirmButtonColor: "#DD6B55",
                                confirmButtonText: "Je suis mineur.",
                                cancelButtonText: "Je suis majeur.",
                                closeOnConfirm: true
                            }, function(){
                                $window.location.href = djangoUrl.reverse("livre_list");
                            });
                    }
                    $scope.livre=out_data.livre;
               })
               .error(function(data, status, headers, config) {
                   swal("Erreur de connexion reseau. Le serveur est injoignable.");
                });
        }
    };

    $scope.setRating = function() {
        var in_data = { livre_id: $scope.livre.id ,rate:$scope.rate};
        djangoRMI.livrejsonview.rate(in_data)
           .success(function(out_data) {
                if (out_data.success==false){
                   swal(out_data.message)
                } else {
                   $scope.livre=out_data.livre;
                }
           })
           .error(function(data, status, headers, config) {
               swal("Erreur de connexion reseau. Le serveur est injoignable.");
           });
    };

    $scope.meRappeler = function() {
        var in_data = { livre_id: $scope.livre.id };
        djangoRMI.livrejsonview.me_rappeler(in_data)
           .success(function(out_data) {
                swal(out_data.message)
           })
           .error(function(data, status, headers, config) {
               swal("Erreur de connexion reseau. Le serveur est injoignable.");
           });
    };

    $scope.demanderNew = function() {
        var in_data = { livre_id: $scope.livre.id };
        djangoRMI.livrejsonview.demander_new(in_data)
           .success(function(out_data) {
                swal(out_data.message);
                if (out_data.success){
                    $scope.livre=out_data.livre;
                }
           })
           .error(function(data, status, headers, config) {
               swal("Erreur de connexion reseau. Le serveur est injoignable.");
           });
    };

    $scope.txt_follow = "Suivre l'auteur"

    $scope.follow_auteur = function(question){
        in_data  = {"auteur":$scope.livre.auteurs,"question":question}
        djangoRMI.livrejsonview.follow_auteur(in_data)
              .success(function (out_data) {
                if (out_data.success){
                    $scope.css_follow=out_data.css_follow;
                    $scope.txt_follow=out_data.txt_follow;
                } else {
                    swal(out_data.message);
                }
              });
    }

    $scope.facebook_share = function(){
        FB.ui(
          {
            method: 'share',
            href: $location.host()+':'+$location.port()+$scope.livre.url,
          },
          // callback
          function(response) {
            if (response && !response.error_code) {
              //alert('Posting completed.');
            } else {
              alert('Error while posting.');
            }
          }
        );
    }

    $scope.sondagesRefresh = function() {
        livre_id = $scope.livre.id;
        if (livre_id){
            var in_data = { livre_id: livre_id };
            djangoRMI.livrejsonview.getsondages(in_data)
               .success(function(out_data) {
                    $scope.sondages=out_data.sondages;
               })
                .error(function(data, status, headers, config) {
                   swal("Erreur de connexion reseau. Le serveur est injoignable.");
                });
        }
    };

    $scope.user_has_chosen_4_extraits = function() {
        if ($scope.sondages.nb_extraits_choisis==4) return true;
        return false;
    }

    $scope.vote = function(proposition_id) {
        var in_data = { proposition_id: proposition_id };
        djangoRMI.livrejsonview.vote(in_data)
           .success(function(out_data) {
               if (out_data.success) {
                   $scope.sondages=out_data.sondages;
                   $scope.livre=out_data.livre;
               } else {
                   swal(out_data.message);
               }

           })
           .error(function(data, status, headers, config) {
                   swal("Erreur de connexion reseau. Le serveur est injoignable.");
                });
    };

    $scope.choisir = function(proposition_id) {
        swal({
            title: "Etes vous sûr ?",
            text: "Toutes les autres propositions seront effacées.",
            // type: "warning",
            imageUrl: "/static/images/warning.png",
            showCancelButton: true,
            confirmButtonColor: "#DD6B55",
            confirmButtonText: "Je confirme mon choix",
            cancelButtonText: "Annuler",
            closeOnConfirm: true }, function(){
                var in_data = { proposition_id: proposition_id };
                djangoRMI.livrejsonview.vote(in_data)
                   .success(function(out_data) {
                       if (out_data.success) {
                           $scope.sondages=out_data.sondages;
                           $scope.livre=out_data.livre;
                       } else {
                           swal(out_data.message);
                       }

                   })
                   .error(function(data, status, headers, config) {
                         swal("Erreur de connexion reseau. Le serveur est injoignable.");
                   });
        });

    };

    $scope.remove_proposition = function(proposition_id) {
        var in_data = { proposition_id: proposition_id };
        djangoRMI.livrejsonview.remove_proposition(in_data)
           .success(function(out_data) {
               $scope.sondages=out_data.sondages;
           })
           .error(function(data, status, headers, config) {
                   swal("Erreur de connexion reseau. Le serveur est injoignable.");
                });
    };

    $scope.$watch('sondages', function(newValue, oldValue) {
        if ($scope.sondages){
            if ($scope.sondages.biographies!=undefined){
                var nb_sondages = $scope.sondages.biographies.length;
                for (var i=0;i<nb_sondages;i++){
                    $scope.sondages.biographies[i].biographie_html = $sce.trustAsHtml($scope.sondages.biographies[i].valeur);
                }
            }
            if ($scope.sondages.extraits!=undefined){
                var nb_sondages = $scope.sondages.extraits.length;
                for (var i=0;i<nb_sondages;i++){
                    $scope.sondages.extraits[i].extrait_html = $sce.trustAsHtml($scope.sondages.extraits[i].valeur);
                }
            }
        }
    },true);

    $scope.options = {
        animate:{
            duration:1000,
            enabled:true
        },
        size: 140,
        barColor:'#1ab667',
        scaleColor:false,
        lineWidth:10,
        lineCap:'butt',
        'track-color' : "#eee"
    };

    $scope.charPropositionSubmit = function(slug,type_proposition) {
        if ($scope.char_data) {
            var data = {'type_proposition' : type_proposition, 'proposition' : $scope.char_data};
            $scope.propositionsubmiting[type_proposition] = true;
            $http.post(djangoUrl.reverse('livre_detail', {slug:slug}), data).success(function(out_data) {
                if (!djangoForm.setErrors($scope.char_form, out_data.errors))
                {
                    $scope.sondages=out_data.sondages;
                    $scope.char_data = "";
                }
                $scope.propositionsubmiting[type_proposition] = false;
            })
            .error(function(data, status, headers, config) {
                   swal("Erreur de connexion reseau. Le serveur est injoignable.");
                   $scope.propositionsubmiting[type_proposition] = false;
                });
        }
        return false;
    };

    $scope.textPropositionSubmit = function(slug,type_proposition) {
        if ($scope.text_data) {
            var data = {'type_proposition' : type_proposition, 'proposition' : $scope.text_data};
            $scope.propositionsubmiting[type_proposition] = true;
            $http.post(djangoUrl.reverse('livre_detail', {slug:slug}), data).success(function(out_data) {
                if (!djangoForm.setErrors($scope.text_form, out_data.errors))
                {
                    $scope.sondages=out_data.sondages;
                    $scope.text_data="";
                }
                $scope.propositionsubmiting[type_proposition] = false;
            })
            .error(function(data, status, headers, config) {
                   swal("Erreur de connexion reseau. Le serveur est injoignable.");
                    $scope.propositionsubmiting[type_proposition] = false;
                });
        }
        return false;
    };
    $scope.numberPropositionSubmit = function(slug,type_proposition) {
        if ($scope.number_data) {
            var data = {'type_proposition' : type_proposition, 'proposition' : $scope.number_data};
            $scope.propositionsubmiting[type_proposition] = true;
            $http.post(djangoUrl.reverse('livre_detail', {slug:slug}), data).success(function(out_data) {
                if (!djangoForm.setErrors($scope.number_form, out_data.errors))
                {
                    $scope.sondages=out_data.sondages;
                    $scope.number_data = "";
                    $scope.number_form.$setPristine();
                }
                $scope.propositionsubmiting[type_proposition] = false;
            })
            .error(function(data, status, headers, config) {
                   swal("Erreur de connexion reseau. Le serveur est injoignable.");
                   $scope.propositionsubmiting[type_proposition] = false;
                });
        }
        return false;
    };

    $scope.commentaireSubmit = function(slug,reply_to) {
        if ($scope.comment_data) {
            var data = {'commentaire' : $scope.comment_data, 'reply_to' : reply_to};
            $http.post(djangoUrl.reverse('livre_detail', {slug:slug}), data).success(function(out_data) {
                if (!djangoForm.setErrors($scope.comment_form, out_data.errors))
                {
                    $scope.comment_data={};
                    $scope.comment_form.$setUntouched();
                    $scope.comment_form.$setPristine();
                    $scope.livre=out_data.livre;
                    $scope.commentToggle($scope.maincommentaire);
                }
            })
            .error(function(data, status, headers, config) {
                   swal("Erreur de connexion reseau. Le serveur est injoignable.");
                });
        }
        return false;
    };

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

    $scope.livreSubmit = function(slug,button,validation) {
        if ($scope.livre_data) {
            var data = {'livre' : $scope.livre_data,
                        'validation':validation};
            $http.post(djangoUrl.reverse('livre_detail', {slug:slug}), data).success(function(out_data) {
                if (!djangoForm.setErrors($scope.livre_form, out_data.errors))
                {
                    var successurl = out_data.success_url;
                    if (successurl){
                        $window.location.href = successurl;
                    }
                    $scope.livre=out_data.livre;
                }
                $scope.buttons[button].value=1;
            })
            .error(function(data, status, headers, config) {
                   swal("Erreur de connexion reseau. Le serveur est injoignable.");
                   $scope.buttons[button].value=0;
                });
        }
        return false;
    };

    $scope.$watch('livre_data.extrait1_txt', function(newValue, oldValue) {
        $scope.livre_data.extrait1_html = $sce.trustAsHtml($scope.livre_data.extrait1_txt);
    },true);

    $scope.$watch('livre_data.extrait2_txt', function(newValue, oldValue) {
        $scope.livre_data.extrait2_html = $sce.trustAsHtml($scope.livre_data.extrait2_txt);
    },true);

    $scope.$watch('livre_data.extrait3_txt', function(newValue, oldValue) {
        $scope.livre_data.extrait3_html = $sce.trustAsHtml($scope.livre_data.extrait3_txt);
    },true);

    $scope.$watch('livre_data.extrait4_txt', function(newValue, oldValue) {
        $scope.livre_data.extrait4_html = $sce.trustAsHtml($scope.livre_data.extrait4_txt);
    },true);

    $scope.$watch('livre_data.pourquoi_ce_livre', function(newValue, oldValue) {
        $scope.livre_data.pourquoi_html = $sce.trustAsHtml($scope.livre_data.pourquoi_ce_livre);
    },true);

    $scope.$watch('livre_data.biographie', function(newValue, oldValue) {
        $scope.livre_data.biographie_html = $sce.trustAsHtml($scope.livre_data.biographie);
    },true);

    $scope.$watch('livre_data.resume', function(newValue, oldValue) {
        $scope.livre_data.resume_html = $sce.trustAsHtml($scope.livre_data.resume);
    },true);

    $scope.$watch('livre_data.instructions', function(newValue, oldValue) {
        $scope.livre_data.instructions_html = $sce.trustAsHtml($scope.livre_data.instructions);
    },true);

    $scope.$watch('livre_data.phrase_cle', function(newValue, oldValue) {
        $scope.livre_data.phrase_cle_html = $sce.trustAsHtml($scope.livre_data.phrase_cle);
    },true);

    $scope.$watch('livre_data.annonces', function(newValue, oldValue) {
        $scope.livre_data.annonces_html = $sce.trustAsHtml($scope.livre_data.annonces);
    },true);


    var calculPrixVenteEnCours=false;
    var promisePrixVente=null;
    $scope.$watch('livre_data.prix_vente', function(newValue, oldValue) {
        if (calculPrixVenteEnCours){
            $timeout.cancel(promisePrixVente);
        }
        promisePrixVente = $timeout(function(){
            if (newValue<$scope.livre_data.cout_production){
                coutMinimum=$scope.livre_data.cout_production;
                coutMinimum=Math.floor(coutMinimum * 10) / 10;
                $scope.livre_data.prix_vente=coutMinimum;
            }
            calculPrixVenteEnCours = false;
        }, 1000, true);
        calculPrixVenteEnCours = true;
    },true);

    var calculPrixPropEnCours=false;
    var promisePrixProp=null;
    $scope.$watch('number_data.valeur', function(newValue, oldValue) {
        if (calculPrixPropEnCours){
            $timeout.cancel(promisePrixProp);
        }
        promisePrixProp = $timeout(function(){
            if (newValue<$scope.livre_data.cout_production){
                coutMinimum=$scope.livre_data.cout_production;
                coutMinimum=Math.floor(coutMinimum * 10) / 10;
                $scope.number_data.valeur=coutMinimum;
            }
            calculPrixPropEnCours = false;
        }, 1000, true);
        calculPrixPropEnCours = true;
    },true);

    $scope.loadTags = function(query) {
        return $http({
            url: djangoUrl.reverse("api-tags-list"),
            method: "GET",
            params: {query: query}
         })
      };

    $scope.commentToggle = function(commentaire){
        function disallowComments(element, index, array) {
            element.commentAllowed=false;
            element.reponses.forEach(disallowComments);
        }
        if ($scope.livre.commentaires){
            $scope.livre.commentaires.forEach(disallowComments);
        }
        commentaire.commentAllowed=!commentaire.commentAllowed;
        if (commentaire.commentAllowed && commentaire!=$scope.maincommentaire){
            $scope.maincommentaire.commentAllowed = false;
        } else {
            $scope.maincommentaire.commentAllowed = true;
        }
        $scope.comment_data={};
        $scope.comment_form.$setUntouched();
        $scope.comment_form.$setPristine();
    }


    $scope.onLivre = function(message){
        if (message.id==$scope.livre.id){
            $scope.livre=message;
            $scope.sondagesRefresh();
        }
    };

    biblioBroadcastWebsocket.connect($scope, 'onLivre', 'LIVRE');

}]);


angular.module('bibliocratie_app').
    controller('LivresCtrl', ['$scope', '$rootScope', '$http', '$timeout', '$sce','djangoRMI', 'djangoUrl', 'biblioBroadcastWebsocket',function($scope, $rootScope, $http, $timeout, $sce, djangoRMI, djangoUrl, biblioBroadcastWebsocket) {
    $scope.livres = null;

    $scope.categories = [];
    $scope.myCategorie = {value: "Categorie", key: ""};

    $scope.genres = [];
    $scope.myGenre = {value: "Genre", key: ""};

    $scope.phases = [];
    $scope.myPhase = {value: "Phase", key: "GETMONEY"};

    $scope.etats = [];
    $scope.myEtat = {value: "Etat", key: ""};
    var page = 1;
    var page_size = 20;
    $scope.isFirstPage=true;
    $scope.isLastPage=true;

    $scope.sondage__type_couvertures=false;
    $scope.sondage__type_prix=false;
    $scope.sondage__type_biographies=false;
    $scope.sondage__type_extraits=false;
    $scope.sondage__type_titres=false;

    $scope.livres_a_la_une={};

    $scope.nb_loaded = 0;

    $scope.loadingmore = true;

    $scope.onImgLoad = function (event) {
        $scope.packery();
    }

    $scope.setPhase = function(phase){
        $scope.phase=phase;
        $scope.myPhase = {value: "Phase", key: phase};
        selecteursRefresh();
        $scope.refreshLivresUne();
        $scope.mySelecteurChanged("");
    }


    $scope.refreshLivresUne = function(){
        $http({
            url: djangoUrl.reverse("api-souscriptions-list"),
            method: "GET",
            params: {
                'phase': $scope.phase,
                'a_la_une':'True',
                'sort_by':"date_souscription:desc",
                'nocache': new Date().getTime()
            }
         }).success(function(data){
            // With the data succesfully returned, call our callback
            $scope.livres_a_la_une=data;
            refreshCarrouselUne();
        }).error(function(data, status, headers, config) {
            swal("Erreur de connexion reseau. Le serveur est injoignable.");
        });
    }

    Object.equals = function( x, y ) {
          if ( x === y ) return true;
            // if both x and y are null or undefined and exactly the same

          if ( ! ( x instanceof Object ) || ! ( y instanceof Object ) ) return false;
            // if they are not strictly equal, they both need to be Objects

          if ( x.constructor !== y.constructor ) return false;
            // they must have the exact same prototype chain, the closest we can do is
            // test there constructor.

          for ( var p in x ) {
            if (p=="timestamp") continue;
              //on ne compare pas les timestamp
            if (p=="$$hashKey") continue;
              //ni la tambouille angularjs

            if ( ! x.hasOwnProperty( p ) ) continue;
              // other properties were tested using x.constructor === y.constructor

            if ( ! y.hasOwnProperty( p ) ) return false;
              // allows to compare x[ p ] and y[ p ] when set to undefined

            if ( x[ p ] === y[ p ] ) continue;
              // if they have the same strict value or identity then they are equal

            if ( typeof( x[ p ] ) !== "object" ) return false;
              // Numbers, Strings, Functions, Booleans must be strictly equal

            if ( ! Object.equals( x[ p ],  y[ p ] ) ) return false;
              // Objects and Arrays must be tested recursively
          }

          for ( p in y ) {
            if ( y.hasOwnProperty( p ) && ! x.hasOwnProperty( p ) ) return false;
              // allows x[ p ] to be set to undefined
          }
          return true;
        }

    $scope.mySelecteurChanged = function(newValue, type){
        switch(type) {
            case 'CATEGORY':
                $scope.myCategorie=newValue;
                page=1;
                break;
            case 'ETAT':
                $scope.myEtat=newValue;
                page=1;
                break;
            case 'PHASE':
                $scope.myPhase=newValue;
                page=1;
                break;
            case 'GENRE':
                $scope.myGenre=newValue;
                page=1;
                break;
            case 'COUVERTURE':
                $scope.sondage__type_couvertures=!$scope.sondage__type_couvertures;
                page=1;
                break;
            case 'PRIX':
                $scope.sondage__type_prix=!$scope.sondage__type_prix;
                page=1;
                break;
            case 'BIOGRAPHIE':
                $scope.sondage__type_biographies=!$scope.sondage__type_biographies;
                page=1;
                break;
            case 'EXTRAIT':
                $scope.sondage__type_extraits=!$scope.sondage__type_extraits;
                page=1;
                break;
            case 'TITRE':
                $scope.sondage__type_titres=!$scope.sondage__type_titres;
                page=1;
                break;
        }

        var params={
            'phase':$scope.myPhase.key,
            'category':$scope.myCategorie.key,
            'genre':$scope.myGenre.key,
            'etat':$scope.myEtat.key,
            'page_size':page_size,
            'page':page,
            'nocache': new Date().getTime()
        };

        switch ($scope.myPhase) {
            case 'GETMONEY':
            case 'SUCCESS':
            case 'ECHEC':
                params['sort_by']="date_souscription:desc";
                params['a_la_une']="False";
                break;
            case 'FEEDBACK':
                params['sort_by']="date_feedback:desc";
                break;
        }
        if ($scope.sondage__type_couvertures===true){params['type_couvertures']="OPEN"};
        if ($scope.sondage__type_prix===true){params['type_prix']="OPEN"};
        if ($scope.sondage__type_biographies===true){params['type_biographies']="OPEN"};
        if ($scope.sondage__type_extraits===true){params['type_extraits']="OPEN"};
        if ($scope.sondage__type_titres===true){params['type_titres']="OPEN"};
        $http({
            url: djangoUrl.reverse("api-souscriptions-list"),
            method: "GET",
            params: params
        }).success(function(data){
            if (!Object.equals($scope.livres,data)){
                if (page==1){
                    $scope.livres=data;
                } else {
                    $scope.livres.results = $scope.livres.results.concat(data.results);
                }
                data.next===null?$scope.isLastPage=true:$scope.isLastPage=false;
                data.previous===null?$scope.isFirstPage=true:$scope.isFirstPage=false;
            }
            $scope.loadingmore = false;
        }).error(function(data, status, headers, config) {
                   swal("Erreur de connexion reseau. Le serveur est injoignable.");
                });
    };

    $rootScope.$on('packeryInstantiated', function (event, args) {
        pckry = args;
    });

    $scope.packery = function(){
        if (typeof pckry != 'undefined'){
            pckry.layout();
        }
    };

    var selecteursRefresh = function() {
        djangoRMI.livrejsonview.getSelecteurs()
           .success(function(out_data) {
                $scope.categories=out_data.categories;
                $scope.genres=out_data.genres;
                $scope.etats=out_data.etats;
                $scope.phases=out_data.phases;
            });
    };

    $scope.onLivre = function(message){
        for (var i=0;i<$scope.livres.results.length;i++){
            if ($scope.livres.results[i].id==message.id){
                $scope.livres.results[i]=message;
            }
        }
    };

    $scope.nextPage = function(){
        if (!$scope.isLastPage){
            page+=1;
            $scope.loadingmore = true;
            $scope.mySelecteurChanged("");
        }
    };

    $scope.$watch('livres', function(newValue, oldValue) {
        if ($scope.livres){
            var nb_livres = $scope.livres.results.length;
            for (var i=0;i<nb_livres;i++){
                $scope.livres.results[i].resume_html = $sce.trustAsHtml($scope.livres.results[i].resume);
            }
        }
    },true);

    stopCaroussel=false;
    $scope.mouseOver = function(){
        stopCaroussel=true;
    }

    $scope.mouseOut = function(){
        stopCaroussel=false;
    }

    $scope.carroussel_livre_une = [];

    const PackeryCarousselSize = 4;

    refreshCarrouselUne = function(){
        if (!stopCaroussel) {
            nbUne = PackeryCarousselSize;
            if ($scope.livres_a_la_une.results.length < PackeryCarousselSize) {
                nbUne = $scope.livres_a_la_une.results.length;
            }
            new_carrousel = false;
            if ($scope.carroussel_livre_une.length == 0) {
                new_carrousel = true;
            };
            if (!new_carrousel && $scope.livres_a_la_une.results.length<=nbUne){
                return;
            }
            for (var i = 0; i < nbUne; i++) {
                do {
                    ok = true;
                    random_book = $scope.livres_a_la_une.results[Math.floor(Math.random() * $scope.livres_a_la_une.results.length)];
                    for (var j = 0; j < $scope.carroussel_livre_une.length; j++) {
                        if (random_book.id == $scope.carroussel_livre_une[j].id) {
                            ok = false;
                            break;
                        }
                    }
                } while (ok == false);
                if (new_carrousel) {
                    $scope.carroussel_livre_une.push(random_book);
                } else {
                    random_location = Math.floor(Math.random() * $scope.carroussel_livre_une.length);
                    $scope.carroussel_livre_une[random_location] = random_book;
                }
            }
        }
        $timeout(function(){
                refreshCarrouselUne();
            },6000)
    }

    $scope.$watch('livres_a_la_une', function(newValue, oldValue) {
        if ($scope.livres_a_la_une.hasOwnProperty('results')){
            var nb_livres = $scope.livres_a_la_une.results.length;
            for (var i=0;i<nb_livres;i++){
                $scope.livres_a_la_une.results[i].resume_html = $sce.trustAsHtml($scope.livres_a_la_une.results[i].resume);
            }
        }
    },true);

    biblioBroadcastWebsocket.connect($scope, 'onLivre', 'LIVRE');
}]);

angular.module('bibliocratie_app')
    .directive('sbLoad', ['$parse', function($parse) {
    return {
        restrict: 'A',
        link: function(scope, elem, attrs) {
            var fn = $parse(attrs.sbLoad);
            elem.on('load', function (event) {
                scope.$apply(function() {
                    fn(scope, { $event: event });
                });
            });
        }
    };
}]);
