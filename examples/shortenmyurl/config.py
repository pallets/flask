import os
import redis

redis_url = os.getenv('REDISTOGO_URL', 'redis://redistogo:9e87a450dd3ef9a69cd9b31c2560a541@greeneye.redistogo.com:11156/')


#redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379');
