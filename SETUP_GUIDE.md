# 📖 Hướng Dẫn Cài Đặt Môi Trường & Build EmuDrop (Cross-Platform Setup Guide)

Tài liệu này hướng dẫn chi tiết cách thiết lập môi trường phát triển (Local Development) và biên dịch đóng gói (Cross-Compilation Build) ứng dụng **EmuDrop** trên các hệ điều hành phổ biến: **macOS**, **Linux (Ubuntu/Debian)** và **Windows (WSL2 / Native)**.

---

## 📑 Mục lục
1. [Yêu cầu chung & Kiến trúc](#-yêu-cầu-chung--kiến-trúc)
2. [Cài đặt môi trường trên macOS (Apple Silicon M1/M2/M3 & Intel)](#-1-cài-đặt-trên-macos-apple-silicon--intel)
3. [Cài đặt môi trường trên Linux (Ubuntu / Debian)](#-2-cài-đặt-trên-linux-ubuntudebian)
4. [Cài đặt môi trường trên Windows (Native & WSL2)](#-3-cài-đặt-trên-windows-wsl2--native)
5. [Tải cơ sở dữ liệu Catalog (Database Setup)](#-4-tải-cơ-sở-dữ-liệu-catalog-database-setup)
6. [Chạy thử nghiệm Local (Testing & Controls)](#-5-chạy-thử-nghiệm-local-testing--controls)
7. [Hướng dẫn Build nhị phân cho máy cầm tay (TrimUI / Anbernic)](#-6-hướng-dẫn-build-nhị-phân-cho-máy-cầm-tay)
8. [Cài đặt file sau khi build vào máy chơi game](#-7-cài-đặt-file-sau-khi-build-vào-máy-chơi-game)
9. [Xử lý lỗi thường gặp (Troubleshooting & FAQs)](#-8-xử-lý-lỗi-thường-gặp-troubleshooting--faqs)

---

## 🎯 Yêu cầu chung & Kiến trúc

* **Ngôn ngữ**: Python 3.9+ (khuyên dùng Python 3.9 đến 3.11).
* **Đồ họa & Âm thanh**: SDL2, SDL2_image, SDL2_ttf.
* **Cơ sở dữ liệu**: SQLite3 (hỗ trợ FTS5).
* **Docker / Podman**: Cần thiết nếu muốn build file nhị phân (Binary) cho hệ điều hành Linux ARM64 của các máy chơi game cầm tay.

---

## 🍏 1. Cài đặt trên macOS (Apple Silicon & Intel)

### Bước 1.1: Cài đặt Homebrew (nếu chưa có)
Mở ứng dụng Terminal và chạy:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Bước 1.2: Cài đặt các thư viện SDL2 hệ thống
```bash
brew install sdl2 sdl2_image sdl2_ttf
```

### Bước 1.3: Tạo môi trường ảo Python và cài đặt thư viện
Tại thư mục gốc của dự án `EmuDrop`:
```bash
# Tạo môi trường ảo
python3 -m venv .venv

# Kích hoạt môi trường ảo
source .venv/bin/activate

# Cập nhật pip và cài đặt dependencies
pip install --upgrade pip
pip install -r requirements.txt python-dotenv
```

---

## 🐧 2. Cài đặt trên Linux (Ubuntu/Debian)

### Bước 2.1: Cài đặt các gói hệ thống và thư viện SDL2
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv \
    libsdl2-dev libsdl2-image-dev libsdl2-ttf-dev \
    build-essential curl git
```

### Bước 2.2: Tạo môi trường ảo và cài đặt Python packages
```bash
# Tạo môi trường ảo
python3 -m venv .venv

# Kích hoạt môi trường ảo
source .venv/bin/activate

# Cài đặt thư viện
pip install --upgrade pip
pip install -r requirements.txt python-dotenv
```

---

## 🪟 3. Cài đặt trên Windows (WSL2 & Native)

### 🔹 Cách 1: Sử dụng WSL2 (Khuyên dùng - tiện cho cả Test và Build)
1. Cài đặt WSL2 với Ubuntu:
   ```powershell
   wsl --install -d Ubuntu
   ```
2. Mở terminal Ubuntu trong WSL2 và làm theo các bước tại phần [2. Cài đặt trên Linux (Ubuntu/Debian)](#-2-cài-đặt-trên-linux-ubuntudebian).

### 🔹 Cách 2: Chạy trực tiếp trên Windows Native
1. Tải và cài đặt **Python 3.10/3.11** từ [python.org](https://www.python.org/downloads/) (nhớ tick chọn `"Add Python to PATH"`).
2. Mở Command Prompt hoặc PowerShell tại thư mục `EmuDrop`:
   ```cmd
   python -m venv .venv
   .venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt python-dotenv
   ```
*(Gói `pysdl2-dll` trong `requirements.txt` sẽ tự động cung cấp file `.dll` của SDL2 trên Windows).*

---

## 💾 4. Tải cơ sở dữ liệu Catalog (Database Setup)

Ứng dụng cần file cơ sở dữ liệu `assets/catalog.db` chứa danh mục hàng chục nghìn game retro.

### Tải tự động bằng lệnh:
* **macOS / Linux / WSL2**:
  ```bash
  curl -L -o assets/catalog.db "https://github.com/ahmadteeb/EmuDrop/releases/download/v2.0.0-db/catalog-v2.0.0.db"
  ```
* **PowerShell (Windows)**:
  ```powershell
  Invoke-WebRequest -Uri "https://github.com/ahmadteeb/EmuDrop/releases/download/v2.0.0-db/catalog-v2.0.0.db" -OutFile "assets\catalog.db"
  ```

---

## 🕹️ 5. Chạy thử nghiệm Local (Testing & Controls)

### Khởi chạy ứng dụng:
```bash
# Đảm bảo đã kích hoạt virtualenv (.venv)
python main.py
```

### Bảng phím điều khiển khi test trên máy tính:
| Phím trên Bàn phím | Nút tương ứng trên Gamepad | Chức năng |
| :--- | :--- | :--- |
| `Mũi tên (Up/Down/Left/Right)` | `D-Pad / Analog` | Di chuyển lựa chọn menu / game |
| `Phím A` | `Nút A` | Chọn / Mở mục / Xác nhận |
| `Phím B` | `Nút B` | Quay lại menu trước (Back) |
| `Phím Y` | `Nút Y` | Bật/Tắt bàn phím ảo (Virtual Keyboard) |
| `Phím X` | `Nút X` | Mở màn hình quản lý tải xuống (Downloads) |
| `Phím L / R` | `Nút L / R (Bumper)` | Chuyển trang nhanh (Page Up/Down) |

*(Bạn có thể cắm trực tiếp bất kỳ tay cầm Gamepad USB hoặc Bluetooth nào như PS4/PS5, Xbox, Switch Pro Controller; ứng dụng sẽ tự động nhận diện).*

---

## 🔨 6. Hướng dẫn Build nhị phân cho máy cầm tay

Để tạo file chạy thực thi `.bin` hoặc nhị phân ARM64 cho máy cầm tay (*TrimUI Smart Pro, TrimUI Brick, Anbernic RG35XX*), chúng ta sử dụng Docker toolchain đã có sẵn trong dự án:

### Bước 6.1: Cài đặt Docker
* **macOS**: Cài đặt [Docker Desktop cho Mac](https://www.docker.com/products/docker-desktop/) hoặc [OrbStack](https://orbstack.dev/).
* **Linux**: `sudo apt install docker.io && sudo usermod -aG docker $USER`.
* **Windows**: Cài đặt Docker Desktop với WSL2 Backend.

### Bước 6.2: Biên dịch và đóng gói bằng lệnh 1-Click (Khuyên dùng)
Tại thư mục gốc của dự án `EmuDrop`:

```bash
# Xem danh sách tất cả tùy chọn đóng gói
make help

# Đóng gói cho NextUI (TrimUI Brick & Smart Pro -> release/EmuDrop.pak)
make package-nextui

# Đóng gói cho CrossMix OS (TrimUI -> release/CrossMix/EmuDrop)
make package-crossmix

# Đóng gói cho Stock OS (TrimUI -> release/StockOS/EmuDrop)
make package-stock

# Đóng gói cho Knulli OS (TrimUI & Anbernic -> release/Knulli/EmuDrop)
make package-knulli

# Đóng gói TẤT CẢ các hệ điều hành cùng lúc vào thư mục release/
make package-all
```

Sau khi chạy lệnh, toàn bộ gói hoàn chỉnh (kèm binary ARM64, assets, script khởi động và file zip) sẽ xuất hiện sẵn trong thư mục **`release/`**!

---

## 📲 7. Cài đặt file sau khi build vào máy chơi game

Tùy vào hệ điều hành mà máy chơi game của bạn đang sử dụng:

### 🎮 Trường hợp 1: CrossMix OS / Stock OS (TrimUI Smart Pro, TrimUI Brick)
1. Copy file `dist/EmuDrop` vừa build vào thư mục:
   `platform/Trimui Smart Pro/EmuDrop/` (ghi đè file cũ nếu có).
2. Copy toàn bộ thư mục `EmuDrop` vào thẻ nhớ MicroSD theo đường dẫn:
   ```text
   [Thẻ nhớ SDCARD]/Apps/EmuDrop/
   ```
3. Cắm thẻ nhớ vào máy TrimUI $\rightarrow$ Vào mục **Apps** $\rightarrow$ Chọn biểu tượng **EmuDrop** để mở.

### 🎮 Trường hợp 2: Knulli OS / Batocera (TrimUI, Anbernic RG35XX series)
1. Copy file `dist/EmuDrop` vừa build vào thư mục:
   `platform/Trimui Smart Pro/EmuDropKnulli/`.
2. Copy toàn bộ thư mục `EmuDropKnulli` vào thẻ nhớ MicroSD theo đường dẫn:
   ```text
   [Thẻ nhớ SDCARD]/roms/pygame/EmuDrop/
   ```
3. Cập nhật Game List trên giao diện Knulli $\rightarrow$ Vào mục **Pygame** $\rightarrow$ Khởi chạy **EmuDrop**.

### 🎮 Trường hợp 3: NextUI (MinUI / NextUI trên TrimUI Smart Pro / Brick)
1. Copy file `dist/EmuDrop` vừa build vào thư mục mẫu:
   `platform/Trimui Smart Pro/EmuDropNextUI/` (hoặc đổi tên thư mục thành `EmuDrop.pak`).
2. Copy thư mục `EmuDropNextUI` và đổi tên thành `EmuDrop.pak` trên thẻ nhớ theo đường dẫn:
   ```text
   [Thẻ nhớ SDCARD]/Tools/EmuDrop.pak/
   (hoặc [Thẻ nhớ SDCARD]/Emus/EmuDrop.pak/)
   ```
3. Trên máy chạy NextUI: Vào mục **Tools** hoặc **Emus** $\rightarrow$ Chọn **EmuDrop** để mở.

---

## ❓ 8. Xử lý lỗi thường gặp (Troubleshooting & FAQs)

### 1. Lỗi `ModuleNotFoundError: No module named 'dotenv'`
* **Nguyên nhân**: Thiếu package `python-dotenv`.
* **Cách khắc phục**: Chạy `pip install python-dotenv`.

### 2. Lỗi `sdl2.ext.common.SDLError` hoặc không tìm thấy SDL2 thư viện
* **Trên macOS**: Chạy `brew install sdl2 sdl2_image sdl2_ttf`.
* **Trên Linux**: Chạy `sudo apt install libsdl2-dev libsdl2-image-dev libsdl2-ttf-dev`.

### 3. Không hiển thị danh sách game (Danh sách trống rỗng)
* **Nguyên nhân**: Thiếu file cơ sở dữ liệu `assets/catalog.db`.
* **Cách khắc phục**: Thực hiện bước [4. Tải cơ sở dữ liệu Catalog](#-4-tải-cơ-sở-dữ-liệu-catalog-database-setup).

### 4. Ứng dụng không chạy được trên TrimUI (bấm vào văng ra ngoài)
* **Nguyên nhân**: Chưa cấp quyền thực thi cho các file script hoặc binary trên thẻ nhớ.
* **Cách khắc phục**: Đảm bảo file `launch.sh` và binary `EmuDrop` có quyền thực thi (`chmod +x launch.sh EmuDrop`).
