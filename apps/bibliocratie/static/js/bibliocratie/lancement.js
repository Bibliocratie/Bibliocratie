angular.module('bibliocratie_app').controller('LancementCtrl', ['$scope', '$rootScope','$http', '$window', '$timeout', '$interval', '$compile', 'djangoForm', 'djangoUrl','djangoRMI',function($scope, $rootScope, $http, $window, $timeout, $interval, $compile, djangoForm, djangoUrl,djangoRMI) {
    $scope.lancement_debut_data = {};
    $scope.lancement_interne_data = {};
    $scope.lancement_fichier_data = {};
    $scope.lancement_couverture_data = {};
    $scope.lancement_prixdate_data = {};
    $scope.lancement_fin_form = {};
    $scope.lancement_fin_data = {
        'certif_modification' : false,
        'certif_proprio' : false,
        'certif_promo' : false,
        'certif_exclu' : false,
        'nb_pages' : 1,
        'nb_exemplaires_cible' : 50
    };

    $scope.lancement_interne_data = {
        nb_carac : 0,
    }


    $scope.calendrier = {
        dates_debut : [[],[]],
        dates_fin : [[]],
    }

    $scope.buttons = [
            { value: 0.0 },
            { value: 0.0 },
        ]

    $scope.message="";

    $scope.format_display = "";

    $scope.nb_pages=0;


    $scope.$watchGroup(['lancement_interne_data.format','lancement_interne_data.nb_carac','lancement_interne_data.nb_chapitres'], function(newValues, oldValues, $scope) {
        switch (newValues[0]) {
            case 'FM1':
                $scope.format_display = '110 x 155 mm';
                $scope.nb_pages = Math.ceil(newValues[2]*0.9+newValues[1]/860);
                $scope.nb_pages = $scope.nb_pages + $scope.nb_pages%2;
                break;
            case 'FM2':
                $scope.format_display = '115 x 180 mm';
                $scope.nb_pages = Math.ceil(newValues[2]*1.2+newValues[1]/1070);
                $scope.nb_pages = $scope.nb_pages + $scope.nb_pages%2;
                break;
            case 'FM3':
                $scope.format_display = '140 x 210 mm';
                $scope.nb_pages = Math.ceil(newValues[2]*0.7+newValues[1]/1600);
                $scope.nb_pages = $scope.nb_pages + $scope.nb_pages%2;
                break;
            case 'FM4':
                $scope.format_display = '210 x 210 mm';
                break;
            case 'FM5':
                $scope.format_display = '210 x 148,5 mm';
                break;
            case 'FM6':
                $scope.format_display = '180 x 240 mm';
                break;
        }
    },true);



    var date_debut = null;

    /* alert on eventClick */
    $scope.alertOnEventDebutClick = function( date, jsEvent, view){
        if (date.className[0]=="date-souscription") return;
        var count = date.source.events.length;
        for(var i = 0; i < count; i++) {
            date.source.events[i].className=[];
            date.source.events[i].tooltip=date.source.events[i].tooltipNotSelected;
            date.source.events[i].title=date.source.events[i].id;
        }
        date.className= ['date-choisie'];
        date.tooltip=date.tooltipSelected; // contenu tooltip
        date.title=date.titre; // titre evenement : nvlle variable titre dans views.py
        $scope.getDatesFin(date.start.toISOString());
        $scope.lancement_prixdate_data.date_souscription=date.start.toISOString();
        $scope.lancement_prixdate_data.date_feedback=date.start.toISOString();

        date_debut = date.start.toISOString();

        $scope.lancement_prixdate_data.nb_jours_campagne=null;
        $('#CalendarDebut').fullCalendar('refetchEvents');
    };

    /* alert on eventClick */
    $scope.alertOnEventFinClick = function( date, jsEvent, view){
        var count = date.source.events.length;
        for(var i = 0; i < count; i++) {
            date.source.events[i].className=[];
            date.source.events[i].tooltip=date.source.events[i].tooltipNotSelected;
            date.source.events[i].title=date.source.events[i].id;
        }
        date.className= ['date-choisie'];
        date.tooltip=date.tooltipSelected; // contenu tooltip
        date.title=date.titre; // titre evenement : nvlle variable titre dans views.py

        $scope.lancement_prixdate_data.nb_jours_campagne=moment(date.start.toISOString()).diff(date_debut,'days')+1;

        if ($scope.lancement_prixdate_data.pre_souscription){
            $scope.lancement_prixdate_data.nb_jours_campagne=$scope.lancement_prixdate_data.nb_jours_campagne-14;
        }

        $('#CalendarFin').fullCalendar('refetchEvents');
    };

    /* Render Tooltip */
    $scope.eventRender = function( event, element, view ) {
      $timeout(function(){
        $(element).attr('tooltip', event.tooltip);
        $(element).attr('tooltip-placement', event.tooltipPlacement);
        $compile(element)($scope);
      });
    };

    $scope.CalandarDebutConfig = {
        height: 460,
        editable: false,
        header:{
          left: '',
          center: 'title today prev,next',
          right: ''
        },
        firstDay:1,
        allDayDefault:true,
        lang:"fr",
        timezone:false,
        eventClick: $scope.alertOnEventDebutClick,
        eventRender: $scope.eventRender
    };

    $scope.CalandarFinConfig = {
        height: 450,
        editable: false,
        header:{
          left: '',
          center: 'title today prev,next',
          right: ''
        },
        firstDay:1,
        allDayDefault:true,
        lang:"fr",
        timezone:false,
        eventClick: $scope.alertOnEventFinClick,
        eventRender: $scope.eventRender
    };


    $scope.getDatesFin = function(date_debut){
        indata = {'date_debut':date_debut,
                  'livre_id': $scope.livre_id }
            djangoRMI.lancementjsonview.GetDatesFin(indata)
                .success(function (out_data) {
                    var count = out_data["dates_fin_souscription"].length;

                    $scope.calendrier.dates_fin[0]=[];

                    for(var i = 0; i < count; i++) {
                        var event = out_data["dates_fin_souscription"][i];
                        event.start = moment(event.start);
                        event._start = moment(event.start);
                        $scope.calendrier.dates_fin[0].push(event);
                    }

                    var event_souscription = out_data["date_souscription"];
                    event_souscription.start = moment(event_souscription.start);
                    if (out_data["pre_souscription"]){
                        event_souscription.className= ['date-souscription'];
                        event_souscription.tooltip=event_souscription.tooltipSelected; // contenu tooltip
                        event_souscription.title=event_souscription.titre; // titre evenement : nvlle variable titre dans views.py
                        $scope.calendrier.dates_debut[1]=[];
                        event_souscription._start = moment(event_souscription.start);
                        $scope.calendrier.dates_debut[1].push(event_souscription);
                    }
                    date_fin = out_data["date_fin"];
                    if (date_fin){
                        $scope.lancement_fin_data.nb_jours_campagne=moment(date_fin).diff(event_souscription.start,'days');
                        $('#CalendarFin').fullCalendar( 'gotoDate', moment(date_fin) );
                    } else {
                        $('#CalendarFin').fullCalendar( 'gotoDate', event.start );
                    }
                })
                .error(function(data, status, headers, config) {
                   swal("Erreur de connexion reseau. Le serveur est injoignable.");
                });
    }

    var init_DateDebut=true;
    $scope.getDatesDebut = function(){
        indata = {'livre_id': $scope.livre_id }
            djangoRMI.lancementjsonview.GetDatesDebut(indata)
                .success(function (out_data) {
                    var count = out_data["dates_possibles"].length;

                    $scope.calendrier.dates_debut[0]=[];
                    if (out_data["pre_souscription"]==true && $scope.lancement_prixdate_data.date_feedback){
                        var date_debut_init = $scope.lancement_prixdate_data.date_feedback.substr(0, 10);
                    } else {
                        if ($scope.lancement_prixdate_data.date_souscription) {
                            var date_debut_init = $scope.lancement_prixdate_data.date_souscription.substr(0, 10);
                        }
                    }

                    //initialisation du calendrier de debut de période
                    date_debut = date_debut_init;
                    for(var i = 0; i < count; i++) {
                        var event = out_data["dates_possibles"][i];
                        if (init_DateDebut && (event.start== date_debut_init) ){
                            event.className= ['date-choisie'];
                            event.tooltip=event.tooltipSelected; // contenu tooltip
                            event.title=event.titre; // titre evenement : nvlle variable titre dans views.py
                        }
                        event._start = moment(event.start);
                        $scope.calendrier.dates_debut[0].push(event);
                    }
                    $('#CalendarDebut').fullCalendar( 'gotoDate', moment(date_debut_init) );

                    //Initialisation de la date de soucription
                    var event_souscription = out_data["event_souscription"];
                    if (init_DateDebut && event_souscription){
                        event_souscription.start = moment(event_souscription.start);
                        event_souscription.className= ['date-souscription'];
                        event_souscription.tooltip=event_souscription.tooltipSelected; // contenu tooltip
                        event_souscription.title=event_souscription.titre; // titre evenement : nvlle variable titre dans views.py
                        $scope.calendrier.dates_debut[1]=[];
                        event_souscription._start = moment(event_souscription.start);
                        $scope.calendrier.dates_debut[1].push(event_souscription);
                    }

                    //initialisation du calendrier de fin de période
                    if (init_DateDebut && $scope.lancement_prixdate_data.date_souscription && $scope.lancement_prixdate_data.nb_jours_campagne){

                        if ($scope.lancement_fin_data.pre_souscription ){
                            date_fin =moment($scope.lancement_prixdate_data.date_feedback);
                            date_fin.add($scope.lancement_prixdate_data.nb_jours_campagne+14,"days")
                        } else {
                            date_fin = moment($scope.lancement_prixdate_data.date_souscription);
                            date_fin.add($scope.lancement_prixdate_data.nb_jours_campagne,"days");
                        }

                        var event = {'start':date_fin,'title':'1'};
                        event.className= ['date-choisie'];
                        event.tooltip="Fin de la souscription";
                        event.title="Fin souscript.";
                        $scope.calendrier.dates_fin[0]=[];
                        event._start = moment(event.start);
                        $scope.calendrier.dates_fin[0].push(event);
                        init_DateDebut=false;
                        $('#CalendarFin').fullCalendar( 'gotoDate', event.start );
                    }
                })
                .error(function(data, status, headers, config) {
                   swal("Erreur de connexion reseau. Le serveur est injoignable.");
                });
    }

    $scope.slider_config = {
        index_nb_exemplaires_cible : 0,
        ceiling:0
    };

    hasExtension = function (fileName, exts) {
        return (new RegExp('(' + exts.join('|').replace(/\./g, '\\.') + ')$')).test(fileName);
    }

    Dropzone.autoDiscover = false;

    $scope.dzFichierAuteur = {
        config: {
            'options': {
                parallelUploads: 3,
                maxFiles: 1,
                maxFileSize: 30,
                paramName: "fichier_auteur",
                autoDiscover: false,
                previewsContainer: '#uploaded_file',
                acceptedFiles: '.odt,.doc,.docx,.zip',
                dictInvalidFileType: "Seuls les fichiers de type .odt / .doc / .docx / .zip sont acceptés",
                previewTemplate: '<div class="dz-preview dz-file-preview">\
                                  <div class="dz-details ng-hide">\
                                    <div class="dz-filename"><span data-dz-name></span></div>\
                                    <div class="dz-size" data-dz-size></div>\
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
                     $scope.refreshData();
                 },
                 'sending': function (file, formData, xhr) {
                 },
                 'success': function (file, response) {
                     $scope.refreshData();
                 }
            },
        }
    }

    $scope.dzFichierAuteurMaquette = {
        config : {
            'options': {
                parallelUploads: 3,
                maxFileSize: 30,
                paramName: "fichier_auteur",
                previewsContainer: '#uploaded_file2',
                acceptedFiles: '.zip',
                dictInvalidFileType: "Seuls les fichiers de type .zip sont acceptés",
                previewTemplate: '<div class="dz-preview dz-file-preview">\
                                      <div class="dz-details ng-hide">\
                                        <div class="dz-filename"><span data-dz-name></span></div>\
                                        <div class="dz-size" data-dz-size></div>\
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
                     $scope.refreshData();
                 }
            },

        },

        init : function() {
                   this.on("success", function(file, responseText) {
                        $scope.refreshData();
                   });
                   this.on("drop", function(file,xhr,formdata){
                        $("#uploaded_file2" ).contents().remove();
                   })
                }
    };

    $scope.dzImageCouverture = {
        config : {
            'options': {
                parallelUploads: 3,
                maxFileSize: 30,
                paramName: "image_couverture",
                previewsContainer: '#uploaded_image',
                acceptedFiles: '.jpg',
                dictInvalidFileType: "Seuls les fichiers de type .jpg sont acceptés",
                previewTemplate: '<div class="dz-preview dz-file-preview">\
                                      <div class="dz-details ng-hide">\
                                        <div class="dz-filename"><span data-dz-name></span></div>\
                                        <div class="dz-size" data-dz-size></div>\
                                        <img data-dz-thumbnail />\
                                      </div>\
                                      <div class="dz-progress"><span class="dz-upload" data-dz-uploadprogress></span></div>\
                                      <div class="dz-success-mark ng-hide"><span>✔</span></div>\
                                      <div class="dz-error-mark ng-hide"><span>✘</span></div>\
                                      <div class="dz-error-message"><span data-dz-errormessage></span></div>\
                                    </div>',
            },
            'eventHandlers': {
                'error': function (file, response, xhr) {
                },
                'complete': function () {
                },
                'sending': function (file, formData, xhr) {
                },
                'success': function (file, response) {
                    $scope.refreshData();
                }
            }
        }
    };

    $scope.dzMaqueteCouverture = {
        config : {
            'options': {
                parallelUploads: 3,
                maxFileSize: 30,
                paramName: "maquete_couverture",
                previewsContainer: '#uploaded_maquette',
                acceptedFiles: '.ai,.psd,.zip',
                dictInvalidFileType: "Seuls les fichiers de type .ai / .psd / .zip sont acceptés",
                previewTemplate: '<div class="dz-preview dz-file-preview">\
                                      <div class="dz-details ng-hide">\
                                        <div class="dz-filename"><span data-dz-name></span></div>\
                                        <div class="dz-size" data-dz-size></div>\
                                        <img data-dz-thumbnail />\
                                      </div>\
                                      <div class="dz-progress"><span class="dz-upload" data-dz-uploadprogress></span></div>\
                                      <div class="dz-success-mark ng-hide"><span>✔</span></div>\
                                      <div class="dz-error-mark ng-hide"><span>✘</span></div>\
                                      <div class="dz-error-message"><span data-dz-errormessage></span></div>\
                                    </div>',
            },
            'eventHandlers': {
                'error': function (file, response, xhr) {
                },
                'complete': function () {
                },
                'sending': function (file, formData, xhr) {
                },
                'success': function (file, response) {
                    $scope.refreshData();
                }
            }
        }
    };

    $scope.dzAvatar = {
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
                'addedfile': function (file) {
                   $('#current_avatar').empty();
                }
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

    $scope.translate = function(value) {
        var newValue = 50;
        if ($scope.slider_config.palliers_nb_exemplaires){
            newValue=$scope.slider_config.palliers_nb_exemplaires[value];
        }
        return newValue;
    };

    $scope.$watch('slider_config.index_nb_exemplaires_cible', function(newValue, oldValue) {
        $timeout(function(){
            if ($scope.slider_config.palliers_nb_exemplaires){
                $scope.lancement_prixdate_data.nb_exemplaires_cible=$scope.slider_config.palliers_nb_exemplaires[newValue];
            }
        }, 0, true);
    },true);

    //$scope.loadTags = function(query) {
    //    console.log("lancement.js loadTags")
    //    return $http.get(djangoUrl.reverse("api-tags-list", {})+'?query=' + query);
    //  };

    $scope.presouscription_toggle = function(bool){
        $scope.lancement_debut_data.pre_souscription = bool;
    }

    $scope.speak = function(){
        var utterance = new SpeechSynthesisUtterance("C'est parti mon kiki");
        var voices = window.speechSynthesis.getVoices();
        utterance.voice = voices.filter(function(voice) { return voice.lang == 'fr-FR'; })[0];
        window.speechSynthesis.speak(utterance);
    }

    $scope.selancer = function(){
        if ($scope.lancement_data) {
            $http.post(djangoUrl.reverse('lancement'), $scope.lancement_data).success(function(out_data) {
                if (!djangoForm.setErrors($scope.lancement_form, out_data.errors))
                {
                    $scope.speak();
                    // on successful post, redirect onto success page
                    var successurl = out_data.success_url;
                    $window.location.href = successurl;
                }
            }).error(function() {
                swal("Erreur de connexion reseau. Le serveur est injoignable.");
            });
        }
        return false;
    }

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

    $scope.lancementSubmit = function(slug,button,next) {
        if ($scope.lancement_debut_data) {
            if (next){$scope.lancement_debut_data.next=next;}else{$scope.lancement_debut_data.next=null;}
            $http.post(djangoUrl.reverse('lancement_debut', {slug:slug}), $scope.lancement_debut_data).success(function(out_data) {
                if (!djangoForm.setErrors($scope.lancement_debut_form, out_data.errors))
                {
                    // on successful post, redirect onto success page
                    var successurl = out_data.success_url;
                    if (next && successurl){
                        $window.location.href = successurl;
                    }
                }
                $scope.buttons[button].value=1;
            }).error(function() {
                swal("Erreur de connexion reseau. Le serveur est injoignable.");
                $scope.buttons[button].value=0;
            });
        }
        return false;
    };

    $scope.lancementInterneSubmit = function(slug,button,next) {
        if ($scope.lancement_interne_data) {
            if (next){$scope.lancement_interne_data.next=next;}else{$scope.lancement_interne_data.next=null;}
            $http.post(djangoUrl.reverse('lancement_interne', {slug:slug}), $scope.lancement_interne_data).success(function(out_data) {
                if (!djangoForm.setErrors($scope.lancement_interne_form, out_data.errors))
                {
                    // on successful post, redirect onto success page
                    var successurl = out_data.success_url;
                    if (next && successurl){
                        $window.location.href = successurl;
                    }
                }
                $scope.buttons[button].value=1;
            }).error(function() {
                swal("Erreur de connexion reseau. Le serveur est injoignable.");
                $scope.buttons[button].value=0;
            });
        }
        return false;
    };

    $scope.lancementCouvertureSubmit = function(slug,button,next) {
        if ($scope.lancement_couverture_data) {
            if (next){$scope.lancement_couverture_data.next=next;}else{$scope.lancement_couverture_data.next=null;}
            $http.post(djangoUrl.reverse('lancement_couverture', {slug:slug}), $scope.lancement_couverture_data).success(function(out_data) {
                if (!djangoForm.setErrors($scope.lancement_couverture_form, out_data.errors))
                {
                    // on successful post, redirect onto success page
                    var successurl = out_data.success_url;
                    if (next && successurl){
                        $window.location.href = successurl;
                    }
                }
                $scope.buttons[button].value=1;
            }).error(function() {
                swal("Erreur de connexion reseau. Le serveur est injoignable.");
                $scope.buttons[button].value=0;
            });
        }
        return false;
    };

    $scope.lancementPrixDateSubmit = function(slug,button, next) {
        if ($scope.lancement_prixdate_data) {
            if (next){$scope.lancement_prixdate_data.next=next;}else{$scope.lancement_prixdate_data.next=null;}
            var in_data = jQuery.extend(true, {}, $scope.lancement_prixdate_data);
            if ($scope.lancement_prixdate_data.pre_souscription) {
                in_data.date_souscription = null;
            }
            else{
                in_data.date_feedback = null;
            }

            $http.post(djangoUrl.reverse('lancement_prixdate', {slug:slug}), in_data).success(function(out_data) {
                if (!djangoForm.setErrors($scope.lancement_prixdate_form, out_data.errors))
                {
                    // on successful post, redirect onto success page
                    var successurl = out_data.success_url;
                    if (next && successurl){
                        $window.location.href = successurl;
                    }
                }

                $scope.buttons[button].value=1;

            }).error(function() {
                swal("Erreur de connexion reseau. Le serveur est injoignable.");
                $scope.buttons[button].value=0;
            });
        }
        return false;
    };

    $scope.lancementVousSubmit = function(slug,button, next) {
        data = {"biblio_user_data":$scope.biblio_userbiolieu_data || {},
                "adresse_data":$scope.adresse_data || {}}
        $http.post(djangoUrl.reverse('lancement_vous', {slug:slug}), data).success(function(out_data) {
            if ((!djangoForm.setErrors($scope.adresse_form, out_data.adresse_form_errors)) && (!djangoForm.setErrors($scope.biblio_userbiolieu_form, out_data.user_form_errors)))
            {
                // on successful post, redirect onto success page
                var successurl = out_data.success_url;
                if (next && successurl){
                    $window.location.href = successurl;
                }
            }

            $scope.buttons[button].value=1;

        }).error(function() {
            swal("Erreur de connexion reseau. Le serveur est injoignable.");
            $scope.buttons[button].value=0;
        });
        return false;
    };

    $scope.lancementFinSubmit = function(slug,button, next) {
        $http.post(djangoUrl.reverse('lancement_fin', {slug:slug}), $scope.lancement_fin_data).success(function(out_data) {
            if (!djangoForm.setErrors($scope.lancement_fin_form, out_data.errors))
            {
                // on successful post, redirect onto success page
                var successurl = out_data.success_url;
                if (next && successurl){
                    $window.location.href = successurl;
                }
            }

            $scope.buttons[button].value=1;

        }).error(function() {
            swal("Erreur de connexion reseau. Le serveur est injoignable.");
            $scope.buttons[button].value=0;
        });
        return false;
    };

    $scope.initLivre = function(livre_id, categories,genres,couleurs,categorie,genre,couleur,pre_souscription,tags){
        $scope.livre_id=livre_id;
        $scope.refreshData();
    }

    $scope.init = function(livre_id, categories,genres,couleurs,categorie,genre,couleur,pre_souscription,tags){
        $scope.livre_id=livre_id;
        $scope.categories=categories;
        $scope.genres=genres;
        $scope.couleurs=couleurs;
        if (categorie){
            $scope.lancement_debut_data.categorie=categorie;
        } else {
            $scope.lancement_debut_data.categorie=categories[0];
        }
        if (genre){
            $scope.lancement_debut_data.genre=genre;
        } else {
            $scope.lancement_debut_data.genre=genres[0];
        }
        if (couleur){
            $scope.lancement_debut_data.couleur=couleur;
        } else {
            $scope.lancement_debut_data.couleur=couleurs[0];
        }
        if (pre_souscription){
            $scope.lancement_debut_data.pre_souscription=(pre_souscription=="True")?true:false;
        } else {
            $scope.lancement_debut_data.pre_souscription=true;
        }
        if (tags){
            $scope.lancement_debut_data.tags=tags;
        } else {
            $scope.lancement_debut_data.tags=[];
        }
        $scope.refreshData();

    }

    $scope.$watchGroup(['lancement_debut_data.maquette', 'lancement_debut_data.couverture'], function(newValues, oldValues, $scope) {
      if (newValues[0]==false){
          swal({
              title: "Vous devrez fournir un seul type technique de fichier aux paramètres suivants : confirmez-vous votre choix ?",
              text: "dossier d'assemblage au format InDesign, comprenant toutes les pages, toutes les polices utilisées, toutes les images / toutes les polices qui ne sont pas disponibles par défaut avec InDesign doivent être vectorisées / toutes les images en CMJN / résolution minimale des images de 300 dpi / images au format tiff, jpeg ou eps / 3mm de fond perdu / marges internes de 6mm / pas de tons directs",
              // type: "warning",
              imageUrl: "/static/images/think.jpg",
              showCancelButton: true,
              confirmButtonColor: "#DD6B55",
              confirmButtonText: "je confirme",
              cancelButtonText: "Bibliocratie le fera pour moi",
              closeOnConfirm: true,
              closeOnCancel: true },
              function(isConfirm){
                  if (!isConfirm) {
                      $scope.lancement_debut_data['maquette']=true;
                      $scope.$apply()
                  }
              });
      }
      if (newValues[1]==false){
          swal({
              title: "Vous devrez fournir un seul type technique de fichier aux paramètres suivants : confirmez-vous votre choix ?",
              text: "couverture dans un dossier d'assemblage séparé, à plat (première, dos et quatrième de couverture) / 5mm de fond perdu / dossier d'assemblage au format InDesign, comprenant toutes les pages, toutes les polices utilisées, toutes les images / toutes les polices qui ne sont pas disponibles par défaut avec InDesign doivent être vectorisées / toutes les images en CMJN / résolution minimale des images de 300 dpi / images au format tiff, jpeg ou eps / pas de tons directs",
              // type: "warning",
              imageUrl: "/static/images/think.jpg",
              showCancelButton: true,
              confirmButtonColor: "#DD6B55",
              confirmButtonText: "je confirme",
              cancelButtonText: "Bibliocratie le fera pour moi",
              closeOnConfirm: true,
              closeOnCancel: true },
              function(isConfirm){
                  if (!isConfirm) {
                      $scope.lancement_debut_data.couverture=true;
                      $scope.$apply()
                  }
              });
      }
    });

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
                    $scope.refreshData();
                }
            },
        }
    };


    $scope.refreshData = function(){
        indata = {'livre_id': $scope.livre_id}
          djangoRMI.lancementjsonview.RefreshData(indata)
              .success(function (out_data) {
                  $scope.lancement_fichier_data.nom_fichier=out_data.nom_fichier;
                  $scope.lancement_fichier_data.url_fichier=out_data.url_fichier;
                  $scope.lancement_fichier_data.image_couverture=out_data.image_couverture;
                  $scope.lancement_fichier_data.maquette_couverture=out_data.maquette_couverture;
                  $scope.lancement_fichier_data.maquette_couverture_fichier_name=out_data.maquette_couverture_fichier_name;
              })
              .error(function(data, status, headers, config) {
                  swal("Erreur de connexion reseau. Le serveur est injoignable.");
              });
    }
    var init_nb_pages=true;
    var refreshCouts = function(){
        indata = {'livre_id':$scope.livre_id,'nb_exemplaires_cible':$scope.lancement_prixdate_data.nb_exemplaires_cible}
            djangoRMI.lancementjsonview.GetCoutProduction(indata)
                .success(function (out_data) {
                    $scope.message=out_data.message;
                    $scope.lancement_prixdate_data.cout_production=out_data.prix_exemplaire;
                    if ($scope.lancement_prixdate_data.prix_vente<out_data.prix_exemplaire){
                        $scope.lancement_prixdate_data.prix_vente=out_data.prix_exemplaire
                    }
                    if (out_data.palliers_nb_exemplaires){
                        $scope.slider_config.palliers_nb_exemplaires=out_data.palliers_nb_exemplaires;
                        $scope.slider_config.ceiling=out_data.palliers_nb_exemplaires.length - 1;
                    } else {
                        $scope.slider_config.palliers_nb_exemplaires=null;
                        $scope.slider_config.ceiling=0;
                        $scope.slider_config.index_nb_exemplaires_cible=0;
                    }
                    if (init_nb_pages && $scope.lancement_prixdate_data.nb_exemplaires_cible && $scope.slider_config.palliers_nb_exemplaires){
                        init_nb_pages=false;
                        $scope.slider_config.index_nb_exemplaires_cible = $scope.slider_config.palliers_nb_exemplaires.indexOf($scope.lancement_prixdate_data.nb_exemplaires_cible);
                    }
                })
                .error(function(data, status, headers, config) {
                   swal("Erreur de connexion reseau. Le serveur est injoignable.");
                });
    }

    $scope.initFin = function(livre_id){
        $scope.livre_id=livre_id;
        $scope.getDatesDebut();
    }

    $scope.initInterne = function(livre_id,maquette,encre){
        $scope.livre_id=livre_id;
        $scope.livre_maquette=maquette=="True";
        $scope.livre_encre=encre;
        $scope.refreshData();
    }

    $scope.choixFormat = function(choix){
        $scope.lancement_interne_data.format=choix;
    }


    var calculEnCours=false;
    var promise=null;
    $scope.$watch('lancement_prixdate_data.prix_vente', function(newValue, oldValue) {
        if (calculEnCours){
            $timeout.cancel(promise);
        }
        promise = $timeout(function(){
            if (newValue<$scope.lancement_prixdate_data.cout_production){
                coutMinimum=$scope.lancement_prixdate_data.cout_production;
                coutMinimum=Math.floor(coutMinimum * 10) / 10;
                $scope.lancement_prixdate_data.prix_vente=coutMinimum;
            }
            calculEnCours = false;
        }, 1000, true);
        calculEnCours = true;
    },true);


    $scope.$watch('lancement_prixdate_data.nb_exemplaires_cible', function(newValues, oldValues, $scope) {
         refreshCouts();
    });

    $scope.$watch('lancement_prixdate_data.cout_production', function(newValues, oldValues, $scope) {
        $scope.lancement_prixdate_data.prix_vente=$scope.lancement_prixdate_data.cout_production+1;
    });

}]);
