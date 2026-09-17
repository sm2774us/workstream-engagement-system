.PHONY: backend-install backend-run backend-test backend-lint rust-build rust-run rust-test frontend-install frontend-run frontend-build frontend-test proto up

backend-install:
	cd backend && pip install -r requirements.txt

backend-run:
	cd backend && uvicorn app.main:app --reload --port 8000

backend-test:
	cd backend && pytest -q

backend-lint:
	cd backend && ruff check app

rust-build:
	cd rust-engine && cargo build --release

rust-run:
	cd rust-engine && cargo run

rust-test:
	cd rust-engine && cargo test

proto:
	python -m grpc_tools.protoc -I rust-engine/proto --python_out=backend/app/generated --grpc_python_out=backend/app/generated rust-engine/proto/risk.proto

frontend-install:
	cd frontend && npm install

frontend-run:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-test:
	cd frontend && npm run test

up:
	docker compose up --build
