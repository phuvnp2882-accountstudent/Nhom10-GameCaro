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
