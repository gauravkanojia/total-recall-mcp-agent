uv run python -c "import os; print(os.getcwd())"

uv run python -c "import app; print(app.__file__)"

uv run pytest tests/test_config.py -v

uv run python -c "from app.core.config import settings; print(settings.DATABASE_URL)"

uv sync

uv run python - <<'PY'
import asyncio
import asyncpg

async def test():
    conn = await asyncpg.connect(
        host="localhost",
        port=26257,
        user="root",
        database="total_recall_mcp_db",
        sslmode="disable",
    )
    print("connected")
    await conn.close()

asyncio.run(test())
PY

uv run python - <<'PY'
import asyncio
import asyncpg

async def test():
    conn = await asyncpg.connect(
        host="localhost",
        port=26257,
        user="root",
        database="total_recall_mcp_db",
        ssl=False,
    )

    print("connected")

    await conn.close()

asyncio.run(test())
PY


postgresql://root@localhost:26257/defaultdb?sslmode=verify-full&sslrootcert=/path/to/certs/ca.crt&sslcert=/path/to/certs/client.root.crt&sslkey=/path/to/certs/client.root.key

docker run -d --name roach1 -p 26257:26257 -p 8080:8080 cockroachdb/cockroach:v26.1.0 start-single-node --insecure

podman run -d \
  --name mcp_roach_db \
  -p 26257:26257 \
  -p 8080:8080 \
  docker.io/cockroachdb/cockroach:v26.1.0 \
  start-single-node --insecure

#   Persistence (Optional): If you want your local database data to survive when you stop/delete the container, add a volume flag
#   -v crdb_data:/cockroach/cockroach-data
podman run -d --name=roach1 --hostname=roach1 --net=roachnet -p 26257:26257 -p 8080:8080 -v "roach1:/cockroach/cockroach-data" cockroachdb/cockroach:v26.2.3 start   --advertise-addr=roach1:26357   --http-addr=roach1:8080   --listen-addr=roach1:26357   --sql-addr=roach1:26257   --insecure   --join=roach1:26357,roach2:26357,roach3:26357


DATABASE_URL=postgresql+asyncpg://username:password@host:26257/database_name?sslmode=require
DATABASE_URL=postgresql+asyncpg://root@localhost:26257/defaultdb?sslmode=disable
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<cluster-host>:26257/defaultdb?sslmode=verify-full



# Docker/Podman commands for local Cockroach DB Setup

# Single Node Setup
# Step 1: Create Docker Volume for the single node
```bash
podman volume create roach-single
```

# Step 2: Start the cluster
```bash
export DATABASE_NAME=total_recall_mcp_db
export USER_NAME=roachkilla
export PASSWORD=baygon

podman run -d \
      --env COCKROACH_DATABASE={DATABASE_NAME} \
      --env COCKROACH_USER={USER_NAME} \
      --env COCKROACH_PASSWORD={PASSWORD} \
      --name=roach-single \
      --hostname=roach-single \
      -p 26257:26257 \
      -p 8080:8080 \
      -v "roach-single:/cockroach/cockroach-data" \
      cockroachdb/cockroach:v26.2.3 \
      start-single-node \
      --insecure \
      --http-addr=roach-single:8080
```
#  Step 3: Check startup details to for nodes in their logs.
#  e.g. log file that contains the string "node starting" and the next 11 lines.
```bash
podman exec -it roach-single grep 'node starting' /cockroach/cockroach-data/logs/cockroach.log -A 11
```

# Step 4: Connect to the cluster
```bash
podman logs --follow roach-single
```

#     Step 4a: To connect to the cluster interactively using  the cockroach sql command-line interface, 
#     set --url cluster's SQL connection string, which is printed next to sql: in the cluster's startup details. 
#     Connect to the roach-single cluster:
```bash
podman exec -it \
      roach-single \
      ./cockroach sql \
      --url="postgresql://root@127.0.0.1:26257/defaultdb?sslcert=certs%2Fclient.root.crt&sslkey=certs%2Fclient.root.key&sslmode=verify-full&sslrootcert=certs%2Fca.crt"
```


# Cluster Setup
# Step 1. Create a bridge network
```bash
podman network create -d bridge roachnet
```

# Step 2: Create Docker volumes for each cluster node
```bash
podman volume create roach1
podman volume create roach2
podman volume create roach3
```

# Step 3: Start the cluster
#   Step 3a: Start the first node in the cluster - roach1:26257
```bash
podman run -d \
      --name=roach1 \
      --hostname=roach1 \
      --net=roachnet \
      -p 26257:26257 \
      -p 8080:8080 \
      -v "roach1:/cockroach/cockroach-data" \
      cockroachdb/cockroach:v26.2.3 start   \
      --advertise-addr=roach1:26357 \
      --http-addr=roach1:8080 \
      --listen-addr=roach1:26357 \
      --sql-addr=roach1:26257 \
      --insecure \
      --join=roach1:26357,roach2:26357,roach3:26357
```

#   Step 3b: Start the second Node in the cluster - roach2:26258
```bash
podman run -d \
      --name=roach2 \
      --hostname=roach2 \
      --net=roachnet \
      -p 26258:26258 \
      -p 8081:8081 \
      -v "roach2:/cockroach/cockroach-data" \
      cockroachdb/cockroach:v26.2.3 start   \
      --advertise-addr=roach2:26357 \
      --http-addr=roach2:8081 \
      --listen-addr=roach2:26357 \
      --sql-addr=roach2:26258 \
      --insecure \
      --join=roach1:26357,roach2:26357,roach3:26357
```

#   Step 3c: Start the third Node in the cluster - roach3:26259
```bash
podman run -d \
      --name=roach3 \
      --hostname=roach3 \
      --net=roachnet \
      -p 26259:26259 \
      -p 8082:8082 \
      -v "roach3:/cockroach/cockroach-data" \
      cockroachdb/cockroach:v26.2.3 start   \
      --advertise-addr=roach3:26357 \
      --http-addr=roach3:8082 \
      --listen-addr=roach3:26357 \
      --sql-addr=roach3:26259 \
      --insecure \
      --join=roach1:26357,roach2:26357,roach3:26357
```

# Step 4: Perform a one-time initialization of the cluster.
```bash
podman exec -it roach1 ./cockroach --host=roach1:26357 init --insecure
```

# Above execution should display: "Cluster successfully initialized"

#   Step 4a: Check startup details to for nodes in their logs.
#  e.g. log file that contains the string "node starting" and the next 11 lines.
```bash
podman exec -it roach1 grep 'node starting' /cockroach/cockroach-data/logs/cockroach.log -A 11
```

# Step 5: Connect to the cluster
```bash
podman exec -it roach1 ./cockroach sql --host=roach2:26258 --insecure
```

#   Step 5a: Run basic CockroachDB statements
#     Refer to roachdb.sql file

#   Step 5b: Validate DB setup from Second Node
```bash
podman exec -it roach2 ./cockroach --host=roach2:26258 sql --insecure
```
