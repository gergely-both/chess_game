import chess_utils.board_params as bp
import tkinter as tk
from collections import namedtuple
from enum import Enum
from itertools import cycle, chain
import os


RESOURCE_PATH = "chess_pieces/"


#########################################
# MODEL
#########################################

NumberedEquivalent = namedtuple("NumberedEuivalent", ["x", "y"])


class Square:
    def __init__(self, name, coordinates, central_coordinates, numbered_equivalent):
        self.name = name
        self.coordinates = coordinates
        self.central_coordinates = central_coordinates
        self.numbered_equivalent = numbered_equivalent

    def __repr__(self):
        return self.name

    @classmethod
    def repr_lettered(cls, num_pair):
        """returns sqaure name from numeric equivalent"""
        if len(num_pair) == 2:
            for obj in squares_obj.values():
                if obj.numbered_equivalent == num_pair:
                    return obj

    @classmethod
    def detect_square(cls, coordinates):
        """detects square by clicked coordinates"""
        for square, obj in squares_obj.items():
            if coordinates in obj.coordinates:
                return obj

    @classmethod
    def square_not_owned(cls, square):
        """scans if square is (already) occupied by own piece"""
        for dict_figure, dict_square in figures_and_squares.items():
            if square is dict_square and dict_figure.color is cls.game_instance.chosen_figure.color:
                return False
        return True


class Color(Enum):
    BLACK = 0
    WHITE = 1


class Figure:
    def __init__(self, color, kind, name, number):
        self.color: Color = color
        self.kind: str = kind
        self.name: str = name
        self.number: int = number
    
    def __repr__(self):
        color = str(self.color).split(".")[1].lower()
        return f"{color}_{self.kind}_{self.number}"

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        return hash(self) == hash(other)

    def passage_free(self, initial, target, positions_dict):
        """scans if any square between initial and target occupied by any side's piece"""
        x = list(range(initial.x + 1, target.x) or range(initial.x - 1, target.x, -1))
        y = list(range(initial.y + 1, target.y) or range(initial.y - 1, target.y, -1))
        if x and y:
            xy = list(zip(x, y))
            for num_pair in xy:
                if Square.repr_lettered(num_pair) in positions_dict.values():
                    return False
        elif x or y:
            xy = list(zip(cycle([target.x]), y) if len(x) < len(y) else zip(x, cycle([target.y])))
            for num_pair in xy:
                if Square.repr_lettered(num_pair) in positions_dict.values():
                    return False
        return True

    @classmethod
    def detect_figure(cls, selected_square):
        """detects piece by selected square"""
        for figure, square in figures_and_squares.items():
            if selected_square is square:
                return figure

    def detect_enemy(self, selected_square):
        return enemy_piece if ((enemy_piece := Figure.detect_figure(selected_square)) and enemy_piece.color != self.color) else None


class Pawn(Figure):
    def __init__(self, color, kind, name, number):
        super().__init__(color, kind, name, number)

    def validate_move(self, initial_square, target_square, positions_dict):
        """validates pawn moves: colors: initial double move / simple move / capturing: simple / en passant"""
        initial, target = initial_square.numbered_equivalent, target_square.numbered_equivalent
        if self.color == Color.WHITE:
            if initial.y == 2 and target.y == 4 and initial.x == target.x \
                    and target_square not in positions_dict.values() \
                    and self.passage_free(initial, target, positions_dict):
                return True
            elif initial.y >= 2 and target.y - initial.y == 1 and initial.x == target.x \
                    and target_square not in positions_dict.values():
                return True
            elif target.y - initial.y == 1 and abs(target.x - initial.x) == 1:
                if self.detect_enemy(target_square):
                    return True
                elif initial.y == 5:
                    enpass_location = Square.repr_lettered((target.x, target.y - 1))
                    enpass_enemy = self.detect_enemy(enpass_location)
                    if enpass_enemy and isinstance(enpass_enemy, Pawn) and {enpass_enemy, str(starting_figs_squares[enpass_enemy])}.issubset(self.game_instance.log[-1]):
                        self.game_instance.enpass_enemy = enpass_enemy
                        return True
        elif self.color == Color.BLACK:
            if initial.y == 7 and target.y == 5 and initial.x == target.x \
                    and target_square not in positions_dict.values() and self.passage_free(initial, target, positions_dict):
                return True
            elif initial.y <= 7 and initial.y - target.y == 1 and initial.x == target.x \
                    and target_square not in positions_dict.values():
                return True
            elif initial.y - target.y == 1 and abs(target.x - initial.x) == 1:
                if self.detect_enemy(target_square):
                    return True
                elif initial.y == 4:
                    enpass_location = Square.repr_lettered((target.x, target.y + 1))
                    enpass_enemy = self.detect_figure(enpass_location)
                    if enpass_enemy and isinstance(enpass_enemy, Pawn) and {enpass_enemy, str(starting_figs_squares[enpass_enemy])}.issubset(self.game_instance.log[-1]):
                        self.game_instance.enpass_enemy = enpass_enemy
                        return True


