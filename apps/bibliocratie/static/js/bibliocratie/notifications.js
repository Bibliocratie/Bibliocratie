angular.module('bibliocratie_app')
.controller("NotificationsCtrl", ['$scope', 'biblioUserWebsocket','$timeout',function($scope, biblioUserWebsocket,$timeout) {
    $scope.notifications = [];

    $scope.onNotification = function(message){
        message.timestamp = new Date(message.timestamp).getTime()
        $scope.notifications.push(message);
        $('#notif-dropdown').dropdown('toggle');
        $timeout(function() {
            if (document.getElementById('notif-dropdown').attributes['aria-expanded'].value=="true"){
                $('#notif-dropdown').dropdown('toggle');
            }
        },5000);
        if (message.reload){
            //location.reload();
        }
    };

    biblioUserWebsocket.connect($scope, 'onNotification', 'NOTIF');

}]);
