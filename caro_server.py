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
        print("Server sẵn sàng!")

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
                    
                    