class King(Figure):
    def __init__(self, color, kind, name, number):
        super().__init__(color, kind, name, number)

    def validate_move(self, initial_square, target_square, positions_dict):
        """simple king move / user-selected castling (not-offensive so not calculated as such): short, long"""
        # NOTE: can not castle from check, through it (both checked below), nor into it (checked back in main cycle later), also entire passage must be free
        initial, target = initial_square.numbered_equivalent, target_square.numbered_equivalent
        if abs(target.x - initial.x) <= 1 and abs(target.y - initial.y) <= 1:
            return True
        elif self == self.game_instance.chosen_figure and abs(target.x - initial.x) == 2 and target.y - initial.y == 0:
            if self.game_instance.chosen_figure not in chain(*self.game_instance.log) and self.in_safety(self.game_instance.chosen_figure, target_square=self.game_instance.initial_square):
                if target.x > initial.x:
                    castle_midpoint_square = Square.repr_lettered((target.x - 1, target.y))
                    if self.game_instance.chosen_figure.color == Color.WHITE and "white_rook_2" not in chain(*self.game_instance.log) and "white_rook_2" in positions_dict:
                        rook_position_num = figures_and_squares["white_rook_2"].numbered_equivalent
                    elif self.game_instance.chosen_figure.color == Color.BLACK and "black_rook_2" not in chain(*self.game_instance.log) and "black_rook_2" in positions_dict:
                        rook_position_num = figures_and_squares["black_rook_2"].numbered_equivalent
                    else:
                        return False
                elif target.x < initial.x:
                    castle_midpoint_square = Square.repr_lettered((target.x + 1, target.y))
                    if self.game_instance.chosen_figure.color == Color.WHITE and "white_rook_1" not in chain(*self.game_instance.log) and "white_rook_1" in positions_dict:
                        rook_position_num = figures_and_squares["white_rook_1"].numbered_equivalent
                    elif self.game_instance.chosen_figure.color == Color.BLACK and "black_rook_1" not in chain(*self.game_instance.log) and "black_rook_1" in positions_dict:
                        rook_position_num = figures_and_squares["black_rook_1"].numbered_equivalent
                    else:
                        return False

                if self.passage_free(initial, rook_position_num, positions_dict) and self.in_safety(self.game_instance.chosen_figure, target_square=castle_midpoint_square):
                    return True

    @classmethod
    def in_safety(cls, chosen_figure, target_square):
        """scans whether moving piece to target square threatens own king"""
        projected_positions = figures_and_squares.copy()

        attacked_piece = chosen_figure.detect_enemy(target_square)
        if attacked_piece and attacked_piece in projected_positions:
            del projected_positions[attacked_piece]
        projected_positions[chosen_figure] = target_square

        if chosen_figure.color == Color.WHITE:
            for figure in projected_positions:
                if figure.color == Color.BLACK and figure.validate_move(projected_positions[figure], projected_positions["white_king_1"], projected_positions):
                    return False
        elif chosen_figure.color == Color.BLACK:
            for figure in projected_positions:
                if figure.color == Color.WHITE and figure.validate_move(projected_positions[figure], projected_positions["black_king_1"], projected_positions):
                    return False
        return True


class Rook(Figure):
    def __init__(self, color, kind, name, number):
        super().__init__(color, kind, name, number)

    def validate_move(self, initial_square, target_square, positions_dict):
        """validates rook moves"""
        initial, target = initial_square.numbered_equivalent, target_square.numbered_equivalent
        return (target.x - initial.x == 0 or target.y - initial.y == 0) and self.passage_free(initial, target, positions_dict)


