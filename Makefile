.PHONY: help build-toolchain build-binary package-nextui package-crossmix package-stock package-knulli package-all run run-brick run-smart-pro run-rg35xx clean

DOCKER := $(shell command -v docker 2> /dev/null)
PODMAN := $(shell command -v podman 2> /dev/null)
TOOL := $(if $(DOCKER),docker,$(if $(PODMAN),podman,))

TOOLCHAIN_NAME := crossmix-toolchain
WORKSPACE_DIR := $(shell pwd)
RELEASE_DIR := $(WORKSPACE_DIR)/release
PYTHON := $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)

help:
	@echo "🎮 EmuDrop Build, Debug & Packaging System"
	@echo "=========================================="
	@echo "🖥️  Chạy Test & Debug trực tiếp trên máy tính:"
	@echo "  make run-brick          - Mở giao diện giả lập TrimUI Brick (1024x768 4:3)"
	@echo "  make run-smart-pro      - Mở giao diện giả lập TrimUI Smart Pro (1280x720 16:9)"
	@echo "  make run-rg35xx         - Mở giao diện giả lập Anbernic RG35XX (640x480 4:3)"
	@echo "  make run                - Mở giao diện mặc định"
	@echo ""
	@echo "📦 Đóng gói cài đặt ra thiết bị thật (Linux ARM64):"
	@echo "  make package-nextui     - Đóng gói cho NextUI (tạo release/EmuDrop.pak cho TrimUI Brick / Smart Pro)"
	@echo "  make package-crossmix   - Đóng gói cho CrossMix OS (tạo release/CrossMix/EmuDrop)"
	@echo "  make package-stock      - Đóng gói cho Stock OS (tạo release/StockOS/EmuDrop)"
	@echo "  make package-knulli     - Đóng gói cho Knulli OS (tạo release/Knulli/EmuDrop)"
	@echo "  make package-all        - Đóng gói TẤT CẢ các hệ điều hành cùng lúc vào release/"
	@echo "  make clean              - Dọn dẹp thư mục build/, dist/, release/"

run-brick:
	@echo "🚀 Khởi chạy EmuDrop ở chế độ giả lập màn hình TrimUI Brick (1024x768 4:3)..."
	@$(PYTHON) main.py --device brick

run-smart-pro:
	@echo "🚀 Khởi chạy EmuDrop ở chế độ giả lập màn hình TrimUI Smart Pro (1280x720 16:9)..."
	@$(PYTHON) main.py --device smart-pro

run-rg35xx:
	@echo "🚀 Khởi chạy EmuDrop ở chế độ giả lập màn hình Anbernic RG35XX (640x480 4:3)..."
	@$(PYTHON) main.py --device rg35xx

run:
	@$(PYTHON) main.py

.check-tool:
	@if [ -z "$(TOOL)" ]; then \
		echo "❌ Lỗi: Cần cài đặt Docker hoặc Podman!"; exit 1; \
	fi

build-toolchain: .check-tool
	@echo "🔨 Đang kiểm tra/build Docker toolchain image: $(TOOLCHAIN_NAME)..."
	@cd tools/toolchain && $(TOOL) build --platform linux/arm64 -t $(TOOLCHAIN_NAME) .
	@touch tools/toolchain/.build
	@echo "✅ Build Toolchain hoàn tất!"

build-binary: build-toolchain
	@echo "🔨 Đang biên dịch EmuDrop binary ARM64 với PyInstaller..."
	@$(TOOL) run --rm --platform linux/arm64 -v "$(WORKSPACE_DIR)":/root/workspace $(TOOLCHAIN_NAME) \
		/bin/bash -c "pyinstaller --onefile --noconsole --name EmuDrop main.py"
	@echo "✅ File binary ARM64 đã được tạo tại: dist/EmuDrop"

package-nextui: build-binary
	@echo "📦 Đang đóng gói cho NextUI (TrimUI Brick & Smart Pro)..."
	@mkdir -p "$(RELEASE_DIR)/EmuDrop.pak"
	@cp -rf "platform/Trimui Smart Pro/EmuDropNextUI/." "$(RELEASE_DIR)/EmuDrop.pak/"
	@cp -rf "assets/images/." "$(RELEASE_DIR)/EmuDrop.pak/assets/images/"
	@cp -rf "assets/fonts/." "$(RELEASE_DIR)/EmuDrop.pak/assets/fonts/"
	@cp -f "dist/EmuDrop" "$(RELEASE_DIR)/EmuDrop.pak/EmuDrop"
	@chmod +x "$(RELEASE_DIR)/EmuDrop.pak/EmuDrop" "$(RELEASE_DIR)/EmuDrop.pak/launch.sh" "$(RELEASE_DIR)/EmuDrop.pak/app_ota.sh" "$(RELEASE_DIR)/EmuDrop.pak/db_ota.sh"
	@cd "$(RELEASE_DIR)" && zip -r "EmuDrop_NextUI.zip" "EmuDrop.pak" > /dev/null 2>&1 || true
	@echo "✅ Đóng gói NextUI hoàn tất!"
	@echo "👉 Thư mục: release/EmuDrop.pak"
	@echo "👉 File nén: release/EmuDrop_NextUI.zip"

