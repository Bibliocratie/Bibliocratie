redis-cli KEYS "ws:*" | xargs redis-cli DEL
