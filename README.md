# 🎮 Game Caro (Multiplayer)

Đây là dự án game Cờ Caro (Gomoku) được lập trình bằng Python, cho phép hai người chơi thi đấu với nhau trong cùng một mạng nội bộ (mạng LAN).

Dự án sử dụng mô hình Client-Server, với giao diện đồ họa được xây dựng bằng Tkinter.



---

## 🚀 Tính năng chính

* **Chơi 2 người (Client-Server):** Một máy tính làm Server (máy chủ) và hai máy tính làm Client (người chơi).
* **Tự động tìm Server:** Client có thể tự động tìm thấy Server đang chạy trong cùng mạng LAN.
* **Giao diện đồ họa (GUI):** Sử dụng thư viện Tkinter để vẽ bàn cờ, quân cờ và hiển thị trạng thái game.
* **Luật chơi chuẩn:**
    * Thắng khi có 5 quân cờ liên tiếp theo hàng ngang, hàng dọc, hoặc đường chéo.
    * Áp dụng luật **chặn 2 đầu** (nước đi 5 quân nhưng bị chặn cả 2 đầu sẽ không được tính là thắng).
* **Xử lý đồng bộ:**
    * Luân phiên lượt đi (X đi trước, O đi sau).
    * Hiển thị nước đi của đối thủ theo thời gian thực.
    * Thông báo khi đối thủ thoát game.
* **Chơi lại:** Cả hai người chơi có thể đồng ý "Chơi Lại" sau khi ván đấu kết thúc.

---

## 🛠️ Công nghệ sử dụng

* **Ngôn ngữ:** Python 3
* **Giao diện:** Tkinter
* **Mạng (Networking):**
    * **Socket TCP/IP:** Dùng cho luồng giao tiếp chính của game (gửi nước đi, trạng thái).
    * **Socket UDP Broadcast:** Dùng cho tính năng "Tự động tìm Server".

---

## 💡 Mô hình hoạt động (Lý thuyết)

Dự án hoạt động theo mô hình **Client-Server**, bao gồm 1 Server (trọng tài) và 2 Client (người chơi). Luồng hoạt động được chia làm 2 giai đoạn:

### 1. Giai đoạn 1: Tìm kiếm Server (UDP Broadcast)

Do người dùng không biết trước IP của Server, chúng ta sử dụng UDP Broadcast để tự động tìm kiếm:

1.  **Client** (Người chơi) khởi động và gửi một tin nhắn `FIND_CARO_SERVER` ra toàn bộ mạng LAN (dùng `socket.SOCK_DGRAM` và `SO_BROADCAST`).
2.  **Server** (Trọng tài) luôn chạy một luồng (thread) riêng để lắng nghe tin nhắn broadcast này (`listen_broadcast`).
3.  Khi Server nhận được tin `FIND_CARO_SERVER`, nó sẽ gửi một tin nhắn `CARO_SERVER_HERE` trả lời trực tiếp về địa chỉ IP của Client đã hỏi.
4.  **Client** nhận được tin `CARO_SERVER_HERE`, lưu lại địa chỉ IP của Server và chuyển sang giai đoạn 2.

### 2. Giai đoạn 2: Chơi game (TCP/IP)

Sau khi đã biết IP của Server, Client chuyển sang dùng TCP để đảm bảo tin nhắn được gửi đi ổn định:

1.  **Client** tạo một kết nối `socket.SOCK_STREAM` (TCP) đến IP của Server.
2.  Client gửi tin nhắn `JOIN_ROOM`.
3.  **Server** quản lý các phòng (`class Room`).
    * Nếu chưa có ai đợi, Server tạo phòng mới và cho Client 1 vào chờ.
    * Nếu đã có người chờ, Server cho Client 2 vào và gửi tín hiệu `START` cho cả hai.
4.  Khi một Client thực hiện nước đi (`handle_click`), Client đó gửi tin nhắn `MOVE|row|col` cho Server.
5.  **Server** nhận nước đi, cập nhật trạng thái phòng, và **chuyển tiếp** (forward) tin nhắn `MOVE|row|col` đó cho Client còn lại.
6.  Client còn lại nhận được tin nhắn, vẽ nước đi của đối thủ lên bàn cờ (`listen_server`).

Tất cả các hành động khác (như `NEW_GAME`, `EXIT`) đều đi qua Server để đảm bảo cả hai máy luôn được đồng bộ.

---

## 📖 Hướng dẫn chạy

Để chơi game, tất cả các máy tính phải được kết nối vào **cùng một mạng LAN** (chung Wi-Fi hoặc chung dây cắm router).

> **Lưu ý:** Nếu muốn chơi qua Internet, tất cả người chơi phải cài đặt và tham gia chung một phòng trên phần mềm mạng LAN ảo (ví dụ: **Radmin VPN** hoặc **Hamachi**).

**Bước 1: Khởi động Server**
1.  Chọn một máy tính làm máy chủ.
2.  Trên máy đó, mở Terminal (CMD) và chạy file `caro_sever.py`:
    ```bash
    python caro_sever.py
    ```
3.  Server sẽ bắt đầu chạy và chờ kết nối.

**Bước 2: Người chơi tham gia**
1.  **Người chơi 1:** Trên máy tính của mình, chạy file `caro_client.py`:
    ```bash
    python caro_client.py
    ```
2.  **Người chơi 2:** Trên máy tính của mình, cũng chạy file `caro_client.py`:
    ```bash
    python caro_client.py
    ```

Ngay khi cả 2 người chơi chạy file client, chương trình sẽ tự động tìm thấy Server và tự động ghép cặp 2 bạn vào phòng. Ván game sẽ bắt đầu.

