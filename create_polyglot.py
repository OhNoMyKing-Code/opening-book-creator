import chess
import chess.polyglot
import chess.engine

MAX_BOOK_WEIGHT = 1000

def format_zobrist_key_hex(zobrist_key):
    return f"{zobrist_key:016x}"

class BookMove:
    def __init__(self, move, weight=0):
        self.move = move
        self.weight = weight

class BookPosition:
    def __init__(self):
        self.moves = {}

    def add_move(self, move, weight):
        uci = move.uci()
        if uci not in self.moves:
            self.moves[uci] = BookMove(move, weight)
        else:
            self.moves[uci].weight += weight

class Book:
    def __init__(self):
        self.positions = {}

    def get_position(self, key):
        if key not in self.positions:
            self.positions[key] = BookPosition()
        return self.positions[key]

    def save_as_polyglot(self, path):
        with open(path, "wb") as f:
            entries = []
            for key_hex, pos in self.positions.items():
                zbytes = bytes.fromhex(key_hex)
                for bm in pos.moves.values():
                    move = bm.move
                    mi = move.to_square + (move.from_square << 6)
                    if move.promotion:
                        mi += ((move.promotion - 1) << 12)

                    mbytes = mi.to_bytes(2, "big")
                    wbytes = bm.weight.to_bytes(2, "big")
                    lbytes = (0).to_bytes(4, "big")
                    entries.append(zbytes + mbytes + wbytes + lbytes)

            for entry in entries:
                f.write(entry)

def build_book_from_fen(fen, engine_path, book_path, depth=12):
    board = chess.Board(fen)
    book = Book()

    with chess.engine.SimpleEngine.popen_uci(engine_path) as engine:
        result = engine.analyse(board, chess.engine.Limit(depth=depth))
        best_move = result["pv"][0]  # lấy best move
        key_hex = format_zobrist_key_hex(chess.polyglot.zobrist_hash(board))
        pos = book.get_position(key_hex)
        pos.add_move(best_move, MAX_BOOK_WEIGHT)

    book.save_as_polyglot(book_path)
    print(f"Book saved -> {book_path}")

if __name__ == "__main__":
    fen = "rnbqkbnr/pp1p1ppp/2p1p3/8/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 1"
    build_book_from_fen(fen, "stockfish", "fenbook.bin")