class Bishop(Figure):
    def __init__(self, color, kind, name, number):
        super().__init__(color, kind, name, number)

    def validate_move(self, initial_square, target_square, positions_dict):
        """validates bishop moves"""
        initial, target = initial_square.numbered_equivalent, target_square.numbered_equivalent
        return abs(target.x - initial.x) == abs(target.y - initial.y) and self.passage_free(initial, target, positions_dict)


class Queen(Figure):
    def __init__(self, color, kind, name, number):
        super().__init__(color, kind, name, number)

    def validate_move(self, initial_square, target_square, positions_dict):
        """validates queen moves"""
        initial, target = initial_square.numbered_equivalent, target_square.numbered_equivalent
        return ((target.x - initial.x == 0 or target.y - initial.y == 0) and self.passage_free(initial, target, positions_dict)) \
            or (abs(target.x - initial.x) == abs(target.y - initial.y) and self.passage_free(initial, target, positions_dict))


class Knight(Figure):
    def __init__(self, color, kind, name, number):
        super().__init__(color, kind, name, number)

    def validate_move(self, initial_square, target_square, positions_dict):
        """validates knight moves"""
        initial, target = initial_square.numbered_equivalent, target_square.numbered_equivalent
        return abs(target.x - initial.x) in {1, 2} and abs(target.x - initial.x) + abs(target.y - initial.y) == 3


# GENERATING OBJECTS FROM STRINGS INTO MULTIPLE REFERENCE DICTS; SAVING COPY FOR STARTING LAYOUT
squares_obj = {}
for square, coordinates in bp.squares_and_coordinates.items():
    central_coordinates = bp.square_centres[square]
    numbered_equivalent = NumberedEquivalent(bp.numeric_equivalent[square[0]], int(square[1]))
    squares_obj[square] = Square(square, coordinates, central_coordinates, numbered_equivalent)

figures_obj = {}
for piece in bp.pieces_and_positions:
    attributes = piece.split("_")
    color, kind, number = attributes[0], attributes[1], int(attributes[2])
    name = color + "_" + kind
    if kind == "pawn":
        figures_obj[piece] = Pawn(Color[color.upper()], kind, name, number)
    elif kind == "king":
        figures_obj[piece] = King(Color[color.upper()], kind, name, number)
    elif kind == "rook":
        figures_obj[piece] = Rook(Color[color.upper()], kind, name, number)
    elif kind == "bishop":
        figures_obj[piece] = Bishop(Color[color.upper()], kind, name, number)
    elif kind == "queen":
        figures_obj[piece] = Queen(Color[color.upper()], kind, name, number)
    elif kind == "knight":
        figures_obj[piece] = Knight(Color[color.upper()], kind, name, number)

starting_figs_squares = {}
for piece, position in bp.pieces_and_positions.items():
    figure = figures_obj[piece]
    square = squares_obj[position]
    starting_figs_squares[figure] = square

figures_and_squares = starting_figs_squares.copy()


#########################################
# VIEW
#########################################

