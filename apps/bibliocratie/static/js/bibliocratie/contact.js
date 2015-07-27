angular.module('bibliocratie_app').controller('ContactCtrl', ['$scope', '$http', '$timeout', '$interval', 'djangoForm', 'djangoUrl', function($scope, $http, $timeout, $interval, djangoForm, djangoUrl) {
    $scope.etat_envoi = "attente";

    $scope.buttons = [
			{ value: 0.0 },
		]

    $scope.contactSubmit = function(button){
        $http.post(djangoUrl.reverse('contact'), $scope.contact_data).success(function(out_data) {
            if (!djangoForm.setErrors($scope.contact_form, out_data.errors))
            {
                $scope.etat_envoi = "ok";
                $scope.contact_data = {};
                $scope.contact_form.$setPristine()

                $timeout(function(){
                    swal({
                        title: "Votre message a été envoyé. Merci.",
                        text: "",
                        timer: 5000
                    });
                    $('#contactModal').removeClass('active');
                }, 1000, true);
            } else {
                $scope.etat_envoi = "erreur";
            }
            $scope.buttons[button].value=1;
        }).error(function() {
            swal("Erreur de connexion reseau. Le serveur est injoignable.");
            $scope.buttons[button].value=0;
        });
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
}]);
