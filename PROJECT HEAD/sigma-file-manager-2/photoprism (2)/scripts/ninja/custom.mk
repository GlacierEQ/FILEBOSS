# Custom build targets for PhotoPrism

# Build with optimized settings
.PHONY: optimize
optimize:
	@echo "Building with optimized settings..."
	@$(MAKE) -f Makefile.ninja CMAKE_BUILD_TYPE=Release build

# Build with debug settings
.PHONY: debug
debug:
	@echo "Building with debug settings..."
	@$(MAKE) -f Makefile.ninja CMAKE_BUILD_TYPE=Debug build

# Build with race detection
.PHONY: race
race:
	@echo "Building with race detection..."
	@GO_RACE_FLAGS="-race" $(MAKE) -f Makefile.ninja build

# Generate documentation
.PHONY: docs
docs:
	@echo "Generating documentation..."
	@go run cmd/photoprism/photoprism.go generate docs
	@cd frontend && npm run docs

# Build for multiple platforms
.PHONY: cross-platform
cross-platform:
	@echo "Building for multiple platforms..."
	@for os in linux darwin windows; do \
		for arch in amd64 arm64; do \
			echo "Building for $$os/$$arch..."; \
			GOOS=$$os GOARCH=$$arch go build -o $(BUILD_DIR)/photoprism-$$os-$$arch$(if $(filter windows,$$os),.exe,) ./cmd/photoprism; \
		done; \
	done

# Create distribution packages
.PHONY: dist
dist: build
	@echo "Creating distribution packages..."
	@$(MKDIR) $(BUILD_DIR)/dist
	@tar czf $(BUILD_DIR)/dist/photoprism-$(shell date +%Y%m%d).tar.gz -C $(INSTALL_DIR) .
	@zip -r $(BUILD_DIR)/dist/photoprism-$(shell date +%Y%m%d).zip $(INSTALL_DIR)
	@echo "Packages created in $(BUILD_DIR)/dist"

# Build with Docker
.PHONY: docker-build
docker-build:
	@echo "Building with Docker..."
	@docker run --rm -v $(PWD):/app -w /app photoprism/develop:latest make -f Makefile.ninja build

# Deploy to Kubernetes
.PHONY: k8s-deploy
k8s-deploy: docker
	@echo "Deploying to Kubernetes..."
	@kubectl apply -f kubernetes/photoprism.yaml

# Create a development environment
.PHONY: dev-env
dev-env:
	@echo "Setting up development environment..."
	@go mod download
	@cd frontend && npm ci
	@echo "Development environment is ready"

# Create a release
.PHONY: release
release:
	@echo "Creating new release..."
	@read -p "Enter version (e.g., 1.0.0): " version; \
	git tag -a "v$$version" -m "Release v$$version"; \
	git push origin "v$$version"

# Benchmark the application
.PHONY: bench
bench:
	@echo "Running benchmarks..."
	@go test -bench=. -benchmem ./...