class Board:
    def __init__(self, master):
        self.master = master
        self.master.title("Chess Game")
        self.master.geometry(f"{bp.TILES_PER_SIDE * bp.TILE_LENGTH}x{bp.TILES_PER_SIDE * bp.TILE_LENGTH}")
        self.master.resizable(False, False)
        self.canvas = tk.Canvas(master=master, width=bp.TILES_PER_SIDE * bp.TILE_LENGTH, height=bp.TILES_PER_SIDE * bp.TILE_LENGTH, highlightthickness=0)

        for i in range(0, bp.TILES_PER_SIDE*bp.TILE_LENGTH, 2*bp.TILE_LENGTH):
            for j in range(0, bp.TILES_PER_SIDE*bp.TILE_LENGTH, 2*bp.TILE_LENGTH):
                for k in range(0, bp.TILES_PER_SIDE*bp.TILE_LENGTH, bp.TILE_LENGTH):
                    self.canvas.create_rectangle(i+k, j+k, bp.TILE_LENGTH+i+k, bp.TILE_LENGTH+j+k, fill=bp.LIGHT_COLOR)
                    self.canvas.create_rectangle((bp.TILES_PER_SIDE*bp.TILE_LENGTH)-i-k, j+k, ((bp.TILES_PER_SIDE-1)*bp.TILE_LENGTH)-i-k, bp.TILE_LENGTH+j+k, fill=bp.DARK_COLOR)
        
        self.canvas.pack()

        self.img_files = os.listdir(RESOURCE_PATH)
        self.imgname_relpath = {os.path.splitext(k)[0]: RESOURCE_PATH + k for k in self.img_files}
        for img in self.imgname_relpath:
            setattr(self, img, tk.PhotoImage(file=self.imgname_relpath[img]))
        for figure, square in figures_and_squares.items():  
            setattr(self, str(figure), self.canvas.create_image(square.central_coordinates, image=getattr(self, figure.name)))

        self.game_instance = None

    def click(self, event, game):
        """establishes contact between types for mutual reference; dispatches GUI event to controller unit"""
        self.game_instance = game
        Figure.game_instance = game
        Square.game_instance = game
        game.board_instance = self

        selected_coordinates = event.x, event.y
        game.select_square(selected_coordinates)

    def show_possibilities(self):
        """creates possibility-showing canvas objects and their ids"""
        game = self.game_instance
        possible_squares = []
        for square, obj in squares_obj.items():
            target_square = obj

            if game.chosen_figure.validate_move(game.initial_square, target_square, figures_and_squares) and King.in_safety(game.chosen_figure, target_square) and Square.square_not_owned(target_square):
                origo = target_square.central_coordinates
                radius = bp.TILE_LENGTH // 8
                fill = "green" if game.turn % 2 != 0 else "purple"
                setattr(self, square, self.canvas.create_oval(origo[0] - radius, origo[1] - radius, origo[0] + radius, origo[1] + radius, fill=fill))
                possible_squares.append(target_square)
                game.enpass_enemy = None
        if not possible_squares:
            game.chosen_figure = None
            game.initial_square = None

    def hide_possibilities(self):
        """deletes possibility-showing canvas objects by ids"""
        for square in squares_obj:
            try:
                self.canvas.delete(getattr(self, str(square)))
            except AttributeError:
                continue


#########################################
# CONTROLLER
#########################################

