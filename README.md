# flask-bulletin
Bulletin board built with Flask


### Useful commands

postgres -D /usr/local/var/postgres

FLASK_APP=bulletin/app.py python3 -m flask run
FLASK_APP=app.app flask routes

### Design Choice
- BigInt as Primary Key: Storage is cheap; database migration (from INT -> BIGINT), however is costly and has the potential to bring down service
- Connection Pool: Connection pool is used, as overhead exists when creating a new connection to the database; remove idle connection after a while (not implemented due to time constraint)
- Split Model.py: For organisation (not implemented due to time constraint)
- Singleton: _Context implemented as Singleton to ensure that particular instance of object is referred to consistently
- Retrieval of secrets dynamically (not implemented - assumed exist)
- Replace hardcoded HTTP status with readable status code (not implemented due to time limit)

### Potential Bottleneck and Solution
- Problem: Documentation of API is not maintained

  Solution: Swagger may be used to document the API; omitted here due to time constraint

- Problem: Read traffic may overwhelm database
  
  Solution: Use database replica, and create a separate read connections to the read replicas

- Problem: Logging not centralised; debugging difficulty

  Solution: Create centralised logging (e.g. ElasticSearch) such that the IP of the machine + relevant logs are captured for ease of debugging

  