package-crossmix: build-binary
	@echo "📦 Đang đóng gói cho CrossMix OS (TrimUI Smart Pro / Brick)..."
	@mkdir -p "$(RELEASE_DIR)/CrossMix/EmuDrop"
	@cp -rf "platform/Trimui Smart Pro/EmuDrop/." "$(RELEASE_DIR)/CrossMix/EmuDrop/"
	@cp -rf "assets/images/." "$(RELEASE_DIR)/CrossMix/EmuDrop/assets/images/"
	@cp -rf "assets/fonts/." "$(RELEASE_DIR)/CrossMix/EmuDrop/assets/fonts/"
	@cp -f "dist/EmuDrop" "$(RELEASE_DIR)/CrossMix/EmuDrop/EmuDrop"
	@chmod +x "$(RELEASE_DIR)/CrossMix/EmuDrop/EmuDrop" "$(RELEASE_DIR)/CrossMix/EmuDrop/launch.sh" "$(RELEASE_DIR)/CrossMix/EmuDrop/app_ota.sh" "$(RELEASE_DIR)/CrossMix/EmuDrop/db_ota.sh"
	@cd "$(RELEASE_DIR)/CrossMix" && zip -r "../EmuDrop_CrossMix.zip" "EmuDrop" > /dev/null 2>&1 || true
	@echo "✅ Đóng gói CrossMix hoàn tất tại: release/CrossMix/EmuDrop"

package-stock: build-binary
	@echo "📦 Đang đóng gói cho Stock OS (TrimUI Smart Pro / Brick)..."
	@mkdir -p "$(RELEASE_DIR)/StockOS/EmuDrop"
	@cp -rf "platform/Trimui Smart Pro/EmuDropStockOS/." "$(RELEASE_DIR)/StockOS/EmuDrop/"
	@cp -rf "assets/images/." "$(RELEASE_DIR)/StockOS/EmuDrop/assets/images/"
	@cp -rf "assets/fonts/." "$(RELEASE_DIR)/StockOS/EmuDrop/assets/fonts/"
	@cp -f "dist/EmuDrop" "$(RELEASE_DIR)/StockOS/EmuDrop/EmuDrop"
	@chmod +x "$(RELEASE_DIR)/StockOS/EmuDrop/EmuDrop" "$(RELEASE_DIR)/StockOS/EmuDrop/launch.sh" "$(RELEASE_DIR)/StockOS/EmuDrop/app_ota.sh" "$(RELEASE_DIR)/StockOS/EmuDrop/db_ota.sh"
	@cd "$(RELEASE_DIR)/StockOS" && zip -r "../EmuDrop_StockOS.zip" "EmuDrop" > /dev/null 2>&1 || true
	@echo "✅ Đóng gói Stock OS hoàn tất tại: release/StockOS/EmuDrop"

package-knulli: build-binary
	@echo "📦 Đang đóng gói cho Knulli OS (TrimUI / Anbernic RG35XX)..."
	@mkdir -p "$(RELEASE_DIR)/Knulli/EmuDrop"
	@cp -rf "platform/Trimui Smart Pro/EmuDropKnulli/." "$(RELEASE_DIR)/Knulli/EmuDrop/"
	@cp -rf "assets/images/." "$(RELEASE_DIR)/Knulli/EmuDrop/assets/images/"
	@cp -rf "assets/fonts/." "$(RELEASE_DIR)/Knulli/EmuDrop/assets/fonts/"
	@cp -f "dist/EmuDrop" "$(RELEASE_DIR)/Knulli/EmuDrop/EmuDrop"
	@chmod +x "$(RELEASE_DIR)/Knulli/EmuDrop/EmuDrop" "$(RELEASE_DIR)/Knulli/EmuDrop/EmuDrop.pygame"
	@cd "$(RELEASE_DIR)/Knulli" && zip -r "../EmuDrop_Knulli.zip" "EmuDrop" > /dev/null 2>&1 || true
	@echo "✅ Đóng gói Knulli hoàn tất tại: release/Knulli/EmuDrop"

package-all: package-nextui package-crossmix package-stock package-knulli
	@echo ""
	@echo "🎉 ĐÃ ĐÓNG GÓI HOÀN TẤT CHO TẤT CẢ CÁC THIẾT BỊ VÀ HỆ ĐIỀU HÀNH!"
	@echo "📂 Xem toàn bộ sản phẩm đầu ra tại thư mục: release/"

clean:
	@rm -rf build dist release *.spec
	@echo "🧹 Đã dọn dẹp sạch các thư mục build."
