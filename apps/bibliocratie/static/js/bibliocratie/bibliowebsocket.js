(function (angular, undefined) {
    'use strict';
    function noop() {
    }

    // Add three-way data-binding for AngularJS with Django using websockets.
    var biblio_ws_module = angular.module('ng.biblio.websocket', []);

    //La websocket Broadcast
    biblio_ws_module.service('$broadcastWebsocket', function () {
        var ws;
        this.connect = function (url) {
            ws = new WebSocket(url);
            ws.onopen = this.onopen;
            ws.onmessage = this.onmessage;
            ws.onerror = this.onerror;
            ws.onclose = this.onclose;
        };
        this.send = function (msg) {
            ws.send(msg);
        };
        this.close = function () {
            ws.close();
        };
    });
    biblio_ws_module.provider('biblioBroadcastWebsocket', function () {
        var _console = {
            log: noop,
            warn: noop,
            error: noop
        };
        var websocket_uri, heartbeat_msg = null;
        // Set prefix for the Websocket's URI.
        // This URI must be set during initialization using
        // biblioBroadcastWebsocketProvider.setURI('{{ WEBSOCKET_URI }}');
        this.setURI = function (uri) {
            websocket_uri = uri;
            return this;
        };
        // Set the heartbeat message and activate the heartbeat interval to 5 seconds.
        // The heartbeat message shall be configured using
        // biblioWebsocketProvider.setHeartbeat({{ WS4REDIS_HEARTBEAT }});  // unquoted!
        // The default behavior is to not listen on heartbeats.
        this.setHeartbeat = function (msg) {
            heartbeat_msg = msg;
            return this;
        };
        this.setLogLevel = function (logLevel) {
            switch (logLevel) {
                case 'debug':
                    _console = console;
                    break;
                case 'log':
                    _console.log = console.log;
                /* falls through */
                case 'warn':
                    _console.warn = console.warn;
                /* falls through */
                case 'error':
                    _console.error = console.error;
                /* falls through */
                default:
                    break;
            }
            return this;
        };
        this.$get = [
            '$broadcastWebsocket',
            '$q',
            '$timeout',
            '$interval',
            function ($broadcastWebsocket, $q, $timeout, $interval) {
                var ws_url, deferred, scope;
                var broadcastCollection = [];
                var is_subscriber = false, is_publisher = false, receiving = false;
                var wait_for_reconnect = 0, heartbeat_promise = null, missed_heartbeats = 0;

                function connect() {
                    _console.log('Connecting to ' + ws_url);
                    deferred = $q.defer();
                    $broadcastWebsocket.connect(ws_url);
                }

                $broadcastWebsocket.onopen = function (evt) {
                    _console.log('Connected');
                    deferred.resolve();
                    wait_for_reconnect = 0;
                    if (heartbeat_msg && heartbeat_promise === null) {
                        missed_heartbeats = 0;
                        heartbeat_promise = $interval(sendHeartbeat, 5000);
                    }
                };
                $broadcastWebsocket.onclose = function (evt) {
                    _console.log('Disconnected');
                    deferred.reject();
                    wait_for_reconnect = Math.min(wait_for_reconnect + 1000, 10000);
                    $timeout(function () {
                        $broadcastWebsocket.connect(ws_url);
                    }, wait_for_reconnect);
                };
                $broadcastWebsocket.onerror = function (evt) {
                    _console.error('Websocket connection is broken!');
                    $broadcastWebsocket.close();
                };
                $broadcastWebsocket.onmessage = function (evt) {
                    var data;
                    if (evt.data === heartbeat_msg) {
                        // reset the counter for missed heartbeats
                        missed_heartbeats = 0;
                        return;
                    }
                    try {
                        data = angular.fromJson(evt.data);
                    } catch (e) {
                        _console.warn('Data received by server is invalid JSON: ' + evt.data);
                        return;
                    }
                    if (is_subscriber) {
                        // temporarily disable the function 'listener', so that message received
                        // from the websocket, are not propagated back
                        receiving = true;
                        scope.$apply(function () {
                            var i;
                            for (i = 1; i <= broadcastCollection.length; i++) {
                                if (data.api_message_type == broadcastCollection[i - 1].facility) {
                                    var fname = "onBcastMessage" + i;
                                    if (angular.isFunction(scope[fname])) {
                                        scope[fname](data);
                                    } else {
                                        angular.extend(scope[fname], data);
                                    }
                                }
                            }
                        });
                        receiving = false;
                    }
                };
                function sendHeartbeat() {
                    try {
                        missed_heartbeats++;
                        if (missed_heartbeats > 3)
                            throw new Error('Too many missed heartbeats.');
                        $broadcastWebsocket.send(heartbeat_msg);
                    } catch (e) {
                        $interval.cancel(heartbeat_promise);
                        heartbeat_promise = null;
                        _console.warn('Closing connection. Reason: ' + e.message);
                        $broadcastWebsocket.close();
                    }
                }

                function listener(newValue, oldValue) {
                    if (!receiving && !angular.equals(oldValue, newValue)) {
                        $broadcastWebsocket.send(angular.toJson(newValue));
                    }
                }

                function watchCollection() {
                    var i;
                    for (i = 1; i <= broadcastCollection.length; i++) {
                        var fname = "onBcastMessage" + i;
                        scope.$watchCollection(fname, listener);
                    }
                }

                function buildWebsocketURL(facility, channels) {
                    var parts = [
                        websocket_uri,
                        facility,
                        '?'
                    ];
                    parts.push(channels.join('&'));
                    ws_url = parts.join('');
                }

                return {
                    connect: function ($scope, scope_obj, facility) {
                        scope = $scope;
                        is_subscriber = true;
                        var connector = {"scope_obj": scope_obj, "facility": facility};
                        var index = broadcastCollection.push(connector);
                        var fname = "onBcastMessage" + index;
                        scope[fname] = scope[broadcastCollection[index - 1].scope_obj] || {};
                        if (broadcastCollection.length==1) {
                            buildWebsocketURL("broadcast", ['subscribe-broadcast']);
                            connect();
                        }
                        if (is_publisher) {
                            deferred.promise.then(watchCollection);
                        }
                        return deferred.promise;
                    }
                };
            }
        ];
    });

    //La websocket User
    biblio_ws_module.service('$userWebsocket', function () {
        var ws;
        this.connect = function (url) {
            ws = new WebSocket(url);
            ws.onopen = this.onopen;
            ws.onmessage = this.onmessage;
            ws.onerror = this.onerror;
            ws.onclose = this.onclose;
        };
        this.send = function (msg) {
            ws.send(msg);
        };
        this.close = function () {
            ws.close();
        };
    });
    biblio_ws_module.provider('biblioUserWebsocket', function () {
        var _console = {
            log: noop,
            warn: noop,
            error: noop
        };
        var websocket_uri, heartbeat_msg = null;
        // Set prefix for the Websocket's URI.
        // This URI must be set during initialization using
        // biblioUserWebsocketProvider.setURI('{{ WEBSOCKET_URI }}');
        this.setURI = function (uri) {
            websocket_uri = uri;
            return this;
        };
        // Set the heartbeat message and activate the heartbeat interval to 5 seconds.
        // The heartbeat message shall be configured using
        // biblioWebsocketProvider.setHeartbeat({{ WS4REDIS_HEARTBEAT }});  // unquoted!
        // The default behavior is to not listen on heartbeats.
        this.setHeartbeat = function (msg) {
            heartbeat_msg = msg;
            return this;
        };
        this.setLogLevel = function (logLevel) {
            switch (logLevel) {
                case 'debug':
                    _console = console;
                    break;
                case 'log':
                    _console.log = console.log;
                /* falls through */
                case 'warn':
                    _console.warn = console.warn;
                /* falls through */
                case 'error':
                    _console.error = console.error;
                /* falls through */
                default:
                    break;
            }
            return this;
        };
        this.$get = [
            '$userWebsocket',
            '$q',
            '$timeout',
            '$interval',
            function ($userWebsocket, $q, $timeout, $interval) {
                var ws_url, deferred, scope;
                var userCollection = [];
                var is_subscriber = false, is_publisher = false, receiving = false;
                var wait_for_reconnect = 0, heartbeat_promise = null, missed_heartbeats = 0;

                function connect() {
                    _console.log('Connecting to ' + ws_url);
                    deferred = $q.defer();
                    $userWebsocket.connect(ws_url);
                }

                $userWebsocket.onopen = function (evt) {
                    _console.log('Connected');
                    deferred.resolve();
                    wait_for_reconnect = 0;
                    if (heartbeat_msg && heartbeat_promise === null) {
                        missed_heartbeats = 0;
                        heartbeat_promise = $interval(sendHeartbeat, 5000);
                    }
                };
                $userWebsocket.onclose = function (evt) {
                    _console.log('Disconnected');
                    deferred.reject();
                    wait_for_reconnect = Math.min(wait_for_reconnect + 1000, 10000);
                    $timeout(function () {
                        $userWebsocket.connect(ws_url);
                    }, wait_for_reconnect);
                };
                $userWebsocket.onerror = function (evt) {
                    _console.error('Websocket connection is broken!');
                    $userWebsocket.close();
                };
                $userWebsocket.onmessage = function (evt) {
                    var data;
                    if (evt.data === heartbeat_msg) {
                        // reset the counter for missed heartbeats
                        missed_heartbeats = 0;
                        return;
                    }
                    try {
                        data = angular.fromJson(evt.data);
                    } catch (e) {
                        _console.warn('Data received by server is invalid JSON: ' + evt.data);
                        return;
                    }
                    if (is_subscriber) {
                        // temporarily disable the function 'listener', so that message received
                        // from the websocket, are not propagated back
                        receiving = true;
                        scope.$apply(function () {
                            var i;
                            for (i = 1; i <= userCollection.length; i++) {
                                if (data.api_message_type == userCollection[i - 1].facility) {
                                    var fn=userCollection[i - 1].user_cback_fonction;
                                    if (angular.isFunction(fn)) {
                                        fn(data);
                                    } else {
                                        angular.extend(fn, data);
                                    }
                                }
                            }
                        });
                        receiving = false;
                    }
                };
                function sendHeartbeat() {
                    try {
                        missed_heartbeats++;
                        if (missed_heartbeats > 3)
                            throw new Error('Too many missed heartbeats.');
                        $userWebsocket.send(heartbeat_msg);
                    } catch (e) {
                        $interval.cancel(heartbeat_promise);
                        heartbeat_promise = null;
                        _console.warn('Closing connection. Reason: ' + e.message);
                        $userWebsocket.close();
                    }
                }

                function listener(newValue, oldValue) {
                    if (!receiving && !angular.equals(oldValue, newValue)) {
                        $userWebsocket.send(angular.toJson(newValue));
                    }
                }

                function watchCollection() {
                    var i;
                    for (i = 1; i <= userCollection.length; i++) {
                        var fname = "onUserMessage" + i;
                        scope.$watchCollection(fname, listener);
                    }
                }

                function buildWebsocketURL(facility, channels) {
                    var parts = [
                        websocket_uri,
                        facility,
                        '?'
                    ];
                    parts.push(channels.join('&'));
                    ws_url = parts.join('');
                }

                return {
                    connect: function ($scope, scope_obj, facility) {
                        scope = $scope;
                        is_subscriber = true;
                        var connector = {"scope_obj": scope_obj, "facility": facility};
                        var index = userCollection.push(connector);
                        var fname = "onUserMessage" + index;
                        var user_cback_fonction = scope[userCollection[index - 1].scope_obj] || {};
                        userCollection[index - 1].user_cback_fonction=user_cback_fonction;
                        scope[fname]=user_cback_fonction;
                        if (userCollection.length==1) {
                            buildWebsocketURL("user", ['subscribe-user']);
                            connect();
                        }
                        if (is_publisher) {
                            deferred.promise.then(watchCollection);
                        }
                        return deferred.promise;
                    }
                };
            }
        ];
    });
}(window.angular));
