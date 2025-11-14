import socket
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import time

BOARD_SIZE = 15
CELL_SIZE = 32
PORT = 5002
BROADCAST_PORT = 5001

BG_COLOR = "#fff3e0"          # nền bàn cờ cam sáng dịu
GRID_COLOR = "#ffb74d"        # đường kẻ ô
HIGHLIGHT_COLOR = "#ffe0b2"   # vùng sáng
MY_TURN_COLOR = "#096b00"     # lượt mình (cam tươi)
OPP_TURN_COLOR = "#c62828"    # lượt đối thủ (đỏ đậm)
COLOR_X = "#c62828"           # X (cam đậm)
COLOR_O = "#0009ad"           # O (đỏ năng động)

class CaroClientMulti:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("🔥 GAME CARO - MULTIPLAYER 🔥")
        self.window.resizable(False, False)
        self.window.configure(bg=BG_COLOR)
        
        style = ttk.Style()
        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR, font=("Arial", 12))
        style.configure("TButton", font=("Arial", 10, "bold"), padding=6)
        
        # Frame chính
        self.main_frame = ttk.Frame(self.window, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame thông tin
        self.info_frame = ttk.Frame(self.main_frame)
        self.info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_label = ttk.Label(self.info_frame, text="Đang tìm server...", font=("Arial", 12, "bold"), foreground=MY_TURN_COLOR)
        self.status_label.pack(side=tk.LEFT)
        
        self.role_label = ttk.Label(self.info_frame, text="", font=("Arial", 12, "bold"))
        self.role_label.pack(side=tk.RIGHT)
        
        # Frame bàn cờ
        self.board_frame = ttk.Frame(self.main_frame)
        self.board_frame.pack()
        
        self.canvas = tk.Canvas(self.board_frame, width=BOARD_SIZE*CELL_SIZE, height=BOARD_SIZE*CELL_SIZE,
                                bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack()
        
        # Frame điều khiển
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.new_game_btn = ttk.Button(self.control_frame, text="CHƠI LẠI", command=self.new_game, state=tk.DISABLED)
        self.new_game_btn.pack(side=tk.LEFT)
        
        self.exit_btn = ttk.Button(self.control_frame, text="THOÁT GAME", command=self.exit_game)
        self.exit_btn.pack(side=tk.RIGHT)
        
        # Biến game
        self.board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.turn = None
        self.role = None
        self.server_addr = None
        self.game_over = False
        self.opponent_disconnected = False
        self.last_move = None
        self.win_line = None

        # Bind
        self.canvas.bind("<Button-1>", self.handle_click)
        self.window.protocol("WM_DELETE_WINDOW", self.exit_game)
        
        self.draw_board()
        
        # Socket + Threads
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", 0))
        
        threading.Thread(target=self.find_server_and_join, daemon=True).start()
        threading.Thread(target=self.listen_server, daemon=True).start()

    def draw_board(self):
        self.canvas.delete("grid")
        for i in range(BOARD_SIZE):
            self.canvas.create_line(i*CELL_SIZE, 0, i*CELL_SIZE, BOARD_SIZE*CELL_SIZE, fill=GRID_COLOR, tags="grid")
            self.canvas.create_line(0, i*CELL_SIZE, BOARD_SIZE*CELL_SIZE, i*CELL_SIZE, fill=GRID_COLOR, tags="grid")
        self.redraw_pieces()

    def redraw_pieces(self):
        self.canvas.delete("piece")
        self.canvas.delete("highlight")
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if self.board[i][j]:
                    highlight_last_move = (self.last_move == (i, j)) if self.last_move else False 
                    self.draw_piece(i, j, self.board[i][j], highlight=highlight_last_move)
        
        if self.win_line:
            self.highlight_win_line(self.win_line)

    def handle_click(self, event):
        if self.role is None or self.turn != self.role or self.game_over or not self.server_addr or self.opponent_disconnected:
            if self.role is None:
                print("Chưa gán vai trò (X/O). Vui lòng đợi Server ghép cặp.")
            return
        
        row, col = event.y // CELL_SIZE, event.x // CELL_SIZE
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE and self.board[row][col] is None:
            self.board[row][col] = self.role
            self.last_move = (row, col)
            self.redraw_pieces()
            self.animate_piece(row, col, self.role)
            self.send_move(row, col)
            win_line = self.check_win(row, col, self.role)
            if win_line:
                self.game_over = True
                self.win_line = win_line
                self.redraw_pieces()
                self.status_label.config(text="🔥 Bạn đã thắng rồi!", foreground=MY_TURN_COLOR)
                self.new_game_btn.config(state=tk.NORMAL)
                messagebox.showinfo("Chiến thắng!", "Chúc mừng! Bạn đã thắng trận đấu! 🏆")
            else:
                self.turn = "O" if self.role == "X" else "X"
                self.status_label.config(text="Đến lượt đối thủ...", foreground=OPP_TURN_COLOR)

    def draw_piece(self, row, col, piece, highlight=False):
        x, y = col*CELL_SIZE+CELL_SIZE//2, row*CELL_SIZE+CELL_SIZE//2
        color = COLOR_O if piece == "O" else COLOR_X
        font = ("Arial", 22, "bold")
        if highlight:
            self.canvas.create_rectangle(col*CELL_SIZE, row*CELL_SIZE, (col+1)*CELL_SIZE, (row+1)*CELL_SIZE,
                                         fill=HIGHLIGHT_COLOR, outline="", tags="highlight")
        self.canvas.create_text(x, y, text=piece, font=font, fill=color, tags="piece")

    def animate_piece(self, row, col, piece):
        for _ in range(2):
            self.canvas.create_rectangle(col*CELL_SIZE, row*CELL_SIZE, (col+1)*CELL_SIZE, (row+1)*CELL_SIZE,
                                         fill=HIGHLIGHT_COLOR, outline="", tags="highlight")
            self.window.update()
            time.sleep(0.12)
            self.canvas.delete("highlight")
            self.window.update()
            time.sleep(0.12)
        self.redraw_pieces()

    def send_move(self, row, col):
        if self.server_addr:
            msg = f"MOVE|{row},{col}"
            self.sock.sendto(msg.encode(), self.server_addr)

    def listen_server(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
                msg = data.decode()
                
                if msg.startswith("START"):
                    _, role = msg.split("|")
                    self.role = role
                    self.turn = "X" 
                    self.game_over = False 
                    self.role_label.config(text=f"Bạn là {self.role}")
                    if self.role == "X":
                        self.status_label.config(text="Bạn đi trước!", foreground=MY_TURN_COLOR)
                    else:
                        self.status_label.config(text="Đối thủ đi trước!", foreground=OPP_TURN_COLOR)
                    messagebox.showinfo("Bắt đầu", f"Bạn là {self.role}. {'Bạn đi trước!' if self.role == 'X' else 'Đối thủ đi trước!'}")
                
                elif msg.startswith("MOVE"):
                    _, coords = msg.split("|")
                    row, col = map(int, coords.split(","))
                    opp = "O" if self.role == "X" else "X"
                    
                    if self.board[row][col] is None:
                        self.board[row][col] = opp
                        self.last_move = (row, col)
                        self.redraw_pieces()
                        self.animate_piece(row, col, opp)
                        win_line = self.check_win(row, col, opp)
                        if win_line:
                            self.game_over = True
                            self.win_line = win_line
                            self.redraw_pieces()
                            self.status_label.config(text="💥 Bạn đã thua rồi!", foreground=OPP_TURN_COLOR)
                            self.new_game_btn.config(state=tk.NORMAL)
                            messagebox.showinfo("Thua cuộc", "Đối thủ đã thắng trận này.")
                        else:
                            self.turn = self.role
                            self.status_label.config(text="Đến lượt của bạn!", foreground=MY_TURN_COLOR)
                
                elif msg == "OPPONENT_DISCONNECTED":
                    self.opponent_disconnected = True
                    self.status_label.config(text="Đối thủ đã thoát game!", foreground=OPP_TURN_COLOR)
                    self.new_game_btn.config(state=tk.NORMAL)
                    messagebox.showinfo("Thông báo", "Đối thủ đã thoát game!")
                
                elif msg == "NEW_GAME":
                    self.reset_game()
                    
            except Exception as e:
                print(f"Lỗi nhận tin nhắn: {e}")
                break

    def find_server_and_join(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(3)
        broadcast_addr = ('<broadcast>', BROADCAST_PORT)
        
        while not self.server_addr:
            try:
                sock.sendto(b"FIND_CARO_SERVER", broadcast_addr)
                data, addr = sock.recvfrom(1024)
                if data.decode() == "CARO_SERVER_HERE":
                    self.server_addr = (addr[0], PORT)
                    self.status_label.config(text="Đã kết nối với Server", foreground=MY_TURN_COLOR)
                    self.sock.sendto(b"JOIN_ROOM", self.server_addr)
                    time.sleep(0.5)
            except socket.timeout:
                continue
        sock.close()

    def check_win(self, row, col, piece):
        def is_valid(r, c): return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE
        opponent_piece = "O" if piece == "X" else "X"
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

        for dx, dy in directions:
            r1, c1 = row, col
            while is_valid(r1 - dx, c1 - dy) and self.board[r1 - dx][c1 - dy] == piece:
                r1 -= dx; c1 -= dy
            r2, c2 = row, col
            while is_valid(r2 + dx, c2 + dy) and self.board[r2 + dx][c2 + dy] == piece:
                r2 += dx; c2 += dy

            block_start = (r1 - dx, c1 - dy)
            block_end = (r2 + dx, c2 + dy)
            consecutive = []
            temp_r, temp_c = r1, c1
            while is_valid(temp_r, temp_c) and self.board[temp_r][temp_c] == piece:
                consecutive.append((temp_r, temp_c))
                temp_r += dx; temp_c += dy
            if len(consecutive) >= 5:
                if len(consecutive) == 5:
                    if (is_valid(block_start[0], block_start[1]) and self.board[block_start[0]][block_start[1]] == opponent_piece) and \
                       (is_valid(block_end[0], block_end[1]) and self.board[block_end[0]][block_end[1]] == opponent_piece):
                        continue
                return consecutive
        return None

    def highlight_win_line(self, win_line):
        for (row, col) in win_line:
            self.canvas.create_rectangle(col*CELL_SIZE, row*CELL_SIZE, (col+1)*CELL_SIZE, (row+1)*CELL_SIZE,
                                         outline="#ff8f00", width=4, tags="highlight")

    def reset_game(self):
        self.board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.game_over = False
        self.opponent_disconnected = False
        self.last_move = None
        self.win_line = None
        self.canvas.delete("all")
        self.draw_board()
        self.turn = "X"
        if self.role == "X":
            self.status_label.config(text="Bạn đi trước!", foreground=MY_TURN_COLOR)
        else:
            self.status_label.config(text="Đối thủ đi trước!", foreground=OPP_TURN_COLOR)
        self.new_game_btn.config(state=tk.DISABLED)

    def new_game(self):
        if self.server_addr:
            self.sock.sendto(b"NEW_GAME", self.server_addr)
            self.reset_game()

    def exit_game(self):
        if self.server_addr:
            self.sock.sendto(b"EXIT", self.server_addr)
        self.window.destroy()

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    CaroClientMulti().run()
