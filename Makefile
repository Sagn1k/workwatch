.PHONY: build build-universal clean clean-all install dev release run run-log

VERSION := 1.0.0
BINARY_NAME := workwatch
DIST_DIR := dist
BUILD_DIR := build
RELEASE_DIR := release
VENV := .venv
PYTHON ?= python3

# Create a build venv (PEP 668 blocks `pip install` against Homebrew Python).
$(VENV)/bin/pyinstaller:
	@echo "🧪 Creating build venv at $(VENV)..."
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --quiet --upgrade pip
	$(VENV)/bin/pip install --quiet pyinstaller
	$(VENV)/bin/pip install --quiet -e .

# Build standalone binary with PyInstaller
build: $(VENV)/bin/pyinstaller
	@echo "🔨 Building WorkWatch v$(VERSION) binary..."
	$(VENV)/bin/pyinstaller workwatch.spec --clean --noconfirm
	@echo "✅ Binary built: $(DIST_DIR)/$(BINARY_NAME)"
	@ls -lh $(DIST_DIR)/$(BINARY_NAME)

# Build for both architectures (run on each machine or use universal2)
build-universal: $(VENV)/bin/pyinstaller
	@echo "🔨 Building universal binary..."
	$(VENV)/bin/pyinstaller workwatch.spec --clean --noconfirm
	@echo "✅ Universal binary: $(DIST_DIR)/$(BINARY_NAME)"

# Create release artifacts
release: build
	@mkdir -p $(RELEASE_DIR)
	@ARCH=$$(uname -m); \
	TAR_NAME="workwatch-$(VERSION)-darwin-$$ARCH.tar.gz"; \
	cd $(DIST_DIR) && tar -czf ../$(RELEASE_DIR)/$$TAR_NAME $(BINARY_NAME); \
	echo "📦 Release: $(RELEASE_DIR)/$$TAR_NAME"; \
	shasum -a 256 ../$(RELEASE_DIR)/$$TAR_NAME

# Install locally. `ditto` preserves the ad-hoc code signature (which
# macOS 26+ strictly validates); plain `cp` breaks it and the binary
# is SIGKILL'd with "Code Signature Invalid" on launch. `sudo` is
# required because `ditto` unlinks the destination, and /usr/local/bin
# is root-owned.
install: build
	@echo "📥 Installing to /usr/local/bin/$(BINARY_NAME) (needs sudo)..."
	sudo rm -f /usr/local/bin/$(BINARY_NAME)
	sudo ditto $(DIST_DIR)/$(BINARY_NAME) /usr/local/bin/$(BINARY_NAME)
	sudo chown $${USER}:staff /usr/local/bin/$(BINARY_NAME)
	@echo "✅ Installed! Run 'workwatch' from anywhere."

# Install from source into the build venv (no global pip pollution).
dev: $(VENV)/bin/pyinstaller
	@echo "✅ Editable install available at $(VENV)/bin/python -m workwatch"

# Clean build artifacts (keeps the venv; use `make clean-all` to nuke it too).
clean:
	rm -rf $(BUILD_DIR) $(DIST_DIR) $(RELEASE_DIR) *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "🧹 Cleaned."

clean-all: clean
	rm -rf $(VENV)
	@echo "🧹 Removed venv."

# Run directly (dev mode)
run: $(VENV)/bin/pyinstaller
	$(VENV)/bin/python -m workwatch

run-log: $(VENV)/bin/pyinstaller
	$(VENV)/bin/python -m workwatch log
