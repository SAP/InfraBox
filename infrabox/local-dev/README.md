# InfraBox Local Dev Stack

本目录提供一套用于本地验证后端功能的 Docker Compose 环境，包含 PostgreSQL、MinIO、OPA 和 API Server。

## 启动前准备

**修改密码**：`docker-compose.yml` 中密码字段已置空，启动前需要自行填入：

```yaml
# postgres 服务
- POSTGRES_PASSWORD=<your-password>

# api 服务
- INFRABOX_DATABASE_PASSWORD=<your-password>   # 与上面保持一致
```

两处填写相同的密码即可，本地测试用简单密码（如 `postgres`）完全可以。

## 启动

```bash
# 首次启动需要构建镜像（API、OPA、Postgres 均从源码构建）
DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0 \
  docker compose -f infrabox/local-dev/docker-compose.yml up -d

# 查看 API 日志
docker compose -f infrabox/local-dev/docker-compose.yml logs -f api
```

## 前端开发服务器

```bash
cd src/dashboard-client
npm install --legacy-peer-deps --ignore-scripts
npm run dev
```

启动后访问 http://localhost:8081（如果 8080 被占用会自动顺延端口）。

API 请求通过 webpack proxyTable 转发到 `http://localhost:8090`，无需手动配置跨域。

## 创建测试用户

```bash
# 生成 bcrypt 密码 hash（Python 环境需安装 bcrypt）
python3 -c "import bcrypt; print(bcrypt.hashpw(b'yourpassword', bcrypt.gensalt()).decode())"

# 插入用户（role 可选 'user' 或 'admin'）
docker exec local-dev-postgres-1 psql -U postgres -c "
  INSERT INTO \"user\" (username, email, password, role)
  VALUES ('alice', 'alice@example.com', '<bcrypt-hash>', 'user');
"
```

登录界面填写 **email**（非 username）。

## 关闭

```bash
docker compose -f infrabox/local-dev/docker-compose.yml down
```

## 说明

- `seed.sql`：初始化时插入一条 `cluster` 记录，API 启动依赖该记录
- API 对外暴露端口 `8090`，内部监听 `8080`
- RSA 密钥复用 `infrabox/test/utils/id_rsa[.pub]`，仅供本地开发使用
- OPA 和 API 均从源码构建，确保包含最新 policy 和 handler
