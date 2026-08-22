PKG_NAME ?= iss-equipment-utilities
VERSION ?= 1.1
ARCH ?= all
BUILD_DIR = build/$(PKG_NAME)_$(VERSION)-1_$(ARCH)

all: deb

clean:
	rm -rf build/
	rm -f *.deb

deb: clean
	mkdir -p $(BUILD_DIR)/DEBIAN
	mkdir -p $(BUILD_DIR)/opt/$(PKG_NAME)
	mkdir -p $(BUILD_DIR)/usr/bin

	# Copy source files
	cp -r equipment_drivers $(BUILD_DIR)/opt/$(PKG_NAME)/
	cp iss_pdu_utility $(BUILD_DIR)/opt/$(PKG_NAME)/
	cp iss_terminal_utility $(BUILD_DIR)/opt/$(PKG_NAME)/
	cp iss_daq_utility $(BUILD_DIR)/opt/$(PKG_NAME)/

	# Make symlinks in /usr/bin
	ln -s /opt/$(PKG_NAME)/iss_pdu_utility $(BUILD_DIR)/usr/bin/iss_pdu_utility
	ln -s /opt/$(PKG_NAME)/iss_terminal_utility $(BUILD_DIR)/usr/bin/iss_terminal_utility
	ln -s /opt/$(PKG_NAME)/iss_daq_utility $(BUILD_DIR)/usr/bin/iss_daq_utility

	# Create DEBIAN/control
	echo "Package: $(PKG_NAME)" > $(BUILD_DIR)/DEBIAN/control
	echo "Version: $(VERSION)-1" >> $(BUILD_DIR)/DEBIAN/control
	echo "Architecture: $(ARCH)" >> $(BUILD_DIR)/DEBIAN/control
	echo "Maintainer: Equipment Admin <admin@example.com>" >> $(BUILD_DIR)/DEBIAN/control
	echo "Description: Equipment Utilities for PDU, TS, and DAQ" >> $(BUILD_DIR)/DEBIAN/control
	echo "Depends: python3" >> $(BUILD_DIR)/DEBIAN/control

	# Build the deb
	dpkg-deb --build $(BUILD_DIR)
	mv build/*.deb .
	@echo "Package built successfully."

deb-docker:
	docker run --rm -v $$(pwd):/app -w /app ubuntu:latest bash -c "apt-get update && apt-get install -y make build-essential dpkg-dev && make deb"

release: deb
	@echo "Publishing GitHub release for v$(VERSION)..."
	@if ! command -v gh > /dev/null 2>&1; then echo "Error: GitHub CLI (gh) is not installed."; exit 1; fi
	@if gh release view v$(VERSION) > /dev/null 2>&1; then \
		echo "Release v$(VERSION) already exists on GitHub. Uploading and updating .deb asset..."; \
		gh release upload --clobber v$(VERSION) *.deb; \
	else \
		echo "Creating new GitHub release v$(VERSION)..."; \
		gh release create v$(VERSION) *.deb --title "Release v$(VERSION)" --notes "Automated release of v$(VERSION)"; \
	fi
