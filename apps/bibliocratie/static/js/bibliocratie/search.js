angular.module('bibliocratie_app').controller('GlobalSearch', ['$scope', 'djangoRMI',function($scope, djangoRMI) {
    $scope.search = ""
    $scope.membres = [];
    $scope.publications = [];
    $scope.ailleurs = [];
    $('#globalSearch').on('shown.bs.modal', function () {
        $('#searchInput').focus()
    })

    var searching = false;

    $scope.$watch('search', function(newValues, oldValues, $scope) {
        if (newValues==""){
            $scope.membres = [];
            $scope.publications = [];
            $scope.ailleurs = [];
            return;
        }
        if (newValues.length<3){
            return;
        };

        var indata = {"search":newValues};
        console.log("searching: " + newValues)
        djangoRMI.globalsearchjsonview.Search(indata)
            .success(function (out_data) {
                $scope.membres = [];
                $scope.publications = [];
                $scope.ailleurs = [];
                if (out_data.search!=$scope.search){
                    return;
                }
                if(out_data.list.length == 0){
                    $scope.membres.push(result = {'username' : 'Aucun résultat'});
                    $scope.publications.push(result={'titre': 'Aucun résultat'});
                    $scope.ailleurs.push(result={'titre': 'Aucun résultat'});
                }
                else{
                    var BiblioUser = 0;
                    var Livre = 0;
                    var ailleurs = 0;
                    for (var i = 0; i < out_data.list.length; i++) {
                        var result = out_data.list[i];
                        switch (result.class_name){
                            case 'BiblioUser':
                                $scope.membres.push(result);
                                BiblioUser++
                                break;
                            case 'Livre':
                                $scope.publications.push(result);
                                Livre++;
                                break;
                            case 'UrlIndex':
                                $scope.ailleurs.push(result);
                                ailleurs++;
                                break;
                        }

                    }
                    if(BiblioUser == 0){
                        $scope.membres.push(result = {'username' : 'Aucun résultat'});
                    }
                    if(Livre == 0){
                        $scope.publications.push(result={'titre': 'Aucun résultat'});
                    }
                    if(ailleurs == 0){
                        $scope.ailleurs.push(result={'titre': 'Aucun résultat'});
                    }
                }
            }).error(function(){
                swal("Erreur de connexion reseau. Le serveur est injoignable.");
            });
    });

}]);