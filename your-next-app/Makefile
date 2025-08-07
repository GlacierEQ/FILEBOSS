up:
	docker compose up --build

down:
	docker compose down

migrate:
	docker compose exec app npx prisma migrate dev

studio:
	docker compose exec app npx prisma studio

logs:
	docker compose logs -f app