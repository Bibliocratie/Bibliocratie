angular.module('bibliocratie_app').controller('CheckoutCtrl', ['$scope', '$http', '$window', 'djangoForm', 'djangoUrl','djangoRMI', function($scope, $http, $window, djangoForm, djangoUrl,djangoRMI) {
    $scope.checkoutSubmit = function() {
        var adress_data = {'facturation_data' : $scope.facturation_data, 'livraison_data' : $scope.livraison_data, 'checkout_data' : $scope.checkout_data};
        if (adress_data) {
            $http.post(djangoUrl.reverse('checkout'), adress_data).success(function(out_data) {
                if (!djangoForm.setErrors($scope.livraison_form, out_data.errors_livraison) &&
                    !djangoForm.setErrors($scope.facturation_form, out_data.errors_facturation) &&
                    !djangoForm.setErrors($scope.checkout_form, out_data.errors_checkout))
                {
                    // on successful post, redirect onto success page
                    var successurl = out_data.success_url;
                    if (successurl) $window.location.href = successurl;
                }
            }).error(function(data, status, headers, config) {
                swal("Erreur de connexion reseau. Le serveur est injoignable.");
            });
        }
        return false;
    };

    $scope.$watchGroup(['facturation_data.pays', 'livraison_data.pays','checkout_data.diff_address'], function(newValues, oldValues, $scope) {
      if (newValues[0] || newValues[1] || newValues[2]){
          var ask_server = false;
          var pays;
          if (newValues[2] && newValues[1]) {
              pays = newValues[1];
              ask_server=true;
          }
          else {
              if (newValues[0]) {
                  pays = newValues[0];
                  ask_server = true;
              }
          }
          if (ask_server) {
              djangoRMI.panierjsonview.setPaysLivraison(pays)
                  .success(function (out_data) {
                      $scope.panier=out_data.panier;
                  });
          }
      }
    });
}]);
