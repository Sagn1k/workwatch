.PHONY: build clean install dev release

VERSION := 1.0.0
BINARY_NAME := workwatch
DIST_DIR := dist
BUILD_DIR := build
RELEASE_DIR := release

# Build standalone binary with PyInstaller
build:
	@echo "🔨 Building WorkWatch v$(VERSION) binary..."
	pip install pyinstaller --quiet
	pyinstaller workwatch.spec --clean --noconfirm
	@echo "✅ Binary built: $(DIST_DIR)/$(BINARY_NAME)"
	@ls -lh $(DIST_DIR)/$(BINARY_NAME)

# Build for both architectures (run on each machine or use universal2)
build-universal:
	@echo "🔨 Building universal binary..."
	pip install pyinstaller --quiet
	pyinstaller workwatch.spec --clean --noconfirm
	@echo "✅ Universal binary: $(DIST_DIR)/$(BINARY_NAME)"

# Create release artifacts
release: build
	@mkdir -p $(RELEASE_DIR)
	@ARCH=$$(uname -m); \
	TAR_NAME="workwatch-$(VERSION)-darwin-$$ARCH.tar.gz"; \
	cd $(DIST_DIR) && tar -czf ../$(RELEASE_DIR)/$$TAR_NAME $(BINARY_NAME); \
	echo "📦 Release: $(RELEASE_DIR)/$$TAR_NAME"; \
	shasum -a 256 ../$(RELEASE_DIR)/$$TAR_NAME

# Install locally
install: build
	@echo "📥 Installing to /usr/local/bin/$(BINARY_NAME)..."
	cp $(DIST_DIR)/$(BINARY_NAME) /usr/local/bin/$(BINARY_NAME)
	chmod +x /usr/local/bin/$(BINARY_NAME)
	@echo "✅ Installed! Run 'workwatch' from anywhere."

# Install from source (no binary, uses pip)
dev:
	pip install -e .

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR) $(DIST_DIR) $(RELEASE_DIR) *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "🧹 Cleaned."

# Run directly (dev mode)
run:
	python -m workwatch

run-log:
	python -m workwatch log