class Game:
    def __init__(self):
        self.board_instance = None
        self.turn = 1
        self.chosen_figure = None
        self.initial_square = None
        self.attacked_figure = None
        self.enpass_enemy = None
        self.promote_piece = None
        self.promote_at = None
        self.log = []

    def detect_turn(self):
        """returns current turn's color"""
        if self.turn % 2 == 0:
            return Color.BLACK
        else:
            return Color.WHITE

    def choose_piece(self, selected_square):
        """finds own piece to move, select attacked piece if own piece selected already"""
        if (detected_figure := Figure.detect_figure(selected_square)):
            if self.detect_turn() is detected_figure.color:
                self.initial_square = selected_square
                self.chosen_figure = detected_figure
                return True
            elif self.chosen_figure:
                self.attacked_figure = detected_figure

    def select_square(self, selected_coordinates):
        """main cycle for selecting squares, pieces, showing options, validating then making moves, log and reset"""
        selected_square = Square.detect_square(selected_coordinates)
        if self.chosen_figure:
            self.board_instance.hide_possibilities()
            target_square = selected_square
            if not self.choose_piece(selected_square):
                if self.chosen_figure.validate_move(self.initial_square, target_square, figures_and_squares) \
                        and King.in_safety(self.chosen_figure, target_square):
                    self.make_move(target_square)
                    self.log.append([self.turn, str(self.chosen_figure), str(self.initial_square), str(target_square)])
                    self.turn += 1
            self.chosen_figure = None
            self.initial_square = None
            self.attacked_figure = None
            self.enpass_enemy = None
        elif self.choose_piece(selected_square):
            self.board_instance.show_possibilities()

    def promote_to(self, img_name, query_window):
        """references figure to promote, its destination, and the desired new figure object"""
        del figures_and_squares[self.promote_piece]
        self.board_instance.canvas.delete(getattr(self.board_instance, str(self.promote_piece)))
        
        new_piece_attrs = img_name.split("_")
        new_piece_color, new_piece_kind = new_piece_attrs[0], new_piece_attrs[1]
        new_piece_name = new_piece_color + "_" + new_piece_kind

        occupied_numbers = []
        for figure in figures_and_squares:
            if figure.name == new_piece_name:
                occupied_numbers.append(figure.number)
        new_piece_number = max(occupied_numbers) + 1

        if new_piece_kind == "rook":
            new_piece = Rook(Color[new_piece_color.upper()], new_piece_kind, new_piece_name, new_piece_number)
        elif new_piece_kind == "bishop":
            new_piece = Bishop(Color[new_piece_color.upper()], new_piece_kind, new_piece_name, new_piece_number)
        elif new_piece_kind == "queen":
            new_piece = Queen(Color[new_piece_color.upper()], new_piece_kind, new_piece_name, new_piece_number)
        elif new_piece_kind == "knight":
            new_piece = Knight(Color[new_piece_color.upper()], new_piece_kind, new_piece_name, new_piece_number)

        setattr(self.board_instance, str(new_piece), self.board_instance.canvas.create_image(self.promote_at.central_coordinates, image=getattr(self.board_instance, img_name)))
        figures_and_squares[new_piece] = self.promote_at

        self.promote_piece = None
        self.promote_at = None
        query_window.destroy()

    def make_move(self, target_square):
        """removes captured figure from positions dict, makes move, dispatches to promotion, executes castling"""
        initial, target = self.initial_square.numbered_equivalent, target_square.numbered_equivalent
        x = (target.x - initial.x) * bp.TILE_LENGTH
        y = (initial.y - target.y) * bp.TILE_LENGTH
        if self.attacked_figure:
            del figures_and_squares[self.attacked_figure]
            self.board_instance.canvas.delete(getattr(self.board_instance, str(self.attacked_figure)))
        elif self.enpass_enemy:
            del figures_and_squares[self.enpass_enemy]
            self.board_instance.canvas.delete(getattr(self.board_instance, str(self.enpass_enemy)))
        self.board_instance.canvas.move(getattr(self.board_instance, str(self.chosen_figure)), x, y)
        figures_and_squares[self.chosen_figure] = target_square

        if (self.chosen_figure.name == "white_pawn" and target.y == 8) or (self.chosen_figure.name == "black_pawn" and target.y == 1):
            promotion_query = tk.Toplevel()
            promotion_query.title("*PROMOTION*")
            tk.Label(master=promotion_query, text="Select the promotion grade: ").grid(column=1, row=0, columnspan=2)
            counter = 0
            for img_name in self.board_instance.imgname_relpath:
                if "pawn" not in img_name and "king" not in img_name:
                    if (self.chosen_figure.color == Color.WHITE and "white" in img_name) or (self.chosen_figure.color == Color.BLACK and "black" in img_name):
                        tk.Button(master=promotion_query, image=getattr(self.board_instance, img_name), command=lambda img_name=img_name: self.promote_to(img_name, promotion_query)).grid(column=counter, row=1)
                        counter += 1
            self.promote_piece = self.chosen_figure
            self.promote_at = target_square

        elif str(self.chosen_figure) == "white_king_1" and abs(target.x - initial.x) == 2:
            if target.x - initial.x == 2:
                self.board_instance.canvas.move(self.board_instance.white_rook_2, -2 * bp.TILE_LENGTH, 0)
                figures_and_squares["white_rook_2"] = squares_obj["f1"]
            elif target.x - initial.x == -2:
                self.board_instance.canvas.move(self.board_instance.white_rook_1, 3 * bp.TILE_LENGTH, 0)
                figures_and_squares["white_rook_1"] = squares_obj["d1"]
        elif str(self.chosen_figure) == "black_king_1" and abs(target.x - initial.x) == 2:
            if target.x - initial.x == 2:
                self.board_instance.canvas.move(self.board_instance.black_rook_2, -2 * bp.TILE_LENGTH, 0)
                figures_and_squares["black_rook_2"] = squares_obj["f8"]
            elif target.x - initial.x == -2:
                self.board_instance.canvas.move(self.board_instance.black_rook_1, 3 * bp.TILE_LENGTH, 0)
                figures_and_squares["black_rook_1"] = squares_obj["d8"]
