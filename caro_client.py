import socket
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import time

BOARD_SIZE = 15
CELL_SIZE = 32
PORT = 5002
BROADCAST_PORT = 5001

HIGHLIGHT_COLOR = "#fff59d"  # vàng nhạt
BG_COLOR = "#e3f2fd"  # xanh nhạt
MY_TURN_COLOR = "#388e3c"  # xanh lá
OPP_TURN_COLOR = "#d32f2f"  # đỏ
  
  
   def __init__(self):
        self.window = tk.Tk()
        self.window.title("Game Caro")
        self.window.resizable(False, False)
        
        # Tạo frame chính
        self.main_frame = ttk.Frame(self.window, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame thông tin
        self.info_frame = ttk.Frame(self.main_frame)
        self.info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_label = ttk.Label(self.info_frame, text="Đang tìm server...", font=("Arial", 12, "bold"))
        self.status_label.pack(side=tk.LEFT)
        
        self.role_label = ttk.Label(self.info_frame, text="", font=("Arial", 12, "bold"))
        self.role_label.pack(side=tk.RIGHT)
        
        # Frame bàn cờ
        self.board_frame = ttk.Frame(self.main_frame)
        self.board_frame.pack()
        
        self.canvas = tk.Canvas(self.board_frame, width=BOARD_SIZE*CELL_SIZE, height=BOARD_SIZE*CELL_SIZE, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack()
        
        # Frame điều khiển
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.new_game_btn = ttk.Button(self.control_frame, text="Chơi lại", command=self.new_game, state=tk.DISABLED)
        self.new_game_btn.pack(side=tk.LEFT)
        
        self.exit_btn = ttk.Button(self.control_frame, text="Thoát", command=self.exit_game)
        self.exit_btn.pack(side=tk.RIGHT)
        
        # Khởi tạo biến game
        self.board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.turn = None
        self.role = None



         self.game_over = False
        self.opponent_disconnected = False
        self.last_move = None
        self.win_line = None

        # Bind events
        self.canvas.bind("<Button-1>", self.handle_click)
        self.window.protocol("WM_DELETE_WINDOW", self.exit_game)
        
        # Vẽ bàn cờ
        self.draw_board()
        
        # Khởi tạo socket và threads
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", 0))
        
        threading.Thread(target=self.find_server_and_join, daemon=True).start()
        threading.Thread(target=self.listen_server, daemon=True).start()
  self.canvas.delete("grid")
        for i in range(BOARD_SIZE):
            self.canvas.create_line(i*CELL_SIZE, 0, i*CELL_SIZE, BOARD_SIZE*CELL_SIZE, fill="gray", tags="grid")
            self.canvas.create_line(0, i*CELL_SIZE, BOARD_SIZE*CELL_SIZE, i*CELL_SIZE, fill="gray", tags="grid")
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
      def draw_piece(self, row, col, piece, highlight=False):
        x, y = col*CELL_SIZE+CELL_SIZE//2, row*CELL_SIZE+CELL_SIZE//2
        color = "red" if piece == "O" else "blue"
        font = ("Arial", 22, "bold")
        if highlight:
            self.canvas.create_rectangle(col*CELL_SIZE, row*CELL_SIZE, (col+1)*CELL_SIZE, (row+1)*CELL_SIZE, fill=HIGHLIGHT_COLOR, outline="", tags="highlight")
        self.canvas.create_text(x, y, text=piece, font=font, fill=color, tags="piece")

    def animate_piece(self, row, col, piece):
        for _ in range(2):
            self.canvas.create_rectangle(col*CELL_SIZE, row*CELL_SIZE, (col+1)*CELL_SIZE, (row+1)*CELL_SIZE, fill=HIGHLIGHT_COLOR, outline="", tags="highlight")
            self.window.update()
            time.sleep(0.12)
            self.canvas.delete("highlight")
            self.window.update()
            time.sleep(0.12)
        self.redraw_pieces()
