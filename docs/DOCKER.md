# Docker mode

- `RSPSRV` uses two databases outside of this compose (build them using [this guide](INSTALL.md#Database))

1. Create `docker/configs/env` directory based on `docker/configs/env.example`
2. Change local variables located in `app.env`
3. Run (build and run) docker containers using `sudo docker-compose up [--build]`
4. Set the full path of `notification-templates` in `docker/.env` file

## Installation

- `sudo docker-compose exec rspsrv_app_1 docker/commands/install.sh`

## Update
- `sudo docker-compose exec rspsrv_app_1 docker/commands/update.sh`

## Templates
- `sudo docker-compose exec rspsrv_app_1 docker/commands/template.sh`


## Port

`RSPSRV` docker mode uses `HAProxy` to load balance between two services of `RSPSRV` app and exposes one port to the host. If you want to change this port you can modify the `tb_ha` section of `docker-compose.yml` file.

- `http` on `8080`