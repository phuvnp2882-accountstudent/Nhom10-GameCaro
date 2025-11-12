import socket
import threading

PORT = 5002
BROADCAST_PORT = 5001

class Room:
    def __init__(self, player1_addr):
        self.players = [player1_addr]
        self.ready = False
        self.game_over = False

    def add_player(self, player2_addr):
        self.players.append(player2_addr)
        self.ready = True
        self.game_over = False

    def get_opponent(self, addr):
        if len(self.players) < 2:
            return None
        return self.players[1] if addr == self.players[0] else self.players[0]

    def reset(self):
        self.game_over = False

class CaroServerMulti:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", PORT))
        self.broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.broadcast_sock.bind(("", BROADCAST_PORT))
        self.rooms = []
        self.addr_to_room = {}
        print("Server đã sẵn sàng!")
    
    def listen_broadcast(self):
        while True:
            try:
                data, addr = self.broadcast_sock.recvfrom(1024)
                if data.decode() == "FIND_CARO_SERVER":
                    print(f"Yêu cầu tìm phòng từ {addr}")
                    self.broadcast_sock.sendto(b"CARO_SERVER_HERE", addr)
            except Exception as e:
                print(f"Lỗi broadcast: {e}")
                continue

    def listen_game(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
                msg = data.decode()
                
                if msg == "JOIN_ROOM":
                    print(f"{addr} yêu cầu vào phòng")
                    if addr in self.addr_to_room:
                        continue
                        
                    # Ghép với client lẻ hoặc tạo phòng mới
                    if self.rooms and not self.rooms[-1].ready:
                        self.rooms[-1].add_player(addr)
                        self.addr_to_room[addr] = self.rooms[-1]
                        self.addr_to_room[self.rooms[-1].players[0]] = self.rooms[-1]
                        
                        # Thông báo cho cả 2 client đã sẵn sàng
                        for idx, player in enumerate(self.rooms[-1].players):
                            role = "X" if idx == 0 else "O"
                            self.sock.sendto(f"START|{role}".encode(), player)
                        print(f"Phòng mới: {self.rooms[-1].players}")
                    else:
                        room = Room(addr)
                        self.rooms.append(room)
                        self.addr_to_room[addr] = room
                    
                elif msg == "EXIT":
                    self.handle_exit(addr)
                
                elif msg == "NEW_GAME":
                    self.handle_new_game(addr)
                
                elif msg.startswith("MOVE"):
                    self.handle_move(addr, msg)
                    
            except Exception as e:
                print(f"Lỗi xử lý game: {e}")

    def handle_exit(self, addr):
        if addr in self.addr_to_room:
            room = self.addr_to_room[addr]
            opponent = room.get_opponent(addr)
            # Thông báo cho đối thủ nếu có
            if opponent:
                self.sock.sendto(b"OPPONENT_DISCONNECTED", opponent)
            # Xóa phòng
            if room in self.rooms:
                self.rooms.remove(room)
            del self.addr_to_room[addr]
            if opponent and opponent in self.addr_to_room:
                del self.addr_to_room[opponent]

    def handle_new_game(self, addr):
        if addr in self.addr_to_room:
            room = self.addr_to_room[addr]
            if room.ready:
                opponent = room.get_opponent(addr)
                room.reset()
                # Thông báo cho cả hai người chơi nếu có đối thủ
                self.sock.sendto(b"NEW_GAME", addr)
                if opponent:
                    self.sock.sendto(b"NEW_GAME", opponent)

    def handle_move(self, addr, msg):
        if addr in self.addr_to_room:
            room = self.addr_to_room[addr]
            if room.ready and not room.game_over:
                opponent = room.get_opponent(addr)
                if opponent:
                    print(f"Nhận MOVE từ {addr}, gửi cho {opponent}: {msg}")
                    self.sock.sendto(msg.encode(), opponent)

    def run(self):
        threading.Thread(target=self.listen_broadcast, daemon=True).start()
        self.listen_game()

if __name__ == "__main__":
    CaroServerMulti().run()
                    