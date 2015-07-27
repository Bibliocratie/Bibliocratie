angular.module('bibliocratie_app').
    controller('MembresCtrl', ['$scope', '$rootScope', '$http', '$timeout', '$sce','djangoRMI', 'djangoUrl', 'packeryService', 'biblioBroadcastWebsocket',function($scope, $rootScope, $http, $timeout, $sce, djangoRMI, djangoUrl, packeryService, biblioBroadcastWebsocket) {
    $scope.membres = null;
    var page_size = 50;
    var page = 1;
    $scope.isFirstPage=true;
    $scope.isLastPage=true;

    $scope.loadingmore = true;

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


    $scope.getMembres = function(){
        var params={
            'page_size':page_size,
            'page':page,
            'nocache': new Date().getTime()
        };

        $http({
            url: djangoUrl.reverse("api-user-list"),
            method: "GET",
            params: params
        }).success(function(data){
            if (!Object.equals($scope.membres,data)){
                if (page==1) {
                    $scope.membres = data;
                } else {
                    $scope.membres.results = $scope.membres.results.concat(data.results);
                }
                data.next===null?$scope.isLastPage=true:$scope.isLastPage=false;
                data.previous===null?$scope.isFirstPage=true:$scope.isFirstPage=false;
            }
            $scope.loadingmore = false;
        }).error(function(data, status, headers, config) {
            swal("Erreur de connexion reseau. Le serveur est injoignable.");
        });
    };

    $scope.packery = function(){
        var promise = packeryService.Packery();
        promise.then(function (object) {
            object.layout();
        });
    };

    $scope.onImgLoad = function (event) {
        $scope.packery();
    }

    $scope.nextPage = function(){
        if (!$scope.isLastPage){
            $scope.loadingmore = true;
            page+=1;
            $scope.getMembres();
            // $scope.mySelecteurChanged("");
        }
    };


}]);
