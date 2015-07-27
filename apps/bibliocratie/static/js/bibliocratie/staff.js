angular.module('bibliocratie_app')
.factory('BiblioUser', ['$resource', function($resource) {
    return $resource('/crud/bibliouser/', {'pk': '@pk'}, {
    });
}]);

angular.module('bibliocratie_app')
.controller('StaffCtrl', ['$scope','djangoRMI','djangoUrl','djangoForm','$http', 'BiblioUser',function($scope,djangoRMI,djangoUrl,djangoForm,$http,BiblioUser) {

    $scope.datejour=moment().startOf('day').toDate();
    $scope.chartdatajour = [];
    $scope.chartoptionsjour = {};

    $scope.datedebut=moment().startOf('month').toDate();
    $scope.datefin=moment().endOf('month').toDate();
    $scope.chartdatamois = [];
    $scope.chartoptionsmois = {};

    $scope.datedebutannee=moment().startOf('year').toDate();
    $scope.datefinannee=moment().endOf('year').toDate();
    $scope.chartdataannee = [];
    $scope.chartoptionsannee = {};

    $scope.search = "";

    $scope.refreshing_jour=false;
    $scope.refreshJour = function(){
        $scope.refreshing_jour=true;
        indata = {'date_jour': $scope.datejour}
            djangoRMI.staffjsonview.getStatVentesJour(indata)
                .success(function (out_data) {
                    if (out_data.success){
                        $scope.chartdatajour = out_data.souscriptions;
                        $scope.chartoptionsjour = out_data.options;
                        $scope.ca_jour = out_data.ca;
                        $scope.nb_commandes_jour = out_data.nb_commandes;
                        $scope.nb_souscriptions_jour = out_data.nb_souscriptions;
                    }
                    $scope.refreshing_jour=false;
                })
                .error(function(data, status, headers, config) {
                    swal("Erreur de connexion reseau. Le serveur est injoignable.");
                    $scope.refreshing_jour=false;
                });
    }

    $scope.refreshing_mois=false;
    $scope.refreshMois = function(){
        $scope.refreshing_mois=true;
        indata = {'date_debut': $scope.datedebut,'date_fin': $scope.datefin}
            djangoRMI.staffjsonview.getStatVentesMois(indata)
                .success(function (out_data) {
                    if (out_data.success){
                        $scope.chartdatamois = out_data.souscriptions;
                        $scope.chartoptionsmois = out_data.options;
                        $scope.ca_mois = out_data.ca;
                        $scope.nb_commandes_mois = out_data.nb_commandes;
                        $scope.nb_souscriptions_mois = out_data.nb_souscriptions;
                        $scope.chartoptionsmois.options = {
                            xaxis: {
                            mode: "time",
                            timeformat: "%Y/%m/%d"
                        }
                          };
                    }
                    $scope.refreshing_mois=false;
                })
                .error(function(data, status, headers, config) {
                    swal("Erreur de connexion reseau. Le serveur est injoignable.");
                    $scope.refreshing_mois=false;
                });
    }

    $scope.refreshing_annee=false;
    $scope.refreshAnnee = function(){
        $scope.refreshing_annee=true;
        indata = {'date_debut': $scope.datedebutannee,'date_fin': $scope.datefinannee}
        $scope.datedebutannee=moment($scope.datedebutannee).startOf('month').toDate();
        $scope.datefinannee=moment($scope.datefinannee).endOf('month').toDate();
            djangoRMI.staffjsonview.getStatVentesAnnee(indata)
                .success(function (out_data) {
                    if (out_data.success){
                        $scope.chartdataannee = out_data.souscriptions;
                        $scope.chartoptionsannee = out_data.options;
                        $scope.ca_annee = out_data.ca;
                        $scope.nb_commandes_annee = out_data.nb_commandes;
                        $scope.nb_souscriptions_annee = out_data.nb_souscriptions;
                    }
                    $scope.refreshing_annee=false;
                })
                .error(function(data, status, headers, config) {
                    swal("Erreur de connexion reseau. Le serveur est injoignable.");
                    $scope.refreshing_annee=false;
                });
    }

    // commandes

    $scope.commande_page = 1;
    $scope.refreshCommandes = function(newValue, type){
        var params={
            'page':$scope.commande_page,
            'search':$scope.search,
            'nocache': new Date().getTime()
        };

        $http({
            url: djangoUrl.reverse("api-staff-commandes-list"),
            method: "GET",
            params: params
        }).success(function(data){
            console.log(data);
            $scope.commandes = data;
        }).error(function(data, status, headers, config) {
           swal("Erreur de connexion reseau. Le serveur est injoignable.");
        });
    };

    $scope.nextPage = function(){
        if ($scope.commande_page < ($scope.commandes.count/10)){
            $scope.commande_page+=1;
            $scope.refreshCommandes();
        }
    }

    $scope.previousPage = function(){
        if ($scope.commande_page > 1){
            $scope.commande_page-=1;
            $scope.refreshCommandes();
        }
    }

    $scope.livresearch='';
    $scope.$watch('livresearch', function(newValues, oldValues, $scope) {
        if (newValues.length>=3){
                $http({
                url: djangoUrl.reverse("api-livres-list"),
                method: "GET",
                params: {
                    'search': newValues,
                    'nocache': new Date().getTime()
                }
            }).success(function(data){
                $scope.livresearch_results=data;
            }).error(function(data, status, headers, config) {
                swal("Erreur de connexion reseau. Le serveur est injoignable.");
            });
        } else {
            $scope.livresearch_results=[];
        }

    });

    $scope.clientsearch='';

    $scope.$watch('clientsearch', function(newValues, oldValues, $scope) {
        if (newValues.length>=3){
                $http({
                url: djangoUrl.reverse("api-staff-users-list"),
                method: "GET",
                params: {
                    'search': newValues,
                    'nocache': new Date().getTime()
                }
            }).success(function(data){
                $scope.clientsearch_results=data;
            }).error(function(data, status, headers, config) {
                swal("Erreur de connexion reseau. Le serveur est injoignable.");
            });
        } else {
            $scope.clientsearch_results=[];
        }

    });

    $scope.commande = {
        souscriptions : [],
        client : "",
    };

    $scope.addLivre = function(livre){
        for (i=0;i<$scope.commande.souscriptions.length;i++){
            souscription=$scope.commande.souscriptions[i];
            if (souscription.id==livre.id){
                souscription.quantite+=1;
                $scope.livresearch='';
                return;
            }
        }
        livre.quantite=1;
        $scope.commande.souscriptions.push(livre)
        $scope.livresearch='';
    }

    $scope.removeLivre = function(index){
        $scope.commande.souscriptions.splice(index, 1);
    }

    $scope.choisirClient = function(client){
        $scope.commande.client=client;
        $scope.clientsearch='';
        $scope.facturation_data.adresse=client.adresse.adresse;
        $scope.facturation_data.code_postal=client.adresse.code_postal;
        $scope.facturation_data.complement_adresse=client.adresse.complement_adresse;
        $scope.facturation_data.nom=client.adresse.nom;
        $scope.facturation_data.pays=client.adresse.pays;
        $scope.facturation_data.phone=client.adresse.phone;
        $scope.facturation_data.prenom=client.adresse.prenom;
        $scope.facturation_data.ville=client.adresse.ville;

    }

    // commentaires

    $scope.commentaire_page = 1;
    $scope.refreshCommentaires = function(newValue, type){
        var params={
            'page':$scope.commentaire_page,
            'search':$scope.search,
            'nocache': new Date().getTime()
        };

        $http({
            url: djangoUrl.reverse("api-staff-commentaires-list"),
            method: "GET",
            params: params
        }).success(function(data){
            $scope.commentaires = data;
        }).error(function(data, status, headers, config) {
           swal("Erreur de connexion reseau. Le serveur est injoignable.");
        });
    };

    $scope.nextPageComm = function(){
        if ($scope.commentaire_page < ($scope.commentaires.count/10)){
            $scope.commentaire_page+=1;
            $scope.refreshCommentaires();
        }
    }

    $scope.previousPageComm = function(){
        if ($scope.commentaire_page > 1){
            $scope.commentaire_page-=1;
            $scope.refreshCommentaires();
        }
    }

    $scope.clientSubmit = function(){
        data = {
            client:$scope.biblio_user_data,
            adresse:$scope.adresse_cli_data,
        }
        $http.post(djangoUrl.reverse('staff_only'), data).success(function(out_data) {
            if (!djangoForm.setErrors($scope.biblio_user_form, out_data.client) && !djangoForm.setErrors($scope.adresse_cli_form, out_data.adresse))
            {
                swal("Le client a bien été créé")
            }
        })
        .error(function(data, status, headers, config) {
               swal("Erreur de connexion reseau. Le serveur est injoignable.");
        });
    }

    $scope.commandeSubmit = function(){
        data = {
            commande:$scope.commande,
            adresse_fact:$scope.facturation_data,
            adresse_livr:$scope.livraison_data,
            diff:$scope.checkout_data,
        }
        $http.post(djangoUrl.reverse('staff_only'), data).success(function(out_data) {
            if (out_data.hasOwnProperty('error_msg')){
                swal(out_data.error_msg);

            }
            else if (!djangoForm.setErrors($scope.facturation_form, out_data.facturation) || !djangoForm.setErrors($scope.livraison_form, out_data.livraison))
            {
                swal("la commande "+ out_data.commande.no_commande+" a bien été créé");
                $scope.commande = {
                    souscriptions : [],
                    client : "",
                };
            }
        })
        .error(function(data, status, headers, config) {
               swal("Erreur de connexion reseau. Le serveur est injoignable.");
        });

    }

    $scope.refreshJour();
    $scope.refreshMois();
    $scope.refreshAnnee();
    $scope.refreshCommandes();
    $scope.refreshCommentaires();
}]);
