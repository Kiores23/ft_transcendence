DC_FILE	= ./srcs/docker-compose.yml

start:
	@echo "Building and starting Docker containers and volumes"
	docker-compose -f $(DC_FILE) up -d --build --remove-orphans

stop:
	@echo "Shutting down Docker containers"
	docker-compose -f $(DC_FILE) stop --timeout=20

fclean:
	@echo "Removing volumes and built containers"
	docker volume rm $$(docker volume ls -q) && docker system prune -af

remove_db:
	@echo "Removing volumes content"

re: stop start

.PHONY: start fclean re remove_